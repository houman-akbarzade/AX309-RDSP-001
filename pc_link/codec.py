"""S02/R1 laboratory wire codec. No FPGA RTL or physical serial I/O."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import struct
import zlib

SOF = bytes.fromhex("a55ac33c")
VERSION = 1
MAX_PAYLOAD = 512
FRAME_OVERHEAD = 17
SID_BYTES = 16
ACTIVE_FLAGS = 1


class PacketError(ValueError):
    """Invalid frame or application payload."""


class Type(IntEnum):
    COMMAND = 1
    IQ_UPLOAD = 2
    STAGE_REQUEST = 3
    STAGE_DATA = 4
    RESULT = 5
    ACK = 6
    NACK = 7
    STATUS = 8
    SESSION_CONTROL = 9


class SessionOp(IntEnum):
    HELLO = 1
    OFFER = 2
    ACTIVATE = 3
    READY = 4


class Command(IntEnum):
    OPEN_CPI = 1
    REQUEST_INPUT_READBACK = 2
    HOST_VERIFIED_INPUT = 3
    RUN_CPI = 4
    QUERY_CPI_STATUS = 5
    RELEASE_CPI = 6
    RECOVER_UNKNOWN = 7


class Status(IntEnum):
    UPLOAD_OPEN = 1
    UPLOAD_COMPLETE_UNVERIFIED = 2
    INPUT_VERIFIED = 3
    PROCESSING = 4
    RESULT_STREAM_START = 5
    CPI_COMMIT = 6
    CPI_ABORT = 7
    TERMINAL_RECONCILED = 8


@dataclass(frozen=True)
class Frame:
    type: Type
    seq: int
    payload: bytes
    flags: int = ACTIVE_FLAGS
    version: int = VERSION

    def encode(self) -> bytes:
        if not 0 <= self.seq <= 0xFFFFFFFF:
            raise PacketError("sequence out of range")
        if len(self.payload) > MAX_PAYLOAD:
            raise PacketError("payload exceeds 512")
        if self.version != VERSION or self.flags not in (0, ACTIVE_FLAGS):
            raise PacketError("unsupported version or flags")
        if (self.type == Type.SESSION_CONTROL) != (self.flags == 0):
            raise PacketError("bootstrap and active flags must not mix")
        if self.type == Type.SESSION_CONTROL and self.seq != 0:
            raise PacketError("bootstrap sequence must be zero")
        header = struct.pack("<BBBIH", self.version, int(self.type), self.flags,
                             self.seq, len(self.payload))
        data = header + self.payload
        return SOF + data + struct.pack("<I", zlib.crc32(data))

    @classmethod
    def decode(cls, raw: bytes) -> "Frame":
        if len(raw) < FRAME_OVERHEAD or raw[:4] != SOF:
            raise PacketError("bad SOF or truncated header")
        version, kind, flags, seq, length = struct.unpack_from("<BBBIH", raw, 4)
        if version != VERSION or length > MAX_PAYLOAD:
            raise PacketError("bad version or payload length")
        if len(raw) != FRAME_OVERHEAD + length:
            raise PacketError("truncated or overlong frame")
        if zlib.crc32(raw[4:-4]) != struct.unpack_from("<I", raw, len(raw) - 4)[0]:
            raise PacketError("CRC32 mismatch")
        try:
            t = Type(kind)
        except ValueError as exc:
            raise PacketError("unknown TYPE") from exc
        f = cls(t, seq, raw[13:-4], flags, version)
        if f.encode() != raw:
            raise PacketError("bad flags or bootstrap sequence")
        return f


class StreamParser:
    """Incremental SOF/length/CRC parser. Reset partial data on byte timeout."""

    def __init__(self):
        self.buffer = bytearray()
        self.rejected = 0

    def reset_partial(self) -> None:
        self.buffer.clear()

    def feed(self, data: bytes) -> list[Frame]:
        self.buffer.extend(data)
        found = []
        while True:
            start = self.buffer.find(SOF)
            if start < 0:
                if len(self.buffer) > len(SOF) - 1:
                    del self.buffer[:-(len(SOF) - 1)]
                break
            if start:
                del self.buffer[:start]
            if len(self.buffer) < 13:
                break
            version, kind, flags, _, length = struct.unpack_from("<BBBIH", self.buffer, 4)
            if version != VERSION or length > MAX_PAYLOAD or flags not in (0, 1) or kind not in set(Type):
                self.rejected += 1
                del self.buffer[0]
                continue
            size = FRAME_OVERHEAD + length
            if len(self.buffer) < size:
                break
            raw = bytes(self.buffer[:size])
            try:
                f = Frame.decode(raw)
            except PacketError:
                self.rejected += 1
                del self.buffer[0]
                continue
            del self.buffer[:size]
            found.append(f)
        return found


def check_sid(sid: bytes) -> bytes:
    if len(sid) != SID_BYTES or sid == bytes(SID_BYTES):
        raise PacketError("SID must be a nonzero opaque 16-byte value")
    return sid


def active_payload(sid: bytes, content: bytes) -> bytes:
    return check_sid(sid) + content


def split_active(frame: Frame, sid: bytes) -> bytes:
    if frame.flags != ACTIVE_FLAGS or len(frame.payload) < SID_BYTES:
        raise PacketError("active frame lacks session prefix")
    if frame.payload[:SID_BYTES] != check_sid(sid):
        raise PacketError("stale/wrong link epoch")
    return frame.payload[SID_BYTES:]


def snapshot_valid(kind: int, valid: int, cpi: int, info: int) -> bool:
    return (kind in range(5) and valid in (0, 1) and
            ((kind == 0 and valid == 0 and cpi == 0 and info == 0) or
             (kind in range(1, 5) and valid == 1 and
              (kind != 1 or info == 0) and
              (kind not in (2, 4) or info <= 702))))


def session_payload(op: SessionOp, sid: bytes, *, mode: int = 0,
                    prior_valid: int = 0, cpi_id: int = 0,
                    kind: int = 0, cpi_valid: int = 0,
                    info: int = 0, result: int = 0) -> bytes:
    check_sid(sid)
    if op == SessionOp.HELLO:
        if mode not in (0, 1) or prior_valid not in (0, 1):
            raise PacketError("bad HELLO mode/valid")
        return struct.pack("<BB16sBBI", op, 1, sid, mode, prior_valid, cpi_id)
    if op == SessionOp.OFFER:
        return struct.pack("<BB16sBBIH", op, 1, sid, kind, cpi_valid, cpi_id, info)
    if op == SessionOp.ACTIVATE:
        return struct.pack("<BB16sBBBIH", op, 1, sid, mode, kind, cpi_valid, cpi_id, info)
    if op == SessionOp.READY:
        return struct.pack("<BB16sBBBIH", op, 1, sid, result, kind, cpi_valid, cpi_id, info)
    raise PacketError("unknown handshake opcode")


def parse_session(frame: Frame) -> tuple[SessionOp, dict]:
    if frame.type != Type.SESSION_CONTROL or frame.flags != 0 or frame.seq != 0:
        raise PacketError("not bootstrap SESSION_CONTROL")
    payload = frame.payload
    if len(payload) not in (24, 26, 27) or len(payload) < 2 or payload[1] != 1:
        raise PacketError("bad handshake revision/length")
    try:
        op = SessionOp(payload[0])
    except ValueError as exc:
        raise PacketError("bad handshake opcode") from exc
    fmts = {SessionOp.HELLO: "<BB16sBBI", SessionOp.OFFER: "<BB16sBBIH",
            SessionOp.ACTIVATE: "<BB16sBBBIH", SessionOp.READY: "<BB16sBBBIH"}
    if len(payload) != struct.calcsize(fmts[op]):
        raise PacketError("handshake opcode/length mismatch")
    a = struct.unpack(fmts[op], payload)
    check_sid(a[2])
    if op == SessionOp.HELLO:
        _, _, sid, mode, valid, cpi = a
        if mode not in (0, 1) or valid not in (0, 1) or (not valid and cpi):
            raise PacketError("invalid HELLO request")
        return op, dict(sid=sid, mode=mode, prior_valid=valid, cpi_id=cpi)
    if op == SessionOp.OFFER:
        _, _, sid, kind, valid, cpi, info = a
        if not snapshot_valid(kind, valid, cpi, info):
            raise PacketError("invalid OFFER snapshot")
        return op, dict(sid=sid, kind=kind, valid=valid, cpi_id=cpi, info=info)
    _, _, sid, first, kind, valid, cpi, info = a
    if not snapshot_valid(kind, valid, cpi, info):
        raise PacketError("invalid ACTIVATE/READY snapshot")
    if op == SessionOp.ACTIVATE and first not in (0, 1):
        raise PacketError("bad ACTIVATE mode")
    if op == SessionOp.READY and first not in (0, 1, 2):
        raise PacketError("bad READY result")
    return op, dict(sid=sid, first=first, kind=kind, valid=valid, cpi_id=cpi, info=info)


def bootstrap(op: SessionOp, sid: bytes, **kw) -> bytes:
    return Frame(Type.SESSION_CONTROL, 0, session_payload(op, sid, **kw), 0).encode()

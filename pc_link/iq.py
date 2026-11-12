"""Deterministic IQ byte vectors, upload/readback, and 99-bit grouping records."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import struct
from .codec import PacketError

PULSES = 33
SAMPLES = 128
CPI_SIZE = PULSES * SAMPLES * 4
IQ_CHUNK = 488
READBACK_CHUNK = 484
RECORD_BYTES = 13
RECORD_BITS = 99
MAX_RECORDS_PACKET = 8


def synthetic_iq() -> bytes:
    """Pure integer fixture, NOT a radar waveform or S04 numeric validation."""
    data = bytearray()
    for m in range(PULSES):
        for n in range(SAMPLES):
            i = ((m * 257 + n * 31 + 19) % 65536) - 32768
            q = ((m * 433 + n * 53 + 97) % 65536) - 32768
            data.extend(struct.pack("<hh", i, q))
    assert len(data) == CPI_SIZE
    return bytes(data)


def upload_chunks(cpi_id: int, raw: bytes):
    if len(raw) != CPI_SIZE:
        raise PacketError("IQ CPI must have exactly 16896 bytes")
    for offset in range(0, len(raw), IQ_CHUNK):
        yield struct.pack("<II", cpi_id, offset) + raw[offset:offset + IQ_CHUNK]


class IQAssembler:
    def __init__(self, cpi_id: int):
        self.cpi_id = cpi_id
        self.data = bytearray(CPI_SIZE)
        self.next_offset = 0
        self.packets = 0
        self.verified = False

    def accept(self, body: bytes) -> None:
        if len(body) < 12 or len(body) > 8 + IQ_CHUNK:
            raise PacketError("IQ_UPLOAD length invalid")
        cpi, offset = struct.unpack_from("<II", body)
        chunk = body[8:]
        if cpi != self.cpi_id or offset != self.next_offset:
            raise PacketError("IQ CPI/offset mismatch, gap or overlap")
        if len(chunk) == 0 or len(chunk) % 4 or len(chunk) > IQ_CHUNK:
            raise PacketError("IQ chunk not complex-sample aligned")
        if offset + len(chunk) > CPI_SIZE:
            raise PacketError("IQ overflow")
        # Enforce unique canonical boundaries for the first laboratory version.
        if len(chunk) != min(IQ_CHUNK, CPI_SIZE - offset):
            raise PacketError("noncanonical IQ chunk length")
        self.data[offset:offset + len(chunk)] = chunk
        self.next_offset += len(chunk)
        self.packets += 1

    @property
    def complete(self) -> bool:
        return self.next_offset == CPI_SIZE

    def readback(self, offset: int, count: int) -> bytes:
        if not self.complete or offset % 4 or count % 4:
            raise PacketError("readback requires complete, aligned CPI")
        if not (0 < count <= READBACK_CHUNK and
                0 <= offset < CPI_SIZE and offset + count <= CPI_SIZE):
            raise PacketError("bad readback range")
        return bytes(self.data[offset:offset + count])

    def sha256(self):
        if not self.complete:
            raise PacketError("partial CPI cannot be hashed as valid")
        return hashlib.sha256(self.data).hexdigest()


def readback_requests(cpi_id: int):
    for offset in range(0, CPI_SIZE, READBACK_CHUNK):
        count = min(READBACK_CHUNK, CPI_SIZE - offset)
        yield struct.pack("<IBIH", cpi_id, 0, offset, count)


def unpack_stage_data(body: bytes) -> tuple[int, int, bytes]:
    if len(body) < 9:
        raise PacketError("short STAGE_DATA")
    cpi, stage, offset = struct.unpack_from("<IBI", body)
    chunk = body[9:]
    if stage != 0 or len(chunk) == 0 or len(chunk) > READBACK_CHUNK or len(chunk) % 4:
        raise PacketError("wrong/unsupported stage or unaligned data")
    return cpi, offset, chunk


@dataclass(frozen=True)
class Record:
    record_id: int
    range_bin: int
    doppler_bin: int
    signed_doppler: int
    peak_power: int
    cluster_cells: int
    peak_tie: int
    equal_power_cells: int

    def pack(self) -> bytes:
        vals = [(self.record_id, 10), (self.range_bin, 7), (self.doppler_bin, 5),
                (self.signed_doppler & 63, 6), (self.peak_power, 46),
                (self.cluster_cells, 12), (self.peak_tie, 1),
                (self.equal_power_cells, 12)]
        if not -32 <= self.signed_doppler < 32:
            raise PacketError("signed Doppler out of range")
        word = 0
        for val, width in vals:
            if not 0 <= val < (1 << width):
                raise PacketError("record field out of range")
            word = (word << width) | val
        assert word.bit_length() <= 99
        return word.to_bytes(RECORD_BYTES, "little")

    @classmethod
    def unpack(cls, data: bytes) -> "Record":
        if len(data) != RECORD_BYTES or data[12] & 0xF8:
            raise PacketError("record must have 13 bytes and five zero padding bits")
        word = int.from_bytes(data, "little")
        fields = []
        for width in (12, 1, 12, 46, 6, 5, 7, 10):
            fields.append(word & ((1 << width) - 1))
            word >>= width
        eq, tie, cells, power, signed, doppler, rbin, rid = fields
        return cls(rid, rbin, doppler, signed - 64 if signed & 32 else signed,
                   power, cells, tie, eq)


def result_payloads(cpi_id: int, records: list[Record]):
    if len(records) > 702:
        raise PacketError("logical 702 cluster upper bound")
    for start in range(0, len(records), MAX_RECORDS_PACKET):
        chunk = records[start:start + MAX_RECORDS_PACKET]
        yield struct.pack("<I", cpi_id) + b"".join(r.pack() for r in chunk)


def parse_result(body: bytes) -> tuple[int, list[Record]]:
    if len(body) < 4 + RECORD_BYTES or (len(body) - 4) % RECORD_BYTES:
        raise PacketError("RESULT length misaligned")
    n = (len(body) - 4) // RECORD_BYTES
    if not 1 <= n <= MAX_RECORDS_PACKET:
        raise PacketError("RESULT must have 1..8 records")
    cpi = struct.unpack_from("<I", body)[0]
    return cpi, [Record.unpack(body[4 + i*RECORD_BYTES:4 + (i+1)*RECORD_BYTES])
                 for i in range(n)]


def synthetic_records(n: int = 702) -> list[Record]:
    """Transport-only sample; NOT actual Grouping radar output or C05 oracle."""
    if not 0 <= n <= 702:
        raise PacketError("record count")
    return [Record(i, 3 + (i % 107), 3 + (i % 26),
                   (i % 32) - 16, (i * 917 + 5) & ((1 << 46)-1),
                   1 + i % 3, int(i % 11 == 0), 1 + i % 2)
            for i in range(n)]

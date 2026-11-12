"""Bidirectional R1 Stop-and-Wait ARQ; ACK/NACK are unsequenced controls."""
from __future__ import annotations
from dataclasses import dataclass
import struct
from typing import Callable
from .codec import (Frame, Type, PacketError, active_payload, split_active,
                    check_sid, MAX_PAYLOAD)

APP_TYPES = frozenset((Type.COMMAND, Type.IQ_UPLOAD, Type.STAGE_REQUEST,
                       Type.STAGE_DATA, Type.RESULT, Type.STATUS))


class RetryExhausted(TimeoutError):
    pass


@dataclass
class ReceiveResult:
    replies: list[bytes]
    delivered: list[tuple[Type, bytes]]
    ignored: bool = False


class ReliableEndpoint:
    """One outstanding reliable packet per sender direction.

    Receive callback validates/apply data atomically before ACK. A reject
    leaves expected_rx_seq unchanged and returns NACK(expected). This code
    models no physical baud/timing; timeout() is driven by a caller's clock.
    """

    def __init__(self, sid: bytes, max_retries: int = 3, timeout_s: float = 2.0):
        self.sid = check_sid(sid)
        self.max_retries = max_retries
        self.timeout_s = timeout_s
        self.tx_next = 0
        self.rx_expected = 0
        self.outstanding: bytes | None = None
        self.outstanding_type: Type | None = None
        self.retries = 0
        self.last_rx_raw: bytes | None = None
        self.last_rx_seq: int | None = None
        self.terminal_ack_uncertain = False
        self.accepted = 0
        self.stale = 0
        self.duplicate = 0
        self.rejected = 0

    def send(self, kind: Type, payload: bytes) -> bytes:
        if kind not in APP_TYPES:
            raise PacketError("not a reliable application type")
        if self.outstanding is not None:
            raise PacketError("Stop-and-Wait: pending ACK")
        if self.tx_next == 0xFFFFFFFF:
            raise PacketError("sequence rollover requires new epoch")
        raw = Frame(kind, self.tx_next, active_payload(self.sid, payload)).encode()
        self.outstanding = raw
        self.outstanding_type = kind
        self.retries = 0
        return raw

    def timeout(self) -> bytes:
        if self.outstanding is None:
            raise PacketError("no outstanding packet")
        if self.retries == self.max_retries:
            if self.outstanding_type == Type.STATUS:
                # Only a decided COMMIT may use this path; caller controls
                # the terminal-decision state, not all STATUS frames.
                self.terminal_ack_uncertain = True
            raise RetryExhausted("retry limit: caller must reconcile/abort safely")
        self.retries += 1
        return self.outstanding  # identical SOF/header/seq/payload/CRC

    def _control(self, kind: Type, header_seq: int, value: int) -> bytes:
        return Frame(kind, header_seq, active_payload(self.sid,
                     struct.pack("<I", value))).encode()

    def receive(self, frame: Frame, apply: Callable[[Type, bytes], None] | None = None) -> ReceiveResult:
        try:
            content = split_active(frame, self.sid)
        except PacketError:
            self.stale += 1
            return ReceiveResult([], [], True)
        if frame.type in (Type.ACK, Type.NACK):
            if len(content) != 4:
                self.rejected += 1
                return ReceiveResult([], [], True)
            val = struct.unpack("<I", content)[0]
            if self.outstanding is None:
                self.stale += 1
                return ReceiveResult([], [], True)
            current = Frame.decode(self.outstanding).seq
            if frame.type == Type.ACK:
                if frame.seq == val == current:
                    self.outstanding = None
                    self.outstanding_type = None
                    self.tx_next += 1
                    self.retries = 0
                    self.terminal_ack_uncertain = False
                    return ReceiveResult([], [])
                self.stale += 1
                return ReceiveResult([], [], True)
            # Valid current NACK may trigger a bounded replay, never an ACK.
            if frame.seq == val == current and self.retries < self.max_retries:
                self.retries += 1
                return ReceiveResult([self.outstanding], [])
            self.stale += 1
            return ReceiveResult([], [], True)

        if frame.type not in APP_TYPES:
            self.rejected += 1
            return ReceiveResult([], [], True)
        if frame.seq == self.rx_expected:
            # Application validator runs before ACK, so invalid data is not
            # written and cannot advance expected_rx_seq.
            try:
                if apply is not None:
                    apply(frame.type, content)
            except (ValueError, PacketError):
                self.rejected += 1
                return ReceiveResult(
                    [self._control(Type.NACK, frame.seq, self.rx_expected)], [], True)
            self.last_rx_raw = frame.encode()
            self.last_rx_seq = frame.seq
            self.rx_expected += 1
            self.accepted += 1
            return ReceiveResult([self._control(Type.ACK, frame.seq, frame.seq)],
                                 [(frame.type, content)])
        if frame.seq == self.last_rx_seq and frame.encode() == self.last_rx_raw:
            self.duplicate += 1
            return ReceiveResult([self._control(Type.ACK, frame.seq, frame.seq)], [])
        self.rejected += 1
        return ReceiveResult([self._control(Type.NACK, frame.seq, self.rx_expected)], [], True)

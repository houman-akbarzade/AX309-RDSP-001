"""Software-only stand-in for FPGA UART endpoint plus PC host integration.

No radar DSP, UART PHY, timing closure or AX309 board is simulated here.
"""
from __future__ import annotations
import hashlib
import json
import struct
from collections import deque
from .codec import (Frame, Type, Command, Status, PacketError,
                    SessionOp, parse_session, split_active)
from .session import PCSession, FPGASessionSimulator, Snapshot
from .arq import ReliableEndpoint, RetryExhausted
from .iq import (CPI_SIZE, IQAssembler, Record, synthetic_iq, synthetic_records,
                 upload_chunks, readback_requests, parse_result, result_payloads,
                 unpack_stage_data, READBACK_CHUNK)


class FPGASoftwareSimulator:
    """Explicitly NOT FPGA RTL. IQ memory and status are in Python RAM."""

    def __init__(self):
        self.session = FPGASessionSimulator()
        self.arq: ReliableEndpoint | None = None
        self.assembler: IQAssembler | None = None
        self.cpi_id: int | None = None
        self.readback_requested = False
        self.input_verified = False
        self.running = False
        self.terminal: tuple[str, int, int] | None = None
        self.pending_stage: bytes | None = None
        self.pending_query: bytes | None = None

    def receive(self, wire: bytes) -> list[bytes]:
        frame = Frame.decode(wire)
        if frame.type == Type.SESSION_CONTROL:
            reply = self.session.receive(wire)
            if self.session.state == "ACTIVE" and (
                    self.arq is None or self.arq.sid != self.session.sid):
                self.arq = ReliableEndpoint(self.session.sid)
                # Old transport in-flight bytes cannot be released by new SID.
                self.pending_stage = None
                self.pending_query = None
            return [reply] if reply else []
        if self.arq is None or self.session.state != "ACTIVE":
            return []
        outcome = self.arq.receive(frame, self._apply)
        outputs = list(outcome.replies)
        if self.arq.outstanding is None:
            if self.pending_stage is not None:
                outputs.append(self.arq.send(Type.STAGE_DATA, self.pending_stage))
                self.pending_stage = None
            elif self.pending_query is not None:
                outputs.append(self.arq.send(Type.STATUS, self.pending_query))
                self.pending_query = None
        # Keep handshake counters a mirror of actual active reliable counters.
        self.session.app_rx_expected = self.arq.rx_expected
        self.session.app_tx_next = self.arq.tx_next
        return outputs

    def _apply(self, kind: Type, body: bytes) -> None:
        if kind == Type.IQ_UPLOAD:
            if self.assembler is None or self.running:
                raise PacketError("IQ upload outside open CPI")
            self.assembler.accept(body)
            return
        if kind == Type.STAGE_REQUEST:
            if len(body) != 11 or self.assembler is None:
                raise PacketError("bad stage request")
            cpi, stage, offset, count = struct.unpack("<IBIH", body)
            if cpi != self.cpi_id or stage != 0 or count != min(READBACK_CHUNK, CPI_SIZE - offset):
                raise PacketError("unsupported stage or noncanonical readback")
            payload = self.assembler.readback(offset, count)
            self.pending_stage = struct.pack("<IBI", cpi, stage, offset) + payload
            self.readback_requested = True
            return
        if kind == Type.COMMAND:
            if len(body) != 5:
                raise PacketError("candidate COMMAND length")
            op, cpi = struct.unpack("<BI", body)
            if op == Command.OPEN_CPI:
                if self.assembler is not None or self.terminal is not None:
                    raise PacketError("CPI already active")
                self.cpi_id = cpi
                self.assembler = IQAssembler(cpi)
                self.session.update_snapshot(Snapshot(1, 1, cpi, 0))
            elif cpi != self.cpi_id:
                raise PacketError("wrong CPI_ID")
            elif op == Command.REQUEST_INPUT_READBACK:
                if not self.assembler or not self.assembler.complete:
                    raise PacketError("input not complete")
                self.readback_requested = True
            elif op == Command.HOST_VERIFIED_INPUT:
                if not self.assembler or not self.assembler.complete or not self.readback_requested:
                    raise PacketError("unverified input")
                self.input_verified = True  # Trusted host assertion, not FPGA self-check
            elif op == Command.RUN_CPI:
                if not self.input_verified or not self.assembler or not self.assembler.complete:
                    raise PacketError("RUN before verified input")
                self.running = True
            elif op == Command.QUERY_CPI_STATUS:
                if self.terminal is None:
                    raise PacketError("terminal status not decided")
                outcome, previous_id, count = self.terminal
                code = Status.CPI_COMMIT if outcome == "COMMIT" else Status.CPI_ABORT
                self.pending_query = struct.pack("<BIH", code, previous_id, count)
            else:
                # RELEASE/UNKNOWN require separate signed host-journal policy;
                # fail closed, do not erase terminal state.
                raise PacketError("command not implemented/signed for simulator")
            return
        raise PacketError("unsupported application direction/type")

    def result_frame(self, payload: bytes) -> bytes:
        if not self.running or self.arq is None or self.terminal is not None:
            raise PacketError("cannot produce results")
        if len(payload) < 17:
            raise PacketError("empty records")
        return self.arq.send(Type.RESULT, payload)

    def commit_frame(self, count: int) -> bytes:
        if not self.running or not 0 <= count <= 702 or self.arq is None:
            raise PacketError("cannot commit CPI")
        if self.arq.outstanding is not None or self.terminal is not None:
            raise PacketError("outstanding output or existing terminal")
        self.terminal = ("COMMIT", self.cpi_id, count)
        self.session.update_snapshot(Snapshot(2, 1, self.cpi_id, count))
        return self.arq.send(Type.STATUS, struct.pack("<BIH", Status.CPI_COMMIT, self.cpi_id, count))

    def timeout_output(self) -> bytes:
        if self.arq is None:
            raise PacketError("no active transport")
        try:
            return self.arq.timeout()
        except RetryExhausted:
            if self.terminal and self.terminal[0] == "COMMIT":
                self.session.update_snapshot(Snapshot(4, 1, self.cpi_id, self.terminal[2]))
            raise


class PCHost:
    """Trusted host's provisional-target ledger. COMMIT checked before ACK."""

    def __init__(self, sid: bytes, expected_iq: bytes, cpi_id: int = 1,
                 prior_cpi: int | None = None):
        self.session = PCSession(sid, mode=int(prior_cpi is not None),
                                 prior_cpi=prior_cpi)
        self.arq: ReliableEndpoint | None = None
        self.cpi_id = cpi_id
        self.expected_iq = expected_iq
        self.readback = bytearray()
        self.records: dict[int, Record] = {}
        self.committed = False
        self.commit_count = 0
        self.terminal = None
        self.cpi_open_acked = False
        self.input_verified = False
        self.run_acked = False

    def receive(self, raw: bytes) -> list[bytes]:
        f = Frame.decode(raw)
        if f.type == Type.SESSION_CONTROL:
            next_wire = self.session.receive(raw)
            if self.session.state == "ACTIVE" and (
                    self.arq is None or self.arq.sid != self.session.sid):
                self.arq = ReliableEndpoint(self.session.sid)
            return [next_wire] if next_wire else []
        if self.arq is None or self.session.state != "ACTIVE":
            return []
        pending = self.arq.outstanding
        result = self.arq.receive(f, self._apply)
        if pending is not None and self.arq.outstanding is None and f.type == Type.ACK:
            prev = Frame.decode(pending)
            if prev.type == Type.COMMAND:
                original = split_active(prev, self.session.sid)
                op, cpi = struct.unpack("<BI", original)
                if op == Command.OPEN_CPI:
                    self.cpi_open_acked = True
                elif op == Command.HOST_VERIFIED_INPUT:
                    self.input_verified = True
                elif op == Command.RUN_CPI:
                    self.run_acked = True
        return result.replies

    def _apply(self, kind: Type, body: bytes) -> None:
        if kind == Type.STAGE_DATA:
            if not self.cpi_open_acked:
                raise PacketError("unsolicited readback before OPEN ACK")
            cpi, offset, payload = unpack_stage_data(body)
            if cpi != self.cpi_id or offset != len(self.readback):
                raise PacketError("unexpected readback offset/CPI")
            if self.expected_iq[offset:offset + len(payload)] != payload:
                raise PacketError("bytewise IQ readback mismatch")
            self.readback.extend(payload)
        elif kind == Type.RESULT:
            if not self.run_acked:
                raise PacketError("unsolicited RESULT before verified RUN ACK")
            cpi, records = parse_result(body)
            if cpi != self.cpi_id or self.committed:
                raise PacketError("wrong CPI or RESULT after COMMIT")
            # Validate the entire RESULT packet before any ledger mutation.
            # A late malformed record must not leave partial application state
            # that prevents a corrected retransmission from succeeding.
            first_id = len(self.records)
            for index, rec in enumerate(records):
                if rec.record_id in self.records or rec.record_id != first_id + index:
                    raise PacketError("RESULT repeated/out of order ID")
            for rec in records:
                self.records[rec.record_id] = rec
        elif kind == Type.STATUS:
            if not self.run_acked:
                raise PacketError("terminal STATUS before verified RUN ACK")
            if len(body) != 7:
                raise PacketError("bad terminal STATUS length")
            code, cpi, count = struct.unpack("<BIH", body)
            if cpi != self.cpi_id or self.terminal and self.terminal != (code, count):
                raise PacketError("conflicting terminal decision/CPI")
            if code == Status.CPI_COMMIT:
                if count > 702 or len(self.records) != count or sorted(self.records) != list(range(count)):
                    raise PacketError("COMMIT without all distinct consecutive records")
                if not self.committed:
                    self.commit_count += 1
                self.committed = True
            elif code == Status.CPI_ABORT:
                if self.committed:
                    raise PacketError("contradictory ABORT after COMMIT")
                self.records.clear()
            else:
                raise PacketError("unsupported STATUS")
            self.terminal = (code, count)
        else:
            raise PacketError("unexpected FPGA application frame")

    def send(self, kind: Type, payload: bytes) -> bytes:
        if self.arq is None:
            raise PacketError("host has no active epoch")
        if self.session.application_locked and kind != Type.COMMAND:
            raise PacketError("recovered UNKNOWN/preterminal session is locked")
        if kind == Type.COMMAND:
            if len(payload) != 5:
                raise PacketError("unsupported command schema")
            op, cpi = struct.unpack("<BI", payload)
            if self.session.application_locked:
                raise PacketError("UNKNOWN/preterminal recovery needs durable host disposition")
            if cpi != self.cpi_id:
                raise PacketError("host CPI mismatch")
            if op == Command.HOST_VERIFIED_INPUT and bytes(self.readback) != self.expected_iq:
                raise PacketError("host has not completed exact bytewise readback")
            if op == Command.RUN_CPI and not self.input_verified:
                raise PacketError("host has not received input verification ACK")
        return self.arq.send(kind, payload)


class SoftwareLink:
    """In-memory full encoded wire pump. Not a physical UART/transceiver."""

    def __init__(self, pc: PCHost, fpga: FPGASoftwareSimulator):
        self.pc = pc
        self.fpga = fpga
        self.trace: list[tuple[str, bytes]] = []

    def transfer(self, sender: str, wire: bytes, max_steps: int = 8):
        queue = deque([(sender, wire)])
        steps = 0
        while queue:
            if steps >= max_steps:
                raise RuntimeError("software link loop; inspect control states")
            src, item = queue.popleft()
            self.trace.append((src, item))
            replies = (self.fpga.receive(item) if src == "PC" else
                       self.pc.receive(item))
            for answer in replies:
                queue.append(("FPGA" if src == "PC" else "PC", answer))
            steps += 1

    def pc_send(self, kind: Type, payload: bytes):
        self.transfer("PC", self.pc.send(kind, payload))

    def fpga_send(self, wire: bytes):
        self.transfer("FPGA", wire)


def run_demo() -> dict:
    raw = synthetic_iq()
    sid = bytes.fromhex("00112233445566778899aabbccddeeff")
    pc = PCHost(sid, raw, cpi_id=23)
    fpga = FPGASoftwareSimulator()
    link = SoftwareLink(pc, fpga)
    link.transfer("PC", pc.session.start())
    if pc.session.state != "ACTIVE":
        raise RuntimeError("handshake not active")
    link.pc_send(Type.COMMAND, struct.pack("<BI", Command.OPEN_CPI, pc.cpi_id))
    for chunk in upload_chunks(pc.cpi_id, raw):
        link.pc_send(Type.IQ_UPLOAD, chunk)
    if fpga.assembler is None or not fpga.assembler.complete:
        raise RuntimeError("CPI incomplete")
    link.pc_send(Type.COMMAND, struct.pack("<BI", Command.REQUEST_INPUT_READBACK, pc.cpi_id))
    for req in readback_requests(pc.cpi_id):
        link.pc_send(Type.STAGE_REQUEST, req)
    if bytes(pc.readback) != raw:
        raise RuntimeError("readback mismatch")
    link.pc_send(Type.COMMAND, struct.pack("<BI", Command.HOST_VERIFIED_INPUT, pc.cpi_id))
    link.pc_send(Type.COMMAND, struct.pack("<BI", Command.RUN_CPI, pc.cpi_id))
    expected = synthetic_records(702)
    for payload in result_payloads(pc.cpi_id, expected):
        link.fpga_send(fpga.result_frame(payload))
    link.fpga_send(fpga.commit_frame(len(expected)))
    if not pc.committed or pc.commit_count != 1 or list(pc.records.values()) != expected:
        raise RuntimeError("synthetic 702-record transport not complete")
    sample = [(src, Frame.decode(w)) for src, w in link.trace]
    first_iq = next(w for src, w in link.trace
                    if src == "PC" and Frame.decode(w).type == Type.IQ_UPLOAD)
    first_iq_seq = Frame.decode(first_iq).seq
    first_iq_ack = next(w for src, w in link.trace
                        if src == "FPGA" and Frame.decode(w).type == Type.ACK
                        and Frame.decode(w).seq == first_iq_seq)
    first_result = next(w for src, w in link.trace
                        if src == "FPGA" and Frame.decode(w).type == Type.RESULT)
    return dict(
        simulator="FPGASoftwareSimulator (Python only, NOT FPGA RTL)",
        pc_session=pc.session.state,
        fpga_session=fpga.session.state,
        cpi_id=pc.cpi_id,
        IQ_bytes=len(raw), IQ_sha256=hashlib.sha256(raw).hexdigest(),
        upload_packets=fpga.assembler.packets, readback_bytes=len(pc.readback),
        synthetic_records=len(pc.records), host_COMMIT_count=pc.commit_count,
        total_wire_frames=len(link.trace),
        first_hello_hex=link.trace[0][1].hex(),
        first_offer_hex=link.trace[1][1].hex(),
        first_activ_hex=link.trace[2][1].hex(),
        first_ready_hex=link.trace[3][1].hex(),
        first_IQ_packet_crc_hex=first_iq[-4:].hex(),
        first_IQ_packet_sha256=hashlib.sha256(first_iq).hexdigest(),
        first_IQ_packet_length=len(first_iq),
        first_IQ_packet_prefix_hex=first_iq[:45].hex(),
        first_IQ_ACK_wire_hex=first_iq_ack.hex(),
        first_RESULT_packet_length=len(first_result),
        first_RESULT_CRC_LE_hex=first_result[-4:].hex(),
        result_packet_count=sum(src == "FPGA" and f.type == Type.RESULT for src, f in sample),
        physical_UART_test="NOT_RUN", RTL_test="NOT_RUN",
    )

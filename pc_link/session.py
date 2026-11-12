"""Four-message R1 link session, including cached READY after its loss."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from .codec import (Frame, Type, SessionOp, PacketError, bootstrap,
                    parse_session, check_sid, snapshot_valid)


@dataclass(frozen=True)
class Snapshot:
    kind: int = 0
    valid: int = 0
    cpi_id: int = 0
    info: int = 0

    def __post_init__(self):
        if not snapshot_valid(self.kind, self.valid, self.cpi_id, self.info):
            raise PacketError("invalid snapshot")

    @classmethod
    def from_fields(cls, v: dict) -> "Snapshot":
        return cls(v["kind"], v["valid"], v["cpi_id"], v["info"])

    def fields(self) -> dict:
        return dict(kind=self.kind, cpi_valid=self.valid, cpi_id=self.cpi_id,
                    info=self.info)


class PCSession:
    def __init__(self, sid: bytes, mode: int = 0, prior_cpi: int | None = None,
                 max_retries: int = 3):
        self.sid = check_sid(sid)
        self.mode = mode
        self.prior_cpi = prior_cpi
        self.max_retries = max_retries
        self.state = "NO_PORT"
        self.outstanding: bytes | None = None
        self.retries = 0
        self.snapshot: Snapshot | None = None
        self.activation_count = 0
        self.application_locked = False

    def start(self) -> bytes:
        if self.state != "NO_PORT":
            raise PacketError("session already starting")
        self.outstanding = bootstrap(SessionOp.HELLO, self.sid, mode=self.mode,
                                     prior_valid=int(self.prior_cpi is not None),
                                     cpi_id=self.prior_cpi or 0)
        self.state = "HELLO_WAIT_OFFER"
        self.retries = 0
        return self.outstanding

    def receive(self, raw: bytes) -> bytes | None:
        frame = Frame.decode(raw)
        if frame.type != Type.SESSION_CONTROL:
            raise PacketError("application frame before active session dispatch")
        op, fields = parse_session(frame)
        if fields["sid"] != self.sid:
            return None  # stale reply
        if self.state == "HELLO_WAIT_OFFER" and op == SessionOp.OFFER:
            snapshot = Snapshot.from_fields(fields)
            if self.mode == 0 and snapshot.kind != 0:
                self.state = "RECOVERY_REQUIRED"
                raise PacketError("FRESH cannot overwrite a retained CPI")
            if self.mode == 1 and snapshot.kind != 0 and snapshot.cpi_id != self.prior_cpi:
                self.state = "RECOVERY_REQUIRED"
                raise PacketError("RECOVER CPI_ID does not match FPGA snapshot")
            # UNKNOWN and active-preterminal CPI must not permit ordinary commands.
            self.application_locked = snapshot.kind in (0, 1) and self.mode == 1
            self.snapshot = snapshot
            self.state = "ACTIVATE_WAIT_READY"
            self.retries = 0
            self.outstanding = bootstrap(SessionOp.ACTIVATE, self.sid,
                                         mode=self.mode, **self.snapshot.fields())
            return self.outstanding
        if self.state == "ACTIVATE_WAIT_READY" and op == SessionOp.READY:
            if fields["first"] != 0 or Snapshot.from_fields(fields) != self.snapshot:
                self.state = "RECOVERY_REQUIRED"
                raise PacketError("READY rejected or snapshot mismatch")
            self.state = "ACTIVE"
            self.outstanding = None
            self.activation_count += 1
            return None
        return None  # unexpected or delayed bootstrap, no transition

    def timeout(self) -> bytes:
        if self.state not in ("HELLO_WAIT_OFFER", "ACTIVATE_WAIT_READY"):
            raise PacketError("no pending handshake request")
        if self.retries >= self.max_retries:
            self.state = "RECOVERY_REQUIRED"
            raise TimeoutError("handshake retries exhausted")
        self.retries += 1
        assert self.outstanding is not None
        return self.outstanding


class FPGASessionSimulator:
    """Only a software stand-in for the FPGA session controller.

    The activated_once latch is not written on duplicates; readiness may be
    delivered repeatedly after the FPGA has already accepted application data.
    """

    def __init__(self):
        self.state = "NO_SESSION"
        self.sid: bytes | None = None
        self.snapshot = Snapshot()
        self.negotiation: bytes | None = None
        self.cached_offer: bytes | None = None
        self.cached_ready: bytes | None = None
        self.activated_once = False
        self.activation_count = 0
        self.app_rx_expected = 0
        self.app_tx_next = 0
        self.retired: set[bytes] = set()

    def update_snapshot(self, snapshot: Snapshot) -> None:
        self.snapshot = snapshot

    def receive(self, raw: bytes) -> bytes | None:
        f = Frame.decode(raw)
        op, fields = parse_session(f)
        sid = fields["sid"]
        if op == SessionOp.HELLO:
            if sid in self.retired:
                return None
            if self.sid == sid:
                return self.cached_offer
            # A trusted new host epoch may supersede negotiation, never terminal
            if self.sid is not None:
                self.retired.add(self.sid)
            self.sid = sid
            self.state = "NEGOTIATING"
            self.activated_once = False
            self.cached_ready = None
            self.negotiation = raw
            self.cached_offer = bootstrap(SessionOp.OFFER, sid, **self.snapshot.fields())
            return self.cached_offer
        if op == SessionOp.ACTIVATE:
            if sid != self.sid or sid in self.retired:
                return None
            if self.state == "ACTIVE":
                # Exact repeated ACTIVATE only, never reinitialize counters
                expected = bootstrap(SessionOp.ACTIVATE, sid, mode=fields["first"],
                                     **self.snapshot.fields())
                if raw == self.cached_activate:
                    return self.cached_ready
                return None
            if self.state != "NEGOTIATING":
                return None
            if Snapshot.from_fields(fields) != self.snapshot:
                return None
            if self.negotiation is None or fields["first"] != parse_session(Frame.decode(self.negotiation))[1]["mode"]:
                return None
            if not self.activated_once:
                self.app_rx_expected = 0
                self.app_tx_next = 0
                self.activation_count += 1
                self.activated_once = True
                self.cached_activate = raw
                self.cached_ready = bootstrap(SessionOp.READY, sid, result=0,
                                               **self.snapshot.fields())
                self.state = "ACTIVE"
            return self.cached_ready
        return None

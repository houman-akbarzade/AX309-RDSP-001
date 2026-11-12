# AX309-RDSP-001 | S05 Link Session / Epoch Addendum R1 (Engineering Candidate)

**Revision:** R1 / candidate v0.1 | **Baseline Git:** `b217849` | **Date:** 2026-11-12
**Authority:** System engineer review requested; **ALL changes herein PROPOSED, NOT APPROVED**.
**Parent:** `engineering/S05-UART-ICD-v1.0-ENGINEER-REVIEW.md` (R2, not signed off).
**Supersedes for review only:** `engineering/S05-LINK-SESSION-EPOCH-ADDENDUM-v0.1.md`. Original evidence is retained.
**Scope:** AX309 CP2102GM USB-to-UART, lab CPI-by-CPI, no Ethernet/continuous transfer. No PC Packetizer/Parser, UART/Frame Controller RTL, resource fit or board proof is implemented by R1.

## 1. Normative boundaries and engineering status

S02 C-UART-01 remains unchanged: `SOF=A5 5A C3 3C` (4 B), `version=1` (1), `TYPE` (1), `flags` (1), `seq:u32LE` (4), `payload_len:u16LE` (2; maximum 512), payload (0..512), `CRC32:u32LE` (4). Fixed overhead **17 B**, absolute maximum frame **529 B**. CRC-32/ISO-HDLC on bytes **version through end of payload**, excluding SOF and appended CRC; reflected 0xEDB88320, init/final XOR 0xFFFFFFFF, check `123456789 -> CBF43926`. The R2 proposals for no ACK-of-ACK, 13-byte record/zero high-five padding bits, <=8 RESULT records, immutable terminal COMMIT and 16,896-byte exact IQ readback remain unapproved wire-ICD details (accepted as lab baselines).

**R1 wire changes proposed, explicitly requiring a new S02/S05 sign-off:** `TYPE=0x09 SESSION_CONTROL`, `flags=0x01` for active session-tagged packets; 16 opaque `session_id` bytes prefixed to *all* reliable application and ACK/NACK payloads. Bootstrap SESSION_CONTROL uses flags=0, header.seq=0 and its own response protocol, without reliable application sequencing or ACK-of-ACK. This makes post-epoch sequence reuse distinguishable within a correctly established new session, but does not authenticate the source.

Logical REQ-LIST-01 completeness (0..702 groups, no Top-K or silent discard) **APPROVED**. Physical buffering, output transport and full REQ-LIST-01 **OPEN**. Seven DSP stage-output schemas **OPEN** under REQ-OBS-01. Numerical Architecture C, Gate-S04, REQ-RNG-03 and Fixed-Point statistics are not changed.

## 2. Exact proposed message fields and byte-level interpretation

Every message is enveloped in the unchanged S02 frame. Little-endian applies to u16/u32/u64 scalar fields; `session_id[16]` is an **opaque byte string**, never an LE integer. Candidate message Type values remain those of the R2 manifest, plus **proposed** `SESSION_CONTROL=0x09`. Ordinary in-session reliable frames use `flags=0x01` and `payload=session_id[16]||existing_type_payload`; ACK/NACK use the same epoch prefix and CRC. No application/sequence/ACK side effects before frame validation and exact current epoch comparison.

| Bootstrap message | Opcode | Payload in strict on-wire order | Payload B | Complete frame B |
|---|---|---|---:|---:|
| `SESSION_HELLO` PC→FPGA | 0x01 | `op:u8, rev:u8=1, sid[16], mode:u8 (FRESH=0, RECOVER=1), prior_valid:u8, prior_CPI_ID:u32LE` | **24** | **41** |
| `SESSION_OFFER` FPGA→PC | 0x02 | `op:u8, rev:u8=1, sid[16], snapshot_kind:u8, cpi_valid:u8, retained_CPI_ID:u32LE, info:u16LE` | **26** | **43** |
| `SESSION_ACTIVATE` PC→FPGA | 0x03 | `op:u8, rev:u8=1, sid[16], accepted_mode:u8, observed_kind:u8, observed_cpi_valid:u8, observed_CPI_ID:u32LE, observed_info:u16LE` | **27** | **44** |
| `SESSION_READY` FPGA→PC | 0x04 | `op:u8, rev:u8=1, sid[16], result:u8 (READY=0, REJECT=1, NEED_RECONCILE=2), snapshot_kind:u8, cpi_valid:u8, retained_CPI_ID:u32LE, info:u16LE` | **27** | **44** |

**R1 correction:** ACTIVATE and READY now include `cpi_valid` so the complete OFFER snapshot is echoed and cross-checked. Hence the 4-message handshake requires **172 bytes**, not the v0.1 **170 bytes**. HELLO and OFFER lengths remain unchanged. A bootstrap message is not a CPI result, not an ACK and does not advance application seq.

`snapshot_kind`: `0=NO_RETAINED_STATE/UNKNOWN`, `1=ACTIVE_PRETERMINAL`, `2=DECIDED_COMMIT`, `3=DECIDED_ABORT`, `4=TERMINAL_ACK_UNCERTAIN_COMMIT`. For kind 0 require `cpi_valid=0, CPI_ID=0, info=0`; for kinds 1..4 `cpi_valid=1` and CPI_ID must be a retained transaction identifier. In kinds 2 and 4, `info=immutable_record_count` in 0..702; in kind 3 `info=immutable_reason_code`; in kind 1 `info=0` unless a separately approved status field is assigned. Reject internally inconsistent snapshots; reject ACTIVATE when any echoed field differs or if the FPGA snapshot has changed during negotiation. No terminal decision is altered by a handshake.

**In-session payload sizes (candidate):** ACK and NACK each `sid[16]||seq:u32LE`, 20 payload bytes, **37 B frame**. IQ_UPLOAD payload `sid[16]||CPI_ID:u32LE||offset:u32LE||raw_chunk[1..488]`; 16,896 B requires **35 packets** (34×488+304). Raw-IQ readback STAGE_REQUEST has sid16+CPI4+stage1+offset4+count2 = **27 payload B**; STAGE_DATA has sid16+CPI4+stage1+offset4+IQ_chunk[1..484 aligned to 4] = up to **509 payload B**; 35 STAGE_DATA packets (34×484+440). RESULT payload sid16+CPI_ID4+K×13 B (1≤K≤8), maximum **124 payload B**, **141 frame B**, 702 records in **88 packets**. Upper five record padding bits must be zero; signed-bin and power integers remain unchanged. `stage_id=0` denotes **proposed raw IQ readback only**, not one of seven approved DSP-stage schemas.

## 3. PC and FPGA state machines, including all four lost messages

### 3.1 State sets and reset/activation invariant

PC transport states: `NO_PORT`, `HELLO_WAIT_OFFER`, `OFFER_CHECKED`, `ACTIVATE_WAIT_READY`, `ACTIVE`, `RECOVERY_REQUIRED` and `UNKNOWN_LOCKED`. FPGA transport states: `NO_SESSION`, `NEGOTIATING(sid,offer_snapshot)`, `ACTIVE(sid,activated_once)`, `TERMINAL_ACK_UNCERTAIN`, `UNKNOWN_LOCKED`. CPI terminal state is an **independent protected field**, not encoded by an ACTIVE flag.

On first valid ACTIVATE in FPGA `NEGOTIATING(sid)` with an exact complete OFFER echo and `activated_once(sid)=false`, atomically:
1. latch `active_sid=sid`, `activated_once(sid)=true`, `app_rx_expected=0`, `app_tx_next=0`, `accepted_application_count=0`;
2. cache the **exact serialized READY frame** (CRC included), set `ACTIVE(sid)`, transmit READY once.
3. **Afterwards** the same ACTIVATE (or same-epoch HELLO) can **only retransmit the cached READY (or OFFER)** and may **not write** `app_rx_expected`, `app_tx_next`, `activated_once`, CPI_ID or terminal decision.

The PC initializes its own directional sequence counters **once** when it receives and validates READY for the SID/snapshot it requested, then enters ACTIVE. The FPGA may be ACTIVE before the PC sees READY; this is an unavoidable four-message handshake asymmetry. The trusted PC sends **no reliable application bytes before valid READY**. The FPGA's first accepted active application packet from that PC may consequently be seq=0 only after the PC's READY check. This contract does not claim the FPGA can know that READY reached the PC without a fifth confirmation message.

### 3.2 Loss/duplicate transition table

| Injected event and initial state | PC state/action | FPGA state/action | Observable guard |
|---|---|---|---|
| **HELLO lost**, FPGA NO_SESSION | `HELLO_WAIT_OFFER`; timeout → send **identical HELLO, same SID**, until candidate budget exhausted | No change until valid HELLO; then NEGOTIATING and send OFFER | No FPGA application seq initialization or CPI mutation before ACTIVATE |
| **OFFER lost**, FPGA NEGOTIATING | `HELLO_WAIT_OFFER`; repeat same HELLO | Retransmit **identical OFFER** and same frozen snapshot, no CPI action | Same OFFER bytes/CRC; zero app-seq resets |
| **ACTIVATE lost**, PC ACTIVATE_WAIT_READY | Timeout → resend **identical ACTIVATE**, same complete snapshot | Remains NEGOTIATING until receipt; then perform exactly one activation | `activation_count(sid)=1`; no early app packet |
| **READY lost**, FPGA already ACTIVE(sid) | Remains ACTIVATE_WAIT_READY; resend identical ACTIVATE | Recognize duplicate ACTIVATE against cached activated SID/snapshot; retransmit **identical READY**; **never reset app counters** | Compare pre/post `app_rx_expected`, `app_tx_next`, `activation_count=1`; preserve accepted data/ACK history even if a delayed duplicate ACTIVATE arrives later |
| Repeated HELLO while NEGOTIATING | Accept only matching SID/mode; otherwise initiate controlled new negotiation with **fresh** SID and quarantine old candidate | Same HELLO → cached OFFER; no overwrite of existing terminal tuple | Snapshot and all fields unchanged |
| Repeated HELLO after READY was sent (ACTIVE same SID) | PC may still be waiting for OFFER from delayed traffic; revalidate current offer only | Cached OFFER may be returned; **not** a new activation, no counter reset | `activation_count` remains 1; active reliable seq unchanged |
| Repeated ACTIVATE after a RESULT was acknowledged | Ignore unsolicited READY if PC already ACTIVE | FPGA resends cached READY, no rewind even if `app_tx_next>0` | Previously ACKed records not retransmitted as new seq |
| Stale OFFER/READY for **different SID** | Reject, do not transition to ACTIVE | No state effect | PC counters/terminal status unchanged |
| Stale HELLO/ACTIVATE for **retired SID** | Do not generate them; reject stale responses | Discard as retired if history available; do not re-activate old epoch | No replay-buffer release; no reset |
| USB disconnect **during HELLO_WAIT_OFFER** | Stop retransmitting over old handle, preserve current CPI state; on reconnect create a **new SID** and restart HELLO | May be NO_SESSION/NEGOTIATING; supersede only the pending negotiation, preserve protected CPI | In-flight old epoch bytes quarantined |
| USB disconnect **during ACTIVATE_WAIT_READY** | Treat outcome of ACTIVATE as **unknown**, never assume FPGA is NO_SESSION; reconnect with a **new SID** | Could be NEGOTIATING or already ACTIVE(old sid); new HELLO transitions to new negotiation while preserving immutable CPI | New OFFER reports actual terminal/pending snapshot; old READY rejected |
| OFFER snapshot changes before ACTIVATE | Reject/restart with **fresh SID**; no RUN/COMMIT | Reject ACTIVATE or READY result REJECT; do not activate on mismatched cpi_valid/kind/ID/info | No application seq initialization |
| Timeout exhausts any handshake leg | `RECOVERY_REQUIRED`; no CPI success, no silently opened next CPI | May remain NEGOTIATING or ACTIVE; **never auto-RELEASE/ABORT** a decided terminal result | Reconnect with new SID; preserve protected state until explicit recovery |
| READY result REJECT or NEED_RECONCILE | `RECOVERY_REQUIRED`, no application data; obtain new OFFER or operator disposition | No activation on non-READY; preserve original CPI | No output accepted as COMMIT |

**Precise lost-READY proof (state invariant):** Let `N(sid)` be the number of FPGA transitions executing `app_rx_expected:=0, app_tx_next:=0` for one SID. The only such transition has guard `state=NEGOTIATING(sid) ∧ exact_ACTIVATE ∧ activated_once(sid)=false`, and atomically changes state to `ACTIVE(sid)` and sets the latch true. Any number of subsequent duplicate ACTIVATE/HELLO frames for that same SID fails the guard, executing only cached reply retransmission. Hence by induction `N(sid)≤1` (and `=1` following the first valid ACTIVATE). A lost READY **cannot cause a second counter initialization** unless the separately documented protected session state itself is lost, in which case the FPGA must not silently resume the old SID. This is a **state-machine argument**, not executed RTL evidence.

### 3.3 Snapshot/quiescence and transitions between epochs

A valid fresh HELLO from the **single trusted PC** suspends old-session packet acceptance and freezes the negotiation snapshot. It **must not abort a preterminal CPI implicitly**, erase a decided COMMIT or release a buffered output record. A changed terminal decision while negotiating causes ACTIVATE rejection and a new snapshot exchange; ACTIVE_PRETERMINAL after link loss remains blocked until a separately approved abort/rerun disposition. On successful READY, the new epoch starts directional reliable seq at 0 once. Old-epoch ACK/NACK/frames are rejected on SID mismatch before any seq or payload effect. No wrap/reuse of the 32-bit counter inside one epoch.

## 4. Laboratory trust model after FPGA power loss (testable, not authentication)

**Assumptions requiring system-engineer acceptance:** (T1) one authorized PC process exclusively owns the CP2102GM serial port (no second writer, rogue device or forged frames); (T2) on reconnect the PC closes the old handle, stops writer threads, purges driver TX/RX queues and records the outcome; (T3) after port re-enumeration the PC observes a proposed **2-second receive-quiet guard**, then generates a fresh nonzero 128-bit SID from the OS CSPRNG, checks against its own retained SID history and logs it; (T4) the PC maintains a **durable CPI journal** for previous commits and failure decisions, with explicit disk flush verified in restart tests; (T5) no arbitrary delayed complete old HELLO/ACTIVATE frame is inserted *after* the purge/quiet guard by the trusted system.

**Observable laboratory checks:** assert exclusive-port acquisition; log purge success/error and last received byte time; record new SID inequality; inject delayed old ACK/HELLO/READY after reconnect and verify current-session rejection; physically power-cycle FPGA while retaining/restarting PC and compare offered UNKNOWN with the durable host record. The 2-second quiet guard is **only a candidate engineering value** (much longer than a maximum 529-byte frame's ≈46 ms line airtime at 115200 8N1), not a proven upper bound on unmeasured USB/driver buffering. If T1–T5 cannot be verified in the lab, mark trust preconditions FAILED and block automatic resumption.

**Explicit limits:** CRC and an opaque 128-bit SID provide accidental stale-byte separation, not cryptographic origin authentication or protection against an active replay attacker. A stale **entire bootstrap exchange** arriving after an FPGA power cycle can be accepted by a device with no retained epoch history and no fresh FPGA boot-incarnation identifier; a PC-generated SID alone cannot prove new device incarnation. No nonvolatile FPGA terminal journal, trusted FPGA nonce or guaranteed USB-disconnect signal is asserted. Engineering decision remains OPEN whether these trust assumptions are sufficient for lab-only operation or an additional device identity mechanism is required.

## 5. RELEASE_CPI and immutable COMMIT when host discards incomplete results

`HOST_DISCARDED_INCOMPLETE_COMMIT` (`host_resolution=3`) is a **candidate explicit fail-closed engineering disposition, NOT a successful CPI and NOT an approved default**. It may be used only when:
1. FPGA still retains **immutable COMMIT(CPI_ID,count)** and the host obtains a CRC/epoch/seq-validated same-decision QUERY reply after recovery; the count is 0..702 and cannot be changed.
2. Host cannot validate every record ID `0..count-1` after the approved retry/recovery path, so it records `FAILED_RESULT_DELIVERY`, never PASS, Pd/Pfa result or a silently truncated list. No next-CPI admission is inferred.
3. The trusted host writes a **durable failure journal entry** (CPI_ID, epoch(s), immutable count, observed record IDs/missing IDs, reason, timestamp and the approved operator/system-engineer disposition). The record must be committed to durable storage before RELEASE is sent.
4. System engineer has **explicitly approved** use of this disposition and its conditions. Otherwise the PC/FPGA remain in unresolved terminal state, no RELEASE and no next CPI.

**Candidate RELEASE wire payload (within S02, but NOT approved):** `sid[16] | command_opcode=0x06:u8 | CPI_ID:u32LE | host_resolution:u8 | expected_outcome:u8 | expected_info:u16LE | audit_id:u64LE` = **33 payload bytes**, **50 framed bytes** (S02 17-byte overhead). `audit_id` is a **nonzero PC-issued reference to the host's durable success/failure journal entry**. FPGA can validate nonzero value, consistent retransmissions and matching CPI/outcome/count, but **cannot verify a PC disk flush or operator approval** over UART; those are explicit trusted-host test preconditions. `expected_outcome=1 COMMIT,2 ABORT`; expected_info=immutable COMMIT count or ABORT reason. An incomplete-COMMIT release requires `host_resolution=3, expected_outcome=1`; wrong CPI_ID, wrong outcome/count, inactive SID, nonterminal CPI, missing/changed audit_id or missing host-failure disposition must reject RELEASE.

**PC transitions:** `HOST_PROVISIONAL -> HOST_INCOMPLETE_NOT_ACCEPTED -> JOURNALED_FAILED_DELIVERY -> RELEASE_PENDING -> RELEASE_CONFIRMED`. Receiving an exact ACK for RELEASE or a new-sequence QUERY showing the matched tombstone completes RELEASE; losing the ACK does not permit silent acceptance. Host stores that the FPGA's immutable decision is COMMIT while the **host delivery outcome is FAILED**, never converts the FPGA terminal decision to ABORT.

**FPGA transitions:** `TERMINAL_COMMIT_DECIDED -> TERMINAL_COMMIT_RELEASE_ELIGIBLE -> RELEASE_TOMBSTONE -> NEXT_CPI_ALLOWED`. Preserve immutable tuple and a small idempotency tombstone `(CPI_ID, COMMIT,count, host_resolution=3, audit_id, accepted_release_seq, epoch)`; identical duplicate RELEASE re-ACKs without releasing the new CPI. New distinct CPI_ID may open only after the host's successful RELEASE acknowledgement/reconciliation and an empty/recovered pipeline. Tombstone is volatile; its retirement window after the next CPI and recovery if RELEASE ACK is lost after tombstone eviction remain OPEN for engineer decision. No partial target list is ever published as successful.

For `VALIDATED_COMMIT` resolution=1 require full host record/count verification and a nonzero host-commit audit_id; for `OBSERVED_ABORT_AND_DISCARDED` resolution=2 require genuine immutable ABORT, all provisional records discarded and a nonzero host failure audit_id. A mere local timeout, a host's missing data, or USB unplug is **not** grounds to mutate the FPGA's COMMIT into ABORT.

## 6. RECOVER_UNKNOWN after global reset or power loss

After any FPGA reset/reconfiguration/power loss that destroys protected terminal state, the device enters `NO_SESSION/UNKNOWN` and may offer `snapshot_kind=0`. It cannot report an earlier historical COMMIT or ABORT. Host behavior depends on its **own prior validation**, not a guessed FPGA state:

| Host prior result | Host action after FPGA UNKNOWN | FPGA action / gate |
|---|---|---|
| **Durably committed and complete** prior CPI (all IDs checked, valid COMMIT, host journal flushed) | Preserve the historical **host-validated COMMITTED** result; separately record `BOARD_TERMINAL_UNKNOWN_AFTER_RESET`. Do not reinterpret it as a new FPGA COMMIT, ABORT or new detection. | Respond UNKNOWN for old CPI; do not fabricate terminal state. Authorize only explicit unknown-recovery for next fresh CPI |
| **Provisional, incomplete or COMMIT never validated** | Mark `HOST_UNKNOWN_NOT_ACCEPTED`, log and discard provisional records; no success or partial-result display. | Respond UNKNOWN, prohibit old-CPI RUN/RESULT/RELEASE and require a fresh verified upload after explicit recovery |
| Host journal missing/corrupt/unflushed | Treat as **not durably validated**, mark UNKNOWN/NOT_ACCEPTED, require operator disposition; do not claim COMMITTED based on volatile memory | Same UNKNOWN gate; no claim of old terminal decision |

**Candidate RECOVER_UNKNOWN command (not approved):** `sid[16] | opcode=0x07:u8 | prior_CPI_ID:u32LE | host_resolution:u8 | audit_id:u64LE` = **30 payload bytes / 47 total frame bytes**. `host_resolution=1 HOST_DURABLY_COMMITTED, 2 HOST_PROVISIONAL_DISCARDED, 3 NO_PRIOR_CPI`; `audit_id` is a nonzero host-generated local journal reference, **not evidence of FPGA historical success**. The FPGA accepts this command only in a new valid epoch, while `snapshot_kind=0`, with no different CPI in progress, a valid packet CRC/sequence and no contradictory stored terminal tuple. It records only the host's recovery acknowledgement in a volatile control register and sends a separately proposed `UNKNOWN_RECOVERY_ACCEPTED` STATUS, carrying the prior CPI_ID and audit_id (specific numeric STATUS code **OPEN**); it must **not** send historical CPI_COMMIT/ABORT. Duplicate command with identical seq and bytes is ACKed idempotently.

PC may open a **new CPI_ID**, distinct from the prior one, only after the recovery STATUS/ACK is matched and its own audit record is durably written; the next 16,896-byte CPI must be uploaded and fully verified anew. If any check fails, remain UNKNOWN_LOCKED. Host control and board outcome are distinguished in the audit trail; this is a candidate lab policy, not a nonvolatile two-phase commit guarantee.

## 7. Proposed handshake timing, retry budget and unresolved-CPI policy

The S02 nominal `2 s per reliable frame` and up to `3 retransmissions` do **not automatically approve** bootstrap SESSION_CONTROL timing. R1 **proposes** reusing them conservatively in the trusted lab, because the largest valid S02 frame takes `529×10/115200≈45.92 ms` to serialize and the new four-message handshake consumes only **172 B ≈14.93 ms**, whereas USB host scheduling/jitter has not been measured.

| Candidate parameter | Proposed value | Interpretation / consequence |
|---|---:|---|
| PC `T_handshake_wait` (HELLO→OFFER and ACTIVATE→READY) | **2 s per attempted request** | After no valid exact response, resend the *identical* request/SID; not a proof of USB upper latency |
| PC retries per HELLO and ACTIVATE phase | **3 retransmissions after original** | Maximum four attempts per phase; about 8 s nominal waiting per failed phase, ignoring serial/host overhead |
| FPGA negotiation idle lease | **12 s since latest valid handshake request** | Candidate > 8 s retry envelope plus 4 s margin. Expiry drops only **pending negotiation**, **never** a decided CPI or an activated epoch |
| FPGA ACTIVE after READY loss | **No automatic counter/session expiry by handshake timeout** | Remain ACTIVE/blocked for matching duplicate ACTIVATE, or replace only by valid new-SID negotiation; do not reset counters |
| COMMIT ACK timeout/retry | S02 nominal 2 s / 3 retries, **ordinary ARQ only** | After exhaustion enter TERMINAL_ACK_UNCERTAIN, not ABORT; same-epoch special replay and new-epoch QUERY require separate approval |
| Unresolved CPI retention / maximum total CPI time | **OPEN, no finite bound approved** | When powered, hold terminal result and block next CPI until explicit reconciliation/RELEASE/UNKNOWN recovery; resource/long-term retention strategy requires approval |

If HELLO/OFFER or ACTIVATE/READY exhausts retries, PC records **HANDSHAKE_FAILED_UNRESOLVED**, closes/reopens USB and starts **a new SID** after trust preconditions; it never asserts that the FPGA did not activate. FPGA lease expiration of a pending negotiation returns it to its prior protected CPI state without clearing COMMIT. Neither timeout nor USB disconnection alone automatically RELEASES, ABORTS or accepts a CPI.

**Illustrative worst failure waiting:** two separately exhausted PC phases might consume approximately **16 s** of modeled handshake waiting in total, if the first phase eventually progresses on its last attempt and the second fails. This is **not** a hard bound: serialization, driver scheduling, host pauses and repeated reconnects are excluded. If the USB link remains absent indefinitely, automatic CPI resolution has **no approved maximum time**. Do not apply the negotiation lease to an ACTIVE COMMIT-uncertain terminal state.

## 8. Wire audit and testing requirements

Existing S02 outer envelope and CRC are not modified. R1 exact proposed handshake full-frame sizes are **41, 43, 44, 44 B**; original v0.1 ACTIVATE/READY each 43 B were missing OFFER's cpi_valid echo. R1 adds one field/byte to each. Normal packets still consume one sequence per direction on first successful acceptance; retransmits keep the exact serialized bytes/sequence. ACK/NACK consume no reliable sequence; every active ACK/NACK/reliable payload carries matching SID. All old epoch frames, including old ACK with the same numerical seq, are rejected before application effect. In case of global reset, the promise is limited by the trust model in Section 4.

**At 115200 8N1** with a proposed 16-B SID prefix and 37-B ACKs, zero retries and no START/STATUS/COMMIT/RELEASE overhead:
- 35 IQ_UPLOAD packets: **19,626 serial bytes**, including ACKs; 34×488+304=16,896 input IQ bytes.
- 35 STAGE_REQUEST and 35 STAGE_DATA packets: **2,835 + 19,661 serial bytes** including ACKs; 34×484+440=16,896 readback bytes.
- 88 RESULT packets for 702 records: **15,638 serial bytes** including ACKs; 87×8+6=702.
- **57,760 bytes = 5.013889 s** of nominal line airtime for upload + complete readback + 702 records. An unretried four-message R1 handshake adds **172 B ≈0.014931 s**. Commands, status, COMMIT/RELEASE, host processing, FPGA processing and retries are extra. This is **not** measured CPI processing rate or an approved latency ceiling.

The new independent plan `engineering/S05-LINK-SESSION-EPOCH-TEST-MATRIX-R1-v0.1.json` preserves **all original LS-01..LS-20** identifiers, expands injection/expected PC/FPGA transition/observable oracle for each and includes a dedicated lost-READY proof-by-trace case, USB disconnect during COMMIT and global-reset UNKNOWN cases. All cases remain `PLANNED_NOT_RUN`; no protocol PASS is claimed. `engineering/S05-LINK-SESSION-EPOCH-R1-WIRE-AUDIT-v0.1.json` contains checked lengths and CRC calculation evidence, not a PC Packetizer/Parser implementation.

## 9. Explicit engineer decisions for R1 sign-off

1. Approve or reject session tag in **every** active frame/ACK, new TYPE 0x09, flags semantics, HELLO/OFFER/ACTIVATE/READY plus R1 `cpi_valid` echo. All are **PROPOSED**.
2. Approve four-message handshake timers, 12-second pending lease, exclusive trusted-PC/driver flush/quiet-guard model; determine whether hardware boot identity is needed for safe operation after power loss. Neither the 2-second quiet period nor host nonce constitutes a security proof.
3. Approve COMMIT outcome immutability and recovery with original same-epoch replay versus new-epoch QUERY, and the scoped exception to S02 post-COMMIT retry exhaustion.
4. Approve or reject explicit `HOST_DISCARDED_INCOMPLETE_COMMIT` resolution, failure-journal requirements, RELEASE tombstone lifetime/next-CPI gate.
5. Approve `RECOVER_UNKNOWN` wire fields, host resolution codes, recovery STATUS schema, reset-state and unique CPI_ID policy. No historical FPGA decision is recoverable after volatile-state loss.
6. Define finite retention, logging capacity and long-term fault behavior if a CPI remains unresolved indefinitely; **do not invent** an overall CPI deadline or automatic success.
7. Seven DSP intermediate-stage readback schemas remain **separately OPEN**, even if this transport addendum is later signed.

**Preserved dispositions:** `REQ-LIST-01 logical completeness=APPROVED`; `REQ-LIST-01 full acceptance=OPEN`; Gate-S04=`CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS`; REQ-RNG-03=`FAIL 4/8` (8/8 criterion unchanged); S04-C02-RISK-PERFORMANCE=`OPEN`; full XC6SLX9 architecture fit=`OPEN`. No numerical RTL, UART RTL, Frame Controller, PC Packetizer/Parser, Ethernet, continuous IQ, tracking, or historical CPI campaign was changed or run in preparing R1.

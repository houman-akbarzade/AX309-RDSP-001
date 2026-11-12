# AX309-RDSP-001 | S05 Link Session / Epoch Engineering Addendum v0.1

**Status:** PROPOSED_FOR_SYSTEM_ENGINEER_REVIEW — NOT APPROVED; NOT UART ICD v1.0 sign-off.
**Baseline:** Git `def322b`; parent `engineering/S05-UART-ICD-v1.0-ENGINEER-REVIEW.md` (R2).
**Date:** 2026-11-12. **Scope:** Laboratory CP2102GM 115200-8N1, CPI-by-CPI/Stop-and-Wait. No UART/Frame Controller RTL or PC Packetizer/Parser implementation authorized by this addendum.

## 1. Problem and contract precedence

S02 C-UART-01 fixes the 17-byte frame overhead, SOF A5 5A C3 3C, version 1, CRC-32/ISO-HDLC, 512-byte maximum payload, independent per-direction reliable sequence, exact ACK, bounded three retransmissions, and nominal two-second per-frame timeout. R2 already proposes application-frame sequencing, no ACK-of-ACK, immutable terminal CPI decision and a distinct new-sequence QUERY reply. **Neither S02 nor R2 has approved a byte-level session epoch protocol.**

A stale ACK containing only a 32-bit sequence may match a different packet after counter restart. A handshake alone, if ordinary packets/ACKs carry no session identity, cannot unambiguously reject stale bytes after sequence reuse. This addendum therefore proposes an explicit **128-bit session ID in every active reliable frame and ACK/NACK**. The proposal changes the payload schema, ACK size and nominal packet counts: it **requires express S02/S05 engineering approval**. Do not implement it as an implicit extension of the existing candidate.

There is no hardware USB-disconnect indication established at the FPGA RXD/TXD interface. Recognition of a lost link is through the host reconnect protocol, serial parser/ARQ timeouts or independently justified board evidence, not an invented USB-connected signal.

## 2. Proposed wire-level epoch envelope

**S02 outer frame remains unchanged:** `SOF[4] | version=0x01[1] | TYPE[1] | flags[1] | seq_LE32[4] | payload_len_LE16[2] | payload[0..512] | CRC32_LE[4]`; CRC covers version through final payload byte.

**Proposal, not approved:**
- Reserve `TYPE=0x09` as `SESSION_CONTROL` for pre-session handshake. This is a **new Type beyond the eight R2 candidate values** and must be approved explicitly.
- Reserve `flags.bit0 = EPOCH_TAG_PRESENT`. For all in-session application packets and ACK/NACK use `flags=0x01`; prepend `session_id[16]` to the payload. Reject `flags!=0x01` or wrong-session IDs while ACTIVE. For bootstrap SESSION_CONTROL only use `flags=0x00`, `header.seq=0` (special pre-session control, not a reliable application seq). Reject other flags or nonzero session-control seq.
- `session_id[16]` is **16 opaque bytes** generated afresh for each new link epoch by the trusted PC using its operating-system cryptographic random source. Preserve byte order exactly as transmitted; it is not an LE integer. Never use all-zero, repeat a previously used PC epoch, or continue after RNG failure. FPGA must not assume onboard random hardware exists. This token guards accidental stale-frame collision; it is **not cryptographic authentication** and cannot defend against an active adversary.
- When ACTIVE, the first 16 bytes of *every* reliable COMMAND/IQ_UPLOAD/STAGE_REQUEST/STAGE_DATA/RESULT/STATUS payload and every ACK/NACK payload are the current session_id. The existing R2 type-specific fields follow unchanged *after* that prefix. CRC covers the prefix. Reject a frame with an old/missing epoch **before** any application/ACK/seq side effect, even if its 32-bit sequence happens to match.
- ACK payload: `session_id[16] | acked_seq:u32LE` (20 bytes), with header.seq=acked_seq; NACK payload: `session_id[16] | expected_seq:u32LE` (20 bytes), with header.seq=rejected_seq; both are **37-byte** framed controls. Both require matching current session, CRC, version, TYPE, flags and length, plus the R2 current-outstanding test. Neither consumes an application sequence nor is ACKed.
- An epoch transition resets application seq to `0` in **each direction only after SESSION_READY is accepted** by the PC and FPGA has activated that same ID. No per-CPI or DSP-reset sequence reset; no u32 wrap within a session. A stale frame from the previous epoch cannot become valid by reusing seq 0 because the 16-byte ID must differ. New-session handshake and epoch reuse safety are sign-off items.

### Effect on packet size (do not silently preserve the old timing model)

| Candidate in-session frame | Payload (including 16-byte session ID) | Maximum payload data | Notes |
|---|---|---:|---|
| IQ_UPLOAD | `session_id[16], CPI_ID_LE32[4], offset_LE32[4], IQ_chunk` | **488 IQ bytes** | 35 upload packets for 16,896 bytes (34×488 + last 304) |
| RESULT | `session_id[16], CPI_ID_LE32[4], K×record[13]`, K=1..8 | **124-byte payload** with K=8 | Full framed RESULT max **141 bytes** |
| STAGE_REQUEST for raw-IQ readback | `session_id[16], CPI_ID[4], stage_id[1], offset[4], count[2]` | 27-byte request payload | Raw-IQ selector still candidate only |
| STAGE_DATA raw-IQ readback | `session_id[16], CPI_ID[4], stage_id[1], offset[4], chunk` | 487-byte limit, **484 IQ bytes** when 4-byte sample-aligned | 35 readback packets (34×484 + last 440) |
| ACK / NACK | `session_id[16], seq_LE32[4]` | 20-byte payload, 37-byte complete frame | R2 original 21-byte control assumption is superseded **only if this addendum is approved** |

Every byte of the 99-bit Grouping record and its five zero padding bits remains the R2 candidate; none of the numerical radar formats change. The previous 34-packet upload and 21-byte ACK timing estimates **continue to describe R2 without epoch prefixes**; they are not valid estimates for this new candidate.

## 3. Candidate SESSION_CONTROL message fields and opcodes

All SESSION_CONTROL frames use the **unmodified S02 outer framing/CRC**, TYPE=0x09 (candidate), flags=0, seq=0, and **no ACK/NACK/ordinary reliable seq allocation**. They may be retransmitted identically by a handshake-specific PC timeout (exact retry/time budget **OPEN**), and duplicate reception has no CPI application effect.

| Opcode | Sender | Exact payload, sequential byte order | Payload/frame lengths |
|---|---|---|---|
| `0x01 SESSION_HELLO` | PC→FPGA | `op:u8, proto_rev:u8=1, session_id[16], requested_mode:u8 (FRESH=0, RECOVER=1), prior_valid:u8 (0/1), prior_CPI_ID:u32LE (0 if absent)` | **24 / 41 bytes** |
| `0x02 SESSION_OFFER` | FPGA→PC | `op:u8, proto_rev:u8=1, session_id[16], snapshot_kind:u8, cpi_valid:u8, retained_CPI_ID:u32LE (0 if absent), info:u16LE (count or reason; 0 if none)` | **26 / 43 bytes** |
| `0x03 SESSION_ACTIVATE` | PC→FPGA | `op:u8, proto_rev:u8=1, session_id[16], accepted_mode:u8 (FRESH=0, RECOVER=1), observed_snapshot_kind:u8, observed_CPI_ID:u32LE, observed_info:u16LE` | **26 / 43 bytes** |
| `0x04 SESSION_READY` | FPGA→PC | `op:u8, proto_rev:u8=1, session_id[16], result:u8 (READY=0, REJECT=1, NEED_RECONCILE=2), snapshot_kind:u8, retained_CPI_ID:u32LE, info:u16LE` | **26 / 43 bytes** |

In `SESSION_OFFER`, proposed `snapshot_kind`: `0=NO_RETAINED_STATE/UNKNOWN`, `1=ACTIVE_PRETERMINAL`, `2=DECIDED_COMMIT`, `3=DECIDED_ABORT`, `4=TERMINAL_ACK_UNCERTAIN_COMMIT`. `info` is the exact immutable record count for COMMIT/UNCERTAIN or reason for ABORT; no invented numeric fault reasons are accepted. For missing state, `cpi_valid=0, retained_CPI_ID=0, info=0`. If the requested old CPI_ID differs from the retained one, FPGA **must not overwrite the retained CPI**; OFFER shows the actual retained ID, PC declines activation or uses a separately approved operator recovery procedure.

For power-loss restart, `NO_RETAINED_STATE` means the **FPGA has no credible terminal history**, not proof that the earlier CPI failed or succeeded. `SESSION_READY` is never a CPI_COMMIT and must not be interpreted as one. No automatically approved `UNKNOWN` TYPE/STATUS numeric code is introduced here; `snapshot_kind=0` is only a bootstrap observation until final ICD sign-off.

## 4. Link-session state machines and permitted transitions

**PC states** (separate from its CPI provisional/committed/invalid record state):

| PC state → event → next state | PC action | FPGA required response / acceptance condition |
|---|---|---|
| `DISCONNECTED/NO_SESSION → port available → HELLO_SENT` | Flush serial receive/transmit OS buffers, stop old writer, create a **fresh nonzero 128-bit session_id**, retain prior CPI_ID and provisional record ledger, send SESSION_HELLO | No application packet may be accepted before new epoch activates |
| `HELLO_SENT → valid matching OFFER → OFFER_CHECKED` | Validate CRC, revision, echoed session_id, retained CPI_ID/outcome/count; if mismatch or unknown, do **not** infer success | FPGA may have retained a decided COMMIT or only UNKNOWN after reset; never silently replace it |
| `OFFER_CHECKED → accepted snapshot/mode → ACTIVATE_SENT` | Echo full observed snapshot in SESSION_ACTIVATE | FPGA compares epoch/mode/snapshot fields against its current OFFER; if changed, respond REJECT and keep quarantined |
| `ACTIVATE_SENT → matching READY result=READY → ACTIVE` | Retain session_id, initialize PC reliable seq=0 for both directions, then send authenticated-by-epoch (not cryptographic) ordinary frames | FPGA must have activated the same epoch, reset that epoch's reliable counters once, and opened acceptance of only correctly tagged new frames |
| `HELLO_SENT/ACTIVATE_SENT → timeout` | Retry **same** handshake bytes/epoch within separately approved handshake budget; no IQ/COMMIT side effect | Repeated HELLO resends identical OFFER snapshot if unchanged; repeated ACTIVATE resends READY without resetting active counters twice |
| `ACTIVE → link timeout/port loss → DISCONNECTED` | Freeze pending CPI state; quarantine all prior session ACKs; create **new** epoch on reconnect, never recycle old sequence | FPGA may not know USB disconnected instantly; once it sees a fresh HELLO, it freezes/quarantines old session traffic while preserving immutable terminal state |
| `ACTIVE_RECOVER → valid STATUS QUERY result → ACTIVE/TERMINAL_RECONCILED` | Validate same CPI_ID, terminal outcome/count and full record ledger before COMMIT; use RELEASE only under Section 6 | FPGA sends fresh-sequenced response in new epoch after old transport is retired |
| `UNKNOWN snapshot → HOST_UNKNOWN` | Do not claim FPGA COMMIT/ABORT. Mark any uncommitted provisional data invalid; only explicitly approved recovery may open a new CPI | No automatic restart; FPGA may start fresh only after host records UNKNOWN and executes explicit recovery command approved in Section 6 |

**FPGA states** (separate protected terminal state and DSP reset):

| FPGA state → trigger → next state | Required actions / transition guard |
|---|---|
| `NO_SESSION → valid fresh HELLO → NEGOTIATING` | Check SOF/version/CRC/opcode/nonce length, stage proposed epoch, preserve existing CPI terminal record; return OFFER |
| `ACTIVE_OLD_EPOCH → fresh valid HELLO → NEGOTIATING` | Quarantine old ACK/data and old retransmission, preserve immutable CPI; reject old epoch traffic as application progress. Do not interpret new HELLO as RELEASE/ABORT |
| `NEGOTIATING → identical HELLO → NEGOTIATING` | Idempotently resend OFFER, no sequence reset or CPI modification |
| `NEGOTIATING → exact ACTIVATE echo → ACTIVE_NEW_EPOCH` | Atomically set current epoch, invalidate old transport sequence/replay eligibility (archive original bytes for diagnostics if retained), initialize directional reliable seq=0 once, respond READY |
| `ACTIVE_NEW_EPOCH → duplicate ACTIVATE/HELLO for the same newly activated epoch → ACTIVE_NEW_EPOCH` | Resend the matching READY/OFFER without a new application side effect; **never reset sequence counters a second time**. HELLO for a different or retired epoch is gated by the trusted-host/new-epoch policy, not treated as ordinary data |
| `ACTIVE → wrong session_id, missing prefix or stale ACK → ACTIVE` | Discard before reliable ACK/sequence/CPI side effects; count diagnostic |
| `ACTIVE → DSP-only reset → ACTIVE` | Retain epoch/replay/terminal register bank; reset only DSP |
| `ACTIVE → global FPGA reset/power loss → NO_SESSION, terminal UNKNOWN` | No claim of retained state, no acceptance of previous session packets; require new handshake and host recovery |
| `ACTIVE → link failure after COMMIT decided → TERMINAL_ACK_UNCERTAIN` | Preserve immutable outcome/count and block next CPI; do not emit contradictory ABORT |
| `TERMINAL_ACK_UNCERTAIN → successful new epoch + QUERY → TERMINAL_DECISION_REPORTED` | Return immutable COMMIT under **new** reliable sequence, not old-epoch wire bytes or old seq |
| `TERMINAL_DECISION_REPORTED → validated RELEASE_CPI → RELEASED` | Retain idempotent release tombstone until next clean CPI transition, then become eligible for new CPI_ID; never change prior COMMIT to ABORT |

**Critical exception to R2 ordinary retry:** In an *unchanged* session, a still-outstanding COMMIT uses **identical wire bytes and original sequence S**, including any separately approved QUERY-triggered recovery replay. Once a **new epoch has been activated**, old S and old session_id cannot be retransmitted as valid new-session traffic. Instead the PC sends `QUERY_CPI_STATUS(CPI_ID)` as a **new PC→FPGA application frame** with new-session seq (initially 0); FPGA replies with a **new FPGA→PC sequence** (initially 0 if no prior new-session reply), reporting the **same immutable COMMIT(CPI_ID,count)**. This is *new status delivery*, not retry of original S. Both paths remain subject to explicit ICD sign-off.

**Active preterminal CPI after USB loss:** If a new-epoch HELLO finds an uploaded/processing but **not yet terminal** CPI, the FPGA must report `ACTIVE_PRETERMINAL` and quarantine old-epoch bytes; the PC must not treat it as a successful run. Whether to explicitly abort/reupload or resume a verified stage from retained buffers is **not approved**. Until a separate disposition is agreed, do not resume processing or accept another CPI.

**Preventing stale HELLO takeover:** Only a trusted PC should drive the sole serial port. FPGA should reject an already-retired epoch ID while it has a retained history, and new HELLO must not clear a running CPI or immutable terminal data. The previous epoch's ACKs are harmless to the new epoch **only because the epoch tag is checked on every frame**. A stale complete HELLO/OFFER/ACTIVATE exchange following an FPGA power cycle cannot be ruled out absolutely without fresh device incarnation evidence, reliable host buffer purge and/or authenticated session binding. **This limitation is OPEN**: propose a required trusted-host receive-buffer flush and fresh PC entropy as a laboratory assumption, not a security or arbitrary-power-loss replay guarantee. The final engineer must decide if extra FPGA boot-identity hardware/nonvolatile evidence is required.

## 5. Stale ACK/NACK, sequence and error rules

1. For in-session ACK acceptance require **all**: valid S02 frame CRC/length/type/flags, 16-byte exact current session_id, ACK header.seq==ACK payload.acked_seq, one outstanding reliable message whose sequence exactly matches, and a valid current CPI/session context. Only then free replay and advance once. Previous-current delayed ACK may complete a still-outstanding retry; duplicate after completion is ignored.
2. ACKs from an old epoch, duplicate or stale previous-CPI ACK, ACK for a future seq, mismatched header/payload, and ACK after session loss must be ignored; none can free a new packet. A stale ACK with the *same numerical 32-bit sequence* as a new-session outstanding packet is rejected because `session_id` differs.
3. For NACK require valid frame and current epoch, but **never treat NACK as ACK**. Only NACK header.seq==current outstanding and expected_seq==outstanding permits bounded identical retransmission. A claim `expected_seq==outstanding+1` does **not** authorize release; exact ACK still required. All stale/future NACKs are diagnostic only.
4. Duplicated accepted application frame re-ACKs without reapplying if it is byte-identical to the immediately last accepted application packet in the same epoch. Future or nonidentical old frame produces expected-sequence NACK where parseable, no application side effect.
5. On epoch activation, both directional app sequences reset to 0 exactly once; no sequence wrap within epoch; epoch re-use forbidden. On malformed frame, no state change. A non-epoch-tagged R2 frame must **never be treated as valid R3 active traffic**, even if its seq happens to match.

## 6. Terminal recovery, RELEASE_CPI and UNKNOWN policy

**CPI_ABORT vs terminal immutability:** An explicit `CPI_ABORT` is legal only while no immutable COMMIT has been selected. A prior COMMIT decision cannot be negated by a later link, ACK or USB error.

**Protected terminal tuple:** `{CPI_ID, outcome=COMMIT|ABORT, count_u16|reason_u16, first_fault, terminal_ack_uncertain, last_outstanding_frame_metadata}`. Once outcome is decided, it is immutable. Stored in a controller/reset domain distinct from pipeline datapath; survives DSP-only reset and parser soft-reset **only while powered and the protected register bank remains intact**. An FPGA reset/reconfiguration/power loss offers **no guarantee** of retaining this tuple; no FPGA nonvolatile journal has been approved.

**SESSION_HELLO RECOVER during TERMINAL_ACK_UNCERTAIN:**
- PC retains last CPI_ID, any already validated provisional target records, prior host-commit state and a fresh session ID; FPGA returns OFFER kind=4 with same CPI_ID and count.
- New-session activation invalidates the **old transport outstanding packet**, but does **not** mutate the terminal decision. PC sends new-sequence QUERY_CPI_STATUS under new epoch, FPGA returns immutable COMMIT using a new-sequence STATUS frame. PC validates record set and count. If complete, it commits/keeps its already committed result idempotently; if missing records, it marks **HOST_INCOMPLETE/NOT_ACCEPTED** and must never claim a successful result solely from the status.
- A query answer does not itself RELEASE the CPI. It is a proof of the FPGA's *terminal decision*, not proof of the PC's data completeness. If host data is incomplete, recovery of those bytes is not guaranteed: Grouping results might no longer be available for retransmission. Any explicit discard-and-release is a **separate candidate disposition requiring approval**; no Top-K or silent loss is introduced.

**Candidate RELEASE_CPI command extension (new schema, NOT APPROVED):** Existing COMMAND keeps `session_id[16] | opcode:u8=0x06 | CPI_ID:u32LE`; RELEASE adds `host_resolution:u8 | expected_outcome:u8 | expected_info:u16LE` (9 bytes after epoch, 25-byte total payload). Codes: `host_resolution=1 VALIDATED_COMMIT`, `2 OBSERVED_ABORT_AND_DISCARDED`, `3 HOST_DISCARDED_INCOMPLETE_COMMIT` (**engineer exception/explicit local failure only**). `expected_outcome=1 COMMIT/2 ABORT`; expected_info equals immutable count or reason. FPGA must reject RELEASE if mismatched CPI_ID, terminal outcome/info, active epoch, unresolved stream or unrecognized host-resolution. There is no silent implicit RELEASE from ACK, QUERY or USB reconnect.
- For `VALIDATED_COMMIT`, PC must hold complete CRC-validated records with IDs 0..count−1 and successful COMMIT/status recovery. For `OBSERVED_ABORT`, PC must have invalidated all provisional records. For `HOST_DISCARDED_INCOMPLETE_COMMIT`, the host records an explicit failed-delivery outcome (never success); FPGA retains the immutable COMMIT decision in its release tombstone. The acceptability of this exception is an OPEN engineer decision.
- RELEASE is reliable and sequence-protected; duplicate identical RELEASE must be re-ACKed without clearing a different CPI. On accepted RELEASE, FPGA records a small **idempotent tombstone** (CPI_ID, immutable terminal tuple, host resolution and accepted seq) until next transaction safely begins. It may admit the next CPI only after valid RELEASE and new distinct CPI_ID. The host cannot assume RELEASE completed until its ACK or an idempotent terminal-status reconciliation confirms it. Tombstone persistence after power loss is not guaranteed.

**UNKNOWN after global reset/power loss:** The FPGA offers snapshot_kind=0/NO_RETAINED_STATE; it must neither invent a historical COMMIT nor emit a historical ABORT. The PC retains its own durable record of a **previously verified COMMIT** if one exists, otherwise marks provisional results UNKNOWN/NOT_ACCEPTED and discards them for ordinary operation. A historical FPGA decision cannot be recovered from volatile RAM after power loss. Propose a separate `RECOVER_UNKNOWN` reliable COMMAND opcode=0x07 with `session_id[16] | opcode:u8 | prior_CPI_ID:u32LE` to record explicit host acknowledgement of irrecoverable FPGA state; only then may a **new CPI_ID with newly verified 16,896-byte upload** be admitted. Do not treat this as RELEASE_CPI or ABORT for the missing transaction; numeric command code, host journal requirements and any physical safety consequences need final approval. If the host has a previously committed durable result, the board still returns UNKNOWN, not a contradictory failure verdict.

**After COMMIT retry exhaustion in the same epoch:** enter TERMINAL_ACK_UNCERTAIN; do not exceed S02 retransmission limit for normal ARQ, do not issue ABORT, and do not release the CPI by timeout. Recovery must use a separately authorized QUERY-triggered same-sequence retry exception in the old active epoch or the **new-epoch** path described above. Neither exception is presently approved.

## 7. Independent test matrix and acceptance boundaries

Tests below are **specified, not executed**. Each test should have preserved packet bytes/CRC, injected timing and session IDs, PC/FPGA state traces, accepted records, ACK/NACK decisions and a PASS/FAIL oracle. `engineering/S05-LINK-SESSION-EPOCH-TEST-MATRIX-v0.1.json` provides the machine-readable cases.

| ID | Injection / setup | Mandatory expected PC and FPGA outcome |
|---|---|---|
| LS-01 | Cold HELLO/OFFER/ACTIVATE/READY, all frames valid | Both ACTIVE with identical fresh epoch, reliable seq starting at 0; no CPI side effect |
| LS-02 | Drop OFFER or READY, duplicate HELLO/ACTIVATE | Retry same handshake fields; idempotent OFFER/READY; **no double seq reset** |
| LS-03 | Old ACK with seq=0 after new epoch has issued seq=0 | Old session_id rejected; current replay remains outstanding; new exact ACK required |
| LS-04 | Old-epoch IQ_UPLOAD/RESULT/STATUS with valid CRC injected into new epoch | Discard before application/seq update, no IQ writes or ghost COMMIT |
| LS-05 | Duplicate/delayed current ACK, mismatched ACK header/payload, stale/future NACK | Only exact current ACK advances once; rejected controls cannot release a replay image |
| LS-06 | FPGA COMMIT transmitted, ACK lost, retransmission still on same epoch | Same bytes/sequence for all authorized ordinary retries; PC deduplicates, no contradictory ABORT |
| LS-07 | **USB unplug after PC received COMMIT but before FPGA receives its ACK**; FPGA protected terminal state survives | New-epoch handshake offers retained decided/ACK-uncertain COMMIT; PC new QUERY, FPGA **new-sequence** same-decision reply; host commits idempotently, explicit RELEASE gates next CPI; old ACK rejected |
| LS-08 | **USB unplug after last RESULT but before any COMMIT reaches host** | PC provisional records stay invalid until recovered same-CPI COMMIT and full ID/count verification; no false success |
| LS-09 | COMMIT retries exhausted while USB down | FPGA stays TERMINAL_ACK_UNCERTAIN; never ABORT, never begin new CPI; later QUERY reports COMMIT |
| LS-10 | Reconnect but one or more provisional RESULT records were lost on PC | QUERY reports immutable COMMIT, PC refuses success; explicit HOST_DISCARDED resolution (if approved) or hold unresolved; no silent drop |
| LS-11 | FPGA power cycle between COMMIT send and ACK; PC had not received valid COMMIT | FPGA offers NO_RETAINED_STATE; PC UNKNOWN/NOT_ACCEPTED; only explicit RECOVER_UNKNOWN plus full new CPI can proceed |
| LS-12 | FPGA power cycle after PC committed but before RELEASE | FPGA UNKNOWN; PC preserves only its independently durable verified result, new FPGA cannot claim previous COMMIT |
| LS-13 | Stale HELLO/READY or old USB buffered data after reconnect | PC requires fresh echoed epoch, FPGA quarantines previous epoch; old app/ACK bytes rejected; malicious/old complete handshake limitation documented |
| LS-14 | RELEASE_CPI wrong CPI_ID, wrong expected count, wrong outcome, duplicate, missing ACK | Reject mismatch; duplicate idempotent; tombstone retained; do not clear unrelated CPI |
| LS-15 | Query arrives while original COMMIT still outstanding, then after new epoch | Same epoch: original exact-frame replay only and deferred new response; new epoch: new-sequence QUERY and fresh reply, immutable decision |
| LS-16 | Global reset during upload, DSP reset during COMMIT, parser reset mid-frame | Upload reset requires new full CPI; DSP-only reset preserves terminal/epoch; parser reset discards partial frame only |
| LS-17 | Sequence wrap, repeated epoch token or nonce-generator failure | Refuse new session/ordinary traffic until safe new unique epoch; never reuse old seq without binding |
| LS-18 | Device says another CPI_ID is retained while PC requests FRESH | FPGA refuses silent overwrite; PC must reconcile existing CPI or record explicit UNKNOWN recovery |
| LS-19 | 35 IQ packets (488-byte max), readback 35 aligned chunks, 88×up-to-8 RESULT | Exact byte/CRC/sequence/epoch coverage; no processing without readback; COMMIT only after verified records |
| LS-20 | Seven DSP stage-output STAGE_REQUEST selectors with no approved schema | Reject unsupported schema/selector; leave seven REQ-OBS-01 schemas OPEN rather than synthesizing guessed encodings |

**No standalone PC Packetizer/Parser, UART RTL, ISim serial test, FPGA synthesis or board test is reported PASS by this addendum.** The older grouping+FIFO8 702/702 laboratory simulation remains valid only for its original scope.

## 8. Engineering decision list; nothing auto-approved

1. **Approve or reject** adding SESSION_CONTROL TYPE 0x09, flags.bit0 epoch present and a 128-bit session ID prefix on every reliable frame/ACK/NACK. This changes the candidate R2 transport payload capacities and timing calculations; S02's fixed framing and CRC remain unchanged.
2. Approve exact HELLO/OFFER/ACTIVATE/READY opcodes, snapshot kinds, duplicate handling and secure-enough **trusted laboratory PC / fresh 128-bit token** assumption, or demand stronger device-boot identity/nonvolatile/session authenticity. No security guarantee is invented.
3. Approve epoch seq reset at READY, handling of stale frames, no rollover, and the normal-ARQ vs. COMMIT-reconciliation scoped exception.
4. Approve RECOVER_UNKNOWN and RELEASE_CPI extended payload/disposition codes, especially whether **HOST_DISCARDED_INCOMPLETE_COMMIT** can unblock a lab CPI without falsely recording success, and whether a durable PC log is mandatory.
5. Approve reset-domain retention obligations, link-loss timeouts, how long unresolved CPI state may be held, and fallback behavior if USB never reconnects. No full-CPI maximum wait is fabricated.
6. Independently specify and approve **seven** DSP stage-output schemas under REQ-OBS-01; none is approved by the raw-IQ selector in this addendum.

**Unchanged:** logical cluster completeness 0..702 APPROVED, no Top-K or silent discard; full REQ-LIST-01 acceptance OPEN; Architecture C stays on FPGA including Clustering, no tracking on FPGA; Gate-S04=CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03=FAIL 4/8; S04-C02 Fixed-Point performance risk=OPEN; full XC6SLX9 feasibility=OPEN. Final UART ICD v1.0 sign-off remains **NOT GIVEN**.


## 9. Quantified impact and explicit link-session gaps (candidate only)

At nominal 115200 baud, 8N1, assuming exactly one 37-byte ACK per reliable frame and no retries, the session-tagged **candidate** yields:

| Phase | Frames | Application/raw and overhead bytes including proposed ACKs | Minimum UART line time |
|---|---:|---:|---:|
| Upload 16,896 raw IQ bytes | 35 IQ_UPLOAD | 19,626 | 1.703646 s |
| Request 35 bytewise readback chunks | 35 STAGE_REQUEST | 2,835 | 0.246094 s |
| Return 16,896 IQ readback bytes | 35 STAGE_DATA | 19,661 | 1.706684 s |
| Send 702 target records, at most 8 per RESULT | 88 RESULT | 15,638 | 1.357465 s |
| **Upload + readback + all 702 outputs** | **193 reliable data frames** | **57,760 bytes** | **5.013889 s** |

A fresh four-message SESSION_HELLO/OFFER/ACTIVATE/READY handshake contributes a further 170 wire bytes, or a nominal **0.014757 seconds**, if all four succeed once; this is **not** included in the table. UART START/STATUS/COMMIT/RELEASE, ACK/retry delays, host scheduling, FPGA processing cycles and actual baud/board turnaround are also excluded. This is not a measured CPI/s throughput or a time bound. The prior R2's 4.465451-second example assumes no epoch prefix and therefore is not interchangeable with this proposal.

**Security and reset limitations:** Session IDs are host-created freshness labels, not MACs. A hostile endpoint that can inject a valid 128-bit epoch and CRC is not prevented by this CRC-protected protocol. Even for a trusted host, stale *complete bootstrap exchanges* after a power cycle need a positive bound on host/device buffered-byte flushing or fresh FPGA boot-incarnation evidence; a PC-created nonce alone does not prove a new FPGA boot instance. Such additional mechanism remains a decision gate. The intent here is deterministic **logical rejection of an old-epoch ACK once a different new epoch is activated**, not a claim of authenticated or nonvolatile replay resistance.

**Staged implementation guard:** Do not modify S02 requirements, the R2 byte-level ICD, any radar numerical RTL, UART RTL or Frame Controller RTL until the engineer decides whether the additional TYPE/flag/payload schema is acceptable. If 16-byte tags on *every* reliable packet are rejected for resource or throughput reasons, a different explicit epoch-binding mechanism must be proposed and independently validated; simply resetting 32-bit seq on USB reconnect is insufficient to guarantee rejection of all stale ACKs.

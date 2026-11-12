# AX309-RDSP-001 | S05 UART ICD v1.0 — ENGINEER REVIEW CANDIDATE

**Status:** REVISED_CANDIDATE_CONDITIONALLY_ACCEPTED_FOR_SPECIFICATION_NOT_SIGNED_OFF. The suffix "v1.0" denotes a **candidate for final engineering sign-off**, not an enacted or verified protocol. Detailed revision R2 rules in Sections 9–11 supersede the shorter descriptions in Sections 3 and 6 where necessary.
**Baseline:** `32e36ab` (earlier candidate derived from `c5160db`). **Date:** 2026-11-12. **Owner of approval:** System engineer. **Revision:** R2, conditional specification review.

## 1. Authority, separation of decisions and constraints

The following **are already approved**: lab-only CPI-by-CPI / Stop-and-Wait over AX309 CP2102GM, nominal 115200 8N1 (to be checked on board), mandatory FPGA MF/MTI/FFT/Power/CA-CFAR/8conn Grouping, no tracking and no continuous-IQ deadline; logical completeness of the 0..702 cluster list, no Top-K, no silent drop, fatal whole-CPI invalidation, provisional results until complete verified COMMIT.

The following **are proposed for sign-off here**, and are **not** production-RTL evidence: 13-byte LE record layout with zero padding, RESULT batch size <=8, an ACK-safe retained wire-frame image, an 8-record *lab prototype* FIFO (not a final production depth), bytewise full input-CPI readback in v1, and idempotent COMMIT/terminal reconciliation keyed by CPI_ID.

Frozen S02 envelope and CRC take precedence over this proposal:
`SOF[A5 5A C3 3C;4] | version=01[1] | TYPE[1] | flags[1] | seq[4 LE] | payload_len[2 LE] | payload[0..512] | CRC-32[4 LE]`.
Frame length=17+payload_len (<=529 bytes). CRC32/ISO-HDLC covers version through last payload octet, excludes SOF and CRC; reflected poly 0xEDB88320, initial/final XOR FFFFFFFF; `123456789 -> CBF43926`. No SOF escaping is required because length and CRC delimit accepted frames. On malformed version/type/length, truncated data, bad sequence or CRC: no application side effect, resynchronize via byte scanning.

## 2. Candidate TYPE and CMD/STATUS assignments — all require approval

The following distinct numeric TYPE identifiers are **proposed**, not observed approved values:

| TYPE | Candidate code |
|---|---:|
| COMMAND | 0x01 |
| IQ_UPLOAD | 0x02 |
| STAGE_REQUEST | 0x03 |
| STAGE_DATA | 0x04 |
| RESULT | 0x05 |
| ACK | 0x06 |
| NACK | 0x07 |
| STATUS | 0x08 |

For v1 proposal, `flags=0x00`; unknown flags or opcodes are rejected, not silently interpreted. Reserved future flags and schema versions require separate approval.

Candidate COMMAND payload: `opcode:u8 | CPI_ID:u32LE` (5 bytes). Opcodes:
- 0x01 `OPEN_CPI`: reserve a new CPI_ID and initialize its upload/transaction state; provides the semantic `CPI_START`.
- 0x02 `REQUEST_INPUT_READBACK`: only after upload coverage complete; host requests bytewise STAGE_DATA.
- 0x03 `HOST_VERIFIED_INPUT`: assertion by the trusted PC that every returned byte equals its original upload; FPGA may mark it verified *only if* its upload coverage/sequence/CRC checks also pass.
- 0x04 `RUN_CPI`: permitted only after full coverage and verified input. Repeated identical RUN for an already-run CPI is idempotent (cannot rerun or double-commit).
- 0x05 `QUERY_CPI_STATUS`: read back persistent CPI state including COMMIT/ABORT for reconnect/reconciliation.
- 0x06 `RELEASE_CPI`: host confirms the terminal state has been reconciled and requests the board to become available for a different CPI_ID; not an implicit ABORT.

Candidate STATUS payload: `status_code:u8 | CPI_ID:u32LE | optional status-specific fields`.
Suggested status_code values: 0x01 `UPLOAD_OPEN`; 0x02 `UPLOAD_COMPLETE_UNVERIFIED`; 0x03 `INPUT_VERIFIED`; 0x04 `PROCESSING`; 0x05 `RESULT_STREAM_START`; 0x06 `CPI_COMMIT` (add `count:u16LE` in 0..702); 0x07 `CPI_ABORT` (add `reason_code:u16LE`); 0x08 `TERMINAL_RECONCILED`. The **internal** COMMIT_ACK_UNCERTAIN state is not a distinct terminal message: QUERY must replay the same CPI_COMMIT(CPI_ID,count), avoiding a second interpretation of success. Exact reason-code table is still a decision item; do not improvise success/error byte encodings in FPGA before sign-off.

## 3. Bidirectional stop-and-wait sequence/ACK proposal

S02 binds a monotonically increasing sequence per direction, exact matching ACK, idempotent duplicate, NACK expected sequence, 2-second nominal timeout **per frame**, and 3 retransmissions after the initial attempt.

**Candidate clarification requiring explicit approval:** sequence `seq` for reliable application frames (COMMAND/IQ_UPLOAD/STAGE_REQUEST/STAGE_DATA/RESULT/STATUS) advances by one per new frame **per transmitter direction**; retries reuse the original seq and identical wire bytes. ACK/NACK are **control responses**, not themselves ACKed or included in that ordered application-data sequence. Their header `seq` reflects the triggering application-frame seq; ACK payload is `acked_seq:u32LE` (4 bytes), NACK payload is `expected_seq:u32LE` (4 bytes). Peer matches ACK to the exact outstanding sender seq and CPI state. This exemption prevents the unbounded ACK-of-ACK loop and missing ACK-control sequence gaps. It must be reviewed as a scoped interpretation of the S02 phrase "sequence per link direction"; a stricter S02 interpretation requires engineering disposition before implementation.

At most one *reliable* packet per direction may be outstanding. A valid duplicate of an already applied reliable packet elicits the same ACK without applying it twice. A future seq elicits NACK with expected seq; a corrupt/malformed frame never advances expected seq or writes IQ. CRC error detection is not mathematically guaranteed for every arbitrary error pattern, but all injected corruption cases must fail safe.

**Replay invariant:** preserve exact serialized bytes including TYPE, seq, payload and CRC until its ACK is accepted, or an explicit fault/terminal outcome. FPGA cannot release the last retransmittable target bytes simply on physical UART transmission.

## 4. PC -> FPGA: whole-CPI upload and bytewise readback (candidate v1)

Normative IQ bytes: 33 pulses x 128 complex samples, pulse-major, I then Q, signed little-endian int16 Q1.15; 16,896 bytes. IQ_UPLOAD payload: `CPI_ID:u32LE | byte_offset:u32LE | raw_bytes[1..504]`. For contiguous maximal 504-byte chunks: 34 packets (33 x 504 bytes + final 264); no overlap, gaps, out-of-bounds byte offsets or mixed CPI_ID.

For v1, **proposed verification** is exact 16,896-byte host readback, not an invented FPGA SHA-256 obligation. Candidate STAGE_REQUEST payload: `CPI_ID:u32LE | stage_id:u8 | offset:u32LE | byte_count:u16LE` (11 bytes); `stage_id=0x00` means **input IQ in its original byte ordering**. Candidate STAGE_DATA payload: `CPI_ID:u32LE | stage_id:u8 | offset:u32LE | byte_chunk[1..500]` (9 bytes prefix, up to 500 bytes IQ), each with frame CRC/seq. Request 34 sequential chunks with four-byte-aligned offsets/counts: 33 x 500 plus final 396 bytes. Host compares all bytes with the source 16,896-byte vector. Only after byte-for-byte equality does PC send HOST_VERIFIED_INPUT, then RUN_CPI. FPGA itself also checks exact reassembly/coverage and cannot RUN earlier.

**Implementation dependency:** The FPGA must preserve uploaded IQ until readback completion. S02 REQ-OBS-01 separately requires all **seven FPGA processing-function outputs** to be available for segmented readback. All seven DSP stage-output schemas (IDs, dimensions, bit widths, signedness, element order, scaling, flags, buffer lifetime and wire encoding) remain **OPEN for separate specification and approval**. The proposed stage_id=0x00 is **only raw-input-IQ readback**, not an approved DSP-stage schema.

## 5. FPGA -> PC: 99-bit record wire image and RESULT batching (candidate v1)

Current Grouping bus packs the exact bit fields as:
`{record_id[9:0], range[6:0], doppler_bin[4:0], signed_doppler[5:0], peak_power[45:0], cluster_cells[11:0], tie_flag[0], equal_power_cells[11:0]}`, occupying bits 98..0 in that order.

Proposed per-record wire representation:
- Interpret the 99-bit concatenation as an **unsigned 104-bit number** with bits [103:99] = 00000.
- Transmit 13 octets **least-significant octet first**; the high five padding bits in the last octet MUST be zero; reject nonzero padding.
- The signed Doppler subfield is the original six-bit two's-complement value, not a byte-swapped or 8-bit signed integer. The power subfield remains the **stored integer**; never rescale or requantize during serialization.

Proposed RESULT payload: `CPI_ID:u32LE | record_0[13] | ... | record_(K-1)[13]`, `1<=K<=8`; `payload_len=4+13K`, maximum **108** bytes. Count K is derived exactly from payload length; reject `(payload_len-4)%13!=0`, K=0, K>8 and inconsistent or repeated record IDs. With 702 records, 88 RESULT frames (87 x 8 plus final 6). A CPI with zero targets skips RESULT packets and sends valid COMMIT count=0.

Use the tested 8-slot FIFO only as a lab reference. **It is not a signed-off production FIFO depth.** The outgoing RESULT transmitter needs a separate retained copy of each **complete framed UART packet** (up to 125 bytes for K=8: 17 overhead + 108 payload), or an equivalently durable replay mechanism. The FIFO may be dequeued once bytes have been transferred into this retained image; the image cannot be overwritten until exact ACK. Grouping keeps out_valid and the record stable on FIFO_FULL. Production FIFO plus replay buffer RAM/LUT/FF cost is **NOT YET MEASURED**.

## 6. CPI_COMMIT / CPI_ABORT and lost-ACK reconciliation (proposed)

State per CPI_ID: `OPEN -> UPLOADING -> COMPLETE_UNVERIFIED -> VERIFIED -> RUNNING -> RESULTS_PROVISIONAL -> COMMIT_SENT -> COMMITTED_RECONCILED`, or `CPI_ABORTED` from any *pre-commit* state on an unrecoverable fault.

A COMMIT status includes `CPI_ID:u32LE + count:u16LE`. Host requires exactly distinct record IDs 0..count-1, all validated CRC/seq and matching CPI_ID, then marks CPI committed. If last record arrives but COMMIT never does, it remains **invalid/uncommitted**. On CPI_ABORT or unrecoverable disconnect *before COMMIT*, discard provisional records. COMMIT for zero records is valid.

**Final-message ambiguity:** after transmitting COMMIT, the FPGA must persist `CPI_ID, COMMIT contents, committed/uncertain state` across ordinary DSP abort/reset; if the COMMIT ACK is lost, it must retransmit **the same COMMIT**, and on retry exhaustion must enter a **terminal-ack-uncertain** status rather than emit a contradictory CPI_ABORT. QUERY_CPI_STATUS is idempotent and returns the **original CPI_COMMIT(CPI_ID,count)** or CPI_ABORT(CPI_ID,reason) terminal content, not merely an ambiguous boolean. A host missing the original COMMIT may accept this replayed COMMIT only after checking the complete record-ID set; a host already committed treats it as an identical duplicate. The host may resend its original COMMIT ACK or issue RELEASE_CPI after successful reconciliation. The next CPI cannot begin until the terminal result is reconciled or an explicit recovery policy is invoked.

This **is an engineering decision point** because S02 normally says "abort CPI after retry exhaustion." Applying that literally to an already delivered COMMIT could violate the previously approved all-or-nothing host contract. Require a **scoped system-engineer approval** of terminal reconciliation instead of retrospective contradictory ABORT. There is no finite protocol that can guarantee simultaneous knowledge of a delivered COMMIT under arbitrary permanent link loss; the safe behavior is persistent, queryable uncertainty, not a fabricated successful transfer.

A fatal DSP error *before COMMIT* latches CPI_ID/error outside the shared DSP reset domain, inhibits successful terminal status, attempts CPI_ABORT when link is available, synchronously resets scanner/grouping regardless of stalled ready, and requires a new full verified CPI upload for any further run. `group_done` and local FIFO empty alone do not authorize COMMIT.

## 7. Sign-off and verification entry criteria

**Sign-off requested (all currently NOT approved):**
1. TYPE/opcode/STATUS codes, ACK/NACK delayed/duplicate/stale response rules, no ACK-of-ACK control-sequence interpretation, session epoch/rollover and flags.
2. 13-byte LE/zero-pad record encoding, RESULT max K=8 and 125-byte maximum framed RESULT image.
3. 500-byte readback data chunks, input-IQ bytewise verification and PC HOST_VERIFIED_INPUT command.
4. Original COMMIT exact-frame replay versus fresh QUERY response, immutable terminal decision, scoped post-COMMIT retry exception, DSP-reset persistence versus unguaranteed global/power reset, UNKNOWN recovery and release semantics.
5. Internal production FIFO depth remains a separate engineering implementation choice after actual integrated resource/serial-flow tests; selecting K=8 records per RESULT **does not itself approve FIFO depth 8**.

After engineer sign-off, create a **PC Packetizer/Parser reference** with golden byte vectors and independent checks for CRC, exact field serialization, IQ upload/reassembly, duplicate, reorder, retry exhaustion, ID mixing, incomplete readback, 702 records, provisional COMMIT/ABORT and lost COMMIT ACK. Only then implement UART RX/TX/ARQ in RTL and perform real serial ISim, measured XST/MAP/PAR and board validation. Historical S04 and previously successful S05 campaigns are not to be rerun.

**Statuses preserved:** `REQ-LIST-01 logical policy=APPROVED`, `REQ-LIST-01 full technical acceptance=OPEN`; Gate-S04=CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03=FAIL 4/8; Fixed-Point statistical risk=OPEN; XC6SLX9 full-chain fit=OPEN.

## 8. Candidate-specific UART airtime (not an accepted FPGA throughput limit)

The earlier S05 timing record used *empty 17-byte ACKs* as a lower-bound assumption. This ICD **proposes** a 4-byte ACK payload carrying the acknowledged seq, so ACK frames would be **21 bytes**; both timings must remain scoped to their respective assumptions.

At 115200 baud, 8N1, with no retries/host latency/processing, no START/COMMIT/STATUS packets and the proposed 21-byte ACK, the nominal byte totals are:

| Candidate phase | UART bytes, including modeled ACKs | Serialization minimum |
|---|---:|---:|
| IQ_UPLOAD 34 packets | 18,460 | 1.602431 s |
| Full bytewise readback: 34 STAGE_REQUEST and their ACKs | 1,666 | 0.144618 s |
| Full bytewise readback: 34 STAGE_DATA and their ACKs | 18,494 | 1.605382 s |
| 702 RESULT records, 8 per packet, 88 packets and ACKs | 12,822 | 1.113021 s |
| **Upload + output only** | **31,282** | **2.715451 s** |
| **Upload + complete readback + output** | **51,442** | **4.465451 s** |

The readback illustration uses 33×500B plus 396B last IQ stage-data chunk, 9-byte STAGE_DATA prefix, and 11-byte STAGE_REQUEST body; these are proposed, not S02 frozen bytes. The total is a **lower bound** even for the candidate ICD because it excludes command/status/COMMIT frames, UART idle/turnaround, host verification CPU time, FPGA processing time, injected retries and potential packet scheduling. There is no approved maximum whole-CPI wait or measured CPI/s.

**Candidate data for automated review:** `engineering/S05-UART-ICD-v1.0-CANDIDATE-MANIFEST.json`. Numeric codes and wire layouts there are explicitly **unapproved** pending system-engineer sign-off.


## 9. Revision R2 — precise ACK/NACK sequence contract (supersedes Section 3 where narrower)

**Status: candidate requiring engineer approval as an explicit S02 interpretation.** Reliable application packets in the PC-to-FPGA and FPGA-to-PC directions each use a separate monotonically increasing unsigned 32-bit sequence number. The application packet types are COMMAND, IQ_UPLOAD, STAGE_REQUEST, STAGE_DATA, RESULT and STATUS. A new application packet gets a fresh sequence in its sender's direction. A retry reuses the same full wire frame and **same sequence**. At most one reliable packet per direction is outstanding; traffic in the opposite direction may have its own independent outstanding packet.

ACK and NACK are control replies, not application packets. They **do not** consume application sequence numbers and are **never themselves acknowledged** (prevents ACK-of-ACK). In this candidate ACK frame, the four-byte header sequence and four-byte little-endian ACK payload both equal the triggering accepted application sequence. In NACK, the header sequence is the rejected incoming application sequence, and the four-byte little-endian payload is the receiver's expected application sequence. Both have the same S02 CRC, envelope and strict length/version/flags checks as other frames; with four-byte control payload, total wire length is 21 bytes.

| Control event | Exact proposed action |
|---|---|
| Valid ACK: header sequence and payload sequence both equal the sender's **currently outstanding** reliable sequence in that direction and current valid link session | Accept once, release its retained replay frame, advance to next sequence |
| Correct but delayed ACK for the same still-outstanding frame after retransmission | Accept exactly once and stop retrying; later duplicates cannot advance twice |
| Duplicate ACK for an already completed frame, stale ACK for prior CPI or no frame outstanding | Ignore and log; never release the current replay image |
| ACK for future/unknown sequence, mismatch between its header/payload, or wrong active link session | Reject/ignore; never treat as confirmation |
| NACK header refers to the current outstanding frame and expected sequence equals its sequence | May retransmit **identical retained frame**, subject to existing retry budget; never allocate a new sequence |
| NACK with stale/future header, or expected sequence different from outstanding (even if receiver claims next sequence) | Ignore/log as diagnostic; do **not** infer ACK or release retained bytes. Wait for exact ACK or bounded retry. A receiver that sees a true duplicate must return an exact ACK |
| Valid duplicate application frame: equal to the immediately previously accepted wire frame, same sequence and CRC-protected contents | Re-ACK that sequence without applying IQ writes, record reception, RUN, COMMIT or other side effects again |
| Future/out-of-order application sequence | Do not apply; send NACK with the current expected sequence (when frame integrity permits) |
| Stale application packet that is not the identical last accepted frame; cross-CPI mismatch; corrupt packet | Do not apply; respond according to safe NACK/resynchronization rules |
| ACK or NACK after link session identity has been lost | Discard as stale, even if the raw 32-bit sequence happens to match |

**No rollover assumption:** The reliable sequence is not reset between CPIs or by a DSP-only reset; 32-bit sequence reuse/wrap is not authorized while delayed old controls may exist. Once a link-session identity or counters are lost (USB reconnect, FPGA reconfiguration, etc.), quarantine in-flight control frames and inhibit application effects until an explicit **new link-session/epoch handshake** has completed. Its exact wire encoding, how to drain stale USB/UART bytes and recovery from counter exhaustion are **OPEN for engineering sign-off**. Without a unique session binding, a numerically matching stale ACK after sequence reuse is not distinguishable; the ICD makes **no unqualified cross-power-cycle anti-replay claim**. CRC is an error detector, not cryptographic authentication.

**Required later independent fault tests:** delayed current ACK after multiple retries, duplicate ACK before/after advancing, stale ACK for previous packet/CPI, forged mismatch of ACK header and payload, current/stale/future NACK, duplicate accepted data frame, future sequence, partial/corrupt control frame, and link loss/resync with delayed old responses. No UART/PC implementation test is claimed here.

## 10. Revision R2 — COMMIT outstanding-frame retransmit vs QUERY reply (supersedes Section 6 where narrower)

The final **application decision** for CPI_ID is immutable after being selected: outcome COMMIT with final count 0..702, or outcome ABORT with reason. Transport delivery and knowledge of delivery are separate states. The application may decide COMMIT only after successful generation and link-layer delivery/ACK eligibility of every RESULT record; local grouping_done or empty FIFO is not sufficient.

| Path | Reliability sequence | Wire identity | Host effect |
|---|---|---|---|
| First FPGA-to-PC STATUS/CPI_COMMIT | Newly allocated FPGA-to-PC application sequence **S** | Retained fully serialized frame, including CPI_ID and exact count | Host validates all contiguous record IDs, integrity and CPI_ID before committing |
| **Retry** of still-outstanding COMMIT after missing ACK | **Same S** | **Exactly identical bytes**: SOF, TYPE, flags, S, length, CPI_ID/count and CRC | Host re-ACKs if already accepted; no second application of COMMIT |
| PC sends a new COMMAND/QUERY_CPI_STATUS(CPI_ID) | Newly allocated **PC-to-FPGA** application sequence **Q** | **New** reliable request frame | Query does not modify terminal decision |
| FPGA replies to QUERY after resolving its outstanding frame or following an explicitly authorized link-session reconciliation | Newly allocated **FPGA-to-PC** application sequence **T**, distinct from S within the same ordered session | **New** STATUS reply frame/CRC, but **identical immutable semantic terminal decision**: same CPI_ID, COMMIT/count or ABORT/reason | Host validates the same decision idempotently and requires complete records before accepting COMMIT |
| Query while COMMIT S still outstanding on the same FPGA-to-PC Stop-and-Wait stream | **No second concurrent FPGA-to-PC frame** | ACK the new PC query on its own control channel, then replay **exact original COMMIT frame S** (same wire image and sequence); do **not** mislabel it as a new-sequence QUERY reply. Once S receives an exact ACK, send the **deferred reply to that QUERY** with fresh reliable sequence T and the same immutable decision. If S cannot be acknowledged, hold TERMINAL_ACK_UNCERTAIN until separately approved link-session reconciliation | Never allocate a new FPGA-to-PC reliable sequence that overtakes S |

**Retry exhaustion after COMMIT:** After the initial COMMIT and up to three identical retransmissions, if no exact ACK is received, set a separate **TERMINAL_ACK_UNCERTAIN** transport substate, retain the original CPI_ID/decision/count and the current replay information, and block the next CPI until reconciliation. **Never emit a contradictory CPI_ABORT for this CPI_ID.** This is a requested scoped exception to S02's general retry-exhaustion-to-ABORT rule. A pre-COMMIT fatal error still follows normal abort behavior. The same immutable decided COMMIT must be returned by future status queries, never converted to ABORT because of a serial timeout.

Host-side invariant: receipt of all target records **without** COMMIT (including disconnection after the final record) leaves the results uncommitted. A newly sequenced query reply containing the original COMMIT decision can complete a CPI **only** when the host still has the entire validated provisional record set and checks exact IDs 0..count−1; otherwise the host must report unresolved/invalid local delivery rather than fabricate acceptance. Identical duplicate COMMIT is harmless; conflicting COMMIT/ABORT for the same CPI_ID is always an error.

**Outstanding-terminal ordering:** The above QUERY-triggered recovery replay of S after the normal retry budget is exhausted is a **separately proposed reconciliation action**, not an unbounded ordinary ARQ retry. Its exception to S02's three-retransmission limit requires express sign-off. A fresh QUERY status reply may not bypass an outstanding COMMIT in the same reliable FPGA-to-PC sequence space. A recovery mechanism must first resolve/reconcile the old outstanding sequence, or establish a separately approved new session epoch; a new query response must then receive a **fresh** valid sequence in that epoch. The epoch/session control wire schema is OPEN, not silently assumed.

## 11. Revision R2 — persistence/recovery boundaries and seven OPEN stage schemas

| Boundary | What must persist (proposed implementation contract) | Safe recovery |
|---|---|---|
| **DSP-only reset or coordinated pipeline Abort/Reset**, with transport/transaction controller powered and not reset | CPI_ID, immutable terminal outcome/count/reason (once decided), first error, reliable seq counters, last accepted seq, outstanding complete wire-image replay, and COMMIT-ACK uncertainty in a **separate reset domain** | Pipeline may reset without losing the transaction decision. Preserve COMMIT even if a late pipeline fault occurs |
| **UART byte-parser soft resynchronization**, with transport-state domain retained | Same session ID/state, sequences, outstanding replay, decided terminal result; only partial byte-frame parser state may be cleared | Discard incomplete byte frame; retransmit outstanding frame without new sequence or changed bytes |
| **USB disconnect / CP2102 re-enumeration**, transport state retained in FPGA but link epoch potentially invalid | Immutable terminal CPI state remains in volatile protected domain; old wire-session ACK validity does **not** persist | Quarantine stale controls, perform newly approved link-session handshake and QUERY; do not advance old replay from a stale ACK |
| **FPGA global reset, reconfiguration, power loss, or loss of protected terminal-state bank** | **Not guaranteed**: FPGA registers/BRAM are volatile; no approved nonvolatile journal exists | Do not invent success/ABORT from missing state. Return UNKNOWN/UNRECOVERABLE when safe protocol permits; host may rely only on its own durable verified transaction record. Require session reconciliation and a new fully verified CPI before processing; old CPI_ID must not be casually reused |
| **Confirmed terminal agreement and explicit host RELEASE_CPI** | Retain until RELEASE/validated reconciliation, then eligible for retirement | Only then permit next CPI_ID. Do not reuse a retired CPI_ID within an ambiguous old session without a separately approved generation/epoch rule |

**Explicit guarantee limit:** A powered register retained across internal resets is **not** nonvolatile storage. Cross-power-cycle exactly-once COMMIT cannot be guaranteed without an approved durable journal or host-owned transaction reconciliation protocol. How long to retain terminal state, UNKNOWN status code, epoch handshake, durable host log/retention and safe retry after permanent link loss remain **open implementation/ICD approval items**. No FPGA resource or recovery RTL evidence exists yet.

**S02 REQ-OBS-01: seven separate DSP stage-output schemas remain OPEN.** For each of the seven mandatory FPGA processing functions, the project must separately approve the stage identifier, output dimensions and coordinate/order convention, data word widths and signedness, scale/rounding/saturation flags, serialization/endian, version, segmented offsets, retained lifetime or deterministic rerun, and an independent bit-true oracle. The proposed stage_id 0x00 in Section 4 is **only a raw input-IQ readback selector**. Neither that selector nor the generic STAGE_REQUEST/STAGE_DATA envelope approves **any** of the seven DSP-stage payload schemas. Do not enumerate/freeze invented stage IDs here. These schemas remain S05 specification work before their functional/board readback acceptance.

**Final sign-off dependencies:** engineer approves (1) control-sequence interpretation, delayed/stale response handling and link-session epoch renegotiation; (2) COMMIT replay versus new-sequence QUERY and the scoped post-COMMIT S02 retry exception; (3) reset-domain persistence and power-loss UNKNOWN behavior; (4) numeric wire codes and 13-byte LE/8-record candidate schema already proposed; and (5) readback stage schemas in **separate** approved contracts. The latter seven do not become accepted merely because the transport ICD is signed off. Production FIFO depth, FPGA UART RTL, real link ACK/CRC/COMMIT tests and full device-fit/timing likewise remain unverified.

**Revision outcome:** logically complete target-list policy remains APPROVED; **full REQ-LIST-01 remains OPEN**. Gate-S04 remains CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03 remains FAIL 4/8 and S04-C02-RISK-PERFORMANCE OPEN. No UART RTL or historical CPI test executed.


## 12. Proposed Link Session / Epoch addendum — not merged into an approved wire baseline

The follow-on `engineering/S05-LINK-SESSION-EPOCH-ADDENDUM-v0.1.md` describes a **new, independently reviewable candidate** for safe link-session restart and stale ACK rejection: a reserved SESSION_CONTROL TYPE, HELLO/OFFER/ACTIVATE/READY bootstrap and 128-bit epoch tags in ordinary frames. It includes PC/FPGA transition guards, terminal recovery/RELEASE/UNKNOWN rules and a planned 20-case test matrix.

**Until explicit system-engineer sign-off, these proposed additions do not modify the R2 framed payloads, 21-byte ACK size, 34-packet upload calculation, numerical TYPE definitions or accepted S02 requirements.** The addendum's 35-packet upload/37-byte ACK example is scoped solely to the proposed epoch-tagged candidate. It is neither an approved S02 amendment nor an RTL/board PASS.


## 14. Link Session/Epoch R1 candidate — separately proposed, not merged into approved R2

The corrected standalone addendum is `engineering/S05-LINK-SESSION-EPOCH-ADDENDUM-R1-v0.1.md` (revises retained v0.1). It adds explicit four-message loss/duplicate/USB-disconnect transitions, a contract-level once-only activation invariant preventing counter reset after a lost READY, trusted-laboratory restart assumptions, a fail-closed HOST_DISCARDED_INCOMPLETE_COMMIT release disposition, UNKNOWN host-history reconciliation, candidate 2-second/three-retry/12-second handshake budgeting, and 20 observable planned tests. ACTIVATE and READY now echo the OFFER cpi_valid field; R1 candidate full-frame lengths are **41/43/44/44 B**, not the historical v0.1 **41/43/43/43 B**.

**No byte-level R1 TYPE, flags, nonce, reset behavior, release disposition or timeout is approved merely by documenting it.** This R2 parent remains CONDITIONALLY_ACCEPTED_FOR_FURTHER_SPECIFICATION_NOT_FINAL_SIGNOFF, and 21-byte ACK/34-frame input timing still belongs strictly to the original untagged R2 proposal. The R1 37-byte tagged ACK/35-frame IQ model is a **separate unapproved alternative**. Seven DSP stage-output schemas, full REQ-LIST-01 and UART RTL acceptance remain OPEN.

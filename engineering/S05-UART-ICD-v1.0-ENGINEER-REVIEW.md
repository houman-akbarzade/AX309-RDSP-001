# AX309-RDSP-001 | S05 UART ICD v1.0 — ENGINEER REVIEW CANDIDATE

**Status:** PROPOSED_NOT_APPROVED. The suffix "v1.0" denotes a complete **candidate for sign-off**, not an enacted or verified protocol.
**Baseline:** `c5160db`. **Date:** 2026-11-12. **Owner of approval:** System engineer.

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

**Implementation dependency:** the FPGA must preserve uploaded IQ until readback completion; stage request/reply, accepted packet ACK and the replay image must not overwrite live received IQ. S02 also requires access to all seven DSP stage outputs, which need separately accepted stage_id/schema definitions; this v1 proposal reserves the STAGE interface but **does not freeze other stage byte schemas**.

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
1. TYPE/opcode/STATUS codes, ACK/NACK control-sequence interpretation and flags.
2. 13-byte LE/zero-pad record encoding, RESULT max K=8 and 125-byte maximum framed RESULT image.
3. 500-byte readback data chunks, input-IQ bytewise verification and PC HOST_VERIFIED_INPUT command.
4. Commit/abort terminal state and lost-COMMIT-ACK reconciliation exception to S02 retry-exhaustion behavior.
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

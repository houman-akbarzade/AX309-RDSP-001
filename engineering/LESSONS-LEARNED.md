# Lessons Learned | AX309-RDSP-001

## LL-AX309-001 — Requirement-driven validation continuity from reference model to hardware

**Status:** Accepted project lesson; input to the next Radar Design Plugin workflow revision.
**Source:** AX309-RDSP-001 S02–S05 engineering experience.
**Scope:** Process lesson only. It does not change any approved project requirement, numeric contract, acceptance limit or gate decision.

### Lesson

Every approved system requirement must be converted, before reference-model qualification, into one or more quantitative test scenarios with a frozen input definition, measurable acceptance rule, expected output and explicit PASS/FAIL/INCONCLUSIVE disposition.

The same immutable scenario corpus must then be replayed through each implementation layer:

1. Floating-point functional reference.
2. Integer/Fraction oracle and Fixed-Point model.
3. RTL simulation.
4. Synthesis and timing/resource analysis.
5. FPGA/board verification where applicable.

A new model must not receive a separately generated, unlinked test set merely because it is a new implementation. If an additional vector is technically necessary, it must have a documented requirement link, a reason for addition, a stable ID and a versioned manifest. It supplements the common corpus; it does not replace or silently alter it.

### Evidence and limitation from this project

S03 provides a validated Float reference for its approved scope. S04 C03–C05 provide independent integer oracles and deterministic bit-true evidence. C06R2 reports 16/16 bounded numerical CPI PASS for its two C01-approved populations. Those results do not establish full requirement coverage: REQ-SCR-01 and REQ-RNG-03 remain OPEN, and the 16-CPI C06R2 campaign is not a statistical Pfa/Pd qualification. RTL equivalence and hardware feasibility are separate S05/S08/S09 activities.

### Required plugin workflow

The Radar Design Plugin should generate and maintain a Requirement-to-Test Traceability Matrix with at least:

- Requirement ID and approved revision.
- Quantitative acceptance criterion and units.
- Test scenario ID, version, profile and parameter envelope.
- Frozen input manifest, seed/source version and SHA-256.
- Expected Float-reference output and its version/hash.
- Float execution result and measured metrics.
- Expected integer/Fraction oracle output and its version/hash.
- Fixed-Point output and exact/quantitative Float-to-Fixed differences.
- RTL output and bit-true comparison result.
- PASS/FAIL/INCONCLUSIVE/STRESS_ONLY disposition at each applicable layer.
- Evidence links, execution environment, owner and approval state.

### Workflow controls

- A requirement cannot become PASS because a generic model or a few unrelated tests exist.
- Test denominators and scenario membership are frozen before execution; no silent deletion, replacement or post-hoc threshold changes.
- The common corpus is immutable after approval. New scenarios are versioned additions with explicit requirement traceability.
- Float-to-Fixed and Fixed-to-RTL comparisons use the same source vectors and scenario IDs.
- Statistical performance, deterministic arithmetic correctness, RTL equivalence and hardware feasibility are separate claims with separate evidence.
- Missing source profiles, undefined acceptance metrics or unsupported physical assumptions remain OPEN; the plugin must not invent them.

### Application to AX309-RDSP-001

Carry this lesson into S05 testbench architecture. Reuse the approved C03–C05 oracle interfaces and C06R2 input corpus where scope permits. Add each RTL vector by stable ID and preserve its originating Float/Fixed source. Do not rerun C06R2 CPI. REQ-SCR-01 and REQ-RNG-03 require separately approved scenario definitions and are not implicitly covered by the current corpus.

## LL-AX309-002 — Stage exit with explicit open-item carryover is not requirement acceptance

**Status:** Accepted project lesson; input to the next Radar Design Plugin workflow revision.
**Source:** AX309-RDSP-001 S04-to-S05 engineer disposition, 2026-11-12.
**Scope:** Process and traceability lesson. It does not change any technical requirement or acceptance threshold.

### Lesson

A system engineer may authorize a stage transition while retaining failed or incomplete technical obligations for later project evaluation. The project records must represent the administrative gate decision separately from each requirement's technical disposition.

In this project:
- Gate-S04 was closed by explicit engineer disposition to permit S05.
- REQ-RNG-03 remained FAIL at 4/8 mandatory scenarios; its 8/8 criterion was not changed.
- Fixed-Point statistical performance remained OPEN; deterministic evidence was not relabelled as statistical qualification.
- Both items were transferred to a versioned final-evaluation carryover register.

### Required plugin workflow

The Radar Design Plugin should maintain two independent state fields:
1. **Technical disposition:** PASS, FAIL, OPEN or INCONCLUSIVE, tied to the exact approved criterion and evidence.
2. **Gate/stage disposition:** OPEN, CLOSED, or CLOSED_WITH_OPEN_ITEMS, tied to an explicit authorized decision.

When a gate is closed with open items, the plugin must:
- Preserve the original test denominator, result, acceptance rule and evidence hash.
- Create a carryover record with a named next review point and final-report obligation.
- Remove the carried item only from the current stage's entry blockers; do not remove it from requirement traceability.
- Prevent any automatic conversion of FAIL or OPEN to PASS.
- Show the carried items in final project evaluation and the final report.

### Application to AX309-RDSP-001

The authoritative carryover record is engineering/S04-OPEN-ITEMS-CARRYOVER-v1.0.json; the engineer decision is decisions/S04-C08-S05-TRANSITION-2026-11-12.json. S05 may proceed, but neither REQ-RNG-03 nor Fixed-Point statistical performance is technically accepted by this transition.

## LL-AX309-003 — RAM inference and output-list policy are independent design controls

**Status:** Accepted S05 implementation lesson; candidate for Radar Design Plugin workflow revision.
**Source:** S05 grouping_8conn ISim/XST artifact and the frozen S02 REQ-LIST-01.

The synthesis resource cost of a small logical table can be dominated by its inferred read/write ports. The initial grouping implementation with multiply addressed parent/statistic memories produced excessive distributed-logic resource use. Refactoring both memories into single synchronous read/write port structures enabled XST block RAM inference while preserving bit-identical output records against the unchanged C05 BFS reference and independent union-find.

The final standalone synthesis shows 6 BRAM, 4,034 LUT, 1,727 registers, 0 DSP48A1 and 0 warnings, not a whole-system fit. The downstream scanner separately uses 12 BRAM; the project must check the actual combined memory lifetime and target capacity before claiming a hardware architecture fit.

**Plugin workflow implication:** Require each proposed streaming RTL memory to state its depth/width, number of reads and writes per cycle, inferred memory technology and resource budgets; inspect XST warnings and actual macro usage before reporting synthesis feasibility. Separately, an internal geometric bound or safe overflow diagnostic must not be treated as approval of an externally visible record-list capacity or selection policy when that decision is still open.

**Evidence:** engineering/S05-GROUPING-EVIDENCE-MANIFEST-v0.1.json, engineering/S05-GROUPING-RTL-VERIFICATION-REPORT-v0.1.md, engineering/S05-GROUPING-TRACEABILITY-v0.1.json. No architecture C/Frozen Fixed-Point change and no REQ-RNG-03 retest were made.


## LL-AX309-003 — Detection-domain boundaries must follow signal support, not only array shape

**Status:** Accepted engineering observation from S05 CUT geometry audit and connected RTL qualification, 2026-11-12.

The 128x32 stored power-map shape alone geometrically permits 3172 nonwrapped 7x7 CA-CFAR CUTs. However, the 16-sample echo in a 128-sample acquisition has complete-support delay indices 0..112. The approved S02 engineering contract requires the full 7x7 range-side CFAR window to remain in that support, restricting CUTs to r=3..109 and b=3..28: 2782 CUTs. The matched filter computes a full 143-output convolution and extracts 128 aligned outputs; it does not produce only 113 outputs. Treating allocated array dimensions as the acceptance domain would silently change the Pfa denominator and detector coverage.

The connected CFAR–Grouping test additionally showed that the scanner and grouping engines use distinct completion events. Fatal grouping overflow can leave the scanner stalled; a later system controller must explicitly reset/abort both engines while preserving the reported invalid-frame status to the host.

**Plugin design implication:** track three independent quantities: stored map shape, physically supported/approved signal-valid domain, and validated CUT domain. Require approved evidence before expanding a CUT region, and require a documented fatal-frame abort protocol when joining valid/ready blocks. Neither module-level oracle equivalence nor connected-subsystem XST fit proves full radar-chain performance or resource fit.

**Evidence:** engineering/S05-CUT-GEOMETRY-AUDIT-v0.1.md; engineering/S05-CFAR-GROUPING-INTEGRATION-REPORT-v0.1.md. No S04 carryover disposition is changed.


## LL-AX309-004 — Resource viability requires phase lifetimes and actual FPGA memory inference

**Source:** S05 REQ-LIST-01/resource-lifetime feasibility review, 2026-11-12.
**Status:** Engineering observation for the radar-design plugin; **not** an Architecture C change.

A correct 4,224-word RAM description may infer very different FPGA resources depending on depth banking and synchronous read style. In isolated ISE 14.7 XST probes, a naive 4,224x50 array used 25 BRAM with an address-range warning; splitting the memory into 4,096+128 words with independently synchronous bank reads used 14 BRAM and 0 warnings. The corresponding 4,224x32 IQ case changed from 16 to 9 BRAM. A first conditional-read banked variant instead mapped into distributed LUTRAM and overran its available memory-LUT class. Consequently, theoretical bit counts alone do not prove a design will fit.

The approved S02 UART contract also requires **full 16,896-byte CPI upload and verification before RUN**, so a one-pulse IQ buffer is insufficient unless another retention mechanism exists. A symbolic lifetime proof demonstrates that pulse-major input IQ can be overwritten by delay-aligned MF, then each range's 33 MF words overwritten by its 32 Doppler powers in address order b*128+r. However the current CFAR scanner contains an independent private range-major power RAM, so shared-storage resource benefits remain an *unimplemented hypothesis* until the scanner interface and bank arbitration are reverified.

The connected CFAR–Grouping block alone uses 76% LUT; clock and full-chain resource fit remain unproven. A fatal grouping overflow can hold the scanner indefinitely at a pending CUT, so the future frame controller must latch the error/CPI ID, force a shared datapath reset and require host-visible invalidation and fresh input upload. Never equate grouping done, scanner done or a reset edge with a successful CPI commit after a fatal fault.

**Process lesson:** freeze the external record-list capacity/overflow policy before building the controller. Preserve separately (1) measured XST resource results, (2) symbolic memory-lifetime feasibility, and (3) completed integrated hardware qualification. Only the third establishes design fit.

**Evidence:** engineering/S05-REQ-LIST-01-DECISION-PACKAGE-v0.1.md, engineering/S05-RESOURCE-LIFETIME-AND-RECOVERY-v0.1.md, engineering/S05-RESOURCE-PROBE-EVIDENCE-v0.1.json. Gate-S04 and its carried technical items are unchanged.

## LL-AX309-005 — Component-count ceiling is not a full-record buffering requirement

**Evidence:** S05 exact 702-component theorem and isolated XST record-store probes, 2026-11-12.

In a 107x26 nonwrapped 8-connected CUT graph, partitioning into at-most-2x2 cliques proves no more than 54x13=702 distinct components; a checkerboard-like alarm placement attains 702 singleton components. A proven *logical count* does not require a 702-record FPGA output RAM. Isolated XST memory probes use 6 BRAM for 702x99 records, versus 0 BRAM and 70 LUT/99 FF for an eight-record distributed store; neither is a complete streaming FIFO or UART implementation. When internal tables already preserve 702 grouping labels, additional full record buffering may be avoidable.

A lossless back-pressured output stream still needs transactional CPI semantics: records are provisional until CPI_COMMIT, and any CPI_ABORT or lost link before COMMIT invalidates the entire CPI. No Top-K or silent discard can be used to mask FIFO overflow. A data-path reset cannot unsend UART bytes, so host-side rollback must be part of the contract. Keep exact mathematical bounds, physical-storage cost, packet reliability and end-to-end acceptance as separate verification categories. No final REQ-LIST-01 PASS is implied.

## LL-AX309-006 — A lossless FIFO still requires retransmission-safe transport and CPI commit

**Evidence:** S05 grouping-to-FIFO prototype and host transaction semantic checks, 2026-11-12.

Grouping output can be stopped without loss: its approved S_OUTPUT state holds record data and ID until READY. A test-only eight-entry distributed FIFO reached hard-full, held the producer for 60,000 consecutive clock cycles and later delivered 702/702 independently oracle-certified component records in order. FIFO depth eight is a validated laboratory choice, NOT an optimal or signed-off production depth.

Producer and UART line rates differ greatly. At hypothetical 50 MHz Grouping's fastest observed output interval is 1,407 cycles, whereas S02's nominal 115200 8N1 UART can carry at most 11,520 gross bytes/sec. A queue alone cannot preserve records during UART retries unless the unacknowledged record or packet is retained elsewhere. **Only ACK, not UART byte transmission, frees the last recoverable copy of an output record.**

CPI_START/RECORDS/COMMIT/ABORT must be transactional: host records remain provisional, COMMIT includes CPI_ID and count, host checks complete contiguous record IDs, and link loss after the final record but before COMMIT leaves the CPI invalid. A local empty FIFO and a grouping-done pulse are NOT a CPI_COMMIT. S02 per-packet timeout/retry is a transport obligation, not a proved whole-CPI timeout.

XST mapped the grouping+FIFO prototype using 6 BRAM and 4,016 LUT, but the stand-alone 195-I/O test interface exceeds the 186 pin budget. Treat this as isolated logic synthesis, not deployable top-level FPGA resource/timing acceptance. Do not change Gate-S04 carryover status, numerical Architecture C or target resolution claims.

## LL-AX309-007 — Packet acceptance, CPI verification and host COMMIT are separate gates

**Source:** S05 CPI-by-CPI UART architecture review, 2026-11-12.

Laboratory CPI-by-CPI operation does not require real-time IQ streaming. The approved 16,896-byte IQ input requires 34 UART frames at 504 data bytes each under the 512-byte payload maximum. Per-frame CRC/sequence ACK does not by itself satisfy the separate full-CPI readback-or-digest verification prerequisite to RUN. In the output direction, an accepted grouping valid/ready FIFO record is not proof that a UART packet has been ACKed: retaining a retransmission-safe packet until ACK prevents loss when the link retries. On the PC, a valid COMMIT with CPI_ID and a record count is a necessary but insufficient condition; record IDs and packet integrity must be complete.

Especially critical: losing the ACK to a COMMIT already received by the host is different from losing COMMIT itself. Issuing an ABORT after such an ambiguous ACK failure could contradict an already committed host transaction. The serial ICD needs idempotent COMMIT replay and explicit terminal-state reconciliation by CPI_ID. The existing S02 2-second **per-packet** timeout cannot be represented as a guaranteed upper bound on the complete CPI cycle. UART serialization, host waits, FPGA cycles and hardware STA must be reported separately.

**Evidence:** engineering/S05-UART-CPI-BY-CPI-PREIMPLEMENTATION-REVIEW-v0.1.md and engineering/S05-UART-CPI-TIMING-EVIDENCE-v0.1.json. No UART RTL implementation, board test, new capacity requirement PASS or architecture-C change is claimed.

## LL-AX309-008 — Approval of a logical target-list contract is distinct from approving its serial transport

**Source:** S05 ICD v1.0 candidate review, 2026-11-12.

The system engineer has already approved 0..702 logical connected-component records, no Top-K and no silent loss. That does not freeze an 8-entry production FIFO, UART result packetization or successful completion of REQ-LIST-01. The reproducible grouping-to-FIFO8 ISim is only a lab valid/ready result.

Packing the current 99-bit RTL record into 13 least-significant-octet-first bytes can preserve every integer field with five explicitly zero high padding bits, but this mapping remains a candidate until byte-level ICD signoff. For proposed eight-record RESULT packets, retain the entire framed packet (up to 125 bytes) until the exact ACK; FIFO handoff is not packet delivery. Likewise, host bytewise full-CPI readback is a distinct prerequisite to FPGA RUN, not implied by 34 individually CRC-valid IQ_UPLOAD packets.

A lost ACK for a COMMIT that the host already accepted creates a genuine terminal-state ambiguity. Per-frame retry exhaustion cannot safely be converted into a contradictory ABORT; an idempotent, persistent CPI_ID-keyed COMMIT reply and status reconciliation need explicit engineer approval. ACK/NACK sequence numbering is another control-plane issue; never settle it silently from the S02 requirement for monotonic data-frame sequences.

**Evidence:** engineering/S05-UART-ICD-v1.0-ENGINEER-REVIEW.md. Neither the ICD candidate nor a packet codec or FPGA UART is qualified in this step.

## LL-AX309-009 — COMMIT retransmission, status query and reset-domain persistence are separate protocol contracts

**Source:** S05 UART ICD v1.0 R2 engineer-review revision, 2026-11-12.

Retransmitting an unacknowledged COMMIT is the **same reliable application packet** with unchanged sequence and wire image. Responding to an independently sequenced QUERY_CPI_STATUS is a **new reliable packet** with a new sequence but the same immutable CPI_ID/terminal outcome/count, and must not overtake an outstanding COMMIT on a Stop-and-Wait direction. A stale/duplicate ACK may never acknowledge a different outstanding packet, even if it arrives after a retry or the next CPI starts. Session/counter reuse after link reset needs an explicit epoch protocol.

Once COMMIT is decided, exhaustion of its ACK retries creates an ACK-uncertain transport state, not an ABORT decision. The terminal result and packet replay must survive only those **DSP resets** whose state is intentionally held in an independent controller domain. Unpowered registers/BRAM are not a nonvolatile transaction journal; after reconfiguration/global reset/power loss, the FPGA cannot promise durable exactly-once terminal recovery without a separately approved persistent mechanism. A generic STAGE_REQUEST/DATA transport contract likewise does not approve the **seven separate DSP stage output schemas** required by REQ-OBS-01.

**Evidence:** engineering/S05-UART-ICD-v1.0-ENGINEER-REVIEW.md R2 and engineering/S05-UART-ICD-v1.0-CANDIDATE-MANIFEST.json. Both remain pending final engineer sign-off; no UART RTL, full REQ-LIST-01 PASS or Gate-S04 change.

## LL-AX309-010 — An epoch must be bound to every ACK and payload, not only to a reconnect handshake

**Source:** S05 Link Session/Epoch engineering addendum, 2026-11-12.

A new UART handshake followed by restarting 32-bit sequence counters does not by itself distinguish an old delayed ACK from a new one with the same sequence number. A proposed 128-bit PC-generated session ID included in every active reliable payload and ACK/NACK resolves this ambiguity **within correctly established unique sessions**. This costs payload capacity: proposed 16-byte tags would change 34 IQ_UPLOAD frames to 35 and R2 21-byte ACK frames to 37. Those wire changes require a new explicit S02/S05 engineering approval and cannot be silently treated as existing R2.

After an ACK-uncertain COMMIT, a retry in the original session reuses exactly the original wire frame/sequence; a new link epoch uses a **new** QUERY and newly sequenced STATUS carrying the **same immutable terminal decision**. The FPGA must never turn a previously decided COMMIT into ABORT. RELEASE_CPI must be an explicit separately verified action, with idempotent duplicate handling. FPGA global reset/power loss destroys unprotected volatile terminal history; UNKNOWN is an epistemic limitation, not evidence that a CPI succeeded or failed. A host-only random session token and CRC do not authenticate a malicious endpoint or guarantee safety against replay of an entire stale bootstrap exchange after power loss.

**Evidence:** engineering/S05-LINK-SESSION-EPOCH-ADDENDUM-v0.1.md and engineering/S05-LINK-SESSION-EPOCH-TEST-MATRIX-v0.1.json (20 planned cases, none executed). Logical REQ-LIST-01 is approved separately from unresolved physical UART/FPGA qualification.

## LL-AX309-011 — Lost READY requires single-shot activation, not merely a duplicate message ACK

**Evidence:** S05 Link Session/Epoch R1 engineering specification, 2026-11-12.

In a four-message HELLO/OFFER/ACTIVATE/READY handshake, the FPGA can become ACTIVE on receipt of ACTIVATE **before** the PC knows READY arrived. Losing READY can cause the PC to resend ACTIVATE, but the FPGA must have an `activated_once(session_id)` latch and a cached READY. The retry can retransmit READY only; it cannot reset the already active directional sequence counters, accepted data or CPI decision. This is a contract-level inductive invariant, not an RTL PASS.

The OFFER snapshot needs a complete echo: R1 adds the previously absent `cpi_valid` byte to ACTIVATE and READY, changing the four-frame handshake to 41/43/44/44 bytes. Session IDs and serial CRC offer logical separation from stale old-epoch frames only under a **trusted single-PC and fresh-nonce** laboratory model; a PC nonce cannot authenticate a device that rebooted and lost all its terminal history.

A COMMIT known to the FPGA may coexist with a host result marked `FAILED_RESULT_DELIVERY` because the host's provisional record list is incomplete. A proposed `HOST_DISCARDED_INCOMPLETE_COMMIT` RELEASE may allow lab recovery **only after** a durable failure record and explicit engineer approval, never as a successful target list or a reversal of immutable FPGA COMMIT. Conversely, after FPGA power loss, a separately durable host COMMIT may remain a valid historical host result while the FPGA correctly reports UNKNOWN. A host with unvalidated provisional records must discard them.

Handshake times (2-second wait, three retries, 12-second pending lease and 2-second receive-quiet guard) are **engineering proposals**, not proven USB latency limits or a whole-CPI deadline. The 20-case R1 observable test matrix is not executed; a structural CRC/length audit is not packet/RTL qualification.

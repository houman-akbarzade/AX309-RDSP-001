# AX309-RDSP-001 | S05 REQ-LIST-01 Bound, Buffering and Transaction Assessment v0.1

**Date:** 2026-11-12
**Decision authority:** System engineer conditional endorsement only.
**Disposition:** 702_COMPONENT_BOUND_MATHEMATICALLY_PROVED; STREAMING_OPTION_CONDITIONALLY_SUPPORTED; REQ_LIST_01_NOT_FULLY_ACCEPTED.

## 1. Exact mathematical bound on component count

Approved graph G has vertices R={3,...,109} × B={3,...,28}, or 107×26=2782 possible alarmed CUT locations. An edge exists exactly when max(abs(delta_range),abs(delta_unshifted_Doppler))=1. No wrap. Cells outside this accepted CUT region are never vertices and cannot bridge clusters. The actual graph on a given CPI is the subgraph induced by the alarmed CUT locations; each cluster has at least one such cell.

**Upper bound:** Partition 107 rows into 54 disjoint blocks of at most two consecutive rows and the 26 Doppler columns into 13 disjoint blocks of two consecutive columns. Their products form 54×13=702 disjoint rectangles of size at most 2×2. Every two distinct cells in a rectangle are 8-adjacent (a clique). Select one representative alarmed vertex from each connected component. Representatives from different components must be non-adjacent; thus at most one representative can lie in each rectangle. The component count is <=702 for EVERY possible binary alarm mask.

**Exact attainment:** Set alarms at (r,b)=(3+2i,3+2j), i=0..53, j=0..12. There are exactly 54×13=702 alarmed cells. Every two differ by at least two in at least one coordinate, so no two are adjacent. Every alarm is a singleton component. Hence the exact maximum is **702**, not an estimate or a general division by four. The proof's partition and construction have independent executable checks in engineering/s05_component_bound_proof_v0.py, output engineering/S05-COMPONENT-BOUND-702-PROOF-v0.1.json (PASS). Accepted C05 CPI campaigns and existing standalone/grouping qualification were NOT rerun.

This is a bound on output *components in the approved CUT graph*, not on physical radar targets or on simultaneous storage. The approved 8-connectivity and non-wrapped Doppler geometry are essential.

## 2. Logical output width versus physical buffering

Current grouping RTL output: record ID 10, range 7, unsigned Doppler 5, signed Doppler 6, stored peak power 46, member count 12, peak-tie flag 1 and equal-power peak count 12 bits = **99 bits per record**. Full 702-record storage represents 69,498 bits (~8,688 octets rounded up). Bit-capacity lower bound: ceil(69498/18432)=4 BRAM18 blocks, which does NOT guarantee practical mapping.

Actual ISE 14.7 XST *isolated storage-probe* results (not complete FIFO/transport cores):

| Storage probe | Logical memory | BRAM sites (XST) | LUT (XST) | FF (XST) | Warnings |
|---|---:|---:|---:|---:|---|
| Entire-frame store | 702×99 | **6** (5 RAMB16BWER + 1 RAMB8BWER) | 0 reported | 0 reported | 2 |
| Small block-memory store | 8×99 | **2** (3 RAMB8BWER) | 0 reported | 0 reported | 1 |
| Small distributed-memory store | 8×99 | **0** | **70** | **99** | 1 |

Each probe has zero synthesis errors but **unusable standalone pin counts** (221 or 207 IOBs versus 186 physical IOBs). They are internal memory-mapping experiments, not a physically placeable board top-level. The 702-depth probe also warns about invalid addresses because a raw 10-bit probe address spans 0..1023: a production implementation must guard address <702. All variants need actual FIFO occupancy/control, UART serializer, retry and status logic, for which these figures are not resource estimates. Logs and exact hashes are kept in engineering/evidence/s05/list_capacity and in the evidence manifest.

## 3. Full-list versus streamed list

| Issue | All 702 output records stored | All records streamed through small FIFO |
|---|---|---|
| Logical completeness | Yes if full store and output verified | Yes only with proven back-pressure and transport/transaction semantics |
| Added isolated storage cost | 6 BRAM | Example 8 slots: 2 BRAM block-style, OR 0 BRAM + 70 LUT + 99 FF distributed-style |
| Overflow selection | Not needed | Not needed; never Top-K |
| Back-pressure | Can serialize after processing; buffer needs space for full list | Must stall grouping and scanner via ready/valid if FIFO/host is blocked, without losing or duplicating records |
| Abort after provisional records sent | Host must invalidate uncommitted records | Host must invalidate uncommitted records |
| Risks | Extra BRAM; record buffer and commit logic | FIFO-full deadlock, watchdog vs valid UART pacing, retries, UART throughput and rollback |
| Verified in completed system? | NO | NO |

Resource arithmetic (not integrated synthesis): current CFAR–Grouping is **18 BRAM / 4,374 LUT**. Adding the isolated full-list storage cost makes 24 BRAM, leaving 8; a separate 14-BRAM MF store would reach 38>32. If future approved memory reuse replaces the private CFAR map, a proposed 14-BRAM shared IQ/MF/power store plus 6 grouping BRAM plus full record buffer 6 = **26 BRAM**, versus **20 BRAM** for the 8-record distributed option (or 22 with a block-memory FIFO), before scratch/UART. No full-chain resource FIT or timing closure follows from these projected sums. The current connected subsystem consumes 76% LUT and has 20.259 ns estimated XST period, so shared memory alone cannot guarantee feasibility.

Initial nominal UART 115200 baud at 8N1 represents at most 11,520 serial octets/s without packet overhead. Packed 99-bit records require at least 13 octets per record, 702×13=9126 octets, a theoretical transmission time of ~0.792 s before CPI metadata, UART framing, CRC, ACK, retry, processing and pauses. The actual UART and board clock remain unverified. S02 caps packet payloads at 512 bytes; record batching and stop-and-wait ARQ matter. No standalone buffer trial establishes end-to-end throughput.

## 4. Conditional transactional transport contract (NOT final ICD)

Engineer endorses the direction **CPI_START -> TARGET_RECORDS -> (CPI_COMMIT or CPI_ABORT)**. These are abstract transaction events, NOT newly approved numeric UART TYPE codes.

- Each record is provisional and indexed by (CPI_ID, record_id). A single CPI transaction is active; retransmissions are idempotent and gaps/conflicting duplicates are rejected. No new CPI records interleave with an old unfinished transaction.
- COMMIT is emitted only after all records are generated, serialized, transported/acknowledged and validated; it carries final count (0..702) and CPI ID. Host marks the CPI successful ONLY upon valid COMMIT with complete IDs 0..count-1.
- On ABORT or transport failure/timeout before COMMIT, host invalidates all provisional records even if received earlier. If ABORT cannot be delivered owing to link loss, absence of COMMIT still prevents success. Once COMMIT is accepted, the same CPI must never later ABORT; duplicate COMMIT/ACK requires idempotent handling.
- A full FIFO must deassert upstream ready through grouping and CFAR, holding valid/data stable and counting every accepted record exactly once. UART packetization and ACK must ultimately drain the FIFO or cause an explicit transaction abort; a watchdog cannot mistake normal bounded UART back-pressure for deadlock.
- Fatal grouping/protocol error or unrecoverable transport fault triggers CPI_ABORT, latching CPI ID/error outside DSP reset. A common scanner/grouping reset is initiated without waiting for stalled CUT ready; no partial successful result may be published. A fresh verified CPI upload is required for recovery.

No new watchdog periods, FIFO depth, UART packet type IDs, physical target count requirements or changes to Architecture C are approved by this analysis. Proposed future verification: full 702-component pattern, FIFO full/host stall, packet retries/duplicate ACK/commit, abort after partial provisional transmission, lost connection before COMMIT, 0-record commit and next-CPI recovery. Existing standalone/connected tests are NOT these transactional tests.

## 5. Final S05 status

- **702 exact bound:** PROVED, with independent constructive executable checks.
- **Option A:** conditionally accepted as *design direction* (all components, no Top-K/silent loss; no simultaneous 702-record storage requirement).
- **Physical queue choice and transactional ICD:** OPEN, requires engineering signoff before acceptance; full REQ-LIST-01 **NOT PASS**.
- **Resource viability:** standalone memory-mapping measurements exist; full XC6SLX9 radar-chain fit and post-route 50 MHz timing **NOT PROVEN**.
- **Existing S04 gate:** CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS (administrative stage exit). REQ-RNG-03 FAIL 4/8, Fixed-Point statistical performance OPEN: unchanged.

**Next action:** Engineer to decide the transactional logical policy and permitted FIFO/host semantics. After that, a small valid/ready FIFO/transaction-control prototype can be implemented and integrated with the frozen S05 CFAR–Grouping baseline. Full Frame Controller waits for this decision and memory-architecture resource work.

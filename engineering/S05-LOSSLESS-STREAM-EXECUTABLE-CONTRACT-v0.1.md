# AX309-RDSP-001 | S05 Minimum Lossless Stream Contract v0.1

**Date:** 2026-11-12
**Authority:** System engineer approved Option A logical policy, not FIFO depth or final requirement PASS.
**Scope:** grouping-to-FIFO proof only; UART/ARQ/physical clock not verified.

## 1. Executable valid/ready contract and stoppability

The immutable grouping_8conn RTL consumes all 2782 range-major/Doppler-minor CUTs before entering its record-output phase. In state S_OUTPUT it asserts out_valid and holds the complete 99-bit record (including record_id) until out_ready rises at a clock edge. No next record is produced meanwhile. An eight-entry distributed FIFO can therefore deassert grouping out_ready on FULL and preserve every pending record; its own output must remain stable under sink back-pressure. The CFAR scanner has finished the CUT stream before output begins, so this downstream halt does not create a CFAR CUT deadlock in the current two-phase grouping architecture. This conclusion is **architecture-specific** and must be retested after any state-machine change.

The new synthesizable prototypes are rtl/transport/record_fifo8.v and rtl/integration/grouping_fifo8_subsystem.v. The lab queue has exactly eight 99-bit entries, synchronous writes, asynchronous RAM reads and simultaneous full dequeue/enqueue support. Depth eight is not frozen as a production requirement. A full FIFO is not an overflow: the source is contractually allowed to hold VALID and its data until READY returns. For data preservation with guaranteed producer stoppability, a direct handshake or single elastic slot may suffice; the amount of buffering needed for throughput and UART replay is a separate issue.

## 2. Record generation rate

For the 702-component deterministic frame, new ISim instrumentation observed the **fastest uninterrupted interval between accepted Grouping records to be 1407 FPGA clock cycles**; the longest observed interval was 61421 cycles due to an explicit 60000-cycle downstream pause. The grouping FSM re-examines up to 702 labels to select each next sorted record. At an *illustrative but not timing-qualified* 50 MHz this fastest interval is 28.14 microseconds / 35,536 record/s. No routed 50 MHz hardware clock is claimed.

The initial S02 UART setting is 115200 baud, 8N1 and subject to board confirmation: gross serial rate <=11520 bytes/s. The actual RTL record bus is 99 bits = 13 packed octets with 5 padding bits if represented on byte boundaries. S02's frame includes 17 overhead bytes and at most 512 payload bytes. The table below uses a **proposed 4-byte CPI_ID inside each RESULT payload**, not yet an approved UART ICD:

| Proposed batching | Record frames for all 702 | Record bytes + CPI IDs + per-frame 17-byte overhead | Optimistic minimum 115200 8N1 airtime |
|---|---:|---:|---:|
| 39 whole records/frame (39*13+4=511-byte payload) | 18 | 9126+72+306 = 9504 | 0.825 s |
| 8 whole records/frame (8*13+4=108-byte payload) | 88 | 9126+352+1496 = 10974 | 0.953 s |

These are **strict lower bounds** excluding START/COMMIT/ACK, retransmissions, host pauses, packet processing, and other traffic. Upper theoretical successful output rates are about 851 records/s (39-batch) and 737 records/s (8-batch) before ACK delays. The UART is orders of magnitude slower than an unblocked Grouping record stream at illustrative 50 MHz, so back-pressure will be necessary.

**ACK/replay invariant:** an output record must not leave its only retransmittable copy merely because UART bytes were transmitted. The sink can acknowledge/dequeue only after exact packet ACK, or copy accepted records into an independent retained packet-replay buffer. Batching 39 records needs storage for the 511-byte payload (or an equivalently replayable source); an eight-entry FIFO alone does NOT guarantee retransmission of a 39-record packet. One-record-per-packet with head held until ACK is simpler but increases link overhead and ACK traffic. Record packing endian, packet TYPE IDs, buffer depth and storage ports are unapproved.

## 3. Maximum wait and abort condition

Approved S02-C-UART-01 stop-and-wait ARQ: nominal **2-second timeout per frame at 115200 baud**, initial attempt plus at most **3 retransmissions**, explicit CPI abort/status if all attempts fail. If all four attempts time out, this is nominally ~8 seconds of ACK waiting for that failed packet, excluding actual serialization and control overhead. **This is not a complete CPI maximum runtime or a new FPGA-wide FIFO watchdog value.**

The production controller must let the full-FIFO back-pressure persist during valid UART pacing, while allowing independently timed protocol/ARQ failure to cause abort. A stuck link must not hold an active CPI forever once permitted retransmissions have been exhausted. Exact watchdog counter and final whole-CPI latency budget still require a system-engineer ICD decision; neither is verified by the mock sink.

## 4. Transactional host acceptance

Abstract events (no new UART numeric TYPE values have been assigned): CPI_START(CPI_ID), TARGET_RECORDS(CPI_ID, record_id), followed by exactly one terminal CPI_COMMIT(CPI_ID, count) or CPI_ABORT(CPI_ID, cause). The host holds every record provisionally and accepts COMMIT only after validating sequence/CRC and **exactly the distinct record IDs 0..count-1**, without gaps or conflicting duplicates. Identical retransmissions are idempotent; a COMMIT before all records have arrived does not qualify the CPI. A link loss **after the last record but before COMMIT** still invalidates the CPI, as does ABORT after a provisional prefix. Commit of zero records is legitimate. No successful CPI can later be aborted.

A fatal producer/transport fault must latch CPI_ID and the first fault outside DSP reset, inhibit successful COMMIT, attempt CPI_ABORT if the link is available, reset scanner/grouping without waiting for a stalled handshake and require a new full verified upload. A host that never received COMMIT discards provisional records even if ABORT itself was lost.

The new grouping_fifo8_subsystem frame_drained signal means **only that the grouping generation completed and the local FIFO emptied with internal counts equal**. It is not proof of UART ACK/host receipt and must not be wired directly to CPI_COMMIT.

## 5. Actual new tests and resource results

The **new** integration test rtl/tb/tb_grouping_fifo8_702.v uses the accepted **unchanged** prior synthetic 702-component C05+independent union-find oracle vectors as read-only input and goldens. Historical standalone grouping tests, REQ-RNG-03 CPI, C06R2 and statistical campaigns were NOT rerun.

**ISim PASS:** 2782 input CUTs, **702/702** complete, ordered oracle-matched 99-bit output records; FIFO occupancy reached **8**; 61423 full-occupancy cycles, **60014** source stalls, **71563** downstream valid-but-not-ready cycles, including a continuous 60000-clock-cycle full-FIFO pause, output-data stability under forced stall, and final produced=delivered=702 with empty FIFO. No result loss or deadlock within this finite mock-host test. This is **not** a physical UART, ARQ, packet replay or host transaction RTL PASS.

**Abstract host policy checker PASS (8 cases):** exact 702 count/commit, identical duplicate accept/conflicting duplicate reject, wrong count reject, abort-after-commit reject, disconnect after all records but before COMMIT invalid, abort after provisional records invalid, zero-record COMMIT valid, missing ID COMMIT reject. This is a Python semantic state machine, NOT a real UART receiver test.

**ISE 14.7 XST on grouping+FIFO RTL:** 0 synthesis errors, 4016 LUT, 1769 FF, 6 BRAM, no DSP reported, default estimated minimum period 9.990 ns; **1 warning, Xst:1336: 195 bonded IOBs versus only 186 device IOBs**. This bare 99-bit diagnostic top is **not placeable as a physical FPGA top**. The resource counts are combined optimized synthesis, not isolated incremental FIFO cost; no board or full radar-chain resource/timing PASS is claimed.

## 6. Decisions and status

- **Logical Option A:** APPROVED by system engineer. Exact upper bound 702; no Top-K, no silent discard; all records must be transported or whole CPI invalidated.
- **FIFO eight slots:** VERIFIED AS LAB PROTOTYPE, **NOT approved as final depth**.
- **Transactional UART ICD / ARQ replay buffer / output watchdog:** OPEN and not implemented in hardware.
- **REQ-LIST-01 technical status:** OPEN, final PASS not claimed.
- **Full XC6SLX9 design feasibility:** OPEN; connected CFAR-Grouping already consumes 76% LUT and has no routed 50 MHz closure.
- **Gate-S04:** CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03 FAIL 4/8 and Fixed-Point statistical performance OPEN unchanged.

**Next:** engineering decision on ACK-safe packet staging (one-record vs batched), FIFO depth and final UART transaction encoding, followed by synthesizable link/commit/abort RTL and testbench with real serial pacing and injected faults.

# AX309-RDSP-001 | S05 Resource, Memory Lifetime and Abort-Recovery Feasibility v0.1

**Status:** engineering feasibility analysis; not full RTL qualification or architecture approval. Baseline bbcac98. Target XC6SLX9-2FTG256, 5,720 LUT, 11,440 FF, 32 BRAM, 16 DSP48A1.

## 1. Actual XST data and scope

| Block or memory | Dimensions | XST BRAM | XST LUT | Status |
|---|---|---:|---:|---|
| Connected CFAR–Grouping | Existing RTL with private 4,096x46 power map and grouping tables | **18** | **4,374** | Actual connected XST PASS; 5 DSP, 1 warning, estimated 20.259 ns |
| Raw IQ, simple inferred array | 4,224x32, 135,168 bits | 16 | N/A | Isolated probe; 1 invalid-range warning |
| Raw IQ, 4096+128 banking | Same data, split memories | **9** | 34 | Isolated probe PASS, 0 warnings |
| MF frame, simple inferred array | 4,224x50, 211,200 bits | 25 | N/A | Isolated probe; 1 invalid-range warning |
| MF frame, 4096+128 banking | Same data, split memories | **14** | 52 | Isolated probe PASS, 0 warnings |

The banked MF mapping uses 13 RAMB16BWER plus 2 RAMB8BWER (14 reported BRAM sites). An initial conditional-read banking experiment incorrectly mapped into distributed LUTRAM and exceeded available LUTRAM; unconditional synchronous bank reads corrected this. Measured results are valid for these isolated probes only.

Theoretical BRAM18 bit-capacity floors are IQ ceil(135168/18432)=8, MF ceil(211200/18432)=12, power ceil(188416/18432)=11. Those are NOT placement/resource guarantees. Port widths, bank structures and XST inference change the realized block count.

Synthesis artifacts: engineering/evidence/s05/resource_budget/*.srp.gz. Probe sources: rtl/tools/resource_probe/*.v. Runner: rtl/tools/resource_probe/run_xst_storage_probes.sh. Nothing modifies the approved numeric RTL.

## 2. Peak BRAM budgets and architectural decision boundary

| Allocation | Projected BRAM total | Conclusion |
|---|---:|---|
| Current connected CFAR–Grouping (18) + separate banked MF (14) + separate complete IQ CPI (9) | **41/32** | Impossible as independently retained memories; other stages not counted |
| Existing connected CFAR–Grouping (18) + co-resident IQ/MF (14) | **32/32** | No BRAM left for other storage; inadequate unless further reuse |
| Grouping (6) + shared MF/power (14) + separate IQ (9) | **29/32** | Conditional, 3 blocks before scratch/UART; requires removing private scanner map |
| Grouping (6) + shared IQ/MF/power (14) | **20/32** | Most promising conditional layout, with 12 blocks nominally remaining; NOT integrated synthesis |

**Do not count the grouping 6-BRAM again on top of the measured connected 18-BRAM value.** Shared-memory rows are feasibility projections, not measured completed subsystems. IQ upload is not a one-pulse input: approved S02-C-UART-01 requires all **16,896 bytes** of the 33x128 complex CPI to be uploaded and verified before run. A mere 128-word pulse buffer cannot satisfy this without external storage or a change to the approved upload protocol.

The connected RTL already consumes 4,374/5,720 LUT (76%), leaving 1,346 LUT for MF/MTI/FFT, controller, UART and memory arbitration. It uses 5/16 DSP, leaving 11. The bare connected subsystem has 159/186 IOBs, which are not final board pins. XST estimated 20.259 ns (49.361 MHz), slower than a hypothetical 20 ns / 50 MHz goal even before placement and routing. No board clock or route timing is verified. **No full-chain XC6SLX9 resource/clock PASS is claimed.**

## 3. Symbolically verified candidate shared-store lifetime

An independent deterministic address-lifetime checker was executed: engineering/s05_memory_lifetime_validate_v0.py. Evidence: engineering/S05-MEMORY-LIFETIME-SYMBOLIC-EVIDENCE-v0.1.json. It uses no waveform CPI or radar numerical processing.

Candidate single 4,224x50 physical buffer (banked 4096+128):

1. Complete Q1.15 IQ upload: pulse-major address p*128+r, p=0..32 and r=0..127; lower 32 bits carry I/Q; full byte verification completes before processing.
2. MF in-place: process each pulse p, delay r ascending. Each 16-tap aligned MF output at r reads raw IQ indices r..r+15 within the acquisition. After reading, overwrite the same address p*128+r with its 50-bit MF output. Subsequent aligned output delays need only samples with indices greater than r, so overwriting at r cannot destroy a future source tap.
3. Range-wise FFT/power: for r ascending, read all 33 MF[p*128+r] words, then overwrite slots b*128+r for b=0..31 with U46.30 power(b,r) padded to 50 bits. These 32 MF slots have just been consumed. Future ranges are untouched.
4. CFAR after the full power map is ready: physically address power(b,r) as b*128+r, although the **logical** CUT order remains r-major then b-minor. The last 128 memory slots retain stale, already-consumed MF data.

**Symbolic result: PASS.** 63,624 raw-tap reads, 4,224 MF-word reads, 2,782 accepted CUTs and 114,062 symbolic power-map accesses (CUT plus 40 training samples). No live IQ, MF or power word is read after its premature overwrite in this proposed schedule.

**Crucial limitation:** the current cfar_2d_scan has an internal independent 4,096x46 memory addressed as r*32+b. The proposed 20-BRAM layout requires an external/shared power-map interface, address translation to b*128+r, and explicit BRAM port arbitration. These are **not implemented or verified**. Destructive IQ overwrite means later raw-IQ readback/replay may require a new host upload; S02 permits deterministic stage reruns but the exact reupload/retention policy must be decided before implementation. A symbolic proof cannot establish timing, synchronous read latency, physical memory packing or full-chain LUT fit.

## 4. Required fatal Abort/Reset and next-frame recovery contract

Existing connected RTL test evidence proves that after fatal grouping label overflow, frame_invalid and overflow_sticky assert while the CFAR scanner can remain blocked in valid&&!ready. The future Frame Controller **must never wait for normal scanner_done or grouping_done before handling a fatal error**.

Proposed fail-closed state/action sequence:

- **UPLOAD/VERIFY:** accept the complete verified CPI and CPI ID, then allow RUN. A partial upload is never eligible.
- **RUN/SCAN/GROUP:** monitor both engines' overflow_sticky, protocol_error, frame_invalid and a bounded watchdog, independently of handshake progress. Only one CPI may be active.
- **FAULT_LATCH:** on any fatal condition, immediately inhibit new input, scan starts and successful RESULT/COMMIT. Preserve the first fault reason and CPI ID in a register **outside the DSP submodule reset domain**. Any records already sent must be treated as uncommitted and discarded by the host for that CPI.
- **ABORT_RESET:** assert a synchronized common reset to scanner, grouping and other stateful pipeline modules; hold until sampled and quiescence confirmed, with bounded timeout. A stalled CUT handshake is not an obstacle to reset. Datapath sticky flags may clear, but the retained host-visible error status must not clear without explicit host acknowledgement.
- **RECOVER:** send explicit failed-CPI STATUS/NACK identifying the original CPI; require complete reupload and byte verification before a new run. Never resume mid-CUT or publish a partial list as a successful result.

When implementing the controller, independently test injected grouping overflow while a CUT is stalled, scanner protocol fault, abort during map loading, timeout during output back-pressure, preservation of the error across reset, correct host rollback, and subsequent clean-frame operation. Reset pulse width, watchdog cycle threshold and exact UART fault-code/packet assignments are **not yet approved** and must not be invented as acceptance limits.

## 5. Open engineering decisions / disposition

1. **REQ-LIST-01:** Choose external list capacity and overflow behavior. Recommended full 702-record stream and whole-CPI invalidation only on fatal exception; see engineering/S05-REQ-LIST-01-DECISION-PACKAGE-v0.1.md. Status OPEN_PENDING_ENGINEER.
2. **Shared storage:** Confirm shared-IQ/MF/power layout and its destructive IQ replay/readback semantics before changing the scanner memory interface; numerical Architecture C, coefficient formats, CA-CFAR geometry and FFT shifts remain fixed. Status PROPOSED_NOT_APPROVED.
3. **Abort implementation:** Require common synchronous datapath reset, independently latched host-visible fault, CPI rollback and full reupload/recovery; confirm watchdog/ICD values before formal RTL acceptance. Status DESIGN_CONTRACT_PROPOSED.

**Conclusion:** independent memory allocations cannot fit within 32 BRAM. An unmodified numerical Architecture C could potentially fit with explicit shared-memory scheduling, but this has only symbolic address-lifetime support; end-to-end RTL resource feasibility remains OPEN, especially given 76% measured LUT usage and unclosed timing. Any numerical architecture/FPGA change requires a separate engineer decision.

Gate-S04 remains CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03 remains FAIL (4/8), S04-C02-RISK-PERFORMANCE remains OPEN. No accepted CPI or previous S05 campaign has been rerun.

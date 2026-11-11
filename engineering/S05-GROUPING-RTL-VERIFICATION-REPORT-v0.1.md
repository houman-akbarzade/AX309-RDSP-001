# AX309-RDSP-001 | S05 8-Connected Grouping RTL and Verification v0.1

**Stage:** S05 implementation; module-level evidence only.
**Source baseline:** Git e9e99d2.
**Technology:** Spartan-6 XC6SLX9-2FTG256C, ISE 14.7/ISim/XST.
**S04 carryover:** REQ-RNG-03 FAIL 4/8, 8/8 criterion unchanged; S04-C02-RISK-PERFORMANCE OPEN. Neither was rerun.

## 1. Approved behavioral contract

Reviewed sources:
- engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json, including REQ-DET-01 and REQ-LIST-01.
- s03_reference/model.py, function clusters_8, for eight-neighbour topology and deterministic peak order.
- engineering/s04_numeric/s04_c05_native_integer_v1.py, function native_clusters, as the signed-off integer-native reference.
- engineering/s04_numeric/s04_c05_integrated_qualification_v1.py, independent_components union-find cross-check.
- engineering/S04-C05-INTEGRATED-POWER-CFAR-GROUPING-QUALIFICATION-v1.0.md and the C05 independent engineer sign-off.
- engineering/S05-RTL-ARCHITECTURE-v0.1.md and rtl/power_cfar/cfar_2d_scan.v.

Approved domain: a 128x32 nonwrapped range-Doppler map, with valid CUTs r=3..109 and unsigned b=3..28. The input stream contains all 2,782 valid CUTs in range-major/bin-minor order, with a one-bit alarm and a stored unsigned U46.30 CUT power. An alarmed CUT belongs to an eight-connected component if its horizontal, vertical or diagonal neighbour is alarmed. The Doppler boundary does not wrap.

Each component's peak is the maximum STORED INTEGER U46.30 power. At equal maximum power choose lower SIGNED Doppler (b<=15: b, else b-32), then lower range, then lower unsigned Doppler. Record order is ascending peak range, then ascending signed Doppler. Each record includes stable sequential record_id, peak coordinates, signed bin, stored power, cluster cell count, equal-maximum-power cell count and tie_flag. Physical unit conversion remains a host-side concern unless explicitly frozen by the interface contract.

## 2. RTL implementation

File: rtl/grouping/grouping_8conn.v.

The block uses a sequential 8-connected raster labeler with two 32-entry row-label banks. Each hit checks the left and three previous-row neighbours, traverses parent pointers, joins different roots, and consolidates counts and stored-power peaks. Parent pointers and 82-bit per-root statistics have a SINGLE synchronous read and write port each to infer BRAM. The lookup is serial to avoid multiport-LUT explosion.

After the 2,782nd CUT the block performs a deterministic selection scan over surviving roots, emits record_id 0..N-1 and holds the entire output unchanged during downstream back-pressure. A new frame can start only after all target records are accepted. Streamed hits are checked against the exact expected coordinates; out-of-order input raises protocol_error and frame_invalid and aborts the frame.

**Capacity clarification:** 702 is the mathematically established maximum number of independent eight-connected components in the 107x26 valid CUT grid, and an upper bound on newly created labels. Internal tables have 10-bit addressing and 1024 padded slots for XST-inferred block RAM; allocation is restricted to 702. The parameter MAX_LABELS permits a deliberately smaller internal allocation limit for fault testing. If that internal limit is exceeded, overflow_sticky and frame_invalid assert, no incomplete output list is emitted, and the frame aborts explicitly. This safety behavior is an RTL diagnostic, NOT a signed-off external target-list selection/truncation policy.

**OPEN ENGINEERING DECISION:** S02 REQ-LIST-01 defers the external target-list capacity and target selection on overflow to S05. This implementation does not pick or silently discard a subset. Decide whether to accept fail-stop, require a specific bounded list and deterministic selection, or allocate the full 702 records. Until approved, do not mark REQ-LIST-01 fully accepted.

## 3. Independent verification

Testbench: rtl/tb/tb_grouping_8conn.v.
Generator: rtl/tools/generate_grouping_vectors.py.
Runner: rtl/tb/run_grouping_isim.sh.

The synthetic vectors have no historical input CPI and do not run the S03/S04 statistical campaigns. The original C05 native clustering code is imported UNMODIFIED to generate target records. A SEPARATELY WRITTEN union-find implementation compares every expected record and cluster field before the vectors are released to ISim. The RTL self-checker then compares each output byte-for-byte at the packed-field level, checks record IDs and holds output under back-pressure.

11 fixed full-frame scenarios (30,602 accepted CUTs) produce 887 exact target records. Cases exercise no detections; independent corner detections; horizontal and vertical connectivity; diagonal connectivity distinct from 4-neighbour topology; late label unions; signed Doppler and equal-power range ties; sparse deterministic hits; one dense 2,782-cell cluster; the 702 independent-cluster capacity bound; deterministic replay; no boundary wrap; explicit overflow with MAX_LABELS=1; out-of-order protocol violation; and input valid gaps/output stall stability.

**RESULT:** actual ISim run PASSED all 11 cases and matched all 887 oracle records. The separate C05 BFS vs union-find generator comparison also PASSED. Scope: block-level deterministic integer grouping only, not a complete radar CPI or statistical performance campaign.

Reproduction:
- python3 rtl/tools/generate_grouping_vectors.py
- bash rtl/tb/run_grouping_isim.sh
- bash rtl/tb/run_isim.sh (combined five-module unit suite)

## 4. XST synthesis and resource implications

Synthesis command: bash rtl/tools/run_xst_grouping_8conn.sh.
Top: grouping_8conn; XC6SLX9-2-FTG256, speed grade -2.

Final accepted synthesis:
- Error count: 0.
- Warning count: 0.
- Slice LUT: 4,034 of 5,720 (70%).
- Slice registers: 1,727 of 11,440 (15%).
- Block RAM: 6 RAMB16BWER of 32 (18%).
- DSP48A1: 0.
- Standalone bonded IOBs: 170 of 186 (91%).
- Default estimated minimum period: 11.797 ns, maximum 84.766 MHz.

No UCF/clock period, place-and-route or post-route timing check was performed. The estimate is not timing closure.

**Risk:** even though grouping alone fits XC6SLX9, 70% LUT usage is substantial. Separate standalone CFAR Scanner synthesis reports another 464 LUT and 12 BRAM. Their arithmetically summed 4,498 LUT (about 79% of 5,720) and 18 BRAM do NOT constitute an integrated synthesis result. The S05 architecture's previous approximately 18-BRAM frame-store estimate, if allocated in addition to both memories without reuse, would exceed the 32-BRAM device; this estimate must be resolved through actual shared-lifetime memory scheduling and integrated synthesis. The 170 standalone I/O count is an unintegrated RTL port count and is not a board pinout.

## 5. Status and exclusions

- Grouping implementation: IMPLEMENTED.
- RTL simulation and C05 software oracle equivalence: PASS, for the 11 synthetic tested cases.
- Standalone XST: PASS at RTL synthesis scope with 0 warnings; target-device resource limit not exceeded by this block alone.
- CFAR-to-grouping connected simulation: NOT RUN.
- Full-stage RTL equivalence, FPGA timing closure and board qualification: NOT RUN.
- S02 REQ-LIST-01 external capacity and overflow record selection: OPEN, requires engineer disposition.
- S04 REQ-RNG-03 and Fixed-Point statistical performance: unchanged.

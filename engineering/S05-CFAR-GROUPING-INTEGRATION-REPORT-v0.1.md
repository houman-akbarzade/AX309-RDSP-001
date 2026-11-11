# AX309-RDSP-001 | S05 CFAR–Grouping Integration Verification v0.1

**Baseline:** b62116d. **Audit and execution:** 2026-11-12.
**Scope:** connected scanner-to-grouping RTL subsystem only, not complete CPI radar or post-route timing.

## CUT geometry decision

The approved S02 range-side CFAR stencil is confined to full-echo MF delay support 0..112, not merely the stored 128-bin power map. A 16-sample echo is fully contained for delay k<=128-16=112. S03 extracts 128 delay-aligned samples from a **full** 143-output convolution; it does not use a 113-output valid-convolution algorithm. Thus for the 7x7 stencil, CUT r+3<=112, r=3..109; Doppler b=3..28; total 107*26=2782 CUTs. The geometric-only stored-map region r=3..124 would yield 3172 CUTs, 390 additional CUTs. The approved 2782 is intentional and binding. See engineering/S05-CUT-GEOMETRY-AUDIT-v0.1.md. No geometry change is made.

## Connected RTL and exact input/output contract

- Top: rtl/integration/cfar_grouping_subsystem.v
- Unchanged modules: rtl/power_cfar/cfar_2d_scan.v, rtl/grouping/grouping_8conn.v and rtl/power_cfar/cfar_compare.v.
- The scanner's ordered 2782 CUT stream connects directly to grouping with equal coordinates, U46.30 stored power and strict CFAR alarm. Valid/ready handshake is one-for-one; ready propagates from grouping to scanner.
- A wrapper-level cut_pause can throttle CUT handshakes **safely on both sides simultaneously**; it does not change detection arithmetic or module interfaces.
- The common frame start initializes grouping while the scanner fills its power-map memory. Scanner done marks the last accepted CUT; grouping done marks completion of the target-record stream, and may occur later.
- Fatal grouping overflow sets frame_invalid and overflow_sticky; no partial/truncated target list is emitted. After fatal overflow, a scanner CUT can remain back-pressured; the system-level abort/recovery mechanism must reset both blocks. This behavior is deliberately exposed as an integration issue.
- Grouping's GROUP_MAX_LABELS=702 default is the established internal independent-component bound, not an approved external target-list truncation policy. Test-only instantiation with limit 1 proves overflow signalling.

## Actual ISim and independent-oracle results

Five fresh synthetic 128x32 integer power maps were generated independently of historical CPI: all-zero, four isolated valid-map corners, diagonal/bridge/late-merging with equal-power signed-Doppler tie, exact CFAR threshold equality with no alarm, and deterministic replay.

The unchanged signed-off S04-C05 native integer software reference produces the CUT decisions and clustering records. A separately written direct CFAR 40-cell-sum/strict-comparison implementation and independent union-find grouping cross-check the oracle. The RTL testbench compares **every accepted CUT's** range, Doppler, strict alarm, U46.30 stored power and U52.30 SUM40, then every output cluster's ID, peak range/Doppler, signed Doppler, peak power, cell count, equal-power peak count and tie flag.

- ISim integrated PASS: 5/5 maps, 20,480 power-map input words, 13,910 accepted CUT handshakes, and 14/14 final oracle-matched cluster records.
- Frame results: 0, 4, 5, 0 and 5 clusters respectively.
- CUT pause: 8 stalled cycles; target-record output stalls: 32 cycles. Data stability during both stalls verified; no CUT loss/duplication.
- Full frame start/end, scanner-done vs grouping-done, repeatability and output order all PASS.
- Test-only reduced internal label capacity: explicit overflow and invalid-frame status, no truncated output. Synchronous reset clears the fatal status.
- Simulation runner: rtl/tb/run_cfar_grouping_isim.sh. Testbench: rtl/tb/tb_cfar_grouping_subsystem.v. Input and expected oracle vectors: rtl/tb/vectors/cfar_grouping/.
- Evidence: engineering/evidence/s05/cfar_grouping/CFAR-GROUPING-ORACLE-v0.1.log and CFAR-GROUPING-ISIM-v0.1.log.

**PASS scope:** connected, deterministic integer CFAR/grouping processing of five synthetic maps. This does **not** establish target physical separation, REQ-RNG-03 PASS, full MF/MTI/FFT/CFAR/Grouping system equivalence, statistical Fixed-Point Pfa/Pd, or board testing.

## Integrated XST observations

Command: rtl/tools/run_xst_cfar_grouping_subsystem.sh.
Top: cfar_grouping_subsystem; device XC6SLX9-2-FTG256, speed grade -2, ISE 14.7 XST.

| Resource | Actual connected synthesis | Device capacity |
|---|---:|---:|
| Slice LUT | 4,374 (76%) | 5,720 |
| Slice registers | 1,849 (16%) | 11,440 |
| BRAM | 18 blocks: 17 RAMB16BWER + 1 RAMB8BWER (56%) | 32 |
| DSP48A1 | 5 (31%) | 16 |
| Standalone/subsystem bonded IOB | 159 (85%) | 186 |

Estimated minimum period: 20.259 ns, estimated maximum frequency: 49.361 MHz. **Neither is post-route timing closure.** Zero synthesis errors. One noncritical XST:2677 warning concerns the unused transient u_scanner/overflow_event output; the persistent scanner overflow_sticky remains exported through the wrapper. The warning is preserved, not misreported as zero.

**Resource bottleneck:** the connected CFAR/Grouping subsystem already consumes 76% of all LUT and 18/32 BRAM. The previously estimated independent MF frame store (~18 BRAM) would bring the naive non-reused total above 32 BRAM, before input storage and other stages. The remaining 1,346 LUTs, 14 BRAM and 11 DSPs are not a demonstrated budget for the complete radar chain. Address-lifetime-safe memory reuse, controller scheduling and integrated full-datapath resource fit require distinct work. Physical I/O and board constraints are not established. Do not add an unapproved data-path or numeric-contract change to make it fit.

**Artifacts:** compressed XST report and netlist in engineering/evidence/s05/cfar_grouping; detailed source and evidence hashes in the S05 tracker.

## Open technical and engineering decisions

1. REQ-LIST-01 external target-list capacity and selection on overflow: **ENGINEER DECISION PENDING**. Internal fail-stop is a provisional diagnostic, not final acceptance.
2. Integration recovery after fatal grouping overflow: scanner can remain stalled; future frame controller must implement an explicit all-engine reset/abort sequence.
3. Full top-level memory reuse/BRAM fit and LUT timing/resource headroom: **OPEN**; no complete radar-chain synthesis or place-and-route has been run.
4. MF edge/padding and aligned address production by the full CPI/frame controller: **OPEN** for S05 implementation verification.
5. Gate-S04 remains CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03 remains FAIL (4/8) and Fixed-Point statistical performance remains OPEN. No CPI rerun, no changes to C architecture, alpha, rounding, FFT shifts or acceptance criteria.

**Next implementation:** resource-aware frame/memory controller integration and explicit external list-capacity engineering disposition before full-system qualification. The connected-subsystem simulation and synthesis are PASS strictly within their measured scopes.

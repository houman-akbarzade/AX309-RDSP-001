# AX309-RDSP-001 | S04-C05 Integrated Power/CFAR/Native Grouping Qualification v1.0

**READY FOR INDEPENDENT SIGN-OFF; C05 OPEN, NOT PASS.** The engineer independently signed C04 PASS; C architecture, Q formats, FFT shift [0,1,0,1,1], C01 g profiles and all open obligations are unchanged. S04 4/8=50%; total 29.1667%; Gate-S04 OPEN.

## Frozen integer algorithm and distinct independent oracles

The new native engine engineering/s04_numeric/s04_c05_native_integer_v1.py computes from signed Q25.15 FFT I/Q each raw 50-bit real multiplication and 51-bit unsigned sum of squared I and Q, then guarded narrowing with explicit saturation to U46.30. SUM40 accumulates the **40 stored U46.30 training cells** in the 7x7 window excluding central 3x3 guard (U52.30). For 107 range positions by 26 Doppler positions, exactly **2782 valid CUTs** are checked. The strict exact integer comparator is:

    40 * Pcut * 65536 > 490007 * SUM40

An exact tie is NO ALARM. Full 68-bit/72-bit unsigned conservative crossproduct capacities are preserved; no floating arithmetic or silent wrapping occurs.

Native 8-neighbor clustering uses unwrapped 128x32 grid connectivity; peak is maximum **stored integer U46.30 power** and exact ties select minimum signed Doppler bin, minimum range bin, then minimum unsigned Doppler bin. Records contain stable sorted record IDs, power integer, range, Doppler bin, signed Doppler, exact rational range/nominal velocity, cluster size, tie flag and number of max-power ties. Independent **union-find** connected-component logic (not the native BFS implementation) independently confirms grouping, peaks, record ordering and flags. C03 independent Fraction power and CFAR checks are separate from C02 and C05 arithmetic helpers.

## Executed tests and numerical evidence

**19/19 independent self-checking unit tests PASS, 0 FAIL.** Tests include full unsigned min/max, U46.30 saturation and raw integer trace, 40-cell geometry/exclusion, maximum U52.30 sum, strict CFAR exactly at 490007/65536 threshold and ±1 CUT boundary, 2782 valid geometry, zero/edge, 8-connected diagonals, no Doppler wrap, signed Doppler ties, minimum range tie resolution, target record rational fields, original S03 host comparison, and immutability/prohibitions.

All 18 preserved deterministic C01 scale-as-arithmetic-profile cases (nine vector patterns at g1 and g5), including deliberately saturated stress vectors, were checked. In total **73,728 power cells** and **50,076 CFAR CUT decisions** exactly agree with selected-C v0.6 integer evidence, independent Fraction arithmetic, and separately authored union-find grouping. The selected C integer output has no observed internal processing saturation on these 18 vectors; input stress saturation remains in evidence (8448 clipped IQ components per overrange vector). This is deterministic qualification, not a claim about statistical CPI/Pfa/Pd.

## Exact reproduction of two v0.6 Float/Fixed peak discrepancies

IDs: g1:phase_interference and g5:phase_interference. For both, the Float S03 original-source CFAR mask and native fixed CFAR alarm mask are **identical**; host clustering on the fixed mask and fixed reconstructed power agrees with native integer grouping. Original Float powers at (range=3,Doppler=20) and (range=4,Doppler=20) are **exactly equal** in the reference: at g1 both 2003.740740417848, and at g5 both 50093.51851044622. S03 resolves the Float tie by smaller range r=3.

The selected C integer powers are r3=33612372401 and r4=33612427349 for both g-scaled versions, a strict integer difference of 54948 favoring r=4. Native grouping therefore selects (4,20), as it must under its **approved integer maximum-power rule**, whereas Float S03 selects (3,20) under exact Float tie resolution. The other cluster remains (4,4).

**Disposition:** quantization breaks the original Float peak-power equality and changes the highest-power coordinate. This is **not** an error in native integer grouping or an unimplemented tie rule. The two differences are explicitly preserved, with exact competing powers, in the evidence JSON; independent acceptance of their end-to-end Float/Fixed impact remains **OPEN for C06**. No retrospective threshold, suppression, waiver or agreement claim is made.

## Files and reproduction

From repo root under /usr/bin/python3 (Python 3.14.4):

    /usr/bin/python3 -B engineering/s04_numeric/s04_c05_integrated_qualification_v1.py
    /usr/bin/python3 -B -m unittest discover -s tests -p test_s04_c05_integer_power_cfar_grouping_v1.py -v

Native code: engineering/s04_numeric/s04_c05_native_integer_v1.py
Independent oracle/union-find and historical exact replay: engineering/s04_numeric/s04_c05_integrated_qualification_v1.py
Unit tests: tests/test_s04_c05_integer_power_cfar_grouping_v1.py
Full evidence: engineering/s04_numeric/S04-C05-integrated-power-cfar-grouping-v1.0.json
Full command logs: engineering/S04-C05-INTEGRATED-v1.0-NATIVE-RUN.log and engineering/S04-C05-INTEGRATED-v1.0-INDEPENDENT-TESTS.log
SHA-256 manifest: engineering/S04-C04-SIGNOFF-C05-INTEGRATED-EVIDENCE-MANIFEST-v1.0.json

## Boundary

**C05 OPEN, READY FOR INDEPENDENT SIGN-OFF.** This package establishes deterministic integer power/CFAR/grouping/record qualification. REQ-SCR-01 and REQ-RNG-03 remain BINDING OPEN; two quantization-induced peak-coordinate differences remain OPEN for independent C06 numerical acceptance, as do statistical performance, hardware resources, hardware overflow trace, RTL and UART/FPGA ICD. No main statistical CPI, accepted S03 seeds, RTL, synthesis or FPGA tests; no architecture changes.

# AX309-RDSP-001 | S04-C03 Independent Engineer Sign-off v1.0

**Decision: S04-C03 = PASS, strictly within independent integer/bit-true primitive qualification.**

**Authority:** the engineer's current explicit independent sign-off directive, following independent review of 24/24 self-checking C03 tests and P01–P08. This document records that engineer decision; no agent-issued approval is inferred.

**Controlling evidence:** commit \`2e540d798518141a42a13f39e46d4add33b52414\`; report \`engineering/S04-C03-INTEGRATED-BITTRUE-PRIMITIVE-QUALIFICATION-v1.0.md\`; independently developed Fraction oracle \`engineering/s04_numeric/s04_c03_independent_oracle_v1.py\`; executable test suite \`tests/test_s04_c03_integrated_qualification_v1.py\`; machine evidence \`engineering/s04_numeric/S04-C03-integrated-qualification-evidence-v1.0.json\`; full event-trace manifests and seven full trace files.

## Exact accepted scope

C03 P01..P08 all **PASS**: IQ g1/g5 rational packing and saturation, independently reconstructed 16 MF coefficients and 31 FFT twiddles, Gaussian integer multiplication/full MF accumulation, MTI and 5-stage FFT Butterfly, RNE and negative signed ties, power/SUM40 and strict alpha CFAR, complete ordered overflow records, independent reproducibility and immutable C contract.

The new C03 test suite passed **24/24**. Prior **39/39 C02 regression tests** were independently retained and rerun but never counted as new C03 tests. Full C03 events: **16,896 input clip** plus **159 forced internal test events** = **17,055** completely saved and SHA/readback verified. Independent exact verification checked the **4096-cell** power map and **2782 valid CFAR CUT**.

**Frozen C02 baseline** remains C with FFT shifts \`[0,1,0,1,1]\`, exact coefficient tables, RNE/narrowing, declared widths and g profiles. No A/B/C reevaluation. This signature does not authorize main statistical CPI, reuse of S03 accepted Pfa/Pd seeds, RTL, synthesis or FPGA.

## Non-waiver and residual risk

The previous \`engineering/S04-C02-SELECTED-C-OPEN-OBLIGATIONS-v1.0.json\` is immutable and continues to bind **REQ-SCR-01, REQ-RNG-03**, native fixed-point clustering, two reference host peak disagreements, final Float/Fixed error-budget criteria, statistical verification, complete **hardware** overflow trace and physical hardware-resource evidence. The Python prototype full-record trace is accepted only for the C03 primitive qualification, not proof of a deployed FPGA logger.

**Progress consequence:** C01 PASS BOUNDED; C02 PASS; **C03 PASS**; C04 OPEN for execution. S04 = 3/8 = **37.5%** and overall = \`(3+3/8)/12 *100\` = **28.125%**, Gate-S04 OPEN. C04 is not credited until a separate independent sign-off.

# AX309-RDSP-001 | S04-C01 Engineer Conditional Sign-off v1.0

**ENGINEER-APPROVED: S04-C01 PASS — BOUNDED INPUT CONTRACT.** This records the explicit engineer/user decision, not an independent agent sign-off. Gate-S04 OPEN; C02 OPEN.

## Signed scope
- Decision ID S04-C01-SIGNOFF-001, criterion S04-C01 baseline/requirements traceability now completed, 1/8.
- NOISE_ONLY_UNIT: source 33x128 complex CN(0,1), no target or clutter, approved rational g=5; **whole-campaign** 20,000-independent-CPI input-saturation stop-risk upper limit 0.001 (0.1%). NOT a per-CPI risk or valid for any other population. Analytic model gives 0.00025973555 for g5 under independent Gaussian assumption.
- SINGLE_TARGET_REFERENCE_LIKE: controlled LAB-only source, single k40 Doppler+4 amplitude0.18 phase0, E|noise|²=0.000324, no clutter, approved rational g=1. The lab test-case manifest is frozen before generating/processing samples, never from observed target amplitude or detections. UNKNOWN operational targets have NO authorized target-dependent gain selection and no approved campaign risk target.
- Configurable pre-CPI g with explicit immutable source/profile/selection-rule IDs, positive reduced integer gain ratio, SHA and replay metadata APPROVED as logical contract. UART/FPGA wire ICD NOT APPROVED.
- Signed Q1.15 I/Q LE pulse-major input q=SAT16(RNE(32768*x/g)), xhat=g*q/32768. Input clipping starts at x>=g*65535/65536 or x<-g*65537/65536. Unsaturated per-component error <=g/65536 and complex error <=sqrt(2)*g/65536 in normalized source amplitude units. Lab g1 LSB 1/32768, max complex error sqrt2/65536, ratios to amplitude0.18 respectively 0.01695421% and 0.01198844%. No claim of processed target amplitude/RMS/Pd.
- Approved VALID_PERFORMANCE / INCONCLUSIVE / STRESS_ONLY dispositions: frozen admissible profile, input payload/dimension/hash checks; count all CPI in preapproved fixed N and preserve sample identities; stop on unexpected clipping/overflow/invalid metadata under strict performance protocol, record attempted/processed count and cause as INCONCLUSIVE, never report a truncated-N PASS. STRESS_ONLY is a separately declared deliberate-overflow corpus excluded prospectively. No deletion, replacement, sample top-up, automatic retry, optional stopping or output-driven gain/threshold tuning. Capture full ordered clipping event trace/count/location/sign, sticky counters and overflow flags.
- REQ-SCR-01 and REQ-RNG-03 stay **binding open S02 obligations**. Historical S03 ownership and prior evidence unchanged. Additional approved future ownership: **C02 numerical coverage DESIGN**, **C06 independent VERIFICATION**. Both must have independently evidenced closure/disposition BEFORE Gate-S04 can close. This is a cross-stage obligation, not S04-C01 population expansion or waiver.

## Limitations and handoff
- C01 PASS only for above no-clutter sources. Stochastic/correlated clutter, SCR±10dB and multi-target/two-target qualification remain OUT OF BOUNDED C01, but NOT waived in S02/project.
- Internal MF/MTI/FFT arithmetic widths, twiddles, FFT shifts, fixed-point CFAR alpha, downstream saturation, numeric RMS/error budgets, Float/Fixed detection/Pd, UART/FPGA ICD and RTL/hardware are NOT approved.
- C02 entry limited to preparation/design proposal and independent subsequent review, with **no A/B variant or width/shift/error selection**.
- Accepted S03 seeds and output are not for numeric retuning. Carry the 4135 unmatched target-present clusters (NOT Pfa), missing full IQ/power archive, and prior Student-t/spatial failures.
- Exact historical engineer message time is not provided: recorded_at_utc of this document is the archival time, NOT a fabricated signed-at timestamp.

## Progress authorized
S04 1/8=12.5%; with 12 equal stage weights overall=(3+1/8)/12*100=26.041666666666668% (~26.04%). Gate-S04 remains OPEN. C02-C08 remain incomplete.

**Basis:** exact engineer/user instruction of this turn, preserved in replay/conversations.jsonl and linked Replay event. Decision is engineer-issued; artifact captures it only.

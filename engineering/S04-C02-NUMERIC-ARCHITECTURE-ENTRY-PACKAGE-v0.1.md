# AX309-RDSP-001 | S04-C02 Numeric Architecture Design — Entry Package v0.1

**DESIGN INPUT ONLY; C02 NOT APPROVED.** Stage S04-C01 engineer PASS bounded input baseline. No numeric architecture or parameter is selected here. Gate-S04 OPEN; S04 1/8 and overall 26.041666666666668%.

## Accepted boundary inputs from C01
- Only two no-clutter laboratory populations are admitted for C01 signoff: NOISE_ONLY_UNIT CN(0,1), g=5, 20,000 CPI theoretical whole-campaign clipping-risk ceiling 0.1% under independence; and SINGLE_TARGET_REFERENCE_LIKE controlled target amplitude .18 / Doppler+4 / k40 with complex noise power .000324, g=1.
- Rational input gain chosen by frozen lab/source-class metadata prior to samples; immutable host audit metadata, exact Q1.15 input RNE/saturation/reconstructed Float-scale semantics, fixed denominators, stop/INCONCLUSIVE, stress-only separation.
- No approval of UART/FPGA wire ICD; operational unknown targets not authorized to use lab target truth.

## Required design trade studies for engineer review
1. Trace all B00..B12 numeric interfaces, signedness, stored and reconstructed domain and coefficient formats under g5 and g1, including explicit stage scale sFFT.
2. Compare previously proposed option A and B, or documented alternative, including W/F of *internal* complex products and accumulation, MF 16-tap growth, MTI subtraction, FFT32 five stages and guard bits; do not select one.
3. Examine FFT stage shift tradeoffs and twiddle coefficient precision. Evaluate rounding RNE on negative/tie boundaries and arithmetic right-shift signs; no silent wrap, saturation counters.
4. Compare power squaring and 40-cell unsigned training sums, strict CUT>alpha*sum40/40, rational integer alpha oracle, threshold near-equality and CFAR decision stability.
5. Propose separate input-only and processing-stage MAX/RMS error budgets and test oracles **prospectively**; C01 input quantizer limits do not prove downstream errors.
6. Assess numeric range for REQ-SCR-01 SCR +10/-10dB clutter conditions and REQ-RNG-03 two equal-power target separation (~600m nominal); preserve source S02 measurement region, tolerance and resolved-pair oracles. Propose complete numeric design coverage but **do not run stochastic accepted tests**. C06 owns eventual independent validation and must independently close both before Gate-S04.
7. Resource tradeoff proxies only; no hardware FPGA or synthesis evidence exists. RTL/synthesis/FPGA tests prohibited without separate authorization.
8. Keep DEV corpus and future ACCEPT corpus independent; historical S03 Pfa/Pd seeds/data are frozen read-only and excluded from tuning.

## Entry gates and open approvals
- C02 remains OPEN until engineer reviews and approves W/F, per-stage scales and shifts, coefficient representation, overflow handling, numeric tolerance criteria and stage evidence contracts.
- REQ-SCR-01 and REQ-RNG-03 have unchanged historical S03 provenance, additional approved C02 design/C06 independent verification responsibility, and mandatory closure **before Gate-S04**.
- C03-C08 not advanced. No CPI generated or RTL started. This packet authorizes no new numeric implementation.

Sources: decisions/S04-C01-ENGINEER-CONDITIONAL-SIGNOFF-v1.0.md; engineering/S04-C01-FINAL-CONDITIONAL-APPROVAL-PACKAGE-v0.8.md; engineering/S04-NUMERIC-CONTRACT-PROPOSED-v0.2.md; approved S02 matrix v1.2.

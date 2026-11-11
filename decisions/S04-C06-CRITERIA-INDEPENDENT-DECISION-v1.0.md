# AX309-RDSP-001 | S04-C06 Independent Criteria Decision v1.0

**Decision: PARTIAL APPROVAL A–E WITH BINDING CONDITIONS; F NOT APPROVED. C06 remains OPEN.** This is a criteria decision only. No C06 acceptance CPI, acceptance dataset, statistical run, RTL, synthesis or FPGA test is authorized by this record.

## Reviewed basis

Reviewed the v0.1 criteria package, its analytic JSON, manifest, and reproducible calculation script. Re-executed `engineering/s04_numeric/s04_c06_preapproval_analytic_bounds_v0.py`; all seven reported analytic bounds and rounded caps reproduced exactly. No empirical C04/C05 results or accepted S03 seeds were used to derive or tune the limits. C01–C05 scope, selected architecture C, formats and FFT shifts `[0,1,0,1,1]` remain frozen.

## Decisions

### A — Stagewise MAX/RMS safety ceilings: APPROVED WITH CONDITIONS

Approve the seven stage ceilings exactly as proposed, in original complex Float amplitude units:

| Stage | g=1 | g=5 |
|---|---:|---:|
| MF | 0.00074 | 0.00366 |
| MTI | 0.00147 | 0.00731 |
| FFT1 | 0.00468 | 0.02337 |
| FFT2 | 0.01286 | 0.06428 |
| FFT3 | 0.03267 | 0.16335 |
| FFT4 | 0.07926 | 0.39629 |
| FFT5 | 0.18636 | 0.93177 |

These are conditional deterministic numerical safety screens only, not radar-performance limits, statistical confidence bounds, or proof of acceptable Pd/Pfa. RMS is reported and checked against the same conservative ceiling because RMS ≤ MAX; it is not an independently calibrated RMS criterion. Applicability requires the exact frozen C arithmetic, no input clipping, no internal overflow/saturation, and satisfaction of the analytic input envelope used by the derivation. If any assumption is violated or cannot be established, mark the affected CPI/result INCONCLUSIVE; do not apply the bound outside its assumptions. `g=5` applies only to the C01-approved noise-only population; `g=1` only to the approved single-target laboratory reference-like population. Deterministic arithmetic vectors at another g remain diagnostics/STRESS_ONLY and do not extend C01 authorization.

### B — Exact integer/bit-true equality: APPROVED

For every eligible sample/cell, require exact agreement with an independently implemented integer/rational oracle for stored stage outputs, U46.30 power, U52.30 SUM40, all 2782 valid CUT decisions, clusters, peak selection and target records. Any integer-to-integer mismatch is FAIL. No tolerance, exclusion or retrospective waiver is permitted.

### C — CFAR Float/Fixed decision margin: APPROVED WITH CLARIFICATION

Use the frozen alpha values and exact integer strict comparator for the Fixed decision. Report every changed CUT in both directions, its Float and Fixed margins, power-error bound, alpha-quantization contribution, cluster and target-record consequences. A changed CUT outside the analytically certified uncertainty envelope is FAIL. A CUT within the envelope is AMBIGUOUS and must remain in all records and denominators; absent a separately preapproved permitted ambiguity count/rule, classify the affected Float/Fixed decision comparison as INCONCLUSIVE, never PASS by default. Exact bit-true Fixed-vs-Oracle equality remains mandatory independently of Float/Fixed ambiguity. No CUT or CPI may be removed or replaced.

### D — Exact Float-tie peak exception: APPROVED, NARROWLY

Permit only the classification `FLOAT_REFERENCE_EXACT_TIE_SPLIT_BY_QUANTIZATION` when all conditions hold: (1) the frozen original-input Float reference proves exact equality of the competing maximum powers; (2) both candidates belong to the same unchanged alarm/cluster component; (3) the Fixed integer peak is selected by the frozen integer maximum/tie rule; and (4) independent integer grouping and target records match exactly. This is not a ±1 range-bin tolerance and does not waive any non-tied peak displacement, cluster split/merge, missed target or record mismatch. The two historical `phase_interference` cases must be replayed and reported explicitly under this classification. The exception does not establish general peak-location or estimator accuracy.

### E — CPI disposition, fixed denominator and evidence lock: APPROVED WITH CONDITIONS

Freeze source profile, g, scenario class, vector/CPI IDs, N, denominator, code/reference hashes and eligibility metadata before processing. `VALID_PERFORMANCE` requires a C01-authorized profile, complete input and stage records, no clipping/overflow, valid input-envelope assumptions, and complete matched references. `INCONCLUSIVE` covers invalid/missing metadata, clipping, internal overflow, violated analytic assumptions, or unclassified ambiguous decisions. `STRESS_ONLY` must be designated before processing for deliberate clipping, limits, ties or overflow; it cannot enter a performance denominator. Preserve all intended CPI/CUTs and every event with pre-narrowing integer value, location, stable ID and hash. No deletion, replacement, automated rerun, retuning or denominator changes. C01's existing noise-only 0.1%/20,000-CPI rule is unchanged and must not be generalized.

### F — SCR and two-target scope: NOT APPROVED / BLOCKING OPEN

Do not claim REQ-SCR-01 or REQ-RNG-03 coverage or close either obligation. Before designing or claiming those tests, obtain independent approval of the SCR measurement region/tolerance, clutter amplitude/phase/statistical envelope at +10 dB and −10 dB, source-profile authorization and dynamic-range coverage; and for two equal-power targets, the equal-power definition, amplitude envelope, relative-phase coverage, fixed range-separation sweep around 600 m, truth-to-cluster association and quantitative separation-success metric. Historical S03 ownership is unchanged. These obligations remain binding blockers to Gate-S04.

## Execution authorization boundary

A–E are approved for prospective deterministic/numerical C06 qualification **only within the two C01-authorized bounded populations and the conditions above**. This decision does not authorize a new main statistical CPI campaign, accepted S03 seed reuse, SCR/clutter or two-target expansion, alpha recalibration, RTL, synthesis, FPGA or hardware testing. No acceptance test was run as part of this decision. C06 remains OPEN until its bounded numeric evidence is executed and independently reviewed; REQ-SCR-01 and REQ-RNG-03 remain separate blockers to Gate-S04.

## State

C01–C05: PASS within approved scopes. C06: OPEN — criteria A–E approved with conditions; F blocked/open; acceptance execution not yet performed. S04 remains 5/8 = 62.5%; overall project remains 30.2083%; Gate-S04 OPEN.

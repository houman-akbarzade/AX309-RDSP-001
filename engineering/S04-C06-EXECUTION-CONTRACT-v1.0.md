# AX309-RDSP-001 | S04-C06 Execution Contract v1.0

**Status: A–E APPROVED WITH CONDITIONS; EXECUTION NOT AUTHORIZED BY THE CURRENT DOCUMENTATION ORDER. C06=OPEN. F NOT APPROVED.**

Decision authority: `decisions/S04-C06-CRITERIA-INDEPENDENT-DECISION-v1.0.md`, decision commit `e8a89dd8472cfbbb4859f924c18ca8386709db44`, document SHA-256 `5427ba6b7b66b8d21fc4f0178ccf557b49678e718ab0570727880f25166a144f`. This v1.0 execution contract transcribes that decision into an executable qualification specification; it does not amend it. The earlier v0.1 proposal remains immutable historical input.

## 1. Frozen scope and authorization boundary

- Selected architecture **C**, frozen formats/coefficients/RNE/narrowing, FFT shifts **[0,1,0,1,1]**. No A/B/C review, no shift or width change.
- Only C01-authorized source populations: **NOISE_ONLY_UNIT, g=5, CN(0,1), no target/no clutter**; **SINGLE_TARGET_REFERENCE_LIKE_LAB, g=1, predeclared single target k=40, Doppler +4, amplitude 0.18, phase 0, noise power 0.000324, no clutter**.
- g=5 must never be used to imply authorization for laboratory targets. g=1 must not be generalized to unknown operational targets. Other-g deterministic vectors are diagnostics/STRESS_ONLY and do not extend C01 authorization.
- This order authorizes documentation and planning only. No C06 acceptance vector, CPI, dataset, statistical campaign, accepted S03 seed reuse, alpha recalibration, SCR/clutter/two-target extension, RTL, synthesis, FPGA or hardware test.
- C06 remains OPEN until bounded A–E evidence is executed under a separate explicit execution authorization and independently reviewed. Even then REQ-SCR-01 and REQ-RNG-03 remain independent Gate-S04 blockers.

## 2. A — approved stagewise MAX/RMS ceilings

All limits below are exact and immutable for this decision. Units are **original complex Float amplitude** (not normalized stored Q15 units, power units, dB, or per-component limits).

| Stage | g=1 MAX and RMS ceiling | g=5 MAX and RMS ceiling |
|---|---:|---:|
| MF | 0.00074 | 0.00366 |
| MTI | 0.00147 | 0.00731 |
| FFT1 | 0.00468 | 0.02337 |
| FFT2 | 0.01286 | 0.06428 |
| FFT3 | 0.03267 | 0.16335 |
| FFT4 | 0.07926 | 0.39629 |
| FFT5 | 0.18636 | 0.93177 |

For each stage k, with paired original Float reference `z_F[n]` and reconstructed C bit-true output `z_C[n]`, define `e_k[n] = z_C[n] - z_F[n]`, `MAX_k = max_n |e_k[n]|`, and `RMS_k = sqrt(sum_n |e_k[n]|^2 / N_k)`. Complex modulus is mandatory. Report I/Q signed component errors diagnostically as well; do not substitute componentwise MAX for complex MAX.

Denominators for one complete CPI: MF=33×128=4224 complex outputs; MTI=32×128=4096; each FFT stage=32×128=4096. Fixed denominator; no sample or CPI removal/replacement.

Reconstruction to original input-amplitude units: MF and MTI Q15 output code is multiplied by `g/32768`. FFT stage j code is multiplied by `g * 2^S_j / 32768`, where `S_j = sum(i=1..j, s_i)` and frozen shifts are [0,1,0,1,1], hence cumulative divisors [1,2,2,4,8].

These are conditional deterministic numerical safety screens only. RMS is checked against the same ceiling because RMS≤MAX; it is not an independently calibrated RMS criterion and these limits do not certify Pd/Pfa or radar performance.

### 2.1 Mandatory applicability assumptions

All must be established for each CPI before its result can be classified VALID_PERFORMANCE:

1. Exact frozen C arithmetic, coefficient tables, stage formats, full-width intermediate arithmetic, ties-to-even rounding locations, and shift vector [0,1,0,1,1] are hash-pinned and unchanged.
2. Profile and gain are authorized exactly as in §1, fixed before sample generation/processing and independent of IQ values or detections.
3. Every input component satisfies the analytic derivation envelope (|Re(x/g)|,|Im(x/g)|\le 1+2^{-15}).
4. No input component clips under the exact C01 quantizer; every input sample and clipping counter/event trace is complete.
5. No internal product, accumulator, MF, MTI, FFT, power, or SUM40 operation overflows or saturates; all pre-narrow guards and complete ordered event traces are present and show zero events.
6. All source, IQ, code, Float reference, oracle, environment and output identities/hashes are complete and match the prelocked manifest.

If any condition is violated **or cannot be established**, the affected CPI/result is INCONCLUSIVE and the bound is inapplicable. Never extrapolate a no-saturation bound across a clipped or overflowed path. Before execution, static interval/headroom analysis must prove the candidate vector's pre-narrow values fit; runtime telemetry must independently confirm zero events. Missing guard coverage/logging blocks execution. **Known pre-existing blocker:** `S04-C02-RISK-FULL-OVERFLOW-TRACE` remains `OPEN_IMPLEMENTATION_EVIDENCE`; the current v0.5 telemetry records only the first 24 events plus a digest/count, not the complete ordered event list. Until full ordered input-clipping and pre-narrow overflow events with stable IDs, pre-limit integers, locations, CPI IDs and readback/non-omission evidence are implemented and independently verified, PF-08 cannot PASS and a C06 candidate cannot qualify as VALID_PERFORMANCE. Do not alter the arithmetic to address this evidence gap.

### 2.2 Error-source decomposition

For the same original Float input `x` and its exact C01 quantized/reconstructed input `x_q = g*q/32768`, independently evaluate the frozen Float S03 chain at both inputs. For stage k:

- `z_F`: Float S03 stage output from original Float `x`.
- `z_Q`: Float S03 stage output from reconstructed input `x_q`, with identical stage scaling/convention.
- `z_C`: selected-C bit-true stage output reconstructed to original amplitude units.
- `e_source = z_Q - z_F`: input quantization/source error.
- `e_processing = z_C - z_Q`: coefficients, arithmetic rounding and fixed processing error.
- `e_total = z_C - z_F = e_source + e_processing`.

Report MAX and RMS for all three. Do not add the MAX or RMS of the two contributions and label the result the exact total; calculate the total from paired complex errors. MF coefficient quantization is reported separately within processing error. FFT twiddle quantization and each stage RNE are separately logged. The shift is exact division by `2^s_j` in the frozen arithmetic; it changes scaling/error propagation but contributes no independent quantization error. Do not replace exact division plus RNE with an arithmetic right shift.

The approved caps are the seven values in §2; do not recalculate, round, relax or tune them. The source analytic JSON and script are immutable derivation evidence, not an alternate authority.

## 3. B — exact independent integer-oracle equality

Use an independently implemented integer/rational oracle. It must not import, call, or derive expected values from the implementation under test. Require zero mismatches for:
- every stored MF, MTI and each of five FFT stage output components;
- every U46.30 power cell and U52.30 SUM40 cell;
- all 2782 valid CUT decisions using frozen alpha and exact strict comparator;
- every cluster/component membership, integer peak/tie selection and complete target record.

Any integer-to-integer mismatch is FAIL. No tolerance, ambiguous-margin exemption, excluded CUT, excluded CPI, retrospective waiver or changed denominator applies to B.

## 4. C — Float/Fixed CFAR decision-margin policy

Fixed decision remains the exact frozen comparator with frozen alpha; no recalibration. Preserve the separate Float S03 reference and its frozen Float alpha. For every valid CUT record both masks, both signed margins, CUT/training power error bounds, alpha quantization contribution, and all cluster/record consequences. Report 0→1 and 1→0 changes separately.

For Float reference margin `m = P_CUT,F - alpha_F * SUM40_F / 40`, use the approved analytical uncertainty envelope `U = E_CUT,P + alpha_C * sum(E_train,i,P, i=1..40)/40 + abs(alpha_C-alpha_F) * SUM40_F/40`.
A changed CUT with `abs(m) > U` is FAIL. A CUT with `abs(m) <= U` is AMBIGUOUS: it remains in all records and denominators, and the affected Float/Fixed decision comparison is INCONCLUSIVE. There is no approved nonzero ambiguity allowance; do not mark it PASS by default. No CUT/CPI deletion, replacement or rerun. Independently, B exact Fixed-vs-integer-oracle equality remains mandatory even when Float/Fixed is ambiguous.

## 5. D — narrow exact Float-tie peak exception

The sole permitted classification is `FLOAT_REFERENCE_EXACT_TIE_SPLIT_BY_QUANTIZATION`, only when all four conditions hold:
1. Frozen original-input Float reference proves exact equality of competing maximum powers (exact comparison, no epsilon).
2. Both candidates belong to the same unchanged alarm/cluster component.
3. Fixed integer peak is selected by the frozen integer max/tie rule.
4. Independent integer grouping and complete target records match exactly.

Replay and report both historical `g1:phase_interference` and `g5:phase_interference` vectors. Preserve their original inputs, Float/Fixed power values, masks, component membership, coordinates, and classification. No general ±1 range tolerance. Any non-tied displacement, split/merge, missed target, or record mismatch is not covered and is FAIL under the applicable check. The exception does not prove estimator accuracy or close REQ-RNG-03.

## 6. E — immutable CPI disposition, denominator and evidence lock

Before processing, lock source profile, g, scenario class, source/generator ID, vector/CPI IDs, complete planned N, denominator, data and code/reference/oracle hashes, environment, and eligibility metadata. Metadata must be independent of detector outputs.

- **VALID_PERFORMANCE:** only a C01-authorized population/profile; complete 33×128 IQ payload and all stage references; verified input envelope; zero input clipping; zero internal overflow/saturation; complete pre-narrow telemetry and all required hashes; no unresolved ambiguous decision affecting the comparison.
- **INCONCLUSIVE:** missing/invalid metadata or payload, wrong/unauthorized profile or g, envelope not established, input clipping, any internal overflow/saturation, missing/incomplete guard/event trace, missing stage/reference data, or ambiguous CFAR decision without a separately approved permitted rule. Preserve attempted/processed counts and all records. Do not remove or replace.
- **STRESS_ONLY:** declared before processing for deliberate clipping/limits/ties/overflow or out-of-profile diagnostics. It may validate event flags/locations against its own oracle, but is excluded from performance denominators and makes no Pd/Pfa claim.

No deletion, replacement, automated rerun, retuning, optional stopping, denominator change, sample top-up or retroactive reclassification. Preserve every input and pre-narrow event with value, stage, location, sign, stable ID and hash. C01's existing noise-only whole-campaign 0.1%/20,000-CPI rule is unchanged and must not be generalized or implicitly run by this C06 plan.

## 7. F — binding blockers, explicitly out of C06-A–E scope

`REQ-SCR-01` and `REQ-RNG-03` remain BINDING OPEN and block Gate-S04. This C06 contract does not authorize or claim their coverage.

- SCR: independently approve measurement region, generator tolerance, clutter amplitude/phase/statistical envelope at +10 dB and −10 dB, source-profile authorization and C02 dynamic-range coverage before defining or claiming the test.
- Two-target resolution: independently approve equal-power definition, amplitude envelope, relative-phase coverage, fixed range-separation sweep around 600 m, truth-to-cluster association and quantitative separation-success metric before defining or claiming the test.

Historical S03 ownership/evidence is unchanged. No clutter, SCR or two-target scope expansion is allowed by this contract.

## 8. C06 closure conditions

The earlier C02 numeric-error criteria gap is superseded for criteria approval by decision e8a89dd (A–E only); its evidence requirement is not completed. The separate `S04-C02-RISK-FULL-OVERFLOW-TRACE` implementation/evidence gap remains OPEN and must be resolved before the relevant preflight can pass. C06 may be proposed for independent sign-off only after a separately authorized execution of the bounded A–E qualification, all required evidence is complete, no FAIL remains, every INCONCLUSIVE is explicitly dispositioned without denominator manipulation, and the independent reviewer signs the exact evidence manifest. C06 PASS does not close F or Gate-S04. Until then: C06=OPEN; S04=62.5%; overall=30.2083%; Gate-S04=OPEN.

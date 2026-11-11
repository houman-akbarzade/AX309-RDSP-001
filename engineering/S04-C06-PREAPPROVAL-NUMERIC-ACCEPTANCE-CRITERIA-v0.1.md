# AX309-RDSP-001 | S04-C06 Prospective Numeric Acceptance Criteria — ENGINEER APPROVAL REQUIRED v0.1

**Status: PROPOSED ONLY / HOLD FOR INDEPENDENT CRITERIA APPROVAL. C06 OPEN. NO NEW C06 ACCEPTANCE TESTS PERMITTED.**

**Inputs frozen:** S04-C01 PASS BOUNDED (NOISE_ONLY_UNIT g=5, laboratory SINGLE_TARGET_REFERENCE_LIKE g=1 only), C02 architecture C and FFT shifts [0,1,0,1,1], C03/C04/C05 engineer PASS within their respective deterministic scope. This package is a decision draft, not a change to the architecture, acceptance baseline, C01 saturation policy, historic S02 test ownership or to S03 accepted seeds.

## C06-REQ-01: error metrics and reference

For stage k in {MF, MTI, FFT1, FFT2, FFT3, FFT4, FFT5}, compare the Float S03 original-input reference against the exact C-bit-true output reconstructed in *original complex-amplitude units*: MF and MTI multiply stored Q15 complex output by g/32768; FFT stage j multiplies by g * 2^(sum FFT shifts through j)/32768. For every predeclared, valid stage sample z, define e_k=z_fixed_reconstructed - z_float_original. MAX_k=max |e_k|, RMS_k=sqrt(sum |e_k|² / N_k). Complex absolute magnitude in original input-amplitude units is mandatory; report real/imag sign separately when diagnostic. Exact eligible denominators per complete CPI are MF=33x128=4224 and MTI/each FFT stage=32x128=4096. Never replace samples/CPI because their errors are high.

Decompose e_k EXACTLY as e_source_k + e_processing_k where e_source_k = S03_stage(original IQ reconstructed from the *same* precommitted g/input integer codes) - S03_stage(original Float IQ); e_processing_k = reconstructed fixed-stage output - S03_stage(reconstructed input IQ), with S03 stage shift and reference scaling matched. Report MAX/RMS per contribution AND total. MAX/RMS of contributions must NOT be added and treated as an exact total.

## C06-REQ-02: prospective conditional numerical ceilings (NOT approved)

Frozen Q16.15 input with no clipping implies per-component |delta x|<=g/65536 and per-complex-sample |delta x|<=sqrt(2)*g/65536. A conservative explicitly conditional input envelope |Re(x/g)|,|Im(x/g)|<=1+2^-15 gives |x/g|<=sqrt(2)(1+2^-15). Use the exact frozen 16-tap Q16.15 MF table, FFT twiddle tables, RNE after exact integer butterfly, and schedule [0,1,0,1,1]. The reproducible script `engineering/s04_numeric/s04_c06_preapproval_analytic_bounds_v0.py` uses **no empirical C04/C05 error** and evaluates:

- MF: E_MF <= (sum|h_hat|)*E_input + M_input*(sum|h_hat-h|) + sqrt(2)/65536, in normalized g units.
- MTI: E_MTI<=2*E_MF (exact signed first difference; same Q15 fractional resolution).
- FFT j: E_j <= (1+beta_j)*E_(j-1)/2^s_j + delta_j*M_(j-1)/2^s_j + sqrt(2)/65536, where beta_j=max|w_hat_j|, delta_j=max|w_hat_j-w_j|, and M_j <= 2*M_(j-1)/2^s_j. Track source, MF coefficients, FFT twiddle and stage RNE as distinct channels. Convert each normalized bound to original amplitude by g * cumulative FFT divisor. Assumptions: no input or internal clipping, full intermediate precision, exact frozen arithmetic; any violation makes these bounds inapplicable.

The **proposed provisional MAX and RMS upper caps** are 1.25 times the analytic worst-case complex MAX, rounded upward to 1e-5 original-amplitude units. The factor 1.25 is merely proposed engineering slack; it is **not derived from Pd/Pfa nor an empirical 95% RMS criterion**. RMS<=MAX is a proven conservative implication, not proof of useful RMS performance. Thus these numbers are eligible for approval **only as deterministic numerical safety screens**, not a stand-alone radar-performance acceptance.

| Stage | Analytic MAX bound / g | Proposed MAX and RMS cap g1 | Proposed MAX and RMS cap g5 |
|---|---:|---:|---:|
| MF | 0.000584126 | 0.00074 | 0.00366 |
| MTI | 0.001168252 | 0.00147 | 0.00731 |
| FFT1 | 0.003739157 | 0.00468 | 0.02337 |
| FFT2 | 0.010283693 | 0.01286 | 0.06428 |
| FFT3 | 0.026134984 | 0.03267 | 0.16335 |
| FFT4 | 0.063405468 | 0.07926 | 0.39629 |
| FFT5 | 0.149082064 | 0.18636 | 0.93177 |

**Engineering issue requiring explicit approval:** the g5 branch corresponds to predeclared noise-only CN(0,1), not an authorization to run g5 laboratory targets. Numerical safety ceilings do not prove a statistically acceptable noise/radar change. Before performance certification, define an independently reviewed tighter **functional decision margin / scene-specific signal minimum** (or a bounded equivalence theorem); do NOT infer one from retrospective C04/C05 peak/error outcomes.

## C06-REQ-03: CFAR and exact decision-margin acceptance

For all 2782 valid CUTs preserve two separate truth objects: (a) independent exact integer bit-true oracle: power U46.30, SUM40 U52.30, strict 40*Pcut*65536 > 490007*SUM40 (equal=>no alarm); and (b) original Float S03 reference with its own calibrated alpha. **Zero** integer-to-integer power, CUT mask, cluster and target-record mismatches is mandatory; any mismatch is FAIL (not an ambiguous margin exemption).

For Float-to-Fixed decision comparison, separately report every changed CUT (0->1 and 1->0), margins in original power units, cluster/record effects, and alpha quantization contribution. A conservative predeclared safety certificate uses |Pfixed-Pfloat| <= 2|Zfloat|*E_FFT5 + E_FFT5² before extra saturation (if any). Define reference CFAR margin m=Pcut_float - alpha_float*SUM40_float/40; if |m| exceeds `E_cutP+alpha_fixed*sum(E_trainP)/40+|alpha_fixed-alpha_float|*SUM40_float/40`, alarm equivalence is analytically guaranteed under assumptions. Any changed CUT **outside** its uncertainty envelope is FAIL. An ambiguous-margin CUT within the envelope MUST remain recorded and included in all denominators; it is NOT automatically PASS: requires a preapproved independent rule/flag. Proposed default: **INCONCLUSIVE** for an otherwise valid performance comparison with noncertifiable decision equivalence, unless separate engineering approval explicitly defines a permitted margin class and its allowed counts BEFORE new tests. Never drop or replace a CPI/CUT to turn it into PASS.

C06 cannot finalize a blanket "zero Float mask changes" or a numerical nonzero allowance without an engineer deciding which evidence population and uncertainty-margin policy is normative. Preserve the S02 bit-true exactness requirement separately from the statistical Pd/Pfa requirement.

## C06-REQ-04: peaks, ties and two known discrepancy vectors

Native grouping remains 8-neighbor, nonwrapped, max stored integer U46.30 power, then smallest signed Doppler, range and bin on an **integer** tie. The S03 Float reference uses analogous ordering but Float power ties are resolved in Float arithmetic. Maintain two independent checks: (1) strict exact bit-true native grouping/records vs an independently constructed integer oracle, ZERO mismatches; (2) Float-vs-Fixed peak positions and all target-record differences with explicit source/model/SCR/g flags.

Historical `g1:phase_interference` and `g5:phase_interference` must **both** remain in every replay: original Float powers at (3,20) and (4,20) tie exactly, so Float chooses (3,20), whereas selected-C stored integer powers 33,612,372,401 and 33,612,427,349 choose (4,20); delta=54,948 integer units, with unchanged CFAR mask. **Proposal subject to independent sign-off:** classify these as `FLOAT_REFERENCE_EXACT_TIE_SPLIT_BY_QUANTIZATION` and permit the coordinate difference *only* when original Float max powers are exactly tied as per the frozen Float oracle, the two candidate peaks belong to the same unaltered integer/Float alarm component, and independent integer grouping/records are exact. This is a very narrow, prospective ambiguity exception—not an arbitrary ±1 range-bin tolerance, a waiver of a real non-tied peak error, or closure of the broader final numeric error budget. Absent explicit approval of this exception, these two cases are **BLOCKED for full Float/Fixed peak-coordinate acceptance**, not silently PASS.

For an eligible clean isolated target, S02 still requires zero clean range-bin error; conditional Doppler estimate error <=0.234375 m/s per approved S02 is separate from the 2-range-sample/1-Doppler-bin matching gate. Neither assignment gate nor tie exception can substitute for estimator performance criteria.

## C06-REQ-05: CPI dispositions, overflow, denominator and evidence locking

Eligibility is decided from **pre-CPI immutable metadata** and the approved source profile, not detector outputs. For `VALID_PERFORMANCE`, predeclared population and finite source, complete 4224 complex IQ values, exact declared g, no input saturation, no internal overflow, complete matched-stage data, fixed reference and hash, and valid FFT/power/CFAR target records are all required; once declared, every intended CPI remains in the planned denominator. `INCONCLUSIVE` applies to a needed performance result with invalid measurement/metadata, input saturation or any internal arithmetic overflow, or uncertifiable near-threshold decision after a predeclared ambiguity policy, and is **not** reclassified or removed after seeing target results. `STRESS_ONLY` is selected **before CPI**, for explicitly designed clipping/limits/ties/overflow; no Pd/Pfa claim or performance-denominator substitution is allowed. Record all events with original integer before narrowing, location, deterministic ID and SHA. No automated rerun, rejection, replacement, retuning or denominator change. Proposed stopping rule: stop reporting the campaign as performance-PASS on any disqualifying required CPI until engineer-reviewed disposition; do not destroy or drop records. The approved C01 noise-only 0.1%/20000 CPI stopping risk remains unchanged and is not generalized to target or stress populations.

**Proposed evidence lock before any acceptance test:** engineer-signed criteria SHA256, selected C implementation/reference and source hashes, original scenario/g/tie class, fixed vector IDs, prospective independent seeds disjoint from accepted S03 and calibration samples, fixed N and eligible denominator, complete per-CUT decisions and margin counts, overflow logs and eligibility flags, signed PASS/FAIL/INCONCLUSIVE/STRESS_ONLY results. No main statistical CPI or acceptance dataset may be created during this preapproval phase.

## C06-REQ-06: S02 requirements still blocking full C06/Gate-S04 closure

| Binding requirement | Approved S02 intent | Missing definition / evidence; responsible stage | Status |
|---|---|---|---|
| REQ-SCR-01 | Target-to-clutter input SCR **+10dB and −10dB**, plus no-clutter; declared measurement region and generator tolerance | **OPEN:** approved reference region, tolerances, clutter amplitude/phase and envelope, C01-authorized bounded extension/source profile, C02 numerical dynamic-range coverage; independent C06 evidence & engineer closure before Gate-S04. Historical S03 owner unchanged | BINDING OPEN / BLOCKER |
| REQ-RNG-03 | Two equal-power targets, range separation near **600m**, verify separate resolved clusters | **OPEN:** formal equal-power convention, fixed spacing sweep, relative phase, truth-to-cluster association, separability success metric and target-amplitude envelope; C02 numeric coverage and independent C06 evidence & engineering closure before Gate-S04 | BINDING OPEN / BLOCKER |
| REQ-CFAR-01/02, REQ-DET-01, REQ-MATCH-01 | Exact bit-true 2D CFAR; independently calibrated alpha and Pfa/Pd protocol; deterministic target records and separate estimator tolerances | No new stochastic evidence or alpha recalibration under this order. S03 Float numerical acceptance, prospective fixed test protocol and later separate approval required | OPEN DOWNSTREAM |

**Approval requested** (each independent checkbox): approve or revise (A) the seven conditional numerical MAX/RMS safety caps above; (B) all-CUT strict bit-true oracle equality; (C) analytical CFAR ambiguity-margin decision and no silent exclusion; (D) exact-Float-tie-only prospective peak exception; (E) fixed N/metadata/CPI dispositions; (F) SCR/pair-scene missing specifications and scope expansion BEFORE claiming those tests in C06. Approval of A–E alone does NOT close F or authorize statistical CPI, RTL, synthesis or FPGA.

**Decision state:** C05 PASS in bounded deterministic scope; **C06 OPEN — CRITERIA PROPOSED / NO ACCEPTANCE RUN AUTHORIZED**; S04=62.5%; overall=30.2083%; Gate-S04 OPEN.

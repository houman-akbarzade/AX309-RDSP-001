# AX309-RDSP-001 | S03 Pd PRE-EXECUTION AUDIT v0.4

**Engineer decision:** APPROVED-IN-PRINCIPLE / **EXECUTION NO-GO**. **Decision of this audit:** READY FOR EXECUTION-AUTHORIZATION REVIEW; **Pd NOT RUN**. No reserved target CPI generated, no use of seed 411091704. All six requested checks PASS with explicit scope limitations.

## Six controls

| Control | Verdict | Evidence and limitation |
|---|---|---|
| SNR input definition versus generator | **PASS (static)** | abs(.18)^2/10^(20/10)=.000324 complex Gaussian variance, real and imag .000162; 16 active echo samples, not CPI-wide SNR; same approved frozen model. |
| Independent CPI and absence of processing state | **PASS (structural only)** | fresh PCG64(SeedSequence([411091704,i,191])) specified for each complete CPI; frozen model uses local RNG and stateless MF/MTI/FFT/CFAR/cluster/matching. Statistical independence NOT experimentally demonstrated; no reserved samples generated. |
| Reserved seed never previously tuned on | **PASS (visible repository scope)** | 411091704 appears only as reserved/constant in evidence and candidate tests; all earlier main Pfa trials use disjoint seed 411091703. External undocumented usage cannot be ruled out. |
| Frozen alpha, clustering, association, success rules | **PASS** | alpha 7.476912055027923, 40-cell 7x7 minus 3x3, strict comparator, 8-connectivity, one-to-one assignment 2 range sample/1 Doppler bin. Model and S02 hashes unchanged. Fixed v0.3 contract only V semantic correction. |
| D, R, V, J traceability to S02 | **PASS** | V now explicitly D AND E AND |velocity error|<=.234375 without tolerance padding. J remains D AND R AND V, numerically preserved in pre-fix 10-case non-V baseline; D/R/matched ID/extra clusters unchanged for all 10 cases. S02 conditional Doppler eligibility preserved; J is report-only, not new 90% acceptance rule. |
| Independent exact Clopper-Pearson k_min=916 | **PASS** | Beta.ppf(.05,915,86)=.8990676705833044 vs Beta.ppf(.05,916,85)=.9001427009482232. Independent Binomial SF at p=.9: Pr(K>=915)=.060693730517966386 and Pr(K>=916)=.04850250689914629. Exactly n=1000 k_D>=916. |

## PD-AUD-001 closure and invariants

- Changed only candidate Pd scorer: V_i := D_i AND E_i AND absolute nominal Doppler-bin error <= 0.234375 m/s. No epsilon extension beyond exact half-bin limit; ineligible even when on-bin produces V=0.
- Invalid matched 32-bin row, NaN, missing power => INCONCLUSIVE. No match => D=0, E=0, V=0, J=0. Preserve additional unmatched clusters.
- Original v0.2 scorer V could be true for a Doppler tie despite E=0. New V=false; J remained false before/after. Diagnostic regression includes D and E truth-table, inside/equal/outside half-bin, valid/tied/zero/wrong row, no match and malformed records.
- **Non-V baseline comparison:** 10 hand-constructed pre-fix cases captured BEFORE editing source. D, R, J, extra cluster count, matched record ID and status identical in all 10. Existing m.truth_match, m.clusters_8, m.cfar_2d and all processing stages untouched.
- **Dependency audit:** repository code searches find only the scorer key and deterministic test references, besides immutable historical audit v0.3. No executed Pd result file or acceptance aggregation consumes V; historical results remain unmodified. The new v0.3 execution contract explicitly freezes the corrected V meaning.
- **Full test suite:** 75/75 PASS, including 8 added regression tests and 67 earlier tests. Test log stored separately; deterministic synthetic records only, not stochastic Pd CPI.
- **Scope of independence check:** structural source check only. It does not demonstrate independence of realized PRNG sequences or physical radar samples. Seed 411091704 remains reserved.

## Frozen criterion and execution prohibition

D accepts iff exactly 1000 valid independent complete CPI give k_D>=916 and one-sided exact CP lower>=0.90. J and its diagnostics are separately reported without binding J>=0.90 population criterion. This does not waive S02 range/velocity obligations. No optional stopping, retry, new sample, source retune or execution without a NEW EXPLICIT authorization. Gate-S03 OPEN; S03 6/8=75%; overall 22.916666666666668%; Pfa PASS unaffected.

## File-level SHA-256 evidence

- s03_reference/model.py: 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b
- s03_reference/pd_acceptance_candidate.py: aa0661b52aa56a1da3b3b41332f0927eba58f4fcddace12a391c2488404784ea
- tests/test_s03_pd_protocol_deterministic.py: 2fa5960a87cafbabd35253e87b5552799eaf948e39192c24042d4e8639a9f2d4
- tests/test_s03_pd_aud001_regression.py: f4ca88f680201e82b574f9f9b7cd1ef5ffe39b9da72f7f8fb93538f1266f6414
- tests/fixtures/s03_pd_v02_pre_fix_nonV_baseline.json: 8264964cca8adb78d5e146114ceb859e2ec711ca4247abafdc32087db4a2e091
- engineering/S03-Pd-independent-fixed-protocol-PROPOSED-v0.2.json: cde5b6efa467cbcf1450798a963555a48a08318e52f8c9d9065ba20105ef6da1
- engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json: 23f07e63950c8bd4f3b04a805c37a46792b0068ae918b25d0713dd65a15c51a0
- engineering/S03-Pd-PD-AUD-001-full-regression-v0.4.log: 77eeac73a06d47ebd389a416490ceb2d8663106f42352b20ab87db305cbc0f25
- engineering/S03-Pd-independent-fixed-execution-contract-v0.3.json: 602e4fe6132c4d8521b33c61a1c2cd413c3e75cc4325fe8b9bca6dea966bed5f

Git HEAD before corrected audit: 414e27e437fdef075656c0c9636a63377c5a3b4b; recorded UTC: 2026-11-11T08:05:37.457252+00:00

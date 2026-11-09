# AX309-RDSP-001 | S03 | Historical Pfa/Pd engineering audit v0.1

**Decision status: NO PERFORMANCE LIMIT RELAXATION JUSTIFIED.**
The engineer permits relaxing at most ONE limit only if an earlier valid, independent performance study failed due to the limit. No such previous study exists. S02 v1.1 remains approved; Gate-S03 OPEN; S03 75%; overall 22.9167%. No final Pfa or Pd experiment was executed in this audit.

## Audit scope and evidence hierarchy
We indexed and SHA-256 checked all 87 existing engineering documents/evidence files and 26 Python code files; see S03-Pfa-Pd-historical-evidence-audit-v0.1.json. We checked all 22 requirement rows, immutable v1.0/v1.1 approved hashes, all synthetic qualification conditions, calibrated alpha, post-alpha diagnostic outcomes and seeded model tests.

Only independent, prospectively specified, statistically valid **performance** evaluations can justify relaxing a bound. Monte Carlo coverage qualification validates a CI METHOD, not the detector. Calibration on the same data is not validation. Diagnostic spatial-transfer failure is not a performance-threshold failure.

## Current approved criteria, proposed comparison
| Criterion | Approved | Proposed after this audit | Result |
|---|---|---|---|
| Pfa design target, noise-only per valid CUT | 0.001 | 0.001 unchanged | No eligible performance failure |
| Pfa binding acceptance, valid one-sided nominal 95% U | U<=0.0015 on 4096 fresh independent CPI, 2782 valid CUT/CPI | U<=0.0015 unchanged | Final Pfa test BLOCKED, never executed |
| Pd single target SNR20/no clutter | >=0.90 DESIGN GOAL, not yet binding acceptance | >=0.90 design goal unchanged | No independent Pd population measurement |
| Pd SNR0/10 | report only, no minimum | unchanged | No numeric acceptance threshold exists |

### Pfa: identify each historical result, not its appearance
1. Original Student-t CPI-method qualification FAILED 7 of 15 predefined IID/Beta-Binomial count conditions, 3000 outer independent repetitions each, 4096 CPI count observations per repetition. It is a valid **negative method coverage qualification**, not a detector Pfa bound failure. File engineering/s03_C04_count_qualification.json, SHA256 b4728d6d93a02e3324f0390dc639add2780dc46aaf9b2d5afba07738480c3ef9.
2. Replacement skew-corrected Studentized v1.1 CI, Delta*=0.28734133322686817. Calibrated on 15x5000 outer count studies, then 15x3000 independent new outer studies, 4096 CPI counts each; all 15 conditions PASS. Worst 95% one-sided Wilson lower for conditional coverage 0.9515520667104338 (minimum accepted 0.93). This is the strongest **valid method** result, but it covers synthetic model distributions, not real-chain Pfa. File engineering/S03_C04_v11_independent_15x3000_qualification.json, SHA256 2aa1e4614b3d3b80ded3b6f7c47a15dd92184635f54619d90f1df8501b2d0ed5.
3. Alpha calibration: 4096 independent CPI, 2782 CUT each, alpha=7.476912055027923, in-sample rate 0.0009999936814791518. This rate is determined by quantile selection, NOT independent performance evidence. Source engineering/S03-C04-independent-alpha-calibration-v0.1.json, SHA256 1a4540f97b38da8739ccf63f3eb68555a6671c50d9c8bc9f25829a03a0cee2fe.
4. Best *descriptive real-chain* point observation: separate 4096-CPI **diagnostic** after alpha freezing, 11433 raw alarms across 11,395,072 CUT, raw observed fraction 0.0010033284563713157. This diagnostic was NOT the final Pfa test; its predeclared spatial transfer diagnostic FAILED at |z|=43.575 >2.5758293 and first 2048 input CPI reused the exploratory spatial seed namespace. We do not retrospectively calculate or report a main-test confidence bound from these observations, nor reinterpret them as a qualified performance PASS/FAIL. Source engineering/S03-C04-post-alpha-spatial-diagnostic-v0.1.json, SHA256 3370d100ff697fd3a5f6848e56450a53d22b8ee95ce4e31d3eb056982650d37a, and provenance addendum SHA256 e306e202843f94e7037c2a6f916da3474525c4e20fb9606ebeafef5d513e5dc2.
5. At true synthetic p=.001, sample acceptance power (fraction of count-model repetitions yielding valid CI U<=.0015) ranged from 3000/3000 IID to 2910/3000 at rho=.05. This measures the CI method on simulated, known-p surrogate count laws, not measured radar Pfa. Source engineering/S03_C04_v11_power_spatial_sensitivity_ANALYSIS.json, SHA256 cd2d990c8dacbe5b4e67dd6597d970e6c5d64a8e18c9f4217e97b22ce56408ca.
**Result:** No independent valid final Pfa FAIL caused by the 0.0015 performance limit exists; relaxing it has no evidence-based numerical justification.

### Pd: no valid population estimate
REQ-PD-01 is classified DESIGN_TARGET_NOT_BINDING_YET: >=0.90 at input SNR20, one isolated target, no clutter. The owner-stage S03 must specify an independent seeded sample count, fixed range/Doppler/test eligibility and a prespecified one-sided lower Pd confidence bound before evidence can become a binding acceptance result. No such completed sample study is in the evidence inventory.
- Original 6 individual-CPI reference smoke scenes: three targets each matched 3/3, with extra clusters (e.g. SNR20 had 7 unmatched clusters); this is not N=3 statistically independent one-target Pd trials.
- Expanded 19 deterministic edge/multiple-target cases: three-target SNR20 matched 3/3 with 7 unmatched detections; two very close target trials often matched 1/2, and edge/stationary tests also missed targets, but these conditions are not the S02 single-dominant-target/SNR20/no-clutter Pd criterion. These findings matter for algorithm quality, not relaxing single-target Pd.
No prespecified independent-trial population Pd or CI exists. Sources: engineering/S03_six_case_reference_smoke.json (SHA256 a3c97fd8002c3da7d4a2a60e68c8a73bf7d2079e332fc1e9cd4f475c076771ab) and engineering/S03_extended_boundary_multitarget_cases.json (SHA256 76ad7e1cd98cfc8992963018422731045c4f9e01b55671501d91b3bed0bfad7e).
**Result:** No valid prior FAIL of Pd>=0.90, and no defensible new numeric minimum exists.

## Assessment of previous methods and future reproducible tests
For Pfa, use the sole qualified method from approved S02 v1.1 (4096 independent CPI, 2782 valid CUT, frozen Delta* and alpha and valid one-sided upper U<=0.0015) only if real CA-CFAR output spatial/count transport is proven by an separately approved, independent method. No final Pfa run now. All code hashes, 5 separate SeedSequence namespaces, sample count, exact INVALID/INCONCLUSIVE rules and stopping rule must be frozen BEFORE any new input. Alpha-calibration, CI calibration, CI-qualification, spatial verification and final tests must never share selection data.
For Pd, no earlier successful population-method qualification exists. Before any final test, propose a separate one-target 20dB no-clutter trial protocol with explicit peak/association correctness, valid CUT and no-edge rules, frozen alpha, independent seeds, sample size/power and one-sided 95% lower confidence method; get engineering approval before data. Do NOT compute a Pd point estimate from the historical deterministic scenarios.

## Change-control outcome
Because no historical independent PERFORMANCE TEST failed an actual Pfa or Pd numerical threshold, **propose NO change to either limit** rather than invent a weakly justified revision to one of them. Do not create an active S02 v1.2. This complies with the rule that only one limit may be relaxed if supported; in this case zero are eligible.

Separate methodological blocker: a predeclared CA-CFAR spatial anisotropy test failed 4/5 gates PASS, 1 FAIL, while v1.1 synthetic count-model method qualification remains 15/15 PASS. Resolve the spatial-transfer validity by a distinct preapproved source-realistic anisotropic model / full-chain requalification OR a formally justified replacement CPI-count method diagnostic using fresh independent data. Neither approach requires assuming the numerical Pfa limit is too strict. Historic FAILs must remain FAILs.

The current audit generates NO synthetic CPI, no main Pfa/Pd data, no change to alpha, Delta*, thresholds or S03 completion. Project status unchanged (S03 6/8, 75%, total 22.9167%, Gate-S03 OPEN). All evidence hashes and sources are preserved in the companion machine-readable audit.

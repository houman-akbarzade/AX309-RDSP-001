# AX309-RDSP-001 | S04-C01 FINAL CONDITIONAL APPROVAL PACKAGE v0.8

**PROPOSED / UNAPPROVED; S04-C01 HOLD; C02 OPEN; Gate-S04 OPEN; S04 0%; project 25%.** This is a decision request, not an engineer signoff. No CPI, RNG, accepted Pd/Pfa seed, RTL, synthesis or hardware operation.

## 1. Bounded admission

C01-POP-N: 33x128 complex CN(0,1) independent source noise, target absent, no clutter, 8448 real components.
C01-POP-T: controlled LABORATORY single-target test with declared k40, Doppler bin +4, phase0, source amplitude 0.18 and complex noise power 0.000324; no clutter. The manifest is frozen before sampling. Not an accepted Pd replay.

**OUT OF SCOPE:** statistical/correlated clutter, SCR ±10dB, multi-target, paired-target resolution, unknown target, off-bin and other SNR source classes. S02 upstream binding REQ-SCR-01 and binding_test REQ-RNG-03 are NOT waived. This contract is NOT full S02 coverage.

## 2. Formal deferred requirements disposition — PENDING and BLOCKERS

| Requirement | Approved S02 oracle | Proposed C02 DESIGN owner | Proposed C06 VERIFICATION owner | Gate-S04 closure | Current |
|---|---|---|---|---|---|
| REQ-SCR-01 | BINDING: SCR +10/-10 dB and no clutter. 10log10(echo active-support mean power/clutter active-support mean power), per-target masks; generator numerical tolerance established before tests | Design admitted dynamic-range and quantization/overflow envelope for target-plus-clutter SCR classes, profile logic and stage-scale contract | Independently check generator input/SCR source definition and Float-to-bit-true numeric performance under approved SCR strata, sample IDs and tolerance | Explicit change-of-owner/deferral engineer signature, qualified evidence/disposition before Gate-S04 | **BLOCKER-SCR** |
| REQ-RNG-03 | BINDING_TEST: paired equal received-power targets around nominal 600m range resolution; resolved-pair oracle, separation sweep, pass fraction/criterion predeclared | Design two-target superposition/dynamic-range, peak/cluster and arithmetic headroom rules | Independent paired-target float-vs-fixed numeric and resolution-oracle qualification with frozen denominators | Approved owner transfer/deferral and evidenced disposition before Gate-S04 | **BLOCKER-RNG** |

**S02 owner integrity:** the currently approved S02 matrix lists S03 as historical owner, not C02 or C06. C02-design/C06-verification assignments above are a proposed FUTURE additional route, requiring separate engineer approval. S03 evidence remains intact. Until approved transfer or expansion and closure plan exists, bounded C01 cannot be marked PASS.

## 3. Individually approvable C01 provisions

| Clause | Exact proposed contractual rule | Evidence | Status | Future owner |
|---|---|---|---|---|
| C01-F01 | Configurable rational gain g selected by immutable approved registry before every CPI, never from current IQ, detection, accepted Pd/Pfa result or postprocessing | v0.4 policy/schema | PENDING | C01 protocol; C02 implementation |
| C01-F02 | NOISE_ONLY_UNIT candidate g=5, N=20000 and proposed maximum whole-campaign any-input-clipping probability 0.001 (0.1%) under independent CN(0,1) CPI | v0.5-v0.7 exact Q1.15 analytic tails | PENDING | C01 contract; C06 audit |
| C01-F03 | Laboratory-only SINGLE_TARGET_REFERENCE_LIKE candidate g=1 chosen solely from predeclared, frozen source-test class, not inferred from received target | S02 C-DAT-01, v0.7 precision | PENDING | C01 experiment design; C06 provenance |
| C01-F04 | For operational UNKNOWN targets, do not assign laboratory g1 by inspecting target truth. A distinct target-blind profile based on prior receiver calibration/noise/envelope metadata requires future approval; otherwise reject profile selection | formal no-peeking rule | PENDING / operational out of scope | future system/C02; C06 |
| C01-F05 | Host metadata includes class, CPI ID, exact positive reduced gain numerator/denominator, registry and selection-rule ID, source/payload SHA, lock event before CPI, stage scales, clip traces and Replay ref; reject missing/mutated metadata | v0.4 proposed JSON schema | PENDING | C01 host; C02/C06 |
| C01-F06 | Candidate input Q1.15 signed int16 I then Q pulse-major LE, 4224 complex = 16896 bytes/CPI, nearest-even RNE: q=SAT16(RNE(32768*x/g)), reconstructed xhat=g*q/32768; upper clip x>=g*65535/65536, lower x<-g*65537/65536 | S02 C-DAT-01; v0.3 20 exact tests | PENDING | C01 quantizer; C02 bit-true |
| C01-F07 | Original Float-domain MF/MTI factor g, FFT factor g*sFFT, RD power/training sum/threshold/peak power factor (g*sFFT)^2, physical range and velocity unchanged. No internal FFT shift or W/F fixed | v0.3 120 boundary checks | PENDING | C01 interface; C02/C06 |
| C01-F08 | Source test-case manifest and gain mapping locked prior to simulation, upload or CPI; no data- or outcome-based profile reassignment; accepted S03 seeds never used for numeric tuning | v0.4-v0.7 provenance | PENDING | C01 test governance; C06 |

**Selection rationale and proof boundary:** Proposed deterministic SELECT(declared_test_manifest,approved_profile_registry) has no IQ samples, target detections or unknown runtime truth as input. A lab manifest with target class is known *because the experiment deliberately constructs the target*, prior to data production; it is not a radar's inference about an unknown operational target. If no approved prior scenario/profile metadata exists in operational use, SELECT must fail closed (UNCONFIGURED/INCONCLUSIVE). This proves non-peeking at the SPECIFICATION level only; future software/bit-true enforcement still needs C06 qualification. g=1 is NOT approved.

## 4. Numeric bounds in original normalized input-amplitude units (not Pd proof)

For N=20000 independent CN(0,1) CPI and g5, analytical risk of ≥1 saturated CPI is about 0.00025973555 =0.02597355%, less than *proposed* 0.001. Noise-only g4 has risk 0.92608949. Independence must be justified; correlated/heterogeneous upper bound is min(1,sum of marginal CPI risks) where valid.

For laboratory target amplitude |a|=0.18, proposed g1: LSB delta=1/32768=3.0517578125e-5 normalized amplitude per real component. Unsaturated component error <=1/65536=1.52587890625e-5 normalized amplitude; complex error magnitude <=sqrt(2)/65536≈2.15791864e-5. Relative step delta/0.18=0.00016954210 =0.01695421%; complex maximum error/0.18=0.00011988437=0.01198844%. g2 doubles these bounds. The proposed INPUT-ONLY acceptance ceiling for engineer review is delta/0.18<=0.00017 and complex absolute error/0.18<=0.00012 conditional on no saturation, with exact bound at every component. This is a mathematical admissible-input candidate, NOT independently proved performance adequacy, and is NOT a tolerance for arbitrarily weak signals.

The quantization error applies to the full noisy received sample, not a separately measured recovered target amplitude. No claims follow about MF peak accuracy, FFT bins, CFAR decision, downstream Float/Fixed errors, or fixed-point Pd. Under frozen isolated target source model, analytic g1 log10(Pr(any input saturation/CPI)) ≈ -901.9848; not zero probability and no stochastic validation run.

## 5. Prospective validity / fixed denominator provisions

| ID | Engineer-approvable clause | Status | Future owner |
|---|---|---|---|
| C01-V01 | Freeze population, N, strata, source manifests, accepted gain registry, risk, rounding, sample IDs and denominator before acceptance begins; never alter after outcomes | PENDING | C01/C06 |
| C01-V02 | VALID_PERFORMANCE: valid frozen metadata/profile/payload, correct 33x128 layout and scale reconstruction, no unapproved input clipping/downstream overflow, CPI counted once in fixed N | PENDING | C06 |
| C01-V03 | INCONCLUSIVE: unknown/changed gain, missing hash or stage data, corrupt CPI, unexpected clip or overflow; under future STRICT test policy stop entire run at first occurrence, report CPI index and count, no partial-N PASS/FAIL | PENDING | C06 |
| C01-V04 | STRESS_ONLY: predeclared overrange vectors tested with independent clipping count/location/flag oracle, never included in Pd/Pfa denominator and never reclassify performance data post hoc | PENDING | C02/C06 |
| C01-V05 | Count and hash complete ordered clip events (pulse, range, I/Q, sign), first occurrence, positive/negative totals, sticky and nonwrapping overflow/status counters, complete trace integrity | PENDING | C02/C06 |
| C01-V06 | No deletion, replacement, top-up, automated retry, optional stopping or changing gain/tolerance according to results. Distinguish Gaussian statistical clipping risk from violation of strict numerical-validity rule | PENDING | C06 governance |

## 6. Separation of C01 / C02 / C06 and approval conditions

**C01 owns:** bounded source class/interface, pre-CPI gain profiles, input risk and source-unit precision, metadata, saturation admission/disposition and exact original-domain reconstruction.

**C02 owns:** internal MF/MTI/FFT W/F, accumulator and coefficient/twiddle widths, FFT shifts, downstream saturation and quantized CFAR alpha/comparator. No C02 architecture is approved.

**C06 owns:** independent Float-vs-bit-true numerical max/RMS, bitwise/threshold match, validated datasets and tested end-to-end stage/error budgets (assuming the 8-criteria S04 plan allocates this responsibility). No acceptance run approved.

| Decision / gate | Owner | Status |
|---|---|---|
| Bounded source classes and proposed g5/g1, 0.1% 20k risk, input numerical floor | C01 independent engineer | **PENDING** |
| Formal disposition of REQ-SCR-01 and REQ-RNG-03 S02 obligations with approved future C02/C06 owners | independent engineer | **BLOCKER pending signature** |
| Downstream numeric architecture and FFT shifts | C02 independent decision | OPEN |
| Independent numerical qualification and preserved legacy constraints | C06 independent decision | OPEN |
| Gate-S04 final close | separate engineer decision, only after all obligations evidenced | OPEN |

Required decision: engineer APPROVE / APPROVE WITH EXPLICIT DEFERRED OBLIGATION AND OWNER / REVISE. **No decision is assumed by preparing this package.** C01 cannot be marked PASS if S02 binding obligation remains silently unassigned. Historical Pd/Pfa evidence and 4135 extra target-present clusters (NOT Pfa), missing complete raw IQ/power arrays, Student-t/spatial FAIL and downstream hardware unknowns preserved.

**Final status: C01 HOLD, C02 OPEN, Gate-S04 OPEN, stage 0%, overall 25%.**

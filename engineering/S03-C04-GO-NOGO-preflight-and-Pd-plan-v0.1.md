# AX309-RDSP-001 — S03-C04 GO/NO-GO preflight and separate Pd plan v0.1

**Current verdict: NO-GO for final Pfa execution; conditional technical GO for the proposed empirical Bernstein theorem and constants.**
User selected EB as development path; S02 v1.2 remains PROPOSED; S02 v1.1 remains active and its spatial-transfer failure is immutable. No new reference, implementation qualification or final Pfa/Pd data generated in this turn.

## 1. Independent math and formula audit

Maurer & Pontil (2009), Theorem 11, https://www.cs.mcgill.ca/~colt2009/papers/012.pdf: given independent X_i in [0,1] with unbiased sample variance V_n=SUM((Xi-Xbar)^2)/(n-1), P(E[average Xi] <= Xbar+sqrt(2*V_n*ln(2/delta)/n)+7 ln(2/delta)/(3(n-1)))>=1-delta. The theorem does NOT assume CUT independence inside each CPI. For identically distributed noise-only CPI, E[average Xi] is the per-valid-CUT mean alarm probability averaged across map positions. This is one fixed-n interval, not an optional-stopping-valid confidence sequence.

At delta=.05, n=20000, Xi=Fi/2782 (Fi integer 0..2782), ln(2/delta)=ln40=3.688879454113936, and the additive finite-sample term 7ln40/[3(19999)]=0.000430390789186. Candidate U=min(1,Xbar+sqrt(2*S2*ln40/20000)+7ln40/[3(19999)]).

Independent pure arithmetic Welford variance and direct moment variance agree on deterministic bounded corner-case values as recorded in S03-C04-independent-GO-NOGO-numeric-audit-v0.1.json. Both existing software unit suite (50 tests) and this formula audit have no new CPI data. Finite-sample coverage >=95% applies if CPI units are actually independent and bounded, not if within-CPI CUTs are iid. Validity of the proof is DIFFERENT from probability of obtaining PASS.

## 2. Sensitivity and power — predictive ONLY, not a test
Historical frozen post-alpha spatial diagnostic has CPI alarm-count variance 3.9913375090621184, CPI rate variance 5.157083961574534e-7. It FAILED old spatial gate; first 2048 underlying source IQ CPIs were shared with earlier exploration. Historical variance is used for planning only. The following table fixes prospective sample variance at a hypothesized multiplier and approximates the random sample mean by a Gaussian mean with variance s2/N. This is an APPROXIMATION of PASS power, not a guarantee or historical pass claim.

| Hypothesized true mean Pfa | Variance relative to historical | EB bound evaluated at mean | Approximate probability of PASS |
|---:|---:|---:|---:|
| 0.0008 | 1x | 0.001244183 | 100.0000% |
| 0.0010 | 1x | 0.001444183 | 100.0000% |
| 0.0010 | 4x | 0.001457976 | 99.9982% |
| 0.0010 | 8x | 0.001469402 | 98.3429% |
| 0.0011 | 1x | 0.001544183 | 0.0000% |
| 0.0012 | 1x | 0.001644183 | 0.0000% |

For target mean .001, U at historic variance is 0.001444183; at 4x variance 0.001457976. Estimate CPU 7.86s by linear extrapolation of earlier Python 4096-CPI run, not new benchmark; full raw IQ 337,920,000 bytes, theoretical 115200 8N1 upload minimum 8.15h. The probability of PASS is NOT a guaranteed 95% under all possible [0,1] CPI distributions. Normal approximation in extreme tails can be inaccurate.

## 3. Proposed operational preflight and strict partitions (not yet executed)
Future NEW PRNG master seeds reserved in draft: reference 411091701 (4096 CPI), independent implementation comparison 411091702 (4096 CPI), final main Pfa 411091703 (20000 CPI), separate Pd 411091704 (1000 CPI). None consumed. Future source selection: PCG64 SeedSequence([master,i,191]) per independent i, with NumPy version and exact source SHA fixed before generating any new data. Original v1.1 CI masters 311091601/602, prior spatial 311091603, alpha calibration 311091604, reserved old Pfa 311091605 and earlier exploratory runs are NOT eligible reuse.

Preflight mandatory steps:
1. Engineer approves proposed limited S02 v1.2 method and n change; retain history of anisotropic spatial z=43.575 FAIL and v1.1 old methods. No acceptance run on active v1.1 under an unapproved EB substitution.
2. Pin source Git commit, source numeric version/SHA, 33x128 IQ, LFM/MF/MTI/32-FFT, strict 2D CA-CFAR powerCUT > alpha*mean40, alpha=7.476912055027923, 7x7 / central 3x3 / 2782 valid CUT, no processing changes.
3. Independently compare reference and second implementation on their own predesignated data; cross-check Fi and Xi in [0,1], sample mean, variance ddof=1 and formula using an independent one-pass Welford routine, precise validity/zero-variance and missing-CPI handling. Failed check => STOP, no tuning on acceptance pool.
4. Prove independently generated CPI by process design: distinct deterministic PCG64 child streams, no input reuse, no pulse overlap or retained pipeline state; same noise distribution and frozen parameters across CPI; review CPI-index manifest, optionally ACF/Ljung-Box as non-proving diagnostics. New diagnostic thresholds cannot be chosen after inspecting results. Failure to support independence => BLOCK, not PASS.
5. Produce distinct manifest hashes for reference, independent implementation and reserved final data. Never reuse alpha-quantile selection, Delta-star calibration, old qualification or historical spatial data as fresh validation. Require a subsequent engineer GO from readiness report BEFORE generating any final Pfa input.

Once AND ONLY ONCE both S02 v1.2 and readiness receive explicit approval, exact n=20000 independent valid CPI, no optional stopping or sample addition, produce ONE U_EB. PASS iff valid U_EB<=.0015; FAIL if valid U_EB>.0015; invalid/unproven independent CPI or source mismatch => INCONCLUSIVE/BLOCKED. All failures retained. Main Pfa is still blocked today.

## 4. Separate prospective Pd readiness
Pd>=.90 at isolated single-target input SNR20dB without clutter is currently a design goal, not binding acceptance. There is no previously completed independent population trial. Propose n=1000 NEW independently seeded noise realizations/complete target CPIs using reserved namespace 411091704. Fix target k in eligible CFAR interior and velocity away from DC/MTI null, Nyquist and half-bin tie; freeze target phase, amplitude, SNR power definition, waveform, and matching/accuracy separations before generating any target data. A success means an authorized correctly associated target detection, while extra clusters are reported separately; do not select favorable target positions after results. Use one-sided exact 95% Clopper–Pearson lower for success Bernoulli trials. At n=1000 PASS of a future binding Pd>=.90 would require at least 916/1000 independent successes, lower exactly 0.900142701. Example acceptance power: true Pd=.9 => 0.04850; true Pd=.93 => 0.96092; true Pd=.95 => 0.999998. The target-to-trial pairing and non-independent target positions must be specified before authorization. This Pd method and sample size are PROPOSED, not yet an approved binding Pd contract. No Pd data generated.

## 5. Final gate and constraints
Theory GO; analytical risk estimate GO as planning only; formally changing S02 v1.2 NO-GO (awaiting engineer approval); freshly executing reference/implementation preflight NOT DONE; final Pfa NO-GO. Gate-S03 OPEN, S03=75%, project=22.9167%. All previous files and failed gates stay immutable.

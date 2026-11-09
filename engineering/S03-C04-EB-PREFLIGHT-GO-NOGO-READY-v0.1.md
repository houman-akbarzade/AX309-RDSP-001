# AX309-RDSP-001 — S03 C04 empirical Bernstein final-test readiness v0.1

**PREFLIGHT TECHNICAL GO (16/16). FINAL Pfa TEST NO-GO pending formal S02 v1.2 approval AND separate engineer authorization.**
S02 v1.2 remains PROPOSED. Gate-S03 OPEN; progress S03=75%, project=22.9167%. No final Pfa/Pd corpus generated.

## Contract and provenance frozen before new data
The 22-row proposed S02 v1.2 matrix changes ONLY REQ-CFAR-02; 21 others are identical to v1.1. The approved v1.0/v1.1 files, historical Student-t 7/15 FAIL and anisotropic spatial FAIL are unchanged. Alpha=7.476912055027923 frozen; Delta*=0.28734133322686817 frozen in history but not used in EB. Pfa target .001 and acceptance 95% one-sided U<=.0015 and Pd design >=.90 preserved.
Source/protocol frozen Git commit: 992966f45e2857e6e9492b0d35bcfa34fb56f17f. Preflight code SHA256 9a67510bb7f1ee607a658ac3b9ee82f67becc11299c39fc59db05d5d11532eba; model SHA256 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b; Python 3.14.4, NumPy 2.3.5, SciPy 1.16.3. Proposed S02 method and change size not yet approved.

## Actual independent preflight, not main acceptance
Exactly 4096 fresh reference CPI at Seed master 411091701 and 4096 fresh implementation CPI at Seed master 411091702, PCG64 SeedSequence([master,i,191]) freshly constructed for each CPI, full 33x128 complex Gaussian noise, same fixed MF/MTI/FFT/power and CA-CFAR 7x7 minus 3x3, 40 training, strict power greater than alpha times mean and 2782 CUT. End-to-end source is pure per-CPI functions without retained state or overlapping pulse inputs.
- **16/16 mandatory checks PASS, zero alarm-mask mismatch in all 8192 CPI** between model.cfar_2d and independently computed summed-area CFAR on identical power maps.
- NumPy and independent scalar Welford online mean, ddof=1 sample variance and empirical Bernstein upper bounds matched at roundoff level: reference absolute U difference 2.602e-18; implementation 3.469e-18.
- Identical-input same-seed regeneration SHA for four selected CPI in each pool, distinct PRNG master streams and checked unique selected IQ signatures. Final seed master 411091703 was not consumed. The two CFAR methods share upstream floating-point MF/MTI/FFT, whose unit tests are distinct historical evidence.
- Count autocorrelation diagnostic: reference lag1 -0.014435, Ljung–Box p=0.6749; independent implementation lag1 -0.007223, Ljung–Box p=0.7397. These do NOT statistically prove independence; construction with fresh child PCG64 streams/no shared state is the primary procedural justification under pseudo-random sampling assumptions.
- Reference preflight observed mean 0.0010227228, second pool 0.0009968344: purely preflight descriptive values, NOT final Pfa performance estimates. At n4096 EB is too conservative for PASS, which is expected; not a failed final acceptance.
- Actual preflight runtime 4.299 seconds, all CPI processed, no early stop.

## Readiness decision
Mathematical EB method and formula checks: GO. Source independence audit: GO under computational PRNG assumptions; empirical autocorrelation alone is not proof. Two independent implementations of CA-CFAR alarm-mask counts and two EB estimators on identical datasets: GO. Source/CFAR/alpha consistency: GO. Proposed S02 v1.2 still NOT APPROVED. Final main 20000-CPI Pfa: **NO-GO until explicit approval of the amended S02 requirements and a distinct engineer GO**. On approval, freeze final input/corpus hashes before readout, exact 20000 fresh CPI master seed 411091703; only then PASS iff valid U_EB<=.0015, FAIL iff valid U>.0015, INCONCLUSIVE for integrity/independence/missing CPI violations. No optional stop, resampling, new threshold or posthoc tuning.
Pd protocol is separate PROPOSED ONLY in engineering/S03-Pd-independent-acceptance-FINAL-REVIEW-PROPOSED-v0.1.md; no Pd data generated. Gate-S03 remains OPEN and progress unchanged.

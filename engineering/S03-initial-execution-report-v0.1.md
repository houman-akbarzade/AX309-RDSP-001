# AX309-RDSP-001 S03 Initial Floating Reference Execution Report v0.1

Scope: source Python NumPy/SciPy model on laptop, no FPGA RTL simulation, synthesis, STA or board verification.
Gate-S02 approved independently with hash-pinned v1.0 spec and matrix.

## Evidence-backed completed work
- 20/20 unit tests pass under python unittest. Includes sampled LFM/MF pulse and boundary k=0,112, first-difference stationary cancel, signed FFT bin and off-grid velocity, 7x7 CA-CFAR geometry 40 training/2782 CUT, strict comparator, 8-connected grouping, deterministic tie and one-to-one truth scorer, noise variance conventions, Q1.15 host serialization and duplicate-run hash.
- Six reproducible single-CPI scenarios run: clean, SNR 0/10/20dB, and SNR20 with SCR+10/-10dB stationary homogeneous clutter. Each contained all 3 truth objects matched under approved *scoring gates*, but produced additional detections/clusters and cannot imply a population Pd/Pfa. Full per-case counts, clipping, input raw SHA256 and first records are in S03_six_case_reference_smoke.json. Source amplitude 0.18 and seeds pinned.
- C04 pre-registered 15-condition count-based Beta-binomial/IID statistical qualification run with 3000 outer trials per condition and 4096 independent CPI counts/study. 8 conditions qualified and 7 FAILED. In the 7 failures, the one-sided lower Wilson bound for conditional coverage was below 0.93, while no studies were INCONCLUSIVE. See s03_C04_count_qualification.json. This is NOT permission to change any threshold or select favorable models.
- First C04 execution computed results but JSON serialization failed due to numpy.bool; source fixed to convert to Python bool with NO change to method, seed or thresholds. Same deterministic study rerun and complete JSON saved.
- A separate 128-CPI exploratory Gaussian noise-only pipeline spatial diagnostic shows sample alarm-count variance 4.30456 vs equal-p iid count variance 2.59913 (overdispersion ratio 1.656). Alpha was the uncalibrated analytic initializer. This is an exploratory dependence diagnostic and NOT alpha calibration, NOT a 4096-CPI Pfa test and NOT a definitive spatial qualification.

## Mandatory block: statistics specification change required before final Pfa evaluation
C-CFAR-02 is approved and immutable. Its method qualification failed 7 of 15 conditions. Therefore, under the exact approved contract, NO main Pfa acceptance trial should run and no Pfa PASS claim is possible.
Potential engineer-level options for separate review:
A. Retain baseline and block C04 until a new formally approved method; advance all unrelated S03 model and verification tasks. Lowest change risk, no final statistical acceptability proof.
B. Propose a NEW candidate CI (e.g. predeclared CPI-level studentized cluster bootstrap / skewness-aware bounded-count interval), and prospectively design cost, calibration/coverage conditions and separate seeds; requires engineer authorization of new S02 baseline version before it replaces current.
C. Rescope qualified dependency envelope after independent genuine radar-chain characterization, with explicit engineer-approved requirement revision BEFORE repeating coverage qualification and final Pfa tests. It must not be selected opportunistically from the 8/15 successful conditions.
Recommendation: A immediately and prepare B for review as one consolidated exceptional decision; no silent policy change.

## Remaining S03 risks
- alpha parameter currently analytic IID initializer; requires disjoint calibration with an approved deterministic algorithm.
- Floating-model peak and grouping rely on seeded synthetic point targets; no population Pd or range error probabilities established.
- Candidate host quantization Q1.15 and internally floating DSP are NOT the hardware bit-true model.
- Large-list reference assignment is exponential in truth count; 3-target baseline only.
- Spatial correlation diagnostics require larger samples and source-realistic clutter.
- FPGA small memory, timing and RTL feasibility are S05/S08/S09 and not proven here.

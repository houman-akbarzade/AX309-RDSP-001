# AX309-RDSP-001 — S03 Cycle 2 Evidence Report v0.2

**Scope:** Independent NumPy floating-point reference. Gate-S02 approved immutable v1.0; Gate-S03 OPEN. C04 official Student-t qualification FAILED 7/15 and main Pfa BLOCKED.

- 26/26 unit tests pass; 19 deterministic edge/multitarget scenarios run. No RTL, synthesis, STA or board test.
- 1024 independent Gaussian noise-only full-chain CPIs used exclusively for *spatial diagnosis*, with **uncalibrated** alpha0. Mean count 2.625977, sample variance 3.618523, independent-CUT variance ratio 1.379274; cannot infer final Pfa.
- Clean three-target case: 3 matched, 6 extra clusters. SNR20 case: 3 matched, 7 extra clusters. At two equal-velocity targets separated by four range samples, 1 matched of 2. Edge k=0 and k=112 are valid full-echo delays but not valid CFAR CUTs; zero truth matches in both explorations.
- Candidate-method pilot compares t vs skewness-corrected Studentized using 250 new seeded runs in each of 15 conditions, plus tiny bootstrap-t pilot (80 outer, B=256) under four dependency models; this is NOT a formal qualification or permissible amendment of current S02.
- Historical C04 file hash unchanged: b4728d6d93a02e3324f0390dc639add2780dc46aaf9b2d5afba07738480c3ef9; 8/15 PASS, 7/15 FAIL preserved. No threshold modified, no main Pfa test or alpha calibration performed.
- Decision exception: propose scoped prospective C-CFAR-02 v1.1 amendment to skewness-corrected CPI Studentized method, preserving 15 conditions/3000 outer reps and all original Wilson thresholds. Needs explicit engineer approval before new formal qualification.
- S03 C01-C05,C07 remain complete; C06 failed/blocker and C08 Gate open; S03 6/8=75%, project 22.9167%.

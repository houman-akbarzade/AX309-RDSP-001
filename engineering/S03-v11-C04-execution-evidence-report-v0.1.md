# AX309-RDSP-001 - S03 v1.1 C04 formal execution report

Stage S03, Gate-S03 OPEN. S02 v1.1 C-CFAR-02 engineer approved; S02 v1.0 and original 7/15 Student-t failures immutable. MAIN Pfa BLOCKED.

## Verified independent preflight, calibration, qualification
- Source locked at commit 8369aa8814893776a800c7a18b36fb8be26b33d2, SHA256 68d5a6ea8a8143ea1a002abc8625c688c96a3289ae4a6d01f9ab0f06a6805b00.
- Preflight: PASS. Independent formula scalar/vector checks, rank 4792, distinct seed namespaces, 100-count guards, Wilson cutoffs, unchanged source baselines.
- CI CRITICAL CALIBRATION: 15 conditions x 5000 independent outer studies x 4096 CPI each. ALL 75,000 valid. Delta_star = 0.28734133322686817. Runtime time.perf_counter = 21.283112255987362 seconds. Evidence SHA256 c6f64522a9fa878474c3431177159f43e3f9e8c42a31b322fb95fed8cd5ccbf9.
- INDEPENDENT QUALIFICATION: 15 same conditions x 3000 outer x 4096 CPI. All 15 PASS. No inconclusive. Lowest one-sided Wilson lower conditional coverage 0.9515520667104338 > 0.93. Runtime 12.843731191998813 seconds. Evidence SHA256 2aa1e4614b3d3b80ded3b6f7c47a15dd92184635f54619d90f1df8501b2d0ed5.
- Synthetic count-model qualification is NOT a real-chain Pfa or alpha calibration result; Beta-Binomial covariance is not real 2D CFAR geometry.

## Synthetic statistical acceptance power at p=0.001
| rho | valid upper <=0.0015 | fraction | one-sided 95 percent Wilson lower |
|---:|---:|---:|---:|
| 0.000 | 3000/3000 | 1.0000 | 0.9991 |
| 0.001 | 3000/3000 | 1.0000 | 0.9991 |
| 0.010 | 3000/3000 | 1.0000 | 0.9991 |
| 0.030 | 2998/3000 | 0.9993 | 0.9980 |
| 0.050 | 2910/3000 | 0.9700 | 0.9644 |
The rows are repeat-study surrogate-count power, NOT measured radar performance. Increasing rho up to 0.05 reduces probability of acceptance but did not force change to Delta_star or criteria.

## Separate actual Python radar-chain diagnostics: NO Pfa verdict
- 2048 independent Gaussian input CPI processed by MF, MTI, FFT, 2D CA-CFAR using only uncalibrated analytic alpha0. Runtime 0.883 seconds.
- count mean 2.696777, count sample variance 3.939765, overdispersion vs equal-p iid CUT 1.462333, lag1 CPI count correlation 0.006019.
- zero-count CPI fraction 0.117676, tail P(F>=8) 0.018066, adjacent range alarm pairs 1058, Doppler pairs 6.
- At empirical marginal p used for DIAGNOSTIC comparison only: independent Binomial zero/tail 0.067334/0.006547, Beta-Binomial rho=.001 zero/tail 0.275373/0.081462.
- Exchangeable Beta-Binomial rho equivalent from variance is 0.00016625, only moment matching; cross-bin spatial correlation and full count-tail compatibility remain unproven at the future calibrated alpha.
- Main Pfa final dataset NOT generated. Independent CFAR-alpha calibration NOT performed. Need prospectively specified alpha calibration and disjoint post-calibration validation of real-chain spatial distribution BEFORE main Pfa.

## Numerical CFAR sidelobe diagnostics, no processing changes
- Clean isolated target k20/v-3: sidelobe CUT at k7,b26 power 65.642577, 40-training mean 2.582264, alpha threshold 19.470503; main target k20,b26 power 6726.644471 and threshold 2724.331103.
- Each isolated target has 3 distinct peaks at k-13,k,k+13. The joint three-target clean map yielded 9 clusters. Sidelobe peaks about 0.976 percent of peak power for each isolated target. Direct sum of 40 training cells was verified for each selected CUT.
- Previous ideal range compression ablation reduced off-grid three-target cluster count from 9 to 6; remaining Doppler/CFAR interactions need further independent study. No acceptance threshold, CFAR geometry, or numeric floor altered.

## Completion and prohibited claims
- 38/38 software unit tests PASS, S03 criteria C01-C05,C07 remain complete, C06 and C08 remain OPEN per engineer instruction. S03 75 percent, total 22.9166667 percent.
- S02 v1.1 method CALIBRATION and SYNTHETIC COUNT QUALIFICATION PASS, but source-realistic operational transfer and independently calibrated alpha not complete. Final Pfa remains BLOCKED; no RTL, synthesis, STA or FPGA evidence.

# AX309-RDSP-001: S03 C04 Alpha Calibration and Spatial Transfer Failure v0.1

**BLOCKED: one predeclared mandatory diagnostic failed. Main Pfa NOT executed. Gate-S03 OPEN.**

Original S02 v1.0 and limited v1.1 approved historical hashes and Student-t FAIL 7/15 preserved. v1.1 count-model qualification 15/15 PASS; fixed Delta_star=0.28734133322686817 unchanged.

## Predeclared methodology and provenance

Prospective criteria for alpha and independent post-alpha 4096-CPI diagnostics committed BEFORE outputs: Git 3336c938c1e7700eb8782808527c581f4ca58223, protocol SHA256 e29ff54a0b324e035e61556b75e913cb4838fd7ded64e4e4c8861728aa88d5d7.

Source locked BEFORE outputs: Git 8db6bac43fb4eb8652f668451d67952150ed8a54, source SHA256 a57c69ee2de4cd10783995af9146fd21de881e7ce0f72f97dca5849054cd9372. 44/44 unit tests PASS.

## Independent alpha calibration: PASS (not Pfa verification)

4096 independent circular Gaussian noise CPI, PCG64 SeedSequence([311091604,i,191]); complete Python MF/MTI/FFT/CA-CFAR ratio map. 2782 CUT/CPI, 11,395,072 finite training-normalized ratios. Alpha chosen once at predetermined upper 0.001 quantile, no validation-data peek.

Frozen alpha=7.476912055027923, calibration sample fraction 0.000999993681, runtime 1.865211 seconds

Calibration file SHA256 1a4540f97b38da8739ccf63f3eb68555a6671c50d9c8bc9f25829a03a0cee2fe; frozen at Git c4d48adfb996b08c1cff9832c87229de609a5f92 BEFORE post-alpha diagnostic.

Calibration sample alert fraction is fixed by order statistics and must NOT be reported as achieved or validated Pfa.

## Independent post-alpha diagnostics: FAIL (not final Pfa)

4096 fresh distinct CPI, master seed 311091603; full Python chain with frozen alpha. 0 invalid CPI.

Mean alarm count 2.791260, variance 3.991338, overdispersion ratio 1.431377

Ljung-Box Q20 p=0.0502061 (passes prespecified p>=0.01), zero fraction 0.112305, count tail >=8 fraction 0.022217; zero/tail 99 percent Wilson intervals overlap predeclared five-model envelope.

Range-neighbor joint positive probability 0.0001932928, Doppler-neighbor 0.0000014603; CPI-cluster paired anisotropy z=43.575446 whereas prespecified |z|<=2.5758293035489004: FAIL.

Passed 4 of 5 preregistered necessary diagnostic checks; overall FAIL_SPATIAL_TRANSFER_GATE, runtime 1.609090 seconds.

This failure is of separately predeclared S03 spatial exchangeability requirement; it does not retrospectively invalidate the passed synthetic 15-model CI qualification. Spatially anisotropic CA-CFAR masks cannot be assumed exchangeable on the basis of scalar Beta-Binomial count parameters. Count-level correspondence alone is insufficient to declare transfer successful.

## Separate deterministic cluster investigation (not Pfa)

With frozen alpha, each isolated clean target yields three clusters at k-13,k,k+13 and combined three clean targets yield nine clusters. All CUT training means checked by independently summing 40 cells.

k=7 Doppler=26 CUT=65.642577, mean40=2.582264, threshold=19.307364, margin=46.335213

k=20 Doppler=26 CUT=6726.644471, mean40=361.312853, threshold=2701.504426, margin=4025.140045

k=33 Doppler=26 CUT=65.642577, mean40=2.582264, threshold=19.307364, margin=46.335213

Nontrivial matched-filter sidelobe peaks cross strictly greater-than local alpha*training thresholds. No CFAR/FFT/MTI/clustering parameters, alpha or Delta were changed.

## Engineering alternatives requiring decision before dependent testing

Option A (preferred): Engineer-approve source-realistic anisotropic spatial/count surrogate generation, including cross-bin covariance and tails; independently qualify CI transport on new frozen datasets at same thresholds, no retroactive change. Higher compute and modeling complexity.

Option B: Engineer-approve a new necessary transfer criterion based on independent CPI count-level distribution plus rigorous justification that directional map anisotropy does not invalidate CPI-cluster CI; prospectively freeze protocol and regenerate all required diagnostics, never relabel the present FAIL. More delicate validity argument.

Option C: Investigate distribution-free CPI bounded-mean CI with substantially larger pre-fixed CPI budget; more conservative, serial FPGA throughput cost and S02 revision needed.

Do not run the main Pfa. S03 75%, project 22.9166667%, Gate-S03 OPEN. No RTL/synthesis/STA/FPGA evidence.

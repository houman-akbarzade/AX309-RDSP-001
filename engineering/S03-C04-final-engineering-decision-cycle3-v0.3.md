# AX309-RDSP-001 — S03 Cycle 3 FINAL ENGINEERING DECISION PACKAGE v0.3

**Scope: Independent technical audit and development only. NOT a change to S02 v1.0.**
Gate-S02 v1.0 remains approved and hash-locked; Gate-S03 OPEN. Existing official 15-condition Student-t method qualification FAILED 7/15, evidence preserved. Main Pfa BLOCKED. No alpha calibration, official replacement qualification, RTL/synthesis/FPGA/physical tests were executed.

## Executive technical disposition
The earlier positive skewness correction is algebraically correct at **first-order Studentized Edgeworth/Cornish-Fisher** accuracy, but is NOT the symmetric Johnson (1978) interval and does NOT guarantee finite-sample coverage. Independent development evidence indicates that **simply replacing t by fixed first- or second-order skew-correction is not yet a credible guarantee of passing all 15 official qualification conditions**. A theory-locked larger G=16384 model also lacks confident full-15 pass evidence and quadruples eventual board transfer cost.

**Single recommended scoped exception:** seek engineer approval for a **new prospective S02 v1.1 C-CFAR-02 only**: G=4096 CPI skewness-corrected Studentized U with an additional nonnegative global critical adjustment Delta_star determined entirely on **new independently seeded, preregistered 15x5000 model-calibration datasets** via Bonferroni-protected order statistics. Freeze the adjustment and source hashes BEFORE an independent **15x3000 formal qualification** using the original strict Wilson conditions; only then run source-realistic spatial checking, independent CFAR alpha calibration and final main Pfa. No threshold change or model removal is proposed.

This is a method design with prospective calibration/qualification, NOT a retroactive fix to failed Student-t evidence, NOT a demonstrated successful alternative.

## 1. Exact first-order formula audit and sign
Let G=4096, X_i=F_i/2782, sample mean xbar, sample SD s=sqrt(sum(X_i-xbar)^2/(G-1)), and sample skew gamma_hat=m3/m2^(3/2), m_j=sum(X_i-xbar)^j/G. For T=sqrt(G)(xbar-p)/s, the leading Edgeworth expansion is
Pr[T<=x]=Phi(x)+gamma*(2*x*x+1)*phi(x)/(6*sqrt G)+O(G^-1).
The inverted lower 5% quantile is q_.05=-z_.95-gamma*(2*z_.95^2+1)/(6*sqrt G)+O(G^-1), hence the one-sided upper bound
U_A=clip(xbar+t_(.95,G-1)*s/sqrt G + gamma_hat*s*(2*z_.95^2+1)/(6G),0,1).
The coefficient (2*z_.95²+1)/6 = 1.06851448469847, sign POSITIVE for positive skew. Replacing normal z by Student t in the leading symmetric term only affects higher-order corrections. The mathematical/implementation sign and central moment convention were checked against independent algebraic code. The earlier formula was valid as **a first-order approximation**, not an exact Johnson bound or a claimed high-order expansion.
A separately theory-derived second-order skewness/kurtosis correction was implemented as a development alternative, but it did not reliably improve the minimum observed coverage across independently seeded studies. No coefficient was tuned to match earlier pilot results.

References:
- Hall, The Bootstrap and Edgeworth Expansion, Springer (1992), DOI 10.1007/978-1-4612-4384-7.
- A 2024 review of skew confidence intervals and first-/second-order Cornish-Fisher coefficients: https://www.mdpi.com/2073-8994/16/11/1424
- Johnson, Modified t Tests and Confidence Intervals for Asymmetrical Populations, JASA (1978), DOI 10.1080/01621459.1978.10480051.
- NIST EDA Handbook: https://itl.nist.gov/div898/handbook/eda/section3/eda35b.htm

## 2. Evidence: independent development, NOT C04 formal qualification
Each method's seed domain differs from the original official failure and previous development pilot; no data were reused for official certification. Coverage is the proportion of independently generated model studies where the candidate upper CI contains the known generating p. All are DEVELOPMENT-ONLY and have considerable Monte Carlo uncertainty:
| Method | Outer repetitions / condition | Smallest observed coverage across 15 conditions | Largest observed coverage |
|---|---:|---:|---:|
| First-order corrected Studentized, G=4096 | 1,200 | 93.42% | 95.92% |
| Second-order skew/kurt corrected, G=4096 | 1,200 | 93.33% | 96.08% |
| First-order corrected Studentized, G=16,384 | 800 | 93.75% | 95.75% |
| Whole-CPI bootstrap-t, B=199 and G=4096 | 120 | 91.67% | 97.50% |
| Signed-root empirical likelihood, G=4096 | 300 | 92.00% | 95.67% |

The 120-study/bootstrap-t and 300-study/empirical-likelihood pilots have very wide uncertainty. Neither currently supports a qualification claim. Even 1,200/condition cannot substitute for the fixed 3,000 formal trials and Wilson score conditions. The first-order method at G=4096 had a worst observed coverage 93.4167%. Under a **plug-in approximation treating those development fractions as true probabilities**, the chance of all 15 independent official coverage tests passing is only ~9.6%. This is highly uncertain and NOT a validated failure probability; it indicates that the fixed first-order variant is a risky path to formal approval. The 16,384-CPI variant was motivated prospectively by first-order normal approximation scaling G^-1/2, not tuned via an accepted qualification result; still insufficient independent evidence for a confident 15/15 PASS.

## 3. Proposed preferable variant: prospective global critical-value calibration
Retain exact first-order skew formula, but define U_cal=clip(xbar + (tcrit+Delta_star)*s/sqrt G + gamma_hat*s*(2*z*z+1)/(6G),0,1).
Delta_star is NOT set today. A new engineer-approved procedure must generate 5000 independent model-calibration trials for each of the SAME 15 conditions, each with 4096 CPI, using entirely NEW seeds. For each VALID trial compute the adverse studentized score A=(p_true-xbar)/(s/sqrt G)-gamma_hat*(2*z*z+1)/(6sqrt G). An invalid trial is separately counted; any condition with fewer than 4750 valid among 5000 blocks calibration. For m valid trials, choose order-statistic rank r=1+BinomQuantile(1-.05/15; m,.95), and set Delta_star=max(0,max across models of A_(r)-tcrit).
If all 5000 are valid, the rank is 4792 of 5000 and the one-sided per-model calibration probability that the order statistic exceeds the population 95th quantile is at least 0.9966667. Bonferroni provides >=95% *joint quantile confidence* across the 15 properly simulated model conditions. This is a meaningful method to address uncertainty of Monte Carlo calibration, and **does not imply that operational CA-CFAR outputs obey these surrogate distributions**. No calibration sample has been generated in this cycle.
After Delta_star is fixed and its source hash recorded, an independent, unchanged 15x3000 qualification must still PASS the three original Wilson bounds, with no dropped conditions. If invalid or out-of-envelope, block, do not re-tune.

### 3a. Project computation budget
- Calibration: 15*5000*4096=307,200,000 CPI count draws.
- Formal qualification: 15*3000*4096=184,320,000 more.
- Total synthetic count draws: 491,520,000, streamable with O(4096) sample memory per study; vastly cheaper than the abandoned nested 614.4-billion-index plan. CPU time is NOT benchmarked for the FULL proposed study.
- Main Pfa stays 4096 CPI instead of 16384. At original UART 115200 bit/s 8N1 and raw 16896 bytes/CPI, the optimistic one-way upload-only minimum is 1.67 hours for 4096 CPI and 6.67 hours for 16384 CPI, excluding handshake/retries/outputs. This is a future physical-validation planning comparison, not measured board throughput.

### 3b. Acceptance power near true p=.001 and conservatism tradeoff
Delta_star is not yet known, hence no honest numerical PASS power can be certified. For the most overdispersed existing beta-binomial rho=.05 synthetic model at p=.001, approximate SE of mean CPI alarm fraction under G4096 is 0.00011081. A **first-order normal plug-in approximation** (freezing ideal sample variance/skew and ignoring their sampling uncertainty) gives probability U_cal<=.0015 of approximately:
| Assumed prospective Delta_star | Illustrative P(U_cal<=.0015), rho=.05, p=.001 |
|---:|---:|
| 0.0 | 99.59% |
| 0.5 | 98.39% |
| 1.0 | 94.98% |
| 1.5 | 87.34% |
| 2.0 | 73.98% |

These figures are analytic sensitivity checks, NOT measured detector performance or future qualification. If the independently calibrated critical is too conservative for useful power, do not change limits or repeat with a friendlier sample; issue a single engineer decision on the method.

## 4. Alternative families if global calibration proves infeasible
- Whole-CPI bootstrap-t: distribution of studentized sample mean by sampling complete CPI records, not CUTs. At G4096 and B799, formal 15*3000 qualification would require 147.27 BILLION resampled CPI indices (~589 GB cumulative uint32 draw volume), still 4.17x fewer than discarded original but far more computation than prospective globally calibrated A. Better asymptotic accuracy often, no guarantee for ultra-skewed zero-heavy data. Independent 120-study/B199 pilot too weak to establish 15/15 success.
- Signed-root empirical likelihood: entirely nonparametric weighting across independent CPI records, with signed root approximately normal; computational burden O(G times root-solving iterations) and sensitivity to skew / boundary effects. A separate 300-study/condition development pilot showed no compelling uniform superiority; no normative adoption recommended.
- Standard finite-sample Hoeffding/Empirical Bernstein [0,1] CPI bounds remain too conservative for main acceptance at G4096 (Bernstein additive term >.0015).
- Fourfold G=16384 with uncalibrated A avoids additional statistical calibration but increases count draws and future physical UART time 4x and was not decisively qualified in 800-study development trials.

## 5. Separate S03 functionality: extra clusters and boundaries
- 38/38 software unit tests passed. Includes exhaustive 113 full-echo MF delay indices and deterministic Doppler tie checks, and new prospective CI critical rank/seed collision tests. This is NOT Bit-True FPGA verification.
- Range/velocity three-target *clean* original model output had 9 target-list clusters for 3 truths. Each isolated clean target produced 3 clusters (sidelobe-like range groups). An artificial ideal range-impulse matched-filter output reduced joint 3-target off-grid clusters from 9 to 6, proving range sidelobe contribution in that diagnostic. The remaining clusters are linked to Doppler/CFAR behavior but not uniquely attributed; do not assume clean zero background implies numerical zero after FFT.
- On-bin artificial ideal compression did not monotonically reduce clusters (14 compared with original 11): this is a warning that exact-zero training windows/roundoff and Doppler clustering can produce unexpected results in a noiseless float simulation. Do not modify CFAR threshold or numerical floor posthoc; S04 must set rounding/zero/noise-floor numerical policy and S03 must test full-chain sensitivity prospectively.
- 19 previously recorded deterministic boundary/multi-target scenarios and 1024 exploratory radar-chain noise-only CPI remain preserved, with no actual alpha calibration or final Pfa.

## 6. Safety, traceability and next decision
Single scoped engineer decision: **whether to approve the drafted v1.1 calibrated skew-Studentized C-CFAR-02 method with a strictly separate predeclared CI critical calibration corpus**. The draft is engineering/S02-v1.1-C04-calibrated-Studentized-PROPOSED-ONLY.md. Approval would authorize formal independent CI calibration and qualification under its fixed algorithm, NOT assert success, not approve Pfa or Gate-S03. If not approved, no change: S02 v1.0 and its failed 7/15 Student-t result continue in force; all nonstatistical S03 activities may proceed.

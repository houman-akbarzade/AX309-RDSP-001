# AX309-RDSP-001 — S03 C04 exceptional decision package v0.1

**Action requested: prospective engineer approval for a narrowly scoped S02 statistical-contract revision. Gate-S03 OPEN. Do not run main Pfa.** Approved S02 v1.0 and historic C04 qualification failure (7 of 15 models) remain immutable.

## Evidence on approved method
The approved uncorrected CPI Student-t interval failed 7 of the 15 fixed qualification conditions. No failing condition was removed; no threshold changed. The failed results file SHA-256 is b4728d6d93a02e3324f0390dc639add2780dc46aaf9b2d5afba07738480c3ef9. Results from a DIFFERENT pilot seed domain cannot be counted as a replacement qualification.

## Alternative A — Recommended to investigate under a NEW approved contract
One-sided skewness-corrected Studentized interval on independent CPI alarm fractions Xi=Fi/2782, G=4096, s=sample SD, gamma=third central moment/variance^(3/2):

U_A=clip(xbar+t_(.95,G-1)*s/sqrt(G)+gamma*s*(1+2*z_.95^2)/(6*G),0,1).

This first-order Studentized Edgeworth correction (a Cornish–Fisher approximation) targets positive skew that caused Student-t undercoverage. The formula is asymptotic, has no distribution-free finite-sample coverage guarantee, and must be independently qualified. It is computationally inexpensive: O(G) per interval, total 15 x 3000 x 4096 = 184,320,000 CPI-count samples for prospective qualification. In a *development-only*, separately seeded 250-study/condition pilot, at true p=.001, corrected CI coverage rates for rho 0,.001,.01,.03,.05 were approximately 0.952,0.932,0.928,0.928,0.952; these are noisy pilot estimates, not proof of meeting the approved Wilson criterion. Pilot upper-bound <=.0015 acceptance fractions at p=.001 were >=.992 for these conditions, but this is not final detector performance.

## Alternative B — Studentized whole-CPI bootstrap-t
Resample complete CPI fractions, estimate the Studentized pivot distribution, and set upper confidence bound using its lower 5% quantile. Under classical smooth-statistic and finite-moment assumptions bootstrap-t can improve approximation accuracy, but sparse alarm counts, zero variance and rare tails remain problematic. Complexity is O(B G) per interval; with B=2000 and the same 15x3000 qualification, 368.64 billion resampled CPI indices, about 1.475 TB cumulative raw uint32 draw volume. A tiny 80-outer/256-resample candidate pilot had estimated coverage 0.95,0.9375,0.9375,0.925 at rho=0,.01,.03,.05 (true p=.001); uncertainty is too large to qualify this method. Alternative B is technically plausible but substantially more expensive than A.

## Alternative C — Distribution-free [0,1] bounded-mean bounds
Treat entire CPI alarm rate as the independent bounded observation. Standard one-sided Hoeffding bound has half-width sqrt(ln(20)/(2*4096))=0.019123. A conservative empirical Bernstein upper bound includes the additive finite-sample term 7ln(40)/(3*4095)=0.002102, **already above the acceptance limit 0.0015 even if sample mean and variance were zero**. This implementation cannot accept p near .001 at the fixed sample size. Such bounds are more assumption-light but not viable without revising sample budget or choosing a different theoretically valid bounded-mean construction.

## Expanded actual NumPy-chain diagnostic (not Pfa test)
1024 *independently seeded* Gaussian noise-only CPI processed through the full floating reference, using the uncalibrated IID analytic threshold alpha0. Count mean=2.625977, count variance=3.618523, variance ratio to equal-p independent-CUT model=1.379274, between-CPI lag-1 count correlation=-0.001828; adjacent alarm pairs range=508, Doppler=2. The measured count overdispersion is not evidence that beta-binomial accurately reproduces the full spatial CA-CFAR field. The chain was NOT calibrated and the 1024-CPI diagnostic was NOT main Pfa acceptance.

## Further independent functional checks
26/26 unit tests PASS; 19 newly executed deterministic edge/multitarget cases. Clean 3-target scenario: 3/3 truth matches and 6 extra clusters; SNR20: 3/3 matches and 7 extras. A single two-target equal-velocity case at 4 range bins separation yielded only 1/2 matches despite nominal theory near 600m. Complete-echo edge delays k=0 and k=112 are NOT valid CA-CFAR CUTs and failed truth matching, as should be distinguished from correct MF peak tests. A k=2 truth can match a nearby k>=3 detection under the broader association gate: that is NOT evidence that k=2 is a valid CFAR CUT or that the range-error criterion passed. No population Pd or Pfa was calculated from these deterministic cases. Follow-up stage-isolation work remains for range sidelobes, Doppler leakage, local threshold interactions and 8-neighbor merging.

## Precise S02 baseline-change request (NOT APPLIED)
1. Issue **new** S02 v1.1 contract document and new approval record referencing immutable approved v1.0 commit/hash. Change only C-CFAR-02 formula from Student-t to the exact U_A formula above; update only REQ-CFAR-02 active method. All 21 other requirements and S01/S02 approval history remain immutable.
2. Keep fixed 4096 independent CPI for main Pfa, valid 2782 CUT per CPI, p target .001, one-sided U<=.0015, and existing >=100 nonzero CPI, >=100 total alarms and positive finite variance guards. Keep exactly the original 15 qualifying cases (IID + beta-binomial rho=.001,.01,.03,.05 at p=.0005,.001,.0015), 3000 independent outer studies each, Wilson lower conditional>=.93, lower unconditional valid-and-cover>=.90, upper inconclusive<=.05, NO post-hoc tuning and no removal of failed conditions.
3. Specify deterministic gamma estimator, quantile and arithmetic edge cases before tests; zero variance or invalid gamma=>INCONCLUSIVE. Allocate **fresh, locked qualification seeds independent of all previous failed and pilot datasets**. Measure real radar-chain spatial/count-tail correspondence with independent diagnostic seeds. Separate alpha calibration and final main Pfa validation datasets.
4. If qualification or spatial validity fails, report FAIL/BLOCKED and request a new approval before amending the contract. Do not run main Pfa before success.

**Recommended engineer decision:** authorize the scoped v1.1 C-CFAR-02 *prospective contract revision to candidate A*, with the above unchanged coverage qualification and Pfa acceptance criteria. This authorizes only a newly approved method and its qualification, NOT a Pfa PASS finding, and does not authorize any unsupported change to RTL/FPGA obligations.

Research basis (not assertions of successful qualification): Johnson, JASA 1978, DOI 10.1080/01621459.1978.10480051; MacKinnon, Nielsen & Webb, Journal of Econometrics 2023, DOI 10.1016/j.jeconom.2022.04.001; Maurer & Pontil, Empirical Bernstein Bounds, arXiv:0907.3740; Studentized bootstrap Edgeworth asymptotics (Hall).

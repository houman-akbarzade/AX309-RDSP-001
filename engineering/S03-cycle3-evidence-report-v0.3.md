# AX309-RDSP-001 — S03 Cycle 3 Evidence Report v0.3

**Gate-S03 OPEN. S02 v1.0 approved and unchanged. C04 approved Student-t qualification remains FAILED 7/15. Main Pfa BLOCKED.**

## Work actually executed
1. Verified first-order Studentized Edgeworth CDF, lower 5% quantile and upper interval formula, including positive skewness sign and coefficient 1.0685144846984709 times gamma*s/G, using peer-reviewed mathematical references and independent algebraic unit checks. No finite-n coverage assertion.
2. Independent CPI-count developmental simulations with entirely new seeds, NOT qualification: first-order corrected Studentized 15x1200, second-order skew/kurt 15x1200, first-order G16384 15x800, bootstrap-t 15x120, and signed-root empirical likelihood 15x300. No previous official or pilot stream used to compute a candidate critical adjustment.
3. Software ablation: off-grid three-target case generated 9 clusters with actual MF but 6 with artificially ideal range-compression output; isolated targets each produced 3 clusters. Remaining extras are not fully causally classified. On-grid ideal range compression can also generate extra tiny-power artifacts in zero-background float simulations, so no posthoc numerical floor or CFAR threshold added.
4. 38/38 NumPy reference unit tests PASS, including 6 new prospective-calibration contract consistency/seed/rank tests and 6 additional skew/Edgeworth tests.
5. Prepared a **draft only** for S02 v1.1: skew-corrected Studentized U with independent 15x5000 Bonferroni-protected global critical calibration, then original 15x3000 qualification and 4096 CPI final test. No such calibration executed, no normative baseline changed.

## Development observed coverage ranges (not qualification)
| Method | Min across 15 conditions | Max across 15 conditions |
|---|---:|---:|
| first_order_G4096 | 93.42% | 95.92% |
| second_order_G4096 | 93.33% | 96.08% |
| first_order_G16384 | 93.75% | 95.75% |
| bootstrap_t_B199 | 91.67% | 97.50% |
| empirical_likelihood | 92.00% | 95.67% |

The first-order G4096 pilot min coverage 93.42% does not provide a reliable 15/15 acceptance prospect. A second-order correction and G16384 independent investigation similarly fail to establish prospective high-confidence qualification. The proposed NEW global critical calibration is mathematically prespecified but NOT executed and its acceptance power depends on a future, independently calibrated critical adjustment. All seed namespaces and model conditions must be frozen before any approved study.

## Mathematical and stage boundaries
- Theorem-first-order sign and coefficient are supported for smooth/asymptotic statistics; beta-binomial discrete heavy tails may violate useful uniform approximation at finite G.
- The proposed Bonferroni order-statistic calibration is valid for the **specified surrogate count models** under genuine independence of outer trials; it is not a distribution-free guarantee for output of the real radar MF/MTI/FFT/CFAR chain.
- Actual radar-chain spatial dependence diagnostics and dedicated CFAR alpha calibration must use separate genuine source-model inputs, plus independent final acceptance corpus.
- No main Pfa, statistical approval, real RTL, bittrue, synth, timing closure or board verification claimed.
- Gate-S03 remains OPEN; S03 C06 and C08 remain incomplete. The current floating reference tests/other six existing S03 criteria are not undone.

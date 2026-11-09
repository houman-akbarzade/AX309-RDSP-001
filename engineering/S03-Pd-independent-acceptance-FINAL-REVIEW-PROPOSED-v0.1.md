# AX309-RDSP-001 — Proposed independent population Pd protocol v0.1

**PROPOSED ONLY; NOT A BINDING ACCEPTANCE CONTRACT. NO TARGET CPI GENERATED.**
The existing S02 single-target/no-clutter/input-SNR20dB Pd design goal >=0.90 is unchanged.
Suggested n=1000 independent one-target CPIs, master PCG64 SeedSequence([411091704,i,191]) i=0..999, source-code SHA/version frozen before inputs. Fix target k=40 valid interior and signed Doppler bin +4 (nominal velocity 1.875 m/s), phase 0, amplitude 0.18, and CN(0, 0.18^2/100) noise. No clutter. This single case does not establish global Pd over all target geometries.
Success per CPI: unique correct target association within original S02 matching gate (range <=2 samples, velocity <=1 Doppler bin); report extra clusters and estimator accuracy separately. Do not treat CUTs or clusters as independent trials.
Proposed one-sided exact Clopper–Pearson 95% lower bound L=Beta.ppf(0.05,k,1000-k+1), k successes (L=0 for k=0). PASS if L>=0.90, requiring >=916/1000 successes; otherwise FAIL, invalid CPI => INCONCLUSIVE. No optional stop or seed re-use. Predictive binomial probability of PASS if true Pd .90=4.850%, .93=96.092%, .95=99.999785%; not measured Pd.
Formal engineer approval of the fixed Pd protocol and binding criterion is required before any target study. Gate-S03 OPEN.

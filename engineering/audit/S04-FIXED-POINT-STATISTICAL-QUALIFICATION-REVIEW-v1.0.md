# Fixed-Point statistical performance: evidence review and proposed qualification

Current stage: S04 carryover review. Status: OPEN_NOT_STATISTICALLY_QUALIFIED. No statistical campaign is authorized or executed by this document.

## What is missing, and what has not failed

The original S04-C02-SELECTED-C-OPEN-OBLIGATIONS-v1.0.json explicitly marks S04-C02-RISK-PERFORMANCE OPEN_NOT_EXECUTED. S04-OPEN-ITEMS-CARRYOVER-v1.0.json carries it as OPEN_NOT_STATISTICALLY_QUALIFIED and explicitly does not authorize a campaign. Later finite numerical/board evidence does not supply the missing qualification.

This is an absence of a completed, accepted statistical Fixed-Point campaign, not a demonstrated statistical Pd/Pfa failure of Fixed-Point. Earlier Float statistical-method failures must not be attributed to this unexecuted Fixed-Point campaign.

| Existing evidence | What it supports | Why it does not close this item |
|---|---|---|
| Accepted S03 Float Pfa and Pd campaigns | Their frozen Float model, source populations, seeds and criteria | Fixed arithmetic is a different numerical path |
| S04 C06R2 16CPIs | Bounded numerical error/contract checks | Not the predeclared independent statistical sample |
| Lab 3noise +3target stage-injected CPIs | Finite functional/numerical behavior of selected paths | Too small; CFAR/grouping injection excludes upstream quantization effects |
| Other finite exact Fixed/hardware matches | Correspondence on the actual archived cases | Numerical equivalence on finite cases is not population-level qualification |

Quantization, FFT scaling/rounding, saturation and CFAR threshold margins can change detection decisions near threshold. This is the mechanism of the residual risk, not evidence that a particular failure occurred. Two resolved noise-free Power peaks do not establish noisy detection probability.

## Recommended bounded protocol (PROPOSED, not approved execution)

1. Select and freeze the exact numeric implementation to qualify. Prefer the final FFT-IP path matching intended delivery, rather than qualifying obsolete C02 and transferring its result. Freeze source/commit/hashes, vendor model/library/version/generics, shifts, rounding, widths, overflow rules, MF coefficients, g profiles, CFAR alpha/window/mask and grouping/record rules. The Lab stage_lab/fft_model.py uses a vendor v7.1 bit-accurate C model; its exact compatibility with the delivered IP path must be documented, not assumed. No model is executed in this review.
2. Declare the population and observation point before generating samples. Use full raw-IQ through the complete bit-true chain, not Power/CFAR injection. Reuse the approved S03 scenario definition and scoring only by explicit extension to the selected Fixed baseline: independent complex noise-only CPIs for Pfa; fixed on-bin single target k40/Doppler+4/SNR20dB for the limited Pd claim. Absolute amplitude, g, noise variance convention and input quantization must be frozen consistently; SNR alone does not define quantization stress.
3. Candidate initial scope: N=20,000 independent noise-only CPIs and N=1,000 independent target-present CPIs. These are proposed fixed counts based on the prior S03 design, not a universal minimum or a guarantee of PASS. New separated acceptance seeds, no optional stopping, top-up, replacement, retuning or deletion of unfavorable CPIs. Any preflight/source-validity work is separate, explicitly authorized and excluded from acceptance samples.
4. Pfa candidate rule: keep the approved 2,782 valid CUT mask per CPI; calculate the false-alarm fraction for each CPI, then the existing frozen one-sided95% empirical-Bernstein bound across independent CPIs; accept only if U95<=0.0015. Do not treat spatial CUTs within a CPI as IID Bernoulli samples. Noise-only detection-cell Pfa is not extra-cluster count in target-present scenes.
5. Pd candidate rule: retain the declared S03 target-to-record association and range/Doppler accuracy events separately; do not redefine statistical detection as the new two-peak Power property. One success/failure per independent target CPI; one-sided95% exact Clopper-Pearson L95>=0.90. For N1,000 this corresponds to at least916 successes under the historical scorer. Verify the frozen scorer and each required event criterion before execution; do not merge detection, association and accuracy claims.
6. Report paired Float and Fixed outcomes on identical source CPIs for diagnosis, while accepting Fixed by its own absolute criteria. Any relative degradation budget requires its own approved threshold; none is invented here.
7. Preserve per-CPI seed/identity/input hash, source-class checks, stage/overflow telemetry, decision/denominator, scoring and CI inputs, software versions/runtime, command, logs and a declared raw-data retention policy. Unexpected clipping/overflow or source invalidity must follow the frozen contract and cannot be silently discarded/replaced; report FAIL/INCONCLUSIVE with the original fixed denominator as applicable.
8. Execute only after separate engineer authorization, in an isolated workspace without changing the stable implementation. First qualify the exact bit-true model at model level, then use stage-appropriate RTL/board correspondence evidence. Sending all20,000CPIs over UART is not automatically required for model-level S04 qualification and is not authorized here.
9. Record results as PASS, FAIL or INCONCLUSIVE under the approved protocol, then seek engineer acceptance. Keep separate confidence statements for Pfa/Pd; these are not automatically a joint95% statement. Broader clutter/SCR, off-bin, multiple-target or dynamic-range populations require a separate declared scope/coverage and cannot be inferred.

## Decision needed next

Choose the numerical baseline and authorize preparation/review of a locked statistical protocol. Recommended: final FFT-IP bit-true path with the limited S03-like population above. Approval of the protocol and bounded execution remains outstanding. Existing Gate-S04 owner closure is preserved; this open technical item is not erased or used to reopen that historical decision automatically.

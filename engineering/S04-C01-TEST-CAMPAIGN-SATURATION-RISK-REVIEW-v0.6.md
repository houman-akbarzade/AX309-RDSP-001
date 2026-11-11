# AX309-RDSP-001 | S04-C01 Campaign Saturation Risk Review v0.6

**PROPOSAL ONLY. S04-C01 HOLD; C02 OPEN; Gate-S04 OPEN. S04 0%, overall 25%.** No g, risk ceiling, A/B format, FFT shifts, or Float/Fixed tolerance approved; no CPI, accepted Pfa/Pd seed, RTL, hardware or main statistical test used.

## Exact saturation and campaign model

Q1.15 round-nearest-even saturation thresholds are input component x >= g*65535/65536 or x < -g*65537/65536. For independent noise CN(0,1), each real component is N(0,1/2). If p(g) is one-component tail probability, then the per-CPI saturation risk is q=1-(1-p)^8448. With independent identically distributed CPI and constant q, **P_stop(N)=1-(1-q)^N=1-(1-p)^(8448*N)**.

The formula assumes independence and the specified Gaussian population; it is not a general radar or clutter conclusion.

| g candidate | q per CPI | P_stop N=1000 | P_stop N=20000 | reconstructed LSB g/32768 |
|---|---:|---:|---:|---:|
| 1 | ~1 | ~1 | ~1 | 3.05176e-5 |
| 2 | ~1 | ~1 | ~1 | 6.10352e-5 |
| 3 | .1702432 | ~1 | ~1 | 9.15527e-5 |
| 4 | .00013023653 | .1221196864 | .9260894895 | .000122070 |
| 5 | 1.298846e-8 | .00001298838 | .00025973555 | .000152588 |
| 6 | 1.817988e-13 | 1.817988e-10 | 3.635977e-9 | .000183105 |
| 8 | 9.482304e-26 | 9.482304e-23 | 1.896461e-21 | .000244141 |

All values are probabilities from 0 to 1, NOT percentages. These are analytical, not measured. Complete source mean classes (noise-only, fixed Pd-like, two illustrative deterministic clutter offsets), two campaign lengths and seven gains appear in accompanying JSON, including log10 tiny tail probabilities. No historical accepted CPI was generated or accessed.

## Three proposed whole-campaign limits (not approved)

| Proposed P_stop bound | Theoretical minimum continuous g, 1000 CPI | g, 20000 CPI | Smallest candidate in comparison grid |
|---|---:|---:|---:|
| 10% | 4.025665 | 4.372997 | 5 |
| 1% | 4.300362 | 4.628035 | 5 |
| 0.1% | 4.554709 | 4.865973 | 5 |

g=5 passes these hypothetical noise-only limits but **is not approved**. A gain that reduces clipping also increases stored-domain quantization step and decreases weak-signal precision.

## Weak-signal reconstruction tradeoff

For unsaturated components, delta=g/32768, absolute reconstruction error <=g/65536; hypothetical *uniform* quantization RMS is delta/sqrt(12) (not certified). At g=4,5,6,8, the LSB is respectively 1.22070e-4, 1.52588e-4, 1.83105e-4 and 2.44141e-4. A component of magnitude .0001 has 0.819, 0.655, 0.546, 0.410 LSB units respectively; at g=8 it may round to zero. This is scalar quantizer resolution, NOT a radar Pd conclusion. Under an additional uniform error model, complex quantization noise power is delta²/6, not a proven SNR degradation.

## Correlated and heterogeneous campaigns

If CPI saturation marginals are heterogeneous but CPI independent, P_any=1-PROD_i(1-q_i). Without independence, **max_i q_i <= P_any <= min(1,SUM_i q_i)**; a conservative union upper bound uses sum of certified marginal upper bounds. Correlated clutter can invalidate the within-CPI independent-component formula itself. No correlated clutter/general multi-target claim is made.

## Numerical exception vs stochastic event

Clipping is a deterministic numerical distortion when it happens, while an unbounded Gaussian source gives a nonzero prospective statistical risk of that event. Campaign-stop risk is an operational design measure, **not authorization to delete or replace CPI**.

Proposed alternatives requiring separate engineering approval: (i) strict no-clipping performance campaign, stop and INCONCLUSIVE on first unexpected clip, preserve fixed N and all sample identities without replacement; (ii) separately declared saturation-tolerant population with prospective all-CPI denominator and measurable clip/accuracy targets; (iii) deliberate overload STRESS_ONLY graded on flags/counters, excluded by predeclared design from performance. None is executable under this authorization.

## Proposed policy — not approved

Maintain CONFIGURABLE rational pre-CPI gain with immutable per-CPI profile/scale metadata. Compare g candidates {4,5,6,8} for noise-only saturation versus resolution, with {1,2,3} as diagnostic cases. The future deterministic rule may choose the **smallest approved rational g** satisfying BOTH an approved whole-campaign risk upper bound for declared class/N and an approved weak-signal resolution limit; if either is absent or no profile qualifies, do not start. Historical Pfa/Pd seeds remain excluded from development and acceptance retuning.

## Can C01 be separately approved without C02?

**Yes in principle, conditional on limiting C01 to source baseline, input population, scaling/normalization, Q1.15 interface, clip-risk/metadata, Float-domain reconstruction and fixed validation rules.** Internal MF/FFT word widths, twiddle precision, FFT shift schedule, CFAR coefficient quantization and final stagewise Float/Fixed error budgets belong to C02/C06. **But C01 is still HOLD:** approved admitted clutter/target envelopes, campaign risk level, g allowlist, minimum signal resolution, and performance/stress/invalid policy are missing.

| C01 trace | Evidence | Review state |
|---|---|---|
| Source S02/S03 and Q1.15 exact thresholds | Frozen v0.2/v0.3, 20 exact threshold checks | REVIEWABLE |
| Noise-only campaign probability, two N | v0.5 and v0.6 independent erfc checks | REVIEWABLE, this Gaussian model only |
| Fixed Pd-like and illustrative clutter | Analytic deterministic means only | LIMITED, not performance qualification |
| Correlated clutter/multi-target admission | Unknown covariance/envelope | OPEN |
| Campaign stop risk and minimum resolution | Three proposed ceilings, quantified tradeoff | OPEN, approval required |
| Approved g registry and pre-CPI selection | Candidate grid and v0.4 metadata | OPEN |
| Valid/INCONCLUSIVE/STRESS rules | Proposed alternatives, no sample replacement | OPEN |
| Stage Float reconstruction and metadata | v0.3 120 boundary checks | REVIEWABLE |
| Internal fixed-point/FFT/final error budgets | C02/C06 not approved | OPEN but separable from a bounded C01 contract |
| C01 independent sign-off | Not granted | HOLD, zero progress credit |

## Evidence and restrictions

Script engineering/s04_numeric/saturation_campaign_review_v06.py; machine-readable data engineering/s04_numeric/S04-saturation-campaign-analytic-v0.6.json; six deterministic regression tests in tests/test_s04_saturation_campaign_v06.py. The first draft of one test failed on the valid q=1 boundary because of log1p(-1); the **test only** was corrected and all 6 tests PASS. Fourteen independent closed-form erfc comparisons passed. Neither script imports the S03 CPI generator or invokes RNG.

Keep v0.3, v0.4 and v0.5 records, 4135 extra unmatched clusters (not Pfa), missing archived full IQ/RD power arrays, and earlier statistical failures as historical risks. S04-C01 HOLD, C02 OPEN, S04 0%, overall 25%.
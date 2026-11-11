# AX309-RDSP-001 | S04-C01 CONFIGURABLE INPUT POLICY — QUANTITATIVE DECISION REVIEW v0.5

**Status: REVIEW-READY PROPOSAL / S04-C01 HOLD; S04-C02 OPEN; Gate-S04 OPEN.** An engineer accepted the CONFIGURABLE INPUT POLICY approach for design comparison, not a value of g or any numerical contract. S04 progress 0/8=0%, project 25%. No accepted S03 seeds, CPI generation, main statistical trial, RTL, synthesis, board or hardware tests.

## 1. Traceability matrix of input class prerequisites

| Requirement ID / class | Bound/physical scale | Noise model | Target signal | Clutter | Qualification state |
|---|---|---|---|---|---|
| C01-IN-01 NOISE_ONLY_UNIT | Unbounded Gaussian Float input pre-Q1.15; 33x128 complex; unit normalized amplitude | E|w|²=1, independent real/imag N(0,1/2), independent samples conditional on class | Absent | Absent | Source-defined model **AVAILABLE**; allowable CPI clipping risk and g remain **OPEN** |
| C01-IN-02 PD_REFERENCE_LIKE | Unbounded Gaussian Float plus deterministic reference target; quantizer admission separate | E|w|²=0.000324, component σ²=0.000162, independent | One LFM echo at delay k40, +4 Doppler bin, amplitude .18, phase 0; 16 samples/pulse | Absent | Source-defined design class **AVAILABLE**, but no replay of accepted Pd test; g and future acceptance corpus **OPEN** |
| C01-IN-03 TARGET_MULTIPLE | Envelope/peak constraint and coherent sum gain not defined | Noise variance and covariance unknown | Number/amplitudes/range-Doppler/phase envelope unknown | Unspecified | **OPEN / INADMISSIBLE FOR QUANTIFIED CPI RISK** |
| C01-IN-04 CLUTTER_STOCHASTIC | Crest and calibration unknown | Noise/clutter correlation law unknown | Target/background overlaps unknown | Marginal law, spatial/pulse correlation and deterministic means unknown | **OPEN / INADMISSIBLE FOR QUANTIFIED CPI RISK** |
| C01-IN-05 CLUTTER_SENSITIVITY_ONLY | Fixed illustrative offset +0.8 or +1.2 real amplitude | E|w|²=.000324 independent components | Same deterministic single target as C01-IN-02 | Uniform deterministic real offset in all 33x128 samples, NOT real radar clutter distribution | **ANALYTIC ILLUSTRATION ONLY**, not approved scenario or general clutter qualification |
| C01-IN-06 SATURATION_STRESS | Explicit deliberately overflowing source vectors | Not a stochastic performance noise model | Optional hand-set test content | Optional hand-set test content | Candidate **STRESS_ONLY**, not in Pd/Pfa performance denominators |

No source S03 Pfa/Pd historical observation is treated as evidence of fixed-point detection performance. For correlated clutter, p(any) requires joint distribution or a conservative union bound; using the independent product formula would be unsupported.

## 2. Exact Q1.15 RNE saturation and probability model

For positive rational g selected before any CPI data, each Float real component x is mapped to:
  q = sat_signed16(RNE(32768*x/g)), reconstructed xhat=g*q/32768.
Strict prospective input saturation occurs at x>=g*(65535/65536), OR x<-g*(65537/65536). Note the upper boundary is inclusive and lower exclusive for ties-to-even.

For independent Gaussian real components Xi with deterministic mean mu_i and common standard deviation σ=sqrt(E|w|²/2), define Li=-g*65537/65536 and Ui=g*65535/65536. Then:
  p_i = Φ((Li-mu_i)/σ) + Φ((mu_i-Ui)/σ).
  E[number saturated]=Σ_i p_i, 0<=Σ_i<=8448.
  Pr(at least one saturation)=1-Π_i(1-p_i) for **conditionally independent** real/imag components.
This probability is computed using Gaussian tail functions, stable logarithmic summation and independent erfc-based crosschecks for the centered unit-noise class. No random draws. Thresholds are quantizer arithmetic, not the approximate |x|>g tail used in v0.2.

### Analytical candidate scale grid (NO g selected)

| g | NOISE_ONLY_UNIT E[clipped components]/CPI | NOISE_ONLY_UNIT Pr(any)/CPI | Worst-case per-component unsaturated Float-domain abs quantizer error g/65536 |
|---|---:|---:|---:|
| 1 | 1328.863702 | ≈1 | 0.000015259 |
| 2 | 39.517505 | ≈1 | 0.000030518 |
| 3 | 0.1866205 | 0.1702432 | 0.000045776 |
| 4 | 0.0001302450 | 0.00013023653 | 0.000061035 |
| 5 | 1.298846e-8 | 1.298846e-8 | 0.000076294 |
| 6 | 1.817988e-13 | 1.817988e-13 | 0.000091553 |
| 8 | 9.482304e-26 | 9.482304e-26 | 0.000122070 |

These are single-CPI conditional probabilities for 8448 independent real components; not extrapolated to a new 1000/20000-CPI acceptance population. A larger g reduces clipping but increases Float-domain LSB size Δ=g/32768 and input rounding error.

- PD_REFERENCE_LIKE at g=1: log10 E[clipped components] ≈-901.98 and log10 Pr(any)≈-901.98. Binary64 displays underflow as 0; it is **not** a mathematical exactly-zero probability.
- Illustrative deterministic +0.8 real offset and small Gaussian noise at g=1: E≈2.120076 clips, Pr(any)≈0.8853774.
- Illustrative deterministic +1.2 real offset and small Gaussian noise at g=1: E≈4221.6624 clips, Pr(any)≈1. They are sensitivity examples only. At g=2 their mathematical tails are extremely small, but neither case warrants a real clutter guarantee.

Full 4 classes × 7 candidate g values, exact thresholds, log-tail outputs and error scale factors are retained in analytical JSON.

## 3. Prospective risk tiers, resolution tradeoff (NONE binding)

| Proposed maximum Pr(any clipping)/CPI in NOISE_ONLY_UNIT | Continuous minimum theoretical g for this model | Worst-case component input error g/65536 | Illustrative RMS component quantization g/(32768√12) |
|---|---:|---:|---:|
| 10% | 3.089475 | 4.71416e-5 | 2.72172e-5 |
| 1% | 3.434665 | 5.24088e-5 | 3.02583e-5 |
| 0.1% | 3.744768 | 5.71406e-5 | 3.29902e-5 |
| 0.01% | 4.031956 | 6.15228e-5 | 3.55202e-5 |
| 0.0001% | 4.554762 | 6.95002e-5 | 4.01259e-5 |

The continuous inverse-Gaussian risk values are computed numerically from exact Q1.15 thresholds and the 8448-component model, **not an approved device profile**. The RMS column assumes uniform quantization error under a high-resolution independence approximation; it is NOT a certified or empirical RMS budget. The MAX column is conditional on no clipping. At the proposed 0.01% CPI risk tier, candidate g=4 does NOT qualify (Pr(any)≈0.0130%), while g≥4.031956 would be required under this specific model; no selection made.

## 4. Candidate g registry and deterministic selection rule (not approved)

Sensitivity grid G_candidate={1,2,3,4,5,6,8}. The user/engineer has NOT approved any of these values or a mandatory threshold. For a declared model class C, a prospectively approved finite allowlist G_allowed, an engineer-approved CPI risk limit ε and a verified source/correlation model M_C, the *candidate* deterministic rule is:

  g*=min{g∈G_allowed : certified upper bound Pr_C(at least one input clipping | g)≤ε}.

If a class, profile metadata, list, valid risk bound or proof is missing, no g is selected: state UNCONFIGURED, NOT g=1. Tie-breaker is the smallest rational g in numeric ascending order, with profile ID then registry version as stable audit keys; no access to current CPI samples, detected targets or postprocessing outcomes is allowed. If no allowed g satisfies ε, mark scenario **OPEN / NOT ADMITTED**, do not widen the list or adjust risk based on the test outcome. For correlated clutter, either predeclare a joint model or conservatively use a certified union bound Σ p_i when marginals are valid; do not silently use conditional independence. A future profile registry must pin the analytic calculator, input class versions, all selected rational gains and immutable SHA metadata before independent data is generated.

No candidate g is approved by tabulating these outcomes. The prospective selection method itself still requires explicit engineering approval.

## 5. Proposed CPI dispositions and fixed denominators

- **VALID_PERFORMANCE (future):** input population and frozen profile approved BEFORE test; g, source/type, byte dimensions, SHA and stage-scale metadata correct; exact input conversion; no unexpected input clipping or internal arithmetic overflow under zero-clipping admission; no missing data; all required numeric traces and validity flags present; CPI counted once in a prospectively declared fixed-N denominator.
- **INCONCLUSIVE:** unapproved/missing g or metadata, wrong class, corrupted frame, unexpected saturation, arithmetic overflow or missing/out-of-range intermediate stage, broken reconstruction or invalid acquisition; record failing CPI index, processed count and cause; STOP the whole fixed-N acceptance procedure. No removal/replacement or automatic rerun; never report a PASS/FAIL acceptance result on a truncated sample.
- **STRESS_ONLY:** deliberately injected overload vector from separately approved stress corpus; compare saturation event count/locations and status against its own arithmetic oracle, exclude completely from performance acceptance denominator.
- **Denominator freeze:** N, strata, sample identities, inclusion requirements, tolerance, intended clip-risk class and acceptance rule fixed BEFORE testing. No posterior denominator change, optional stopping, reweighting, scenario switching, gain retune or using 411091704/411091703 for development.

CPI zero-clipping VALID rule is a *proposed strict performance policy*, not a guarantee of 100% yield when admitted Pr(any)>0. Engineers must decide in advance whether nominal saturations cause an INCONCLUSIVE study or lead to a separately designed alternate performance metric; no automatic exceptions.

## 6. S04-C01 requirements decision matrix

| ID | Criterion | Current evidence | Proposed review verdict |
|---|---|---|---|
| C01-R01 | S02/S03 source traceability and 33x128/Q1.15 boundary | Frozen v0.2/v0.3 audits, source hashes, Gate-S03 | READY FOR ENGINEERING ACCEPTANCE (not approved) |
| C01-R02 | Accurate asymmetric Q1.15 RNE thresholds | v0.3 20 boundary assertions | READY FOR ENGINEERING ACCEPTANCE |
| C01-R03 | Quantitative unit-noise/Pd conditional Gaussian risk | New 4-class/7-g analytic grid, independent 7 erfc crosschecks, new 7 unit tests | READY for specified analytical classes; external population claims NOT approved |
| C01-R04 | Validated target/multi-target/clutter admission envelopes | Missing real clutter covariance/dynamic range, no approved test domain | OPEN |
| C01-R05 | CPI risk limit and g allowlist | 5 candidate tiers and 7 candidate g only | OPEN — explicit engineer decision |
| C01-R06 | Deterministic pre-CPI profile selection | Defined minimum-g candidate rule; no approved registry or joint clutter proof | OPEN |
| C01-R07 | Explicit gain metadata and reconstructed domain | v0.4 JSON Schema/proposal, v0.3 120 boundary checks | READY for technical review; wire ICD OPEN |
| C01-R08 | CPI status and saturation event trace | Proposed VALID/INCONCLUSIVE/STRESS_ONLY rules, archive and checks | OPEN for prospective engineer policy approval and numeric proof |
| C01-R09 | Float/Fixed numeric and decision error budgets | No approved twiddle/FFT/word width or certified errors | OPEN, belongs also to C02/C06 |
| C01-R10 | Independent DEV/ACCEPT corpus and execution gates | Separation and source lock specified, no new data | OPEN for independent validation design approval |
| C01-R11 | Immutable audit trail and future conversations | append-only readback and hash verification, previous historical gaps reported | Partial; manual archive capture required, auto-capture NOT VERIFIED |
| S04-C01 | Final baseline audit criterion | Full evidence review and engineer decision pending | **HOLD / 0 credit** |
| S04-C02 | Fixed-point contract approval | No selected A/B, FFT shifts, numerical tolerance or scaling | **OPEN / 0 credit** |

## 7. Reproducibility and risk custody

Preserve v0.3 reports/analytic JSON, 176 arithmetic assertions and 8 tests and v0.4 decision package. New quantitative script uses only deterministic exact quantizer constraints, Gaussian normal CDF and an analytic deterministic target mean; no source stochastic generator, PCG64, SeedSequence or original accepted sample. Every future source code/run must first archive the exact user request and then log/verbatim final agent answer if accessible, verify unique role/source refs, SHA and event joins, and state the historical gaps honestly. This operational requirement is distinct from an unimplemented automatic capture integration.

Carried risks unchanged: Pd fixed single on-bin SNR20 only; 4135 extra target-present clusters NOT Pfa; no complete original IQ/power arrays archived; old Student-t/spatial FAIL kept; Float vs Fixed threshold flips, saturated input and unknown hardware timing/resource estimates OPEN.

**Engineering disposition:** the configurable policy remains selected for *design study only*, with no g, input risk tier, A/B format, FFT shifts, numeric tolerance, C01 completion or Gate-S04 approval. S04 progress 0%, total project 25%.

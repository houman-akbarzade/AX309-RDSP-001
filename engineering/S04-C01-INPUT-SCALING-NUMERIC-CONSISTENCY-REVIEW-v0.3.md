# AX309-RDSP-001 — S04-C01 Input Scaling and Numeric Consistency Review v0.3

**Engineer authorization:** S04-C01 HOLD / INPUT SCALING DESIGN REVIEW AUTHORIZED.
**Verdict:** DESIGN ANALYSIS COMPLETED; S04-C01 remains HOLD, S04 numeric contract NOT APPROVED. No scale, A/B selection, FFT shifting policy, numerical error acceptance limit, RTL or hardware choice approved. S04 0/8=0%; overall project 25%; Gate-S04 OPEN. No acceptance corpus or reserved S03 Pfa/Pd seed was consumed, and no radar CPI was generated.

## 1. Exactly defined quantizer and input relation

Let original Float complex input be x = I+jQ, and let g>0 be the *declared input division factor*. Each real component is independently represented:
  q = SAT16(RNE(32768*x_component/g)),
  xhat_component = g*q/32768.
where RNE is nearest-integer, exact half-integer chooses the EVEN integer, including negative values. The input representation is signed two's-complement Q(16,15), pulse-major little-endian I then Q (16,896 B/CPI), with frozen metadata for g and input admission policy. The signal unit is normalized sample amplitude, not calibrated volts; power is normalized amplitude squared.

**Exact pre-clipping quantizer boundaries:**
- Upper first clipping event: x_component/g >= 65535/65536 = 0.9999847412109375. At the half-LSB tie, raw 32768 is even and out of range.
- Lower first clipping event: x_component/g < -65537/65536 = -1.0000152587890625. At the exact tie, RNE returns even -32768, still valid.
- Therefore real source boundaries are g*(65535/65536) inclusive above and -g*(65537/65536) exclusive below. The threshold asymmetry is a real effect of RNE and the two's-complement endpoints.
- For unsaturated conversion, each real/imag reconstruction error <= g/65536, and complex magnitude error <=sqrt2*g/65536. The bound excludes coefficient/DSP errors and clipping.
- With g>1, the smaller integer input magnitude raises the reconstructed Float-domain quantization step to g/32768. This trades fewer saturation events against lower weak-signal resolution.

## 2. Three input populations, with analytical saturation results

A CPI has 33*128=4224 complex samples, i.e. 8448 real Gaussian component observations. For a deterministic mean mu_i and independent real/imag Gaussian noise variance sigma²/2, define for component i:
  u_g=g*(65535/65536), l_g=-g*(65537/65536).
  p_i(g)=Pr(X_i>=u_g)+Pr(X_i<l_g)
        =Phi((mu_i-u_g)/sigma)+Phi((l_g-mu_i)/sigma).
Expected saturations E[C]=SUM_i p_i. Under independent noise components *conditional on deterministic means*, Pr(C>=1)=1-PROD_i(1-p_i). Neither expected count nor Pr(any) requires radar simulation. For stochastic correlated clutter, the product formula is NOT valid without conditioning and specifying its joint law; E[C] remains sum of marginal exceedance probabilities when defined.

### Observations for candidate scales (NO scale approved)

| Source scenario | g | E[clipped I/Q components per CPI] | Pr(at least one clipped component) |
|---|---:|---:|---:|
| Noise-only CN(0,1) | 1 | 1328.863702 | effectively 100% |
| Noise-only CN(0,1) | 2 | 39.517505 | effectively 100% |
| Noise-only CN(0,1) | 4 | 0.0001302450 | 0.0001302365 (0.01302365%) |
| Noise-only CN(0,1) | 8 | 9.48230e-26 | 9.48230e-26 |
| Pd fixed single on-bin target amplitude 0.18, SNR20, sigma²=0.000324 | 1 | log10(E)=-901.9848 | log10(Pr(any))=-901.9848 |
| Pd fixed single on-bin target amplitude 0.18, SNR20, sigma²=0.000324 | 2 | log10(E)=-4441.0631 | log10(Pr(any))=-4441.0631 |

In the Pd lines, decimal probabilities underflow to zero in binary64; log10 values preserve the theoretical tiny tails. The deterministic means were computed analytically from the S03 midpoint chirp, target delay k=40, Doppler bin +4 and pulse phase. This is **not an execution of the accepted Pd trial**, not a rerun or new stochastic CPI.

To demonstrate heterogeneous target/clutter conditions without pretending to specify a clutter probability law, two **illustrative deterministic** uniform clutter offsets were added to the same analytic Pd mean, retaining the same independent Gaussian variance:
- +0.8 real-amplitude clutter at g=1: E[clips]=2.120076, Pr(any)=0.8853774. At g=2, log10(E)=-1395.9137.
- +1.2 real-amplitude clutter at g=1: E[clips]=4221.662398, Pr(any) effectively 1; at g=2, log10(E)=-516.3703.
These offsets are sensitivity examples, not approved real-world SCR cases or randomly simulated clutter. For arbitrary multi-target/clutter amplitude and correlation, the full deterministic means, input noise and joint conditional model must be specified first; there is no single universal saturation probability.

## 3. Three input admission and scaling policies — proposal only

| Alternative | Mechanism | Advantages | Risks, evidence and replay impact |
|---|---|---|---|
| FIXED g | Freeze one g before dataset design, apply to all full CPIs in the declared population | Identical binary-point meaning, simplest records and hardware, predictable physical scale | Can overclip noise-only or waste precision for small-SNR-target scenes; one universal g must cover declared input admission with a predeclared risk bound; every run has frozen g and source SHA |
| CONFIGURABLE g | Engineer-approved set of g values, selected by metadata before each CPI/batch, no lookahead at reserved test results | Allows noise and target/clutter dynamic-range envelopes, supports compare/reconstruct per CPI, straightforward calibration management | g must be pre-selected based on allowed metadata, logged per CPI and used by host/FPGA at all stage boundaries; wrong/missing/changed g invalidates result; acceptance datasets must specify strata/g and their weights in advance |
| ADAPTIVE g | A fully specified detector derives g from input block/max/RMS and encodes exponent/scale metadata | Can reduce clipping over varying amplitudes, exploit representable dynamic range | Depends on sample values; changes admitted population and quantizer noise/error, requires buffering or equivalent causal/streaming policy; can couple gain and target/clutter statistics. Requires new independent qualification and predetermined method/flags; never select algorithm from accepted Pfa/Pd corpus |

For configurable/adaptive policies: serialize scale as exact rational or pinned binary representation, record its derivation/selection version, per-CPI ID, chosen g, header and stage metadata hashes. Ensure Float comparison uses the original unscaled reference x, not x/g by accident. Never infer g from accepted Pfa/Pd outcomes after the fact.

## 4. Complete stored-domain and reconstructed-domain correction for v0.2

Stage stored integer q represents stored-domain real z=q*2^-F. The *original Float-domain reconstruction* is x_reconstructed = S_total * z. The prior contract v0.2 listed FFT and power stage scales assuming **g=1**; with an input division g, these factors must be corrected.

| Boundary | A: reconstruction factor | B: reconstruction factor | Quantity / rule |
|---|---|---|---|
| B00 Float original | 1 | 1 | source reference amplitude |
| B01 quantized IQ | g | g | normalized input amplitude |
| B02 coefficients | 1 | 1 | dimensionless MF coefficients |
| B03 MF | g | g | output of linear matched filter in original sample-amplitude units |
| B04 MTI | g | g | signed amplitude (linear difference) |
| B05 FFT | g | 8g | signed complex Doppler amplitude; B shift total /8 |
| B06 RD power | g² | 64g² | power: square of amplitude factor |
| B07 sum40 | g² | 64g² | sum40 integer powers, common B06 unit |
| B08 average / threshold | g² | 64g² | mean40 and alpha times mean; alpha dimensionless |
| B09 CFAR mask | not scaled | not scaled | exact Boolean strict decision for quantized powers |
| B10 peak power | g² | 64g² | reported peak power reconstructed to source reference units |
| B11 normalized input target amplitude | g | g | if represented from input; do not confuse with FFT-bin amplitude |
| B11 range / Doppler label | 1 | 1 | meters and m/s are not rescaled by input gain |
| B12 output metadata | serialized g and stage scales | serialized g and stage scales | not an arithmetic signal quantity |

**Example B at g=4:** stored FFT complex values reconstruct using 32, while stored power, 40-training sum and threshold reconstruct using 1024. If the FFT stores real/imag integer qI,qQ at F=13, an *unrounded* stored power integer at F=26 equals qI²+qQ², and original reference-domain power is 1024*(qI²+qQ²)*2^-26. This does **not** prove that later narrowed hardware implementation equals the unrounded expression.

Under common positive power factor K=g²*S_FFT² and infinite exact arithmetic, CUT > alpha*mean is invariant to K; fixed-point rounding/clipping/alpha representation and near-threshold effects can break exact Float equivalence. Quantized alpha integer comparison remains 40*P*2^Fa > A*SUM40 if P and SUM40 are stored in the same binary scale. Strict equality is false; no hidden division rounding is allowed. The earlier 22 Fraction-vs-integer oracle checks remain historical separate evidence.

## 5. Saturation policy candidate, NOT APPROVED

Propose per-CPI record: saturated component count, at least one saturation flag, saturation index list (pulse, range, I/Q, positive/negative), first-event index, max unquantized magnitude and selected g; if an event list is truncated for storage, record truncation and a digest of the complete indexed event stream. At each MF/MTI/FFT/power/training stage also record stage ID, overflow/saturation count, sticky flag, and detector invalid status; counters must not silently wrap.

Predeclared status proposal:
- VALID_NUMERIC_PERFORMANCE only when expected input admission/scale metadata exists, no unexpected saturation/overflow, finite data and all stage unit conversions verify.
- VALID_SATURATION_STRESS_ONLY when clipping is deliberate for a separately designated saturation test; never combine that CPI with performance acceptance.
- INCONCLUSIVE on missing/changed g metadata, unapproved scale, corrupted/invalid CPI, unexpected clipping or arithmetic overflow during future fixed-vs-float performance qualification; stop and do not replace samples unless a separately approved protocol defines another rule.
- An intentional negative test that passes its *error-detection oracle* does not imply valid radar performance. Acceptance dataset exclusion rules and denominators MUST be frozen before any tests.

The C01 report does not choose which numeric performance domains admit any clipping or fix a maximum rate; these require independent engineer approval. No parameter optimization is permitted using accepted Pd seed 411091704 or Pfa seed 411091703.

## 6. Independent checks executed under analysis authorization

- Exact Fraction quantizer boundaries, RNE signed half-LSB and reverse decode for g=1/4: 20 assertions.
- A/B stored vs reconstructed FFT-complex, power, and strict integer-vs-rational CFAR checks for g=1/4/8: 36 assertions.
- Full boundary scale metadata propagation and unit consistency for 13+ boundaries in A and B with g=1/2/4/8: 120 assertions.
- **176 deterministic assertions** in engineering/s04_numeric/input_scaling_analysis_v03.py.
- Independent unittest suite with 8 selected deterministic tests: PASS. It crosschecks CN(0,1) probability using math.erfc (independent of the vectorized scipy.special implementation) and tests source Pd deterministic means without any noise draw.
- Inputs are mathematical constants and analytic means only; no model.generate_cpi, noise_only_cpi, PCG64, SeedSequence, reserved acceptance data, RTL or hardware.

The output JSON provides probabilities including log10 tiny tails, exact threshold ratios, g options and all boundary reconstruction scales. Both files are hash-registered in the evidence manifest.

## 7. Engineering decision needed before C01 release

1. Define allowed input populations, source normalization, g availability/metadata format, and admissible input-clipping status. Decide fixed/configurable/adaptive **without tuning on accepted data**.
2. Select a policy for future Float-vs-Fixed comparisons: original amplitude reference domain, exact stage scale S, and nonzero scaling/quantization effects.
3. Choose A/B/hybrid, FFT shifts and stage rounding only after separate assessment; then freeze numeric budgets, binding RMS/max, margin classification and sample-inclusion rules BEFORE qualification.
4. Independently review and approve C01; C02 requires its own numeric-contract approval. Both remain HOLD, S04 0%, overall 25%.

No approved S02/S03 artifact, historic Pfa/Pd result, or official progress/Gate file was modified by this review.

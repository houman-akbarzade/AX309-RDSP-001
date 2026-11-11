# AX309-RDSP-001 | S04-C02 Deterministic Integer Bit-True Prototype v0.5

**UNAPPROVED PROTOTYPE.** C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN, S04=12.5%, overall project=26.0416667%. No stochastic CPI, accepted S03 seed, RTL, synthesis or FPGA test.

## 1. Provenance, commands and environment

Sources: signed C01 bounded input contract, S03 frozen Float model (s03_reference/model.py), v0.2 A/B/C formats, v0.3 quantized MF and FFT twiddle tables, v0.3.1 CFAR widths, v0.4 conditional stagewise error model. Host interpreter /usr/bin/python3 version 3.14.4, NumPy 2.3.5, no dedicated repo virtualenv identified. All fixed arithmetic is Python arbitrary-precision integer arithmetic. Floats/NumPy occur only in deterministic original Float input creation, S03 Float reference outputs and error statistics; the fixed MF/MTI/FFT/power/SUM40/CFAR calculations contain no Float operations.

Reproduction from repository root:

    /usr/bin/python3 -B engineering/s04_numeric/s04_c02_integer_bittrue_v05.py
    /usr/bin/python3 -B engineering/s04_numeric/s04_c02_v05_stage_audit.py
    /usr/bin/python3 -B -m unittest discover -s tests -p test_s04_c02_integer_bittrue_v05.py -v

Complete execution and 14/14 unit-test logs are preserved in engineering/S04-C02-V05-INTEGER-RUN.log and engineering/S04-C02-V05-INTEGER-UNITTESTS.log. The first erroneous Float comparison at FFT stages omitted the inverse cumulative shift on the Float reference; this was corrected **before evidence freeze and prior to the final reported MAX/RMS**. No historical v0.4 baseline was changed.

## 2. Executed, but unapproved, integer contract

Input: C01 signed Q16.15 interleaved I/Q with exact RNE(2^15*x/g) and SAT16, reconstructed source xhat=g*q/2^15. Only approved profile values g=5 noise-only and g=1 laboratory single target are used as **scaling factors**. The deterministic patterns are NOT certified stochastic members of either approved statistical test population.

MF16: source order h[k]=conj(chirp[15-k]), full convolution output index r+15. For each tap, signed int input Q16.15 times signed candidate coefficient Q16.15 A/C or Q14.13 B. Compute four exact real products and form real Ir*hr−Ii*hi, imaginary Ir*hi+Ii*hr. Full product signed width=16+Wcoef, pair width=product+1, full 16-tap signed accumulator width=product+5 at fractional precision 15+Fcoef. Round only once with integer rational RNE to MF output (A/C 22/15, B20/13); guard every multiplication, pair, raw sum and output before limiting.

MTI2: exact difference between MF[p+1] and MF[p], signed raw subtraction width Wmf+1, then output signed A/C23/15 or B21/13 with separate pre-narrow guard and candidate single RNE.

FFT32: S03 negative-exponential forward unnormalized FFT, input pulse bit reversal and five radix2 DIT stages. For each butterfly calculate t=what*v with four exact signed integer real products, plus=u+t and minus=u−t at aligned fractional precision; exact division by 2^s followed by one integer RNE per output component. Twiddle A/C Q16.15, B Q14.13. Candidate stage output A28/15, B23/13, C25/15. Full real twiddle product width Winput+Wtwiddle, signed complex real pair product width +1; aligned u has Winput+Ftwiddle; pre-shift butterfly conservative width max(pairW,alignedUW)+1. The implemented candidate guards all these intermediate widths, logs overrange operands, and saturates only after recording output guard violations. **No silent wrap.** This is a specific mathematical prototype, not a final RTL scheduling choice.

For negative integers raw arithmetic right shift is not equivalent to RNE, e.g. -1>>1=-1 but RNE(-1/2)=0. Rounding before addition differs from rounding after full-precision addition. All policies remain candidates.

## 3. Deterministic vectors, audit status and no post-hoc exclusion

Nine deterministic rational vector formulas produce 33x128 complex samples: zero, isolated impulse, positive signed maximum, negative signed minimum, near upper/lower clip edge, positive/negative half-LSB ties, alternating pattern, quadrature phase interference and deliberate overrange stress. Each is evaluated with both approved g scalars; the independent vector manifest contains 18 full-formula source hashes and example rational coordinates. This generates **18 deterministic runs for each of 12 architectures/schedules = 216 full arithmetic executions**. This is not a stochastic CPI acceptance campaign; no Pfa/Pd inference is possible.

Every vector remains in the JSON. Overrange stress saturates all 8448 input I/Q components by construction. Further FFT and power overflow events are recorded by stage, sign, original unbounded integer value, range/Doppler index, total count and an ordered SHA-256 event digest. For v0.4 comparisons, **no-input/no-intermediate-saturation cases** and stress/saturated cases are shown separately; this is a prospectively defined mathematical bound applicability condition, never a deletion or retry.

## 4. MAX/RMS comparison, 12 candidate combinations

Observed complex amplitude errors are reconstructed to the **original normalized Float source units**, using g times cumulative FFT inverse-shift. The MAX and RMS of the eligible cases are distinct from statistics including all stress cases. All values are observed on deterministic vectors, NOT statistically meaningful expected RMS. Memory is a full hypothetical 128×32 complex FFT buffer bit proxy from v0.2, not measured BRAM/FF utilization.

| Candidate | FFT shifts | eligible/18 | MAX eligible | RMS eligible | MAX all incl. stress | RMS all | internal saturation events | v0.4 7-stage bound check | FFT buffer bits proxy |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| A | [0, 0, 0, 0, 0] | 16/18 | 0.263869 | 0.0126836 | 416.403 | 16.5652 | 0 | True | 229376 |
| A | [1, 1, 1, 0, 0] | 16/18 | 0.267411 | 0.0126997 | 416.407 | 16.5651 | 0 | True | 229376 |
| A | [0, 1, 0, 1, 1] | 16/18 | 0.265579 | 0.0126626 | 416.405 | 16.5652 | 0 | True | 229376 |
| A | [1, 1, 1, 1, 1] | 16/18 | 0.268331 | 0.0127501 | 416.408 | 16.5651 | 0 | True | 229376 |
| B | [0, 0, 0, 0, 0] | 14/18 | 0.366927 | 0.0160795 | 442.681 | 18.1472 | 932 | True | 188416 |
| B | [1, 1, 1, 0, 0] | 16/18 | 1.04863 | 0.0488027 | 417.18 | 16.594 | 0 | True | 188416 |
| B | [0, 1, 0, 1, 1] | 16/18 | 1.042 | 0.0486428 | 417.173 | 16.5943 | 0 | True | 188416 |
| B | [1, 1, 1, 1, 1] | 16/18 | 1.05197 | 0.0489699 | 417.184 | 16.5938 | 0 | True | 188416 |
| C_hypothetical | [0, 0, 0, 0, 0] | 14/18 | 0.0976146 | 0.00442064 | 442.417 | 18.1355 | 944 | True | 204800 |
| C_hypothetical | [1, 1, 1, 0, 0] | 16/18 | 0.267411 | 0.0126997 | 416.407 | 16.5651 | 0 | True | 204800 |
| C_hypothetical | [0, 1, 0, 1, 1] | 16/18 | 0.265579 | 0.0126626 | 416.405 | 16.5652 | 0 | True | 204800 |
| C_hypothetical | [1, 1, 1, 1, 1] | 16/18 | 0.268331 | 0.0127501 | 416.408 | 16.5651 | 0 | True | 204800 |

**Bound check:** for every candidate and shift, v0.4 conditional stage bounds for MF, MTI and each of 5 FFT stages were compared to observed MAX after correct original-unit reconstruction. There were **zero violations on no-saturation cases**. No bound is asserted for clipped inputs or stages. A false universal theorem must not be inferred from finite vector testing.

**Overflow:** In the tested common-stage-width proxy, B and C with no FFT shift show output FFT stage5 and power clipping on near-clip input, including its g1 and g5 scaled manifestations, while A and the other candidate shift cases have no internal overflow on these vectors. B/C zero shift can be re-engineered with other internal widths, therefore this is not architectural rejection. These observations do not estimate probability of overflow under Gaussian or clutter input.

## 5. Fixed integer power and CA-CFAR

At signed FFT W and fractional F, compute raw nonnegative I^2+Q^2 exactly (2W+1 conservative width) then candidate narrowing to unsigned power U(Wp,2F); use exact integer sum of 40 training cells at the frozen S03 7x7 outer/3x3 guard geometry, range 3..109 and Doppler 3..28, total 2782 valid CUT, with unsigned SUM40 guard. Strict comparison after candidate narrowing: 40*Pcut*2^Fa > Aalpha*SUM40; equality is NO ALARM. Candidate alpha A/C=490007/2^16 and B=30625/2^12. The v0.3.1 corrected conservative narrowed L/R widths are A74/78, B61/65, C68/72 and raw full path A79/83, B65/69, C73/77. All integer products are computed exactly and checked against relevant conservative widths; no silent truncation or wrap. Independent Fraction test cases for CUT=Aalpha-1, Aalpha, Aalpha+1 at SUM40=40*2^Fa yield false/false/true. No Float-vs-bittrue CFAR acceptance margin or Pfa/Pd test has been authorized.

## 6. Decision barriers and evidence

REQ-SCR-01 and REQ-RNG-03 are binding OPEN S02 obligations, with C02 numerical design and C06 independent verification before Gate-S04. Do not infer absolute clutter target amplitudes, multiple-target phases or novel gain profiles. Historic S03 evidence unchanged.

OPEN: selection of A/B/C or shift schedule; real intermediate RTL operator scheduling, LUT/DSP/memory usage, certified Float-Fixed MAX/RMS budgets, hardware overflow counters/ICD, full 2D CFAR decision stability, independent stochastic performance qualification. The integer prototype's saturated vectors cannot support the v0.4 bounded error claim; even eligible observed MAX/RMS are limited to these deterministic patterns.

Artifacts: engineering/s04_numeric/s04_c02_integer_bittrue_v05.py, engineering/s04_numeric/s04_c02_v05_stage_audit.py, engineering/s04_numeric/S04-C02-deterministic-test-vectors-v0.5.json, engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json, tests/test_s04_c02_integer_bittrue_v05.py, and execution/test logs.

**C01 PASS BOUNDED | C02 OPEN | Gate-S04 OPEN | S04 12.5% | overall 26.04%.**

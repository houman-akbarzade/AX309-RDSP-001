# AX309-RDSP-001 | S04-C02 Coefficient Precision and FFT Shift-Schedule Review v0.3

**DESIGN ANALYSIS / NO APPROVAL.** C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN; S04 12.5%, overall 26.04%. No CPI, accepted S03 seed, RTL, synthesis or FPGA operation.

## 1. Exact signed/unsigned width correction
Signed Q(W,F) range: [-2^(W-F-1), 2^(W-F-1)-2^-F]. Unsigned U(W,F): [0,2^(W-F)-2^-F]. To cover a continuous symmetric real magnitude M>=0, set K=ceil(M*2^F) with exact rational arithmetic. Minimum positive-symmetric signed width W=max(2,1+bit_length(K)); unsigned nonnegative W=max(1,bit_length(K)). This is a conservative enclosure for continuous real signals; an already quantized integer set can require fewer bits if its extrema are known exactly.
Signed minimum -2^(W-1) is representable, +2^(W-1) is not; at power-of-two endpoints signed width needs one more bit than an unsigned integer of that magnitude. Previous v0.2 floating log2 formulas were numerically fragile near powers-of-two. Exact Fraction/integer tests validate boundary endpoints, negative/positive asymmetry and F=0,1,2,7,13,15,26,30. **No listed v0.2 ideal-stage minimum widths changed** after exact arithmetic verification: MF21/F15, MTI22/F15, FFT27/F15 unshifted or FFT22/F13 shifted8, power U52/F30, training sum U57/F30, shifted8 power U42/F26 and sum U47/F26. The v0.2 source/report is preserved unchanged.

## 2. Frozen S03 coefficient conventions
MF: 16 midpoint chirp samples, Fs=1 MHz, B=250 kHz; h=conjugate(reverse(chirp)), as frozen s03_reference/model.py. FFT: unnormalized forward 32-point negative-exponential FFT. Radix2 DIT stages m=2,4,8,16,32 use w=exp(-i*2*pi*j/m), j=0..m/2-1, with bit-reversed input ordering for natural output order. These reproduce the mathematical Float reference, not a prescribed RTL butterfly realization. 16 MF and 31 radix2 stage-twiddle occurrences are serialized in numerical JSON, including decoded coefficient integer pairs, component errors, phase errors and magnitude errors.
Candidate coefficient encoding: signed RNE separately per real/imag part with endpoint saturation. This rounding is proposed, NOT approved for coefficient/twiddle or internal arithmetic.

| Variant | MF coeff W/F | Twiddle W/F, candidate | MF max complex error | MF max phase error rad | max |MF coeff| | Twiddle max complex error | Twiddle max phase error rad | max |Twiddle| |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A | 16/15 | 16/15 | 1.4679484e-05 | 1.1905082e-05 | 1.0000142 | 3.0517578e-05 | 1.0605834e-05 | 1.0000116 |
| B | 14/13 | 14/13 | 7.4169839e-05 | 5.8135586e-05 | 1.0000267 | 0.00012207031 | 3.1231439e-05 | 1.0000658 |
| C_hypothetical | 16/15 | 16/15 | 1.4679484e-05 | 1.1905082e-05 | 1.0000142 | 3.0517578e-05 | 1.0605834e-05 | 1.0000116 |
Quantized Twiddle maximum modulus A/C ~1.00001157, B ~1.00006582; unit-modulus assumptions from v0.2 are not certified for these actual rounded coefficients. The signed +1 coefficient becomes the positive maximum representable value, not exact +1.

## 3. Quantized MF16 and MTI2 bounds, separate errors
For |IQstored|<=sqrt2 after approved input SATQ15 and candidate rounded taps hhat[k], triangle inequality gives |MF|<=sqrt2*SUM|hhat| and |MTI|<=2*sqrt2*SUM|hhat|, on an exact-complex-operations assumption. Coefficient-only MF error relative to ideal h is bounded by sqrt2*SUM|hhat-h|, distinct from internal multiply/accumulator rounding. The full raw real product of signed Q16.15 input and coefficient signed W/F uses 16+W bits (fraction 15+F), complex pair 17+W bits, exact 16-term pair accumulator 21+W bits before narrowing.
| Variant | sum |hhat| | MF magnitude bound | MTI magnitude bound | coefficient-only MF error | raw product bits | raw complex pair bits | raw 16-tap acc bits |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 15.999957 | 22.627357 | 45.254713 | 0.00021727398 | 32 | 33 | 37 |
| B | 15.999755 | 22.62707 | 45.25414 | 0.0010119858 | 30 | 31 | 35 |
| C_hypothetical | 15.999957 | 22.627357 | 45.254713 | 0.00021727398 | 32 | 33 | 37 |
Input Q1.15 error has a separate C01 budget. To claim bounded real MF/MTI implementation error, the exact product narrowing, rounding, saturation, post-accumulator and MTI-output bit widths must be independently fixed.

## 4. FFT five-stage shift schedules and conditional bounds
For stage j with quantized beta_j=max|what_j|, delta_j=max|what_j-w_j|, shift s_j=0/1: M_j<=M_(j-1)*(1+beta_j)/2^s_j, given exact complex multiplication/addition. At each stage the JSON records M_j, integer-exact minimum signed W for the proposal F, candidate W/F, remaining signed positive capacity, shift, twiddle error and the candidate one-output-RNE rounding bound. This uses the SAME candidate final FFT W/F at every stage as a sensitivity proxy; actual internal stage-specific widths are OPEN.

| Schedule | divide factor | FFT reconstructed amplitude at g5 / g1 | reconstructed power at g5 / g1 |
|---|---:|---:|---:|
| ALL_5 [1, 1, 1, 1, 1] | 32 | 160/32 | 25600/1024 |
| DISTRIBUTED_3 [0, 1, 0, 1, 1] | 8 | 40/8 | 1600/64 |
| EARLY_3 [1, 1, 1, 0, 0] | 8 | 40/8 | 1600/64 |
| ZERO [0, 0, 0, 0, 0] | 1 | 5/1 | 25/1 |

### ALL_5, stages 1–5, shifts [1, 1, 1, 1, 1]
| Variant | stage | shift | complex magnitude upper | required signed W | candidate W/F | positive capacity minus bound | post-stage RNE max component error |
|---|---:|---:|---:|---:|---|---:|---:|
| A | 1 | 1 | 45.254023 | 22 | 28/15 | 4050.7459 | 1.5258789e-05 |
| A | 2 | 1 | 45.254023 | 22 | 28/15 | 4050.7459 | 1.5258789e-05 |
| A | 3 | 1 | 45.254023 | 22 | 28/15 | 4050.7459 | 1.5258789e-05 |
| A | 4 | 1 | 45.254285 | 22 | 28/15 | 4050.7457 | 1.5258789e-05 |
| A | 5 | 1 | 45.254546 | 22 | 28/15 | 4050.7454 | 1.5258789e-05 |
| B | 1 | 1 | 45.251378 | 20 | 23/13 | 466.7485 | 6.1035156e-05 |
| B | 2 | 1 | 45.251378 | 20 | 23/13 | 466.7485 | 6.1035156e-05 |
| B | 3 | 1 | 45.252867 | 20 | 23/13 | 466.74701 | 6.1035156e-05 |
| B | 4 | 1 | 45.254357 | 20 | 23/13 | 466.74552 | 6.1035156e-05 |
| B | 5 | 1 | 45.255846 | 20 | 23/13 | 466.74403 | 6.1035156e-05 |
| C_hypothetical | 1 | 1 | 45.254023 | 22 | 25/15 | 466.74595 | 1.5258789e-05 |
| C_hypothetical | 2 | 1 | 45.254023 | 22 | 25/15 | 466.74595 | 1.5258789e-05 |
| C_hypothetical | 3 | 1 | 45.254023 | 22 | 25/15 | 466.74595 | 1.5258789e-05 |
| C_hypothetical | 4 | 1 | 45.254285 | 22 | 25/15 | 466.74568 | 1.5258789e-05 |
| C_hypothetical | 5 | 1 | 45.254546 | 22 | 25/15 | 466.74542 | 1.5258789e-05 |
### DISTRIBUTED_3, stages 1–5, shifts [0, 1, 0, 1, 1]
| Variant | stage | shift | complex magnitude upper | required signed W | candidate W/F | positive capacity minus bound | post-stage RNE max component error |
|---|---:|---:|---:|---:|---|---:|---:|
| A | 1 | 0 | 90.508046 | 23 | 28/15 | 4005.4919 | 1.5258789e-05 |
| A | 2 | 1 | 90.508046 | 23 | 28/15 | 4005.4919 | 1.5258789e-05 |
| A | 3 | 0 | 181.01609 | 24 | 28/15 | 3914.9839 | 1.5258789e-05 |
| A | 4 | 1 | 181.01714 | 24 | 28/15 | 3914.9828 | 1.5258789e-05 |
| A | 5 | 1 | 181.01819 | 24 | 28/15 | 3914.9818 | 1.5258789e-05 |
| B | 1 | 0 | 90.502756 | 21 | 23/13 | 421.49712 | 6.1035156e-05 |
| B | 2 | 1 | 90.502756 | 21 | 23/13 | 421.49712 | 6.1035156e-05 |
| B | 3 | 0 | 181.01147 | 22 | 23/13 | 330.98841 | 6.1035156e-05 |
| B | 4 | 1 | 181.01743 | 22 | 23/13 | 330.98245 | 6.1035156e-05 |
| B | 5 | 1 | 181.02338 | 22 | 23/13 | 330.97649 | 6.1035156e-05 |
| C_hypothetical | 1 | 0 | 90.508046 | 23 | 25/15 | 421.49192 | 1.5258789e-05 |
| C_hypothetical | 2 | 1 | 90.508046 | 23 | 25/15 | 421.49192 | 1.5258789e-05 |
| C_hypothetical | 3 | 0 | 181.01609 | 24 | 25/15 | 330.98388 | 1.5258789e-05 |
| C_hypothetical | 4 | 1 | 181.01714 | 24 | 25/15 | 330.98283 | 1.5258789e-05 |
| C_hypothetical | 5 | 1 | 181.01819 | 24 | 25/15 | 330.98178 | 1.5258789e-05 |
### EARLY_3, stages 1–5, shifts [1, 1, 1, 0, 0]
| Variant | stage | shift | complex magnitude upper | required signed W | candidate W/F | positive capacity minus bound | post-stage RNE max component error |
|---|---:|---:|---:|---:|---|---:|---:|
| A | 1 | 1 | 45.254023 | 22 | 28/15 | 4050.7459 | 1.5258789e-05 |
| A | 2 | 1 | 45.254023 | 22 | 28/15 | 4050.7459 | 1.5258789e-05 |
| A | 3 | 1 | 45.254023 | 22 | 28/15 | 4050.7459 | 1.5258789e-05 |
| A | 4 | 0 | 90.508569 | 23 | 28/15 | 4005.4914 | 1.5258789e-05 |
| A | 5 | 0 | 181.01819 | 24 | 28/15 | 3914.9818 | 1.5258789e-05 |
| B | 1 | 1 | 45.251378 | 20 | 23/13 | 466.7485 | 6.1035156e-05 |
| B | 2 | 1 | 45.251378 | 20 | 23/13 | 466.7485 | 6.1035156e-05 |
| B | 3 | 1 | 45.252867 | 20 | 23/13 | 466.74701 | 6.1035156e-05 |
| B | 4 | 0 | 90.508713 | 21 | 23/13 | 421.49116 | 6.1035156e-05 |
| B | 5 | 0 | 181.02338 | 22 | 23/13 | 330.97649 | 6.1035156e-05 |
| C_hypothetical | 1 | 1 | 45.254023 | 22 | 25/15 | 466.74595 | 1.5258789e-05 |
| C_hypothetical | 2 | 1 | 45.254023 | 22 | 25/15 | 466.74595 | 1.5258789e-05 |
| C_hypothetical | 3 | 1 | 45.254023 | 22 | 25/15 | 466.74595 | 1.5258789e-05 |
| C_hypothetical | 4 | 0 | 90.508569 | 23 | 25/15 | 421.4914 | 1.5258789e-05 |
| C_hypothetical | 5 | 0 | 181.01819 | 24 | 25/15 | 330.98178 | 1.5258789e-05 |
### ZERO, stages 1–5, shifts [0, 0, 0, 0, 0]
| Variant | stage | shift | complex magnitude upper | required signed W | candidate W/F | positive capacity minus bound | post-stage RNE max component error |
|---|---:|---:|---:|---:|---|---:|---:|
| A | 1 | 0 | 90.508046 | 23 | 28/15 | 4005.4919 | 1.5258789e-05 |
| A | 2 | 0 | 181.01609 | 24 | 28/15 | 3914.9839 | 1.5258789e-05 |
| A | 3 | 0 | 362.03218 | 25 | 28/15 | 3733.9678 | 1.5258789e-05 |
| A | 4 | 0 | 724.06855 | 26 | 28/15 | 3371.9314 | 1.5258789e-05 |
| A | 5 | 0 | 1448.1455 | 27 | 28/15 | 2647.8545 | 1.5258789e-05 |
| B | 1 | 0 | 90.502756 | 21 | 23/13 | 421.49712 | 6.1035156e-05 |
| B | 2 | 0 | 181.00551 | 22 | 23/13 | 330.99437 | 6.1035156e-05 |
| B | 3 | 0 | 362.02294 | 23 | 23/13 | 149.97694 | 6.1035156e-05 |
| B | 4 | 0 | 724.0697 | 24 | 23/13 | -212.06983 | 6.1035156e-05 |
| B | 5 | 0 | 1448.1871 | 25 | 23/13 | -936.18719 | 6.1035156e-05 |
| C_hypothetical | 1 | 0 | 90.508046 | 23 | 25/15 | 421.49192 | 1.5258789e-05 |
| C_hypothetical | 2 | 0 | 181.01609 | 24 | 25/15 | 330.98388 | 1.5258789e-05 |
| C_hypothetical | 3 | 0 | 362.03218 | 25 | 25/15 | 149.96779 | 1.5258789e-05 |
| C_hypothetical | 4 | 0 | 724.06855 | 26 | 25/15 | -212.06858 | 1.5258789e-05 |
| C_hypothetical | 5 | 0 | 1448.1455 | 27 | 25/15 | -936.14552 | 1.5258789e-05 |
Zero-shift B/C final-width-at-every-stage proxies fail at later stages (negative margins); A fits conditional twiddle growth. Other schedules fit these particular stage-output proxies but do not prove full intermediate-product overflow freedom.

### Separation of twiddle quantization and rounding errors
Under the explicitly hypothetical exact-products/one RNE per stage and exact MF/MTI arithmetic before output narrowing, complex error recursion is E_j<=((1+beta_j)E_(j-1)+delta_j*Mideal_(j-1))/2^s_j+sqrt2*2^(-F-1). Initial E_0 includes actual MF coefficient-only error, one MF output RNE and one MTI output RNE. Twiddle-only errors omit MF/MTI coefficient and operation rounding. Both are **conditional analytical envelopes**, not formally certified worst-case Float-to-fixed bounds or empirical RMS; additional internal butterfly product rounding, shifts, twiddle ordering or saturation invalidates this simplification.
| Schedule | A conditional error | B conditional error | C conditional error | twiddle-only A/B/C |
|---|---:|---:|---:|---|
| ALL_5 | 0.0040598783 | 0.016526115 | 0.0040598783 | 0.0034526504 / 0.013810884 / 0.0034526504 |
| DISTRIBUTED_3 | 0.015958982 | 0.064982281 | 0.015958982 | 0.013810602 / 0.055243536 / 0.013810602 |
| EARLY_3 | 0.016131617 | 0.065672869 | 0.016131617 | 0.013810602 / 0.055243536 / 0.013810602 |
| ZERO | 0.12713237 | 0.51770022 | 0.12713237 | 0.11048481 / 0.44194829 / 0.11048481 |
Schedules with equal net 3 shifts have identical physical reconstruction factor but different intermediate headroom and conditional rounding-error propagation; no FFT shift schedule selected.

## 5. Power and strict CA-CFAR full-width integer arithmetic
For W-bit signed FFT I/Q, full signed products need 2W bits; I²+Q² conservatively needs 2W+1 before narrowing. Exact sum of 40 nonnegative power words needs power W+ceil(log2 40) bits before narrowing. Strict candidate decision with alpha=A/2^Fa and same stored power scale on CUT and 40-cell SUM is 40*Pcut*2^Fa > A*SUM40. Equality gives NO alarm. Exact integer examples with SUM40=40*2^Fa and CUT=A-1,A,A+1 return FALSE,FALSE,TRUE. This does NOT qualify Pd/Pfa or near-threshold decision match against Float.
| Variant | 2W real square | 2W+1 I²+Q² | power W/F | sum40 W/F | comparison left/right conservative bits | alpha numerator / 2^Fa |
|---|---:|---:|---|---|---|---|
| A | 56 | 57 | 52/30 | 58/30 | 74/490065 | 490007/2^16 |
| B | 46 | 47 | 43/26 | 49/26 | 61/30674 | 30625/2^12 |
| C_hypothetical | 50 | 51 | 46/30 | 52/30 | 68/490059 | 490007/2^16 |

## 6. Cost and comparative numerical risks (pre-synthesis proxies only)
| Option | MF coeff bits | raw MF accumulator bits | full FFT buffer bits | full power buffer bits | FFT zero-shift proxy fits? | numeric risk and controller complexity |
|---|---:|---:|---:|---:|---|---|
| A | 512 | 37 | 229376 | 212992 | True | wide F15 with no FFT shift |
| B | 448 | 35 | 188416 | 176128 | False | narrow F13 and larger coefficient errors |
| C_hypothetical | 512 | 37 | 204800 | 188416 | False | retains F15 with three shifts |
A 32-point radix2 FFT has 5x16=80 complex butterfly computations per transform; MF has 16 complex products per output, each optionally four real products; sum40 can be computed with 39 additions without reuse. These are operation counts, NOT instantiated multipliers, LUT/FF/DSP48/BRAM usage, measured timing, throughput or synthesis area. Real memory packing, pipeline control and multiplier sharing remain OPEN. Near CFAR threshold, finite precision and different FFT shift sites can flip alarms; no acceptable margin threshold selected.

## 7. Outstanding S02 binding requirements and limits
| Obligation | Additional approved C02 owner | C06 independent verifier | Unavailable source conditions | Gate-S04 |
|---|---|---|---|---|
| REQ-SCR-01, SCR +10/-10 dB and no clutter | design numeric target+clutter dynamic-range and gain profile | independent S02-prescribed scenario coverage | absolute target/clutter amplitudes, joint distribution/crest, phase, source mask and admitted g | BINDING OPEN, close before gate |
| REQ-RNG-03 two equal-power targets around nominal 600m | design coherent superposition, MF sidelobes, list/cluster headroom | independent frozen resolved-pair oracle and Float/Fixed coverage | absolute target envelope, relative phase, overlaps and denominator | BINDING OPEN, close before gate |
S02 historical S03 ownership remains unchanged; newer C02/C06 responsibilities derive from explicit engineer C01 signoff. No new clutter source law or target envelope adopted.

## 8. Evidence and held decision
Source: engineering/s04_numeric/s04_c02_coeff_shift_v03.py. Data: engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json, with complete 16-tap and 31 twiddle coefficient vectors and detailed five-stage errors. Unit tests: tests/test_s04_c02_coeff_shift_v03.py; exact rational/integer independent boundary-width tests, negative half-LSB RNE, MF reverse conjugate, FFT sign/twiddles, multi-stage margins and strict CFAR comparator. An early unit test rejected the substring ISE appearing in NOISE, then was corrected; no source numerical model change or statistical trial resulted.
The highest-risk OPEN decisions are real internal FFT stage widths and product rounding, coefficient/twiddle rounding policy, five shift schedule, downstream saturation handling, certified numerical MAX/RMS bounds and independent threshold-decision acceptance. No A/B/C selected, no bit-true Pd or Pfa inference, no RTL or synthesis. **C01 PASS BOUNDED; C02 OPEN; Gate-S04 OPEN; S04 12.5%; overall 26.04%.**

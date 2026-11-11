# AX309-RDSP-001 | S04-C02 NUMERIC RANGE & BIT-GROWTH ANALYSIS v0.2

**STATUS: ENGINEERING DESIGN PROPOSAL / C02 OPEN — NO ARCHITECTURE APPROVED.** C01 PASS BOUNDED INPUT CONTRACT; Gate-S04 OPEN; S04 1/8=12.5%, overall 26.041666666666668%. Analytical inequalities and deterministic unit tests only. No stochastic CPI, accepted S03 seed, RTL, synthesis or FPGA trial.

## 1. Governing baseline, units and quantitative meaning

Authoritative: decisions/S04-C01-ENGINEER-CONDITIONAL-SIGNOFF-v1.0.md, engineering/S04-C02-NUMERIC-ARCHITECTURE-ENTRY-PACKAGE-v0.1.md, approved S02 requirements matrix v1.2, s03_reference/model.py. Earlier engineering/S04-NUMERIC-CONTRACT-PROPOSED-v0.2.md is UNAPPROVED A/B design input.

C01-approved classes: (N) NOISE_ONLY_UNIT: 33x128 independent CN(0,1), no target/clutter, g=5, theoretical whole-campaign stop-risk ≤0.001 for 20,000 independent CPI; (T) SINGLE_TARGET_REFERENCE_LIKE LAB: single k40, Doppler+4, amplitude 0.18, source noise E|w|²=0.000324, no clutter, g=1. No other class is admitted by C01.

For each I and Q, signed int16 Q(16,15) input candidate **approved at C01 interface** encodes q=SAT16(RNE(2^15*x/g)); original normalized-Float-domain reconstruction xhat=g*q*2^-15. On unsaturated input, each real reconstruction error ≤g*2^-16. Thus g5: Delta=5/32768, maximum component error=5/65536; g1: Delta=1/32768 and maximum component error=1/65536. C01-approved input clip status is distinct from **postquantizer** representable input bound Re/Im in [-1,1−2^-15]. These bounds are deterministic conditional on valid input, not Gaussian typical-signal statistics. Neither g changes the **stored-domain** FFT/MF bit-growth bound for the same quantizer envelope, but original reconstructed Float-domain amplitude is multiplied by g.

Convention: signed Q(W,F) stored numeric range [-2^(W−F−1), 2^(W−F−1)−2^-F], unsigned U(W,F) [0, 2^(W−F)−2^-F]. A stage with physical reconstruction factor S represents original normalized units as S*q*2^-F. Units are normalized complex sample amplitude or its squared amplitude, never calibrated volts/watts. RNE is approved **only at C01 input**; post-input rounding, saturation policies and internal formats require separate C02 approval.

## 2. Full B00–B12 source-to-target numerical boundary audit

For candidate fields, format notation A/B/C indicates **unapproved stored representations**, not three actual implemented buses. W/F marked OPEN when no numeric stage width has been authorized.

| ID, shape and semantics | Type / signedness | Numeric W,F or representation | Stored range; original reference units and S | Rounding / unresolved |
|---|---|---|---|---|
| B00 Float source IQ, 33x128 complex | complex Float64, signed I/Q | 2x binary64; non-fixed W/F | unbounded Gaussian before input quantization; normalized amplitude, S=1 | floating generator rounding as S03; source quantization not fixed-point |
| B01 interleaved IQ, 33x128 | 2x int16 signed two's complement | **C01-approved Q(16,15)** | each real [-1,1−2^-15] stored, original source amplitude S=g (5 or1) | C01-approved RNE+SAT16; count every clipped component |
| B02 16 MF coefficients | complex signed, dimensionless | A Q(16,15), B Q(14,13), C Q(16,15), all candidates | ideal |h|=1; quantized magnitude, stored factor/coeff phase OPEN | coefficient rounding, twiddle/ROM encoding and norm excess OPEN |
| B03 matched-filter 33x128 aligned output | complex signed | A Q(22,15), B Q(20,13), C Q(22,15) | ideal magnitude ≤16√2 stored; original amplitude factor g | full complex-product W and 16-term accumulation; narrowing rounding OPEN |
| B04 MTI 32x128, two-pulse difference | complex signed | A Q(23,15), B Q(21,13), C Q(23,15) | ideal magnitude ≤32√2 stored; original amplitude factor g | signed subtraction and narrowing OPEN |
| B05 FFT32 128x32 | complex signed | A Q(28,15), B Q(23,13), C Q(25,15) | ideal magnitude ≤1024√2/sFFT stored, original S=g*sFFT; sFFT A1, B8, C8 **proposals only** | 5 radix-2 stage shifts/rounding, twiddle W/F and guard placement OPEN |
| B06 RD linear power, 128x32 | unsigned nonnegative real | A U(52,30), B U(43,26), C U(46,30) | ideal ≤2^21/sFFT² stored; original squared amplitude S=(g*sFFT)² | two squares+sum full precision then optional narrowing, sites OPEN |
| B07 CA-CFAR 40-training sum for 2782 valid CUT | unsigned nonnegative | A U(58,30), B U(49,26), C U(52,30) | ideal ≤40*2^21/sFFT²; source power S=(g*sFFT)² | exact 40-term accumulator and narrowing OPEN; valid region r=3..109, d=3..28 |
| B08 mean40, threshold alpha, comparator operands | unsigned powers and unsigned rational coefficient | mean/threshold W,F OPEN; alpha candidate A/C U(20,16), B U(16,12) | stored power scale S=(g*sFFT)²; alpha dimensionless | do NOT divide then round before strict compare; integer cross-product implementation W OPEN |
| B09 CFAR valid/alarm mask 128x32 | Boolean (unsigned 1-bit) | 1-bit flags, decision arithmetic separate | exactly 2782 valid CUT, 40 training, 8-neighbor follow-on; no amplitude scale | strict threshold equality must be false |
| B10 8-connected target clusters / peaks | indexes unsigned, signed Doppler labels, nonnegative powers | range index uint7, raw bin uint5; power A/B/C candidate; cluster count/capacity OPEN | r 0..127; Doppler bin 0..31; selected peak power factor (g*sFFT)² | tie ordering and list overflow flags OPEN |
| B11 target records, truth association at host | normalized integer bin IDs, range/velocity real; power nonnegative | storage field W/F and list capacity OPEN; host Float64 possible | range in m, velocity in m/s, power in source amplitude²; no multiplicative g for range/velocity | one-to-one truth matching separate from FPGA; range/doppler conversion rounding OPEN |
| B12 readback/evidence and header | serialized signed/unsigned fields, hashes/flags | UART/FPGA ICD byte widths OPEN (host logical metadata approved) | stage W/F/S and g needed; non-numeric event/hash fields | C01 host metadata locked, wire ICD and stage diagnostic layout OPEN |

This table is a **boundary specification audit**, not a claim that all tentative stage widths are frozen. B03 full convolution has 143 samples per pulse before selecting delay-aligned 128 samples. B04 uses 33→32 pulses, FFT has exactly 32 Doppler samples, RD map 128×32.

## 3. Conditional worst-case ideal growth and minimum stored widths

For post-SAT16 I/Q (|Re|≤1, |Im|≤1) and **ideal** unit-modulus complex coefficients/twiddles, triangle inequality gives |x|≤√2 normalized stored amplitude:
MF16 ≤16√2=22.6274; MTI2 ≤32√2=45.2548; FFT32 unshifted ≤1024√2=1448.1547; FFT with total scale 8 ≤128√2=181.0193. FFT power ≤(1024√2/sFFT)²=2^21/sFFT²; CA sum40 ≤40*2^21/sFFT².

For signed per-component bound M and fractional bits F, conservative minimal W obeys 2^(W−F−1) > M (strict representable maximum reduced by LSB); **W_min=F+1+floor(log2 M)+1 when M exactly power of 2, otherwise F+1+ceil(log2 M)**. For unsigned nonnegative M, require 2^(W−F)−2^-F ≥ M (at exact powers of two add a headroom bit). The audited script calculates these as numeric mathematical bounds and tests them against actual proposed stage ranges.

| Stage | ideal stored M | minimum A-style W at F=15 or F=30 | minimum B-style W at F=13 or F=26 | retained candidate A | retained candidate B |
|---|---:|---:|---:|---:|---:|
| MF signed component | 16√2 | 21 (F15) | 19 (F13) | 22 | 20 |
| MTI signed component | 32√2 | 22 | 20 | 23 | 21 |
| FFT unshifted | 1024√2 | 27 | 25 | 28 (unshifted) | — |
| FFT shifted /8 | 128√2 | 24 | 22 | — | 23 |
| Power unshifted | 2^21 | 52 (F30) | 48 (F26) | 52 | — |
| Power shifted /8 | 2^15 | 46 (F30) | 42 (F26) | — | 43 |
| Sum40 unshifted | 83,886,080 | 57 (F30) | 53 (F26) | 58 | — |
| Sum40 shifted /8 | 1,310,720 | 51 (F30) | 47 (F26) | — | 49 |

**Validity caveat:** These are ideal mathematical stage-output bounds under input clipping and unit-modulus coefficients, not guarantees for quantized taps/twiddles, unapproved internal rounding, vector sum ordering, saturation or unbounded Float source before quantization. They do not yield a numerical downstream overflow probability. Actual g=5 and g=1 have identical stored-domain ideal bounds but original reference-domain max amplitudes scale with g and powers g².

Raw complex MF multiplication at input Q(16,15) and coefficient Q(16,15) produces signed real product width ≤32 bits, pair add/sub ≤33 bits, and 16-term exact sum ≤37 bits at 30 fractional bits (A/C proxy). For Q(14,13) coefficients, exact products ≤30 bits, pair ≤31 bits, accumulated sum ≤35 bits at 28 fractional bits (B proxy). These are **conservative full-width arithmetic proxies**, not chosen RTL implementations. Intermediate FFT twiddle multiplication, butterfly ordering and saturation guard width need separate design and proof.

## 4. A/B/C architecture candidates — all unapproved

| Attribute | A | B | C (new hypothetical hybrid) |
|---|---|---|---|
| MF coefficient | signed 16/15 | signed 14/13 | signed 16/15 |
| MF output signed W/F | 22/15 | 20/13 | 22/15 |
| MTI output signed W/F | 23/15 | 21/13 | 23/15 |
| FFT output signed W/F | 28/15 | 23/13 | 25/15 |
| FFT net right-shift | 0 | 3 | 3 |
| Power unsigned W/F | 52/30 | 43/26 | 46/30 |
| Sum40 unsigned W/F | 58/30 | 49/26 | 52/30 |
| Alpha rational candidate | 490007/65536 | 30625/4096 | 490007/65536 |
| MF coefficient ROM bits (16 complex) | 512 | 448 | 512 |
| Full 128x32 complex FFT buffer bits | 229376 | 188416 | 204800 |
| Full 128x32 power map bits | 212992 | 176128 | 188416 |
| Raw exact 16-tap complex signed accumulator bits (proxy) | 37 | 35 | 37 |
| Numeric tradeoff | highest stored FFT resolution, larger FFT power | smallest storage, lower fractional precision and earlier /8 shifts | retain F15 and shift /8, intermediate resource compromise |

Cost model assumes complete double-component buffers and no compression, no memory banking or packing; number of complex MF coefficient products per range output 16; radix-2 FFT of 32 requires 80 complex butterfly operations per 32-point transform; CA sum40 requires 39 pairwise additions per CUT if no reuse. Multiply area/LUT/DSP inference, register count, BRAM primitives, frequency, dynamic power, streaming buffering, scheduling and timing are **OPEN**, not measured. Larger stage W may increase arithmetic/comparator area and control fan-out; exact cost cannot be stated without RTL and synthesis, which are prohibited.

All three candidate formats satisfy ideal stored output bounds in the deterministic checker. **No candidate has been proven free of overflow with real quantized coefficients and a particular FFT shift schedule.** B/C higher fractional precision tradeoffs are not tested for Float/Fixed Pd or CFAR decision stability.

### Arithmetic, register, memory and control cost comparison (non-synthesis proxies)

| Hardware cost dimension | A | B | C candidate | Interpretation and unknowns |
|---|---:|---:|---:|---|
| One complex FFT output register (2W, bits) | 56 | 46 | 50 | per sample, not actual register-file/retiming count |
| One complex MF output register (2W, bits) | 44 | 40 | 44 | excludes pipelines and guard bits |
| One sum40 accumulator register (bits) | 58 | 49 | 52 | without pipeline or signed comparator widths |
| 16 complex MF coefficient words (bits) | 512 | 448 | 512 | may map to LUT/BRAM or constants, not known |
| Whole RD complex FFT buffer (bits) | 229376 | 188416 | 204800 | 4096 complex samples; hypothetical full buffering |
| Whole RD power map (bits) | 212992 | 176128 | 188416 | 4096 power samples; hypothetical full buffering |
| Exact MF arithmetic product operand widths (bits) | 16×16 | 16×14 | 16×16 | four generic real multipliers per complex multiply as upper operation count |
| Exact 16-tap accumulated real-component width (bits) | 37 | 35 | 37 | prior to rounding and final stage storage |
| Generic real multiply operations per MF output (unshared) | 64 | 64 | 64 | coefficient symmetries/constant multipliers may reduce |
| Generic FFT complex butterflies per FFT32 transform | 80 | 80 | 80 | 5 stages ×16, not concurrent multiplier instances |
| Naive real adds per CFAR 40-cell sum | 39 | 39 | 39 | per CUT, reuse/windowing may reduce physical operations |
| Controller complexity / risk | lower shift control, wider datapath | 3 per-stage shifts plus reduced F, increased tie/quantization risk | 3 shifts with F15 and added scale handling | shift placement, rounding, saturation, metadata, retries/flags need design |

Actual flip-flop/DSP slices, BRAM mapping, adder-multiplier sharing, cycle latency, clocks and logic utilization remain **OPEN**. Operation counts cannot be read as instantiated parallel resources and none are synthesis evidence.

## 5. FFT32 five-stage shifts and exact scale reconstruction

| Candidate schedule (five radix-2 stages) | Total divide | Stored FFT magnitude bound ideal | Original FFT amplitude reconstruction | Power/CFAR reconstruction |
|---|---:|---:|---|---|
| [0,0,0,0,0] | 1 | ≤1024√2 | g | g² |
| [1,1,1,0,0] | 8 | ≤128√2 | 8g | 64g² |
| [0,1,0,1,1] | 8 | ≤128√2 | 8g | 64g² |
| [1,1,1,1,1] | 32 | ≤32√2 | 32g | 1024g² |

At g5, the [three-shift] FFT reconstructs amplitude with factor40 and power with factor1600; at g1 factors8 and64. These are exact source-unit conversions, not post-processing scalar choices. Two schedules with equal net scale differ in *intermediate* growth/rounding error and overflow risk. Delaying shifts allows larger intermediate values; early shifts attenuate weak values before later calculations. Twiddle W/F and |w_hat| modulus must be bounded independently. For stage j, with coefficient modulus upper bound beta_j, additive quantizer error eps_j and twiddle perturbation delta_j, an indicative recursion is:
E_(j+1) ≤ (1+beta_j)/2^s_j * E_j + delta_j*M_j/2^s_j + eps_j.
This is a prospective MAX-bound structure only; beta, delta, rounding-site eps, input M_j and the actual order are OPEN. The arithmetic checker includes a separate conditional (1+beta)^5 bound for beta=1 and beta=1.0001 to demonstrate that ideal unit-twiddle growth cannot be treated as a certified quantized FFT bound.

## 6. Squared magnitude, training sum and strict CFAR

Given FFT stored I/Q integer components qI,qQ with F_FFT fractional bits and no product narrowing, integer stored power is qI²+qQ² at fractional precision F_power=2*F_FFT (30 for A/C, 26 for B). For a complex stored magnitude bound M_FFT, P<=M_FFT². Sum40 <=40 P; at F30 unshifted require U52 for power and at least U57 for sum40; at /8 F26 require at least U42 power and U47 sum40. Any coefficient modulus excess, processing overflow or narrower intermediate operation invalidates the simplistic proof.

Alpha is dimensionless. If P_CUT and SUM40 are integer quantities **at the same stored power scale**, quantized alpha A/2^Fa is compared without intermediate rounding as **40*P_CUT*2^Fa > A*SUM40**. Equality gives NO ALARM. Candidate alpha A/C 490007 with Fa16; B 30625 with Fa12, both not approved. Conservative unsigned crossproduct widths: A 74 vs 78; B 61 vs65; C 68 vs72 bits (left vs right), pre-retiming/addition proof still required. With exact common positive gain the comparison outcome is invariant to scale, but fixed-point rounding, alpha quantization, register saturation, peak/tie and near-threshold samples can flip Boolean alarms. A useful prospective stability condition is |M_float| > E_power + |alpha|*E_training + |delta_alpha|*(|Z|+E_training) + E_compare; **all E terms OPEN** until C06 budget and precision analysis are approved. Do not declare near-equality cases valid without independent numerical evidence.

## 7. Statistical operating points versus proof of headroom

Source input for NOISE_ONLY_UNIT is unbounded CN(0,1) before approved g5 Q1.15; the exact C01 approved *campaign-level input clip-risk* ceiling 0.001 for 20000 independent CPI is not a downstream MF/FFT saturation probability. SINGLE_TARGET_REFERENCE_LIKE has a declared source echo amplitude .18 and noise variance .000324, but the Gaussian tail remains unbounded, so even nominal MF peak 16*.18=2.88, MTI gain and FFT peak roughly70.5 are NOT safe hardware headroom arguments.

The report supplies **zero measured fixed-point overflow rates** because no test CPI, bit-true arithmetic or hardware run was permitted. Any actual probability for MF/FFT/power saturation would require a chosen rounding/word-width/twiddle/shift design plus a preapproved statistical model/validation corpus.

## 8. Pending binding S02 obligations in dynamic-range analysis

- **REQ-SCR-01**, SCR ±10dB clutter: still binding and OPEN. C02 assigned numeric envelope and gain/calibration arithmetic design; C06 independently validates and must close it before Gate-S04. Need exact active-support target/clutter power, defined mask and SCR measurement, correlation law, crest factors, coherent phase relationships, admitted source amplitude ceilings, clipping criteria and conditional threshold errors. Ratios in dB alone DO NOT give absolute full-scale amplitude bounds. No clutter model or g approved for this class.
- **REQ-RNG-03**, two equal-power targets around nominal 600m range resolution: still binding and OPEN. C02 must bound coherent sum vs separation/phase, MF sidelobes, cluster/peak numerical headroom and target-list overflow; C06 owns independent paired-target verification and accepted resolved-pair criterion/denominator. Equal power and range separation do NOT define absolute amplitudes or relative phases. No numeric dynamic range bound certified for this class.
- Historical S03 ownership and evidence unchanged; C02/C06 are additional approved forward owners under engineer C01 signoff. Both obligations must be resolved before Gate-S04.

## 9. Evidence, conclusion, and explicit open decisions

Computations: engineering/s04_numeric/s04_c02_range_bitgrowth_v02.py and its JSON output. Unit tests in tests/test_s04_c02_range_bitgrowth_v02.py include separate ideal bounds, minimal W/F, A/B/C headroom proxies, reconstruction factor checks at g1/g5, strict comparator equality, twiddle nonunit risk, non-use of acceptance data and storage-bit cost proxy. Early development test failures reflected an unsigned-width boundary calculation and test field naming issue, corrected **before evidence freeze**. No stochastic radar trial was executed.

**OPEN decisions for engineer review:** select internal per-stage W/F, coefficient and twiddle encoding, overflow guard policy, exact five FFT shifts, integer comparator and counter sizing, prospective numerical stage MAX/RMS and Boolean error budgets, buffering/resource schedule and C06 acceptance. UART/FPGA ICD is not approved. C02 remains OPEN; nothing has been selected. Legacy S03 Pfa/Pd scope, 4135 unmatched clusters (not Pfa), unavailable original IQ/power arrays, historical failures and two binding S02 obligations are preserved.

**Gate-S04 OPEN | C01 PASS BOUNDED | C02 OPEN | S04 12.5% | overall 26.041666666666668%.**

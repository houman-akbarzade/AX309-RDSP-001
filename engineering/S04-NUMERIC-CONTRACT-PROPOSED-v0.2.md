# AX309-RDSP-001 | S04 NUMERIC CONTRACT v0.2 — PROPOSAL ONLY

STATUS: NUMERIC CONTRACT NOT APPROVED. Stage S04 0/8, overall 25%, Gate-S04 OPEN. No numerical architecture, FFT shift schedule, tolerance or physical RTL chosen; no radar CPI, fixed-point model, RTL, synthesis or hardware operation executed.

## 1. Governing semantics and two candidate fixed-point designs

Stage data is integer q with decoded Float-scale value S*q*2^(-F). Signed Q(W,F) has range [-2^(W-F-1),2^(W-F-1)-2^(-F)], unsigned U(W,F) [0,2^(W-F)-2^(-F)]. All IQ amplitudes are normalized (not measured volts); power means normalized squared amplitude. These candidates assume componentwise quantized input in [-1,1), not unbounded prequantization Gaussian IQ.

| Boundary | Option A precision/headroom | Option B lower-width/FFT scaling |
|---|---|---|
| IQ I/Q signed | Q(16,15) S=1 | Q(16,15) S=1 |
| MF coefficient signed | Q(16,15) S=1 | Q(14,13) S=1 |
| MF result signed | Q(22,15) S=1 | Q(20,13) S=1 |
| MTI result signed | Q(23,15) S=1 | Q(21,13) S=1 |
| FFT output signed | Q(28,15) S=1 | Q(23,13) S=8 (net three /2 stages) |
| RD power unsigned | U(52,30) S=1 | U(43,26) S=64 |
| sum40 training unsigned | U(58,30) S=1 | U(49,26) S=64 |
| alpha unsigned | U(20,16), 490007/65536 | U(16,12), 30625/4096 |
| CFAR strict comparator | 40*P*65536 > 490007*SUM | 40*P*4096 > 30625*SUM |
| Intermediate compare bits conservative | left 74, right 78 | left 61, right 65 |
| FFT shifts candidate | [0,0,0,0,0] | [1,1,1,0,0] or [0,1,0,1,1] |

Widths are proposed STORED stage formats, not complete internal signed complex multiplier, accumulation, butterfly or twiddle formats. B may have greater precision loss and decision flips; no variant is approved. No arbitrary universal Q1.15 rule for internal stages.

## 2. Analytic bit growth and domain distinction

For ideal taps of magnitude1 and bounded post-input-quantizer complex magnitude <=sqrt2, MF of length16 has magnitude bound 16sqrt2 (4 gain bits), MTI difference 32sqrt2 (1 additional), unnormalized FFT32 1024sqrt2 (5 additional). RD power <=2^21, 40-training sum <=40*2^21=83,886,080 <2^27. A stage-wide ideal FFT scale8 reduces power and training sums by64, but does NOT guarantee integer alarm-mask invariance. Gaussian source Float values remain unbounded; sample clipping must be counted and cannot be excluded.

For a single clean on-bin echo amplitude .18, ideal MF magnitude 2.88, MTI on bin +4 gain 2*sin(pi/8) and FFT32 ideal peak around70.54 in normalized units. This nominal case is not worst-case noise, clutter or multiple-target headroom.

## 3. Hardware proxies (NOT synthesis)
- 16 complex taps each 2 components: coefficient memory A=16*2*16=512 bits, B=16*2*14=448 bits, excluding representation overhead.
- If all 128*32 complex FFT outputs buffered, A=229376 bits and B=188416 bits; actual streaming memory allocation belongs S05.
- If full power-map buffered, A=212992 bits, B=176128 bits.
- Core coefficient operands 16x16 A versus 16x14 B, FFT arithmetic 28 versus23 bits, train sum58 versus49 bits, comparator product max width78 versus65 bits. Full complex intermediate product widths and twiddle quantization are UNDECIDED.
- These bit-count proxies are NOT measured DSP48, LUT, FF, BRAM, timing or power utilization on XC6SLX9; no implementation claim.

## 4. Rounding and negative signed arithmetic

Candidate policy round-to-nearest ties-to-even (RNE) at each explicitly approved reduction of fractional bits, including negative half-LSB. Integer n/2 test cases: -5 -> -2, -3 -> -2, -1 -> 0, 1 -> 0, 3 -> 2, 5 -> 2. A signed arithmetic right shift of negative numbers corresponds to floor division by 2^r: -3 >> 1 = -2 and -1 >> 1 = -1; this is NOT generally RNE or truncation toward zero. Guard, round and sticky bits and sign extension must be specified. RNE at Q1.15 host input follows existing contract; internal truncation versus RNE is an unapproved alternative. Define each exact quantization site and order before bit-true model implementation.

## 5. Overflow handling candidates by stage

| Stage | Proposed action / observable signal |
|---|---|
| IQ pack | saturate to int16 two's-complement endpoints; count clipped real/imag and set sticky IQ flag; clean vectors should be saturation-free |
| MF tap and 16-term multiply/accumulate | full-width products/widened accumulation, then explicit RNE and saturate on MF output; per-component saturation count and flag |
| MTI | widen signed subtraction before output narrowing; saturation count, flag and exact signed minimum corner case |
| FFT butterflies and twiddles | declare exact stage growth and shifts; count saturation by stage; explicit scale exponent, no silent data loss |
| RD power | full two squares and nonnegative addition then narrow; unsigned saturation counter |
| CFAR 40-sum and alpha products | widened sum and cross-products; any unexpected arithmetic overflow INVALID/FAIL, never silent wrap |
| Peak/list | deterministic peak ties and zero status, variable record count and overflow flag; capacity and arbitration deferred to S05 |

Wrap may be proposed later only with explicit proof of equivalence in admitted range and engineer approval. Saturation counters must themselves be non-wrapping or have explicit overflow indication.

## 6. FFT32 five-stage shift options and effects

A0 [0,0,0,0,0] gives S=1, maximum ideal stored magnitude1448.15. B1 [1,1,1,0,0] and B2 [0,1,0,1,1] both give S=8, max magnitude181.019; early shifts reduce overflow risk but round weak signals early; later shifts preserve early precision but require intermediate guard bits. Full per-stage shifts [1,1,1,1,1] give S=32, maximum45.255 but more weak-signal attenuation in finite precision. Stage twiddle W/F, multiply rounding and butterfly loss are unquantified. Under exact scale and no rounding, global power scale cancels in CFAR CUT/training ratio and ideal FFT peak index; under finite precision it can alter Doppler ties, E/V, threshold decisions and J.

## 7. Exact CA-CFAR integer/rational arithmetic (22 independent checks PASS)

Let P be integer CUT power and SUM the sum of 40 power cells at the same scale. Alpha is A/2^Fa; the EXACT strict decision with chosen quantized alpha is 40*P*2^Fa > A*SUM (no division, no overflow). Equality implies NO ALARM.
- A: A=490007, Fa=16, alpha_q=7.4769134521484375, delta alpha=+0.0000013971205145 from 7.476912055027923.
- B: A=30625, Fa=12, alpha_q=7.476806640625, delta alpha=-0.000105414402923.
- Nearest-round alpha error bound: A <=7.62939453125e-6; B <=0.0001220703125.
- Independent Fraction reference compared to integer cross-products on 11 cases per option, including exact threshold, below and above: 22/22 arithmetic checks PASS. With SUM=40*2^Fa, threshold P=A; at P=A-1 false, P=A false, P=A+1 true.
- Float S03 code is binary64; direct equality with decimal Fraction cannot be assumed at rounding scale. Finite alpha quantization creates a near-threshold ambiguity region, not automatically an acceptable mismatched alarm.

## 8. Proposed per-stage MAX and RMS error budget, not binding

Define eps_x=sqrt2*2^-16 for unsaturated input complex quantization; eps_h=sqrt2*2^(-Fc-1) for coefficient complex quantization. Define eps_prod as complex product narrowing error, eps_sub as MTI subtraction narrowing, eps_bfly for FFT butterfly and eps_twiddle for quantized FFT twiddles. The following are conditional worst-case magnitude inequalities, NOT measured error:

| Stage | Proposed MAX bound or method | Proposed RMS threshold pending approval | Detection effect |
|---|---|---|---|
| IQ | real or imag <=2^-16, complex magnitude eps_x (unless saturated) | RMS <=eps_x as conservative bound; tighter objective needs independent model | input gain/clipping |
| taps | each real/imag <=2^(-Fc-1), complex eps_h (unless saturated) | RMS <=eps_h; refine from design requirements, not results | MF sidelobes |
| MF | E_MF <=16*(eps_x+sqrt2*eps_h+eps_x*eps_h+eps_prod) | RMS <=certified E_MF | range peak/extra clusters |
| MTI | E_MTI <=2*E_MF+eps_sub | RMS <=certified E_MTI | DC notch/response |
| FFT | E_FFT <=(32/S_FFT)*E_MTI+eps_bfly+eps_twiddle | RMS <=certified E_FFT | signed Doppler peak/eligibility |
| RD power | E_P <=2*M*E_FFT+E_FFT^2+eps_power, M=1024sqrt2/S_FFT | RMS <=certified E_P | threshold/peak ordering |
| 40-training mean | E_Z <=E_P+eps_div after 40-sum precision | RMS <=certified E_Z | threshold |
| CFAR margin | E_M <=E_P+abs(alpha)*E_Z+abs(delta_alpha)*(abs(Z)+E_Z)+eps_compare | RMS <=certified E_M | alarm sign stable if abs(M_float)>E_M |
| clustering and D/R/V/E/J | exact integer decisions on certified stable regions; separately report ambiguous-margin mismatches | discrete flags: mismatch counts, not RMS | target-list decisions |

Actual eps_bfly/eps_twiddle/eps_power/eps_div and saturation effects cannot be assumed zero. Attached illustrative decimal error figures EXCLUDE FFT twiddle/shift errors and ARE NOT certified limits. RMS upper bounds here are trivial consequences of MAX; they are not operational RMS estimates. Before any numeric acceptance test, choose and approve per-stage measured RMS tolerance with explicit unit and relevant input population, worst-case proof assumptions, decision-margin rule and exact/inconclusive criteria. No outcome-driven thresholds.

## 9. Development versus independent acceptance dataset firewall

DEV-ARITH: deterministic hand-written negative ties, overflow and rational CFAR values (22 checks now executed, no CPI).
DEV-NUM: NEW development-specific seed namespace only after engineer authorization; numeric candidate optimization may use it; no historical Pd or Pfa samples.
ACCEPT-NUM: separately reserved unknown/frozen independent namespace and fixed scenarios/tolerances BEFORE running verification; cannot be mixed with DEV-NUM, no optional stops/topups.
S03 accepted Pd master 411091704 and Pfa master 411091703: historical acceptance evidence only, no tuning and no reexecution.

Planned cases include input boundary/full-scale, LFM/MF edges k0/112, MTI DC, FFT b±4/off-bin/Nyquist/ties, power zeros, 40-cell overflow, CFAR exact equality and ±one integer unit, CUT edges and invalid masks, 8-neighbor cluster extra/duplicate records, target-list overflow. Require independent integer/Fraction oracle and evidence hashes.

## 10. Explicit engineer decisions required

1. Admit input normalization, clipping and data interface W/F/S.
2. Select A/B/hybrid and full intermediate widths, coefficient/twiddle precision and five FFT shifts.
3. Ratify every rounding site, signed shift and saturation/exception counters.
4. Approve quantized alpha and strict comparator plus ambiguity-margin handling.
5. Approve predeclared numeric max/RMS/decision-mismatch thresholds, test corpus, independence rules and oracle.

**None of these decisions is approved by drafting v0.2.** C01 remains pending independent audit approval; C02 and all later S04 criteria remain incomplete. No RTL/hardware tests permitted.

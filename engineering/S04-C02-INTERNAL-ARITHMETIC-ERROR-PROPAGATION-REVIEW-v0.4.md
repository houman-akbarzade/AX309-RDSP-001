# AX309-RDSP-001 | S04-C02 INTERNAL ARITHMETIC CONTRACT AND ERROR PROPAGATION v0.4

**DESIGN CANDIDATE / NOT APPROVED.** C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN; S04=12.5%, overall=26.0416667%. No accepted S03 seed, new CPI, RTL, synthesis, or FPGA operation.

## 1. Actual test interpreter and rerun
Authorized host: houman-Vivobook-ASUSLaptop-X1502ZA-R1502ZA, repository /home/houman/AX309-RDSP-001. Python executable /usr/bin/python3, version 3.14.4, sys.prefix=sys.base_prefix=/usr, system NumPy 2.3.5. Search under /home/houman to depth 4 found no pyvenv.cfg; no project virtual environment was found or invented. Full environment capture, command and test log: engineering/S04-C02-V04-PYTHON-ENV-AND-V031-RERUN.log.

Exact command executed from repo root:
    /usr/bin/python3 -B -m unittest discover -s tests -p test_s04_c02_cfar_repair_v031.py -v
Actual output: Ran 9 tests in 0.160s; OK (all 9 PASS).

New independent deterministic unit tests: /usr/bin/python3 -B -m unittest discover -s tests -p test_s04_c02_internal_arithmetic_v04.py -v; 11/11 PASS. This is not a stochastic radar performance test.

## 2. Frozen input and precise candidate internal arithmetic
C01 input Q(16,15), signed little-endian I/Q, q=SAT16(RNE(2^15*x/g)), reconstruction original normalized Float amplitude xhat=g*q/2^15. Only two approved source profiles: NOISE_ONLY_UNIT with g5 and SINGLE_TARGET_REFERENCE_LIKE lab with g1. The C01 0.1% stop-risk for 20000 independent CPI applies ONLY to noise-only. The input error limit is conditional on NO clipping: absolute per real component <=g/65536 and complex error <=sqrt(2)*g/65536. Candidate internal RNE below is NOT approved.

Candidate MF16 operation order: signed real products Ir*hr, Ii*hi, Ir*hi, Ii*hr at full operand product precision; real part = Ir*hr−Ii*hi, imag = Ir*hi+Ii*hr, sum exactly across all 16 ordered conjugate-reversed LFM taps before one RNE per MF output I/Q. Check overflow before narrowing; do not silently wrap. A/C MF taps signed 16/15, output 22/15; B taps 14/13, output 20/13.

Candidate MTI2: exact consecutive-pulse complex MF difference then one RNE of output I/Q and overflow detection; A/C output signed 23/15, B signed 21/13. No intermediate narrowing.

Candidate FFT32: S03 forward unnormalized DIT butterfly, input bit-reversal for natural bin order. At each of five stages: full complex twiddle multiply t=what*v; plus=u+t, minus=u−t with exact aligned sums; divide exact rational by 2^s_j (s_j in 0,1); ONE RNE per output component to signed stage W/F; record overrange before clip. Candidate output stage W/F A=28/15, B=23/13, C=25/15, with common width at all five stages only a *comparison proxy*. Twiddle A/C signed16/15, B signed14/13. Actual pipeline register allocation, truncation schedule, coefficient rounding and butterfly ordering are OPEN, not RTL.

Intermediate signed width proxies (not a mandatory FPGA implementation): MF real product W=16+Wcoef, real complex pair W=17+Wcoef, raw 16-tap sum W=21+Wcoef; their fractional bit count is 15+Fcoef. MTI subtraction requires up to Wmf+1 before narrowing. For FFT stage j, real twiddle product W=Winput+Wtwiddle with F=Finput+Ftwiddle; real complex pair requires +1 bit; aligned u path Winput+Ftwiddle; conservative pre-shift butterfly signed W=max(Winput+Ftwiddle,Winput+Wtwiddle+1)+1. The JSON enumerates these values for A/B/C and all five stages.

Operation order is significant. At F1, individually RNE(0.25) + RNE(0.25) gives 0, but RNE(0.25+0.25) gives 0.5. Arithmetic signed right shift floors negative codes: -1>>1=-1 while nearest-even RNE(-1/2)=0; -5>>1=-3 versus RNE(-5/2)=-2. Exact division then RNE, as modeled here, is not interchangeable with raw arithmetic shift. Neither policy is selected for hardware.

## 3. Input Float error propagated to MF, MTI and five FFT stages
Reference for error is **original Float source IQ**, not merely previously quantized input. Conditional on no clipped source I/Q: in normalized stored units x/g, complex source input error e0 <=sqrt(2)/65536 and conservative source magnitude <=sqrt(2)*(1+2^-15). For actual quantized MF taps hhat and frozen S03 ideal h:
MF input-origin error ≤ e0*sum|hhat|;
MF coefficient error ≤sqrt(2)*(1+2^-15)*sum|hhat-h|;
MF output RNE ≤sqrt(2)*2^(-F_MF-1).
MTI doubles each MF error category and adds one MTI output RNE ≤sqrt(2)*2^(-F_MTI-1). These are absolute bounds; no RMS conclusion.

At FFT stage j define beta_j=max|what_j| and delta_j=max|what_j−w_j| from the v0.3 quantified twiddles, total net shift s_j. Propagate EACH previous error component by (1+beta_j)/2^s_j; independently add twiddle contribution delta_j*Mref_(j-1)/2^s_j and one candidate complex output RNE sqrt(2)*2^(-F_FFT-1). Mref follows ideal (2/2^s_j) stage growth. Each component and stagewise sum appears explicitly in machine-readable JSON. Every cumulative total is in **normalized stored complex amplitude**; multiply by approved g*2^(sum s_j) for reconstructed original Float-amplitude error. Never add unscaled stored errors to original Float errors.

No clipping, no internal product narrowing, exact butterfly additions, exact division before one RNE and the common proposed stage format are *assumptions*. Violation invalidates these conditional error envelopes; saturation-induced error is OPEN/unbounded. The estimates may be excessively conservative and cannot be called demonstrated bit-true maximum or RMS.

## 4. Candidate comparison: stage output headroom and reconstructed error
The JSON covers 3 architectures × 4 schedules × 5 FFT stages with per-stage magnitude, overflow margin, source error components, and reconstructed errors for g1/g5. Summarized values (original normalized Float complex amplitude units for errors):

| Candidate | Shift vector | Sfft | final output headroom, stored | reconstructed error upper g1 | g5 |
|---|---|---:|---:|---:|---:|
| A | [0,0,0,0,0] | 1 | +2647.85174 | 0.14923311 | 0.74616556 |
| A | [1,1,1,0,0] | 8 | +3914.98120 | 0.15115368 | 0.75576839 |
| A | [0,1,0,1,1] | 8 | +3914.98137 | 0.14977260 | 0.74886298 |
| A | [1,1,1,1,1] | 32 | +4050.74525 | 0.15201685 | 0.76008424 |
| B | [0,0,0,0,0] | 1 | -936.19815 | 0.53981327 | 2.69906633 |
| B | [1,1,1,0,0] | 8 | +330.97416 | 0.54749600 | 2.73747998 |
| B | [0,1,0,1,1] | 8 | +330.97485 | 0.54197129 | 2.70985646 |
| B | [1,1,1,1,1] | 32 | +466.74334 | 0.55094871 | 2.75474355 |
| C | [0,0,0,0,0] | 1 | -936.14826 | 0.14923311 | 0.74616556 |
| C | [1,1,1,0,0] | 8 | +330.98120 | 0.15115368 | 0.75576839 |
| C | [0,1,0,1,1] | 8 | +330.98137 | 0.14977260 | 0.74886298 |
| C | [1,1,1,1,1] | 32 | +466.74525 | 0.15201685 | 0.76008424 |

Headroom assumes exact operations and specified candidate output RNE without other narrowing; positive margin does not validate internal products or stage overflow in an actual RTL topology. B/C with no FFT shifts have negative conditional headroom. Numerical upper estimates are loose; they are NOT measured Float/Fixed error or an approved pass criterion. For A/B/C schedule cases g1 and g5 share stored headroom but reconstructed errors scale with g.

## 5. Power, SUM40 and strict CFAR
v0.3.1 verified conservative unsigned cross-product widths for **narrowed operands**: A 74/78, B 61/65, C 68/72 bits (L/R); **full arithmetic prior to power narrowing**: A 79/83, B 65/69, C 73/77. The full signed FFT real square and I²+Q², 40-cell training sum, quantized alpha and integer comparator must use a consistent chosen path; no silent wrap. Exact strict decision 40*Pcut*2^Fa > Aalpha*SUM40 (equality false). A/C alpha 490007/2^16; B 30625/2^12; all candidates.

If z is original reconstructed FFT complex amplitude and e is its error, power error is bounded by 2|z||e|+|e|² before *additional* narrowing. Error in SUM40 is the sum of 40 respective cell errors; power/mean/SUM narrowing, alpha quantization and decision compare errors require further bounds. If Float decision margin approaches zero, an LSB may flip the alarm. There is NO approved numerical margin, no Pfa or Pd validation, and no certified Float/Fixed alarm equivalence.

## 6. Unresolved obligations and evidence
REQ-SCR-01 and REQ-RNG-03 remain binding OPEN S02 obligations; C02 owns subsequent numeric range design and C06 independently validates before Gate-S04. Do not invent absolute target/clutter amplitudes, statistical covariances or multi-target phase. Historic S03 owner/evidence retained.

Reproducible analytic source: engineering/s04_numeric/s04_c02_internal_arithmetic_v04.py; numerical results: engineering/s04_numeric/S04-C02-internal-arithmetic-error-propagation-v0.4.json; independent unit tests: tests/test_s04_c02_internal_arithmetic_v04.py. Full host environment and executed v0.3.1 nine-test rerun: engineering/S04-C02-V04-PYTHON-ENV-AND-V031-RERUN.log. v0.4 tests: engineering/S04-C02-V04-INTERNAL-ARITHMETIC-TESTS.log.

**OPEN:** real butterfly topology/operation rounding sites, internal multiplier/accumulator stagewise W/F, counters and saturation, verified Float/Fixed max and RMS, source-class admission for SCR and paired targets, Pfa/Pd, resource/timing. **NO architecture A/B/C or FFT shift schedule approved.** C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN; stage 12.5%, overall 26.04%.

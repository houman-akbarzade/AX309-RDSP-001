# AX309-RDSP-001 | S04-C02 CFAR Audit Repair v0.3.1

**CORRECTION ONLY — NOT APPROVED NUMERIC ARCHITECTURE.** C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN. S04 12.5%, overall 26.0416667%. Historical v0.3 report, JSON and generator unmodified.

## 1. Root cause of invalid right comparator width

The exact source bug in engineering/s04_numeric/s04_c02_coeff_shift_v03.py is:

    right_width = WS + f['alpha'][0]

The alpha tuple contains [numerator,Falpha], so the old expression incorrectly added 490007 (A/C) or 30625 (B) rather than an alpha unsigned word width. The Markdown renderer merely read the incorrect JSON value. The recorded erroneous widths were 490065 (A), 30674 (B), and 490059 (C); the left widths were correct. v0.3.1 uses explicit candidate alpha word widths A/C=20, B=16, and independent integer bit_length confirmation.

## 2. Independent full-precision and narrowed paths

Exact strict comparison: L=40*Pcut*2^Falpha > R=alphaNum*SUM40. Both power operands must have identical fractional scale, and exact equality produces NO ALARM.

Path N (narrowed operands): CUT and SUM40 are already unsigned Wpower and Wsum words respectively. Their independent maxima are 2^Wpower−1 and 2^Wsum−1. A conservative left product word requires Wpower+6+Falpha bits, and right requires Wsum+Walpha bits. Exact minimal product-width by bit_length(maximum integer product) is also computed.

Path F (unnarrowed full-precision arithmetic): signed FFT components have Wfft bits; their magnitude can be 2^(Wfft−1) for negative minimum. Thus max raw I²+Q² = 2*(2^(Wfft−1))², and max raw 40 sum is 40 times that value. Conservative raw power width is 2*Wfft+1; raw sum width adds 6 guard bits. Conservative product words are (2*Wfft+1)+6+Falpha on left and (2*Wfft+1)+6+Walpha on right. Independent exact bit lengths of the mathematically maximum values are also supplied. These are unsigned arithmetic-capacity estimates, not selected RTL.

| Option | Narrowed conservative L/R | Narrowed exact max L/R | Full-path conservative L/R | Full-path exact max L/R |
|---|---:|---:|---:|---:|
| A, Wfft28, Wpower52, Wsum58 | **74/78** | 74/77 | **79/83** | 77/80 |
| B, Wfft23, Wpower43, Wsum49 | **61/65** | 61/64 | **65/69** | 63/66 |
| C, Wfft25, Wpower46, Wsum52 | **68/72** | 68/71 | **73/77** | 71/74 |

The two paths are not interchangeable. Narrowing can lose power information *before* otherwise-overflow-safe comparator arithmetic; a full-precision path needs separately established internal accumulator widths. Neither path nor its saturation or rounding policy is approved.

## 3. Deterministic boundary checks

All candidate formats were independently checked at maximum Pcut, maximum SUM40, both maximum products, full raw negative FFT extremum squared on I and Q, maximum raw 40-cell training sum, and exact bit_length capacity. No product may wrap or silently saturate. Three exact threshold examples use SUM40=40*2^Falpha and Pcut=alphaNum−1, alphaNum, alphaNum+1: false / false / true under strict comparison. All are independently cross-checked using Python Fraction. Further tests exhaustively enumerate small unsigned width analogues to verify exact product sizing and decision equality.

**Nine deterministic unit tests PASS.** No stochastic CPI generated; these tests do not imply Pfa/Pd certification.

## 4. Audit of v0.3 FFT error coverage

v0.3 uses decoded stored input *after* C01 Q1.15 quantization as its reference input. Its quoted FFT error is therefore **not the error against the original unquantized Float source IQ**.

| Error source | Twiddle-only v0.3 | Combined conditional v0.3 | Remaining status |
|---|---|---|---|
| Original Float → input Q1.15 | Excluded | **Excluded** | C01 input error is separately bounded; full propagation OPEN |
| MF coefficients | Excluded | Included | candidate quantization only |
| Internal MF products / accumulators | Exact assumed | Exact assumed | **OPEN** |
| One MF output rounding | Excluded | Included as hypothetical RNE | site and policy OPEN |
| MTI arithmetic | Ideal | Exact subtraction + one output RNE | internal narrowing OPEN |
| FFT Twiddle approximation | Included | Included | actual coefficient format OPEN |
| Internal twiddle products | Exact assumed | Exact assumed | **OPEN** |
| Butterfly additions/subtractions | Exact assumed | Exact assumed | **OPEN** |
| FFT right shift implementation | Ideal division | Ideal division before one output RNE | signed shift/tie ordering OPEN |
| One output RNE per FFT stage | Excluded | Included hypothetically | actual site OPEN |
| Overflow / saturation | Excluded | Excluded | **OPEN** |

Input-only g=5 or g=1 bounds are |real reconstruction error| <= g/65536 and complex error <= sqrt(2)*g/65536 in normalized Float amplitude, provided no clipping. FFT stored-domain amplitude error converts to original Float-domain amplitude with multiplier g*Sfft; power uses (g*Sfft)^2. Input error cannot be simply appended numerically to v0.3 output error without propagating it through all MF/MTI/FFT operations.

## 5. Retained schedule comparison (no selection)

| FFT five-stage shifts | Sfft | Float amplitude reconstruction g5/g1 | Float power reconstruction g5/g1 | Candidate uniform stage-width conditional headroom |
|---|---:|---:|---:|---|
| [0,0,0,0,0] | 1 | 5 / 1 | 25 / 1 | A fits; B/C fail |
| [1,1,1,0,0] | 8 | 40 / 8 | 1600 / 64 | A/B/C fit, under stated assumptions |
| [0,1,0,1,1] | 8 | 40 / 8 | 1600 / 64 | A/B/C fit, under stated assumptions |
| [1,1,1,1,1] | 32 | 160 / 32 | 25600 / 1024 | A/B/C fit, under stated assumptions |

These comparisons use quantized MF and twiddle coefficients, but stage-format proxies and exact intermediate operations. They do not certify internal FFT product widths, processing saturation or bit-true error. C02 must select and approve actual internal operand W/F, butterfly ordering, rounding/shifting sites, and bounds before full architecture decision.

## 6. Binding unresolved obligations and evidence

REQ-SCR-01 and REQ-RNG-03 remain binding OPEN S02 requirements. C02 designs numerical dynamic range for declared clutter and multi-target inputs; C06 independently validates both before Gate-S04. Their missing source magnitude/phase/correlation specifications are not invented. Historical S03 owner and evidence unchanged.

Evidence: engineering/s04_numeric/s04_c02_cfar_audit_repair_v031.py; engineering/s04_numeric/S04-C02-cfar-width-arithmetic-audit-v0.3.1.json; tests/test_s04_c02_cfar_repair_v031.py; engineering/S04-C02-CFAR-ARITHMETIC-TESTS-v0.3.1.log. The v0.3 artifacts are left intact for historical comparisons. No main statistical CPI, accepted S03 seed, RTL, synthesis or FPGA testing.

**Official unchanged: C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN, S04 12.5%, project 26.04%.**

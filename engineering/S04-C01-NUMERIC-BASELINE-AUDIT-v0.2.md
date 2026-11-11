# AX309-RDSP-001 | S04-C01 NUMERIC BASELINE AUDIT v0.2

STATUS: READY FOR INDEPENDENT REVIEW / NOT APPROVED. S04 0/8; overall project 25%. Read-only audit of approved S02 v1.2, S03 Gate and Float model. No CPI, bit-true, RTL or hardware work.

## 1. Verified reference boundaries
S02 frozen input 33x128 complex samples, 16 chirp taps, MF aligned q=k+15, MTI33->32, unshifted FFT32 (5 radix-2 stages), 128x32 linear-power map, 40-cell CA-CFAR with 2782 valid CUT, strict CUT>alpha*mean40, 8-neighbor clustering, host one-to-one truth assignment. Signed Doppler labels -16..15; nominal velocity spacing 0.46875 m/s; exact range increment 149.896229 m; nominal 150 m. Input 16-bit pulse-major little-endian IQ layout is binding, Q1.15 numerical encoding a documented candidate.

Q(W,F) = signed W-bit two's-complement integer times 2^(-F) times explicit stage scale S; U(W,F) unsigned. IQ physical amplitude is normalized, NOT calibrated volts; power is normalized amplitude squared, NOT watts. Gaussian Float IQ is unbounded before clipping.

## 2. Complete boundary map
| ID | Interface and shape | Signedness, scale, unit | Bound under clipped IQ and ideal coefficient / precision need |
|---|---|---|---|
| B00 | 33x128 Float IQ | signed real/imag, normalized amplitude | Unbounded before quantizer; SNR active-echo; input clipping must be explicit |
| B01 | packed IQ 33x128 complex | signed int16 I/Q, candidate Q(16,15), S=1 | each component [-1,1-2^-15], magnitude <sqrt2, RNE and clipping count |
| B02 | MF taps 16 complex | signed, unitless complex | ideal magnitude 1; quantization width and phase error pending |
| B03 | MF 33x128 complex output | signed, normalized amplitude | magnitude <=16sqrt2=22.627417; convolution full 143 aligned outputs |
| B04 | MTI 32x128 complex | signed, normalized amplitude | magnitude <=32sqrt2=45.254834; signed subtraction |
| B05 | FFT32 128x32 complex | signed, scaled amplitude S=1 or 8 | unscaled magnitude <=1024sqrt2=1448.154688; scaled /8 <=181.019336 |
| B06 | RD power 128x32 | unsigned, squared amplitude S² | unscaled P<=2^21=2097152; /8 FFT case stored P<=32768 |
| B07 | 40-training power sums over 2782 CUT | unsigned, scaled power | unscaled sum <=83886080 <2^27; /8 case <=1310720 |
| B08 | mean and threshold | unsigned power and rational alpha | alpha=7.476912055027923, strict > and equality false |
| B09 | CFAR mask 128x32 | bool validity and alarm | valid range 3..109, unshifted Doppler bin 3..28 |
| B10 | 8-connected clusters | unsigned indexes, counts, nonnegative power | range 0..127, Doppler 0..31; exact ties, 8-neighbors no Doppler wrap, overflow flags |
| B11 | target list and host D/R/V/E/J | integer IDs; signed velocities m/s; ranges meters | Doppler bin signed mapping, nominal vs exact range, host matching distinct from FPGA list |
| B12 | readback and evidence | serialized W/F/S, integer flags and SHA | bit-exact diagnostics, I/Q endian, saturation counter and stage trace |

For input bounded only after quantization, the worst-case ideal MF gain is x16 (+4 amplitude bits), MTI x2 (+1), FFT x32 (+5). Power growth is square, sum40 needs +ceil(log2 40)=6 nonnegative integer bits. These are mathematical triangle-inequality bounds, not the expected operating distribution or guaranteed bounds after twiddle quantization and saturation. A clean target with amplitude .18 would have MF peak magnitude 2.88; this nominal signal-only fact cannot justify reducing worst-case guard widths for unbounded noise/clutter.

## 3. Traceability and limitations
- S02 source: engineering/S02-engineering-contracts-FINAL-PROPOSED-v1.0.md; engineering/S02-C-CFAR-02-CONTRACT-APPROVED-v1.2.md and approved requirements matrix.
- S03 Gate: decisions/GATE-S03-approved-baseline.json; model.py Float source and accepted Pfa/Pd are not bit-true data.
- S04 entry eight criteria and risk register remain unaffected.
- Historical Student-t 7/15 and spatial-transfer FAIL preserved. Pd 4135 unmatched target-present clusters are NOT noise-only Pfa. Full IQ and power-map arrays unarchived, only hashes and selected metrics remain.
- OPEN for C01 review: exact numeric formats and unit conversions, FFT quantized twiddles and intermediate arithmetic, source clipping/overflow budgets, CFAR near-threshold error classification, target-list capacity, and prospective oracle/test data.
- C01 has NOT been approved. No architecture committed; S04 0%, total 25%.

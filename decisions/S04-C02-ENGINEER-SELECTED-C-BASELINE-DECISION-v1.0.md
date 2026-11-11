# AX309-RDSP-001 | S04-C02 Engineer Baseline Decision and Sign-off Readiness v1.0

**ENGINEER-SELECTION APPROVED; CRITERION C02 OPEN.** Decision ID S04-C02-BASELINE-SELECTION-001. This document records the explicit current engineer selection of **C** and **FFT shift [0,1,0,1,1]**; it does not issue independent C02 final sign-off, reopen A/B/C option studies, or alter historical v0.5/v0.6 evidence. Original engineer message preserved in Replay event AX309-E0124; exact original platform send time not asserted.

## 1. Frozen numeric formats

| Interface | Selected format |
|---|---|
| Signed input and MF coefficient | Q16.15 |
| Signed MF output | Q22.15 |
| Signed two-pulse MTI output | Q23.15 |
| Signed FFT twiddle | Q16.15 |
| Signed outputs of all 5 FFT stages | Q25.15 |
| Unsigned power | U46.30 |
| Unsigned 40-cell sum | U52.30 |
| Fixed alpha | 490007/65536, numerator unsigned 20 bits |
| Strict CFAR | `40*Pcut*65536 > 490007*SUM40` |

All W/F values denote total word width W and fractional bit count F. The frozen integer tables for 16 MF taps and all 31 five-stage twiddle occurrences, endpoint formats, intermediate widths, Q scaling and operation semantics appear in `engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json`. Their source is the previously run v0.3 quantized coefficients; no accepted S03 seed is used.

## 2. Operational exact arithmetic contract selected from the executable v0.5/v0.6 model

**Input** follows approved C01 signed Q16.15 interleaved I/Q, little endian pulse-major: `q=SAT16(RNE(32768*x/g))`, with frozen pre-CPI g=5 for CN(0,1) noise-only or g=1 for the specified reference-like single-target laboratory test. Profile, logical metadata and event/INCONCLUSIVE/STRESS_ONLY policy remain immutable and cannot be adapted from observed detections. Physical UART/FPGA ICD is a separate future approval.

**MF16:** Frozen S03 reversed-conjugate LFM taps `h[k]=conj(chirp[15-k])`. For each output (pulse p, range r), full-convolution index r+15: sum k=0..15 samples at r+15-k (zero outside 0..127). Four signed real products of 16x16 bits give signed **W32/F30**; subtract/add into signed **W33/F30** complex pairs; complete 16-tap accumulation requires **W37/F30**. Calculate all integer products and sums exactly, then RNE to F15 **once per real/imag output**; guard then SAT to Q22.15. No multiplication or tap-level pre-rounding.

**MTI:** Exact `MF[p+1,r]-MF[p,r]` for p=0..31, 128 range bins. Signed full difference W23/F15; output signed Q23.15. RNE(F15 to F15) is identity. Guard against signed minimum and maximum and log any overrange before saturating.

**FFT32:** Forward, unnormalized, negative-exponent radix-2 DIT, bit-reverse the 32-point MTI input and preserve natural output bin order. Five butterfly spans (2,4,8,16,32), exact integer complex Twiddle multiply and exact aligned plus/minus computation. The input u is aligned to twiddle-product F30 via left shift 15. Perform exact `t=v*w`, then `u+t` and `u-t` with signed full width, then divide by `2^(15+s_j)` and apply **RNE ties-to-even once per output component**, followed by pre-narrow range check and SAT signed Q25.15.

| FFT stage | input W/F | product W/F | complex pair W/F | full butterfly W/F | shift | RNE integer divisor | output |
|---|---|---|---|---|---|---|---|
| 1 | 23/15 | 39/30 | 40/30 | 41/30 | 0 | 2^15 | 25/15 |
| 2 | 25/15 | 41/30 | 42/30 | 43/30 | 1 | 2^16 | 25/15 |
| 3 | 25/15 | 41/30 | 42/30 | 43/30 | 0 | 2^15 | 25/15 |
| 4 | 25/15 | 41/30 | 42/30 | 43/30 | 1 | 2^16 | 25/15 |
| 5 | 25/15 | 41/30 | 42/30 | 43/30 | 1 | 2^16 | 25/15 |

Extra pipeline/guard registers may be added without numerical changes; **no narrower intermediate arithmetic or moving the rounding location** is allowed without formal change authorization. RNE of a negative half is not a signed arithmetic right shift: `RNE(-1/2)=0`, whereas `(-1)>>1=-1`. Full real multiplication and butterfly addition precede each RNE.

**Power:** signed FFT real and imaginary components at W25/F15 squared at full signed **W50/F30**, summed as unsigned **W51/F30**, then guarded and saturated to **U46.30** with no power rounding/scale shift. Record original integer if outside the U46 interval; never silently wrap.

**SUM40:** Exact integer sum of 40 **already-narrowed** unsigned U46.30 powers from 7x7 training less central 3x3 guard, into **U52.30**. There are 2782 valid CUT. Perform strict integer CFAR: `40*Pcut*65536 > 490007*SUM40`. Comparison equality yields NO ALARM. Safe conservative unsigned crossproduct widths: **L68/R72** after narrowing, distinct from the **L73/R77** pre-power-narrowing capacity. Reference S03 alpha remains the separately approved Float **7.476912055027923**, not the model's default design initializer.

**Overflow:** No wrap, no silent saturation. Every intermediate product, complex pair and accumulator guard is checked; record site, pulse/range/Doppler/tap, component, sign, exact integer before limiting, range and sticky counter. At output/storage narrowing, record first, then saturate signed/unsigned according to frozen format. Any performance test subject to an unexpected overflow follows already approved C01 INCONCLUSIVE handling, fixed original denominator and no deletion/substitution/automatic retry. Stress-only patterns remain prospectively separate.

**Original Float reconstruction:** MF/MTI original amplitude = g*stored_integer/32768. FFT has cumulative division **8**: original amplitude = `g*8*FFT_integer/32768`, g1 gain factor 8, g5 factor 40. Stored power in original Float power units = `(g*8/32768)^2 * power_integer`, g1 multiplicative factor 64 and g5 1600 relative to normalized stored power. The actual SAT flags cannot be erased by reconstruction.

## 3. Selected baseline rationale, evidence and accepted limits

The engineer has decided **C**; prior paired evidence only supports and explains that decision. On the identical **14-ID no-saturation intersection** in v0.6, A/C distributed-shift FFT absolute error matched at **28,672 bins for each g**. For matched B vs C at each g, B had smaller error at 779 bins, C at 9469, with 18,424 equal; no formal statistical ranking is claimed. Hypothetical 128x32 complex FFT buffer bits: A=229376, C=204800, B=188416; no synthesis utilization inference. On the executed deterministic corpus, C distributed shift had no internal saturation events and zero changed CFAR CUT relative to the frozen S03 reference; this is not a general dynamic-range, Pfa or Pd guarantee.

**Known residual risk:** two S03 host cluster *peak signatures* differ even when C distributed-shift CFAR masks match. A native integer eight-connected cluster/peak/target-list implementation is not present. Neither full target-list matching nor output detection accuracy is approved. The engineering selection accepts this as a tracked downstream qualification item, **not** a waiver.

## 4. Ownership, required evidence and timing

Exact stage owners and pass conditions are frozen in `engineering/S04-C02-SELECTED-C-OPEN-OBLIGATIONS-v1.0.json`:

| Outstanding item | Owner / stage | Pass condition |
|---|---|---|
| Two host peak signature differences | C05 design, C06 independent | Reproduce both and pass native integer cluster/peak-tie oracle or explicit preapproved tolerance |
| Native integer grouping/target list | C05, C06 independent | 8-neighbor grouping, peak/tie rules and record format pass independent vectors |
| Final Float/Fixed MAX/RMS and CFAR budget | C06, with engineer preapproval | Fixed source-unit per-stage and end-to-end numerical tolerances approved *before* tests |
| Actual FPGA area/timing/power/memory | Future separately authorized RTL/hardware owners | Synthesis/implementation only after permission; meet approved resource/timing target |
| Fixed-point stochastic Pfa/Pd | C06/C07/C08 | Independently approved fixed-N design and qualification, separated seeds, no replacement or optional stopping |
| **REQ-SCR-01 BINDING OPEN** | C02 dynamic-range design, C06 independent | S02 SCR ±10dB source-region/phase/clutter envelope and numeric coverage independently qualified |
| **REQ-RNG-03 BINDING OPEN** | C02 coverage, C06 independent | S02 two-target separability near 600m and numeric coverage independently qualified |
| Complete ordered overflow trace (prototype currently first 24 + digest/count) | C03/C07, independent reviewer | Store all events and verify hashes/indices/readback before qualification |
| UART/FPGA ICD | Future interface engineer | Independent physical field/byte/metadata/overflow protocol approval |

Historical S03 ownership/evidence remain intact. No clutter or paired-target input profile/gain has been invented, and neither S02 obligation is implicitly passed. If later S02 source envelopes are inconsistent with the selected numerical contract, issue an explicit engineer change-control decision; never silently change architecture or input profile. Both binding requirements require explicit closure **before Gate-S04**, irrespective of this numeric baseline selection.

## 5. Engineering sign-off disposition

**C02: OPEN — READY FOR INDEPENDENT SIGN-OFF.** This package resolves the operative **numerical implementation semantics** needed to reproduce the selected C baseline: exact MF/FFT coefficient integers, W/F and signedness, full intermediate product/accumulator widths, stage shifts, RNE ties and timing of narrowing, SAT/no-wrap, physical source scales, SUM40 and strict alpha comparison. No critical ambiguity preventing construction of this deterministic arithmetic baseline was found in the readback and selected-C reruns.

Residual numeric performance acceptance, native cluster/record behavior, approved SCR and range-pair source models, and hardware resources are documented downstream requirements, not silently declared achieved. The independent reviewer must audit the selected files and decision authority. **Do not set C02=PASS until a separate explicit engineer approval message**. S04 remains **1/8 = 12.5%** and overall project **26.0416667%**, Gate-S04 OPEN. New A/B/C analysis v0.7 is not authorized. Historical data and signatures are unchanged.

## 6. Reproduction, traceability

Executable machine contract: `engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json`

Builder: `engineering/s04_numeric/freeze_s04_c02_selected_C_contract_v10.py`

Independent audit tests: `tests/test_s04_c02_selected_C_contract_v10.py`

Primary evidence: `engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json` and `engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json`.

Required reproducible selected-C test run from root:
`/usr/bin/python3 -B -m unittest discover -s tests -p test_s04_c02_selected_C_contract_v10.py -v`

No statistical acceptance CPI, S03 historical acceptance seeds, RTL, synthesis or FPGA use in this action. Git SHA and conversation replay archival readback are documented in evidence manifests linked to this decision.

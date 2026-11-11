# AX309-RDSP-001 | S05 CUT Geometry Audit v0.1

**Date:** 2026-11-12
**Disposition:** APPROVED_2782_CUT_GEOMETRY_CONFIRMED; no change to numerical or RTL baseline.

## Mathematical derivation

The 128 fast-time acquisition samples are n=0..127. The 16-sample chirp echo beginning at integer delay k occupies n=k..k+15. Complete echo containment requires 0<=k<=112 (128-16+1=113 complete-echo delays).

The approved matched filter is h[j]=conj(s[15-j]), j=0..15. It uses **full** linear convolution, 143 samples indexed q=0..142, and delay-aligns 128 outputs p[k]=z[k+15], k=0..127. It is **not** a 113-output valid-convolution processor. Delay-aligned outputs k=113..127 may be nonzero owing to partial support, but correspond to no fully contained echo beginning at those delays.

For an unwrapped 7x7 CFAR window, the purely geometric 128x32 stored map permits CUT r=3..124 and b=3..28: 122*26=3172. The approved S02 contract imposes the additional requirement that *the entire range-side CFAR window* remain in complete-echo support k=0..112. Therefore r+3<=112; r=3..109, b=3..28, giving (109-3+1)*(28-3+1)=107*26=2782 CUTs. The 15-range-row upper-boundary difference means 15*26=390 additional geometric-only CUTs are excluded; it is not a 15-CUT difference.

Full-echo-supported delay indices 110..112 are excluded as CUT centers because their CFAR windows would extend beyond 112. Indices 113..127 lack full-echo target support; their delay-aligned MF outputs are not necessarily identically zero. The first three range bins are excluded by the lower window border. Doppler CUT bins exclude 0..2 and 29..31, without wrap.

## Code and approved evidence

- Approved system contract: engineering/S02-engineering-contracts-APPROVED-AMENDMENT-v1.1.md (echo model, full linear MF convolution and delay alignment, complete-echo delay range 0..112, CFAR region r=3..109/b=3..28, 2782-CUT Pfa denominator).
- Approved requirement matrix: engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json (MF full echo containment distinct from CUT validity; frozen REQ-CFAR-02 CUT geometry and strict comparator).
- Float model: s03_reference/model.py, generate_cpi() checks k<=N-L, pulse_compress() executes np.convolve(...,mode='full') then selects z[:,L-1:L-1+N], VALID_R=slice(3,110), VALID_D=slice(3,29); cfar_2d() computes 40 training-cell powers for the fixed window.
- Integer oracle: engineering/s04_numeric/s04_c05_native_integer_v1.py, CUT_R=range(3,110), CUT_D=range(3,29), len(valid CUTs)=2782, strict stored-integer CFAR.
- MF RTL: rtl/mf16/mf16_serial_mac.v implements one supplied 16-tap output and range tag, not an MF convolution/frame controller; range scheduling and zero-outside-input-support are future controller responsibilities.
- CFAR RTL: rtl/power_cfar/cfar_2d_scan.v scans through last CUT (109,28) in ordered raster, no wrap, guard 3x3 excluded, 40 training cells.
- Existing unit TB: rtl/tb/tb_cfar_2d_scan.v checks the 4096 power-map loads and all 2782 ordered CUTs. Architecture record: engineering/S05-RTL-ARCHITECTURE-v0.1.md freezes the aligned MF output and 2782-CUT region.

## Decision and detection coverage

The asymmetry is **intentional and technically justified by the approved full-echo support and CFAR window constraints**. The existing 2782-CUT contract is CORRECT. A shift to 3172 CUTs would add 390 detection opportunities, alter the S02 Pfa denominator and the calibrated source population, and require explicit system-engineer contract change approval.

Within the accepted CUT domain, range centers correspond approximately to 449.689 m (r=3) through 16,338.688961 m (r=109) for c=299792458 m/s and Fs=1 MHz. Target delays outside this CUT region are not qualified for CFAR detection by this contract. This is distinct from any claim about REQ-RNG-03 target separability.

**Open S05 implementation check:** eventual full-CPI MF controller must prove alignment, zero-padding outside received input support, and valid address schedule. The MF serial MAC alone does not establish those integrated properties.

No CUT-region or numerical contract change is authorized or made. Gate-S04 remains CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03 FAIL 4/8 and Fixed-Point statistical performance OPEN remain unchanged. No CPI retested.

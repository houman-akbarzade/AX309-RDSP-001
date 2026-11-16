# AX309-RDSP-001 | MATLAB reference and fixed-point models

This folder contains **executable MATLAB R2024a counterparts** of the approved *software numerical chains* of the radar DSP laboratory. These models **do not replace** the signed baseline Python, Xilinx vendor C-model, board build, gate decisions, or retained statistical evidence.

## Getting started

On the authorized Linux machine (MATLAB R2024a, Python 3, NumPy, and locally installed licensed Xilinx ISE 14.7 required):

```matlab
cd('/home/houman/AX309-RDSP-001/matlab_model')
run_validation        % compares saved independent reference CPI outputs
demo_ax309            % plots Float and Fixed range-Doppler power
```

**Models:** `ax309_float.m` (entire S03 floating chain), `ax309_fixed.m` (integer MF/MTI/Power/CFAR/Grouping with actual FFT-IP v7.1 C-model), `ax309_grouping.m` (8-neighbor grouping), `ax309_generate_float.m` (optional MATLAB source generator), and `fft_vendor_bridge.py` (binary interface). `demo_ax309.m` visualizes the same saved input in both models. `run_validation.m` checks three replayable CPI fixtures.

The MATLAB Fixed model performs the stages **inside MATLAB** except for the FFT, which invokes the **exact vendor Xilinx FFT v7.1 bit-accurate C-model** through the repository's validated `engineering/s04_numeric/fft_ip_fullchain_v1.py` wrapper. This distinction is essential: substituting `fft()`, MATLAB fixed-point `fi/fft`, or a generic radix-2 FFT would **not** reproduce that IP's rounding, scaling, or overflow semantics. The vendor library is not bundled and the bridge verifies its SHA-256 identity.

### Pipeline and dimensions

1. **Input:** 33 × 128 complex IQ; for Fixed, signed 16-bit Q1.15, 16,896 bytes/CPI in pulse-major interleaved I/Q.
2. **MF16:** 16-tap complex matched filter, convolution output delayed by 15 samples; MF 22-bit signed, 15 fraction bits; coefficient integer Q1.15; **RNE once per complete dot product**, then saturation.
3. **MTI2:** difference of successive compressed pulses (33 → 32), 23-bit signed, 15 fraction bits.
4. **32-point Doppler FFT:** across the 32 retained slow-time pulses for each of 128 ranges, natural-order output. For the selected model: Xilinx xfft v7.1 radix-2 lite burst/BRAM, 25-bit input/output, 16-bit twiddle, convergent rounding, scaling schedule `[0,1,0,1,1]`. The bridge uses the original library SHA `4a8f02f24f269bc947d5f0d3e89a73916f763b8491c7a0f4e68b4bee88a994a9`. No MATLAB-only FFT is asserted bit-accurate.
5. **Power:** `I^2 + Q^2` with unsigned 46-bit saturation. All stored values and comparisons are **integer**.
6. **CA-CFAR:** 7 × 7 window minus 3 × 3 guard (40 training cells), 107 × 26 = 2,782 valid CUTs, strict `>`; fixed threshold ratio exactly `490007/65536` times the training mean. For exact comparison, `40 * CUT * 65536 > 490007 * SUM40` is evaluated by a **two-limb unsigned integer multiplier**, not in double. Float uses the separately frozen S03 `alpha = 7.476912055027923`.
7. **Grouping:** nonwrapped 8-connected flood fill, maximum stored Power, signed-Doppler bin minimum tie break, sorted records with **zero-based** range and Doppler indices. MATLAB array indices remain one-based.

### Source and reference mapping

| MATLAB | Canonical repository source |
|---|---|
| `ax309_float.m` | `s03_reference/model.py` |
| `ax309_generate_float.m` | `s03_reference/model.py` input waveform/source population |
| `ax309_fixed.m`, frontend coefficients | `engineering/s04_numeric/s04_c04_selected_C_stage_capture_v1.py` and `S04-C02-coeff-shift-quant-analysis-v0.3.json` |
| Xilinx FFT bridge | `engineering/s04_numeric/fft_ip_fullchain_v1.py` |
| Integer Power, CFAR, grouping | `engineering/s04_numeric/s04_c05_native_integer_v1.py` |
| `testvectors/` | Freshly saved outputs produced by the canonical Python pipelines, separately from MATLAB code |

### Input examples

```matlab
% Generate an ordinary MATLAB synthetic input (not sample-identical to NumPy PCG64):
target = [40, 1.875, 0.18, 0, 0];
iq = ax309_generate_float(target,20,12345,[]);
F = ax309_float(iq);
Q = ax309_fixed(iq,1);       % gain = 1 for a target-present CPI

% For noise-only Pfa-like inputs, project tests often use gain = 5 before quantization.
noise = (randn(33,128)+1i*randn(33,128))/sqrt(2);
Q0 = ax309_fixed(noise,5);
```

Use the **binary IQ archived from a specific board CPI** when performing a paired FPGA/MATLAB replay. A matching seed alone does not reproduce NumPy PCG64 samples in MATLAB. The local numeric suite does not grant hardware Pd/Pfa qualification.

### Verification performed

- MATLAB R2024a executed `run_validation` on **three CPIs**: all zeros, a single target with SNR 20 dB, and noise-only input (gain 5). The target and noise fixtures use respectively `SeedSequence([761113261,0,611])` and `SeedSequence([761113262,0,611])` in `s03_reference/model.py`.
- Float range-Doppler Power compared with Python `s03_reference/model.py` (relative floating-point tolerance).
- Fixed MTI words, vendor FFT integer words, 46-bit Power cells, 2,782-cut CFAR decisions, grouped target positions, counts and record IDs compared with separately generated Python source outputs; **all exact** for these three CPI fixtures.
- No clips or IP overflow on these fixtures. This is **finite regression evidence**, not exhaustive proof or a new statistical gate.
- The MATLAB process embeds older libstdc++ versions. To prevent NumPy loading the wrong ABI, the bridge launches Python with `LD_LIBRARY_PATH` and `LD_PRELOAD` unset; no global system changes.

### Limitations

- Floating `ax309_generate_float` draws pseudo-random samples from MATLAB's own MT19937 stream. It **does not** promise sample-identical output to NumPy PCG64 even with identical numeric seeds. The `testvectors/` files preserve exact samples and represent the valid cross-language comparison.
- The floating physical quantities use metres and m/s derived from a **hypothetical** 10 GHz carrier. The development board has no corresponding operational RF receiver.
- MATLAB model is not identical to the HDL line-by-line; Stage Lab, RTL, vendor C-model, and physical FPGA are separate implementations/evidence classes.
- Accepted S11 Pd/Pfa claims, amendments, scope restrictions and the older original-method gaps remain as recorded in `decisions/` and `engineering/`. Do not rerun a Monte Carlo test with different parameters and label it approved.

MATLAB models are for reproducible learning, inspection, and paired verification. No changes to accepted RTL, bitstream or frozen campaign records are made by this addition.

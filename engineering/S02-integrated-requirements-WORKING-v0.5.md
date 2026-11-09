# AX309-RDSP-001 — Integrated S02 Requirements & Acceptance v0.5 (WORKING)
Gate-S02: OPEN. S01 baseline previously approved. This review document is not an approved S02 baseline.
Full seven radar DSP functions MUST execute on AX309 FPGA, but not necessarily as seven RTL modules. Python only generates test IQ, comparison references and host control.
Source decisions S02-D01 through S02-D24; source index includes the engineer messages.
## Numeric and algorithmic baseline
- 33 pulses x 128 IQ samples/CPI, fs=1 MS/s, 16+16 bit input candidate, PRI=1ms, LFM center -125..+125kHz, duration 16us and 16 active samples, rectangular pulse envelope.
- For integer echo delay k, complete support k..k+15 inside 0..127 requires 0<=k<=112, or 0..16.8km range-equivalent. This is **not** valid matched-filter/CUT range by itself.
- SNR from isolated target active-echo average power versus complex Gaussian variance E|w|²=sigma²; component variance sigma²/2. Inputs SNR 0/10/20dB.
- Range bin 150m, noiseless grid-aligned single target exact corrected peak index; 20dB noisy ±1 bin is design target pending probability threshold. 600m LFM nominal resolution evaluated separately for two targets.
- Radial speed positive approaching; rectangular 32-pt Doppler FFT, 0.46875m/s bin step (10GHz assumed carrier) and conditional max half-bin speed error 0.234375m/s. MTI and off-bin leakage tested.
- FPGA CA-CFAR 2D mandatory. OS-CFAR optional. In independent seeded Gaussian noise-only CPI runs: Pfa design target 1e-3 per valid CUT and one-sided 95% upper CI must not exceed 1.5e-3, accounting for CUT dependence.
- Pd>=0.9 design goal for isolated target/no clutter/20dB. At 0/10dB measure Pd without minimum. No untested universal Pd promise.
- Clutter none, SCR +10/-10dB; input power support defined for calculation. Strong stationary clutter must challenge MTI.
- Variable-length list, explicit overflow, linear selected RD-cell power and scale, full stage readback available by reproducible rerun.
- UART CRC-32, length, sequence, fault handling, with platform-specific framing still to freeze.
- No FPGA architecture/SDRAM choice frozen; no physical fit inferred from raw 72KiB BRAM size; all resource limits and STA binding.

## Inspectable requirements traceability
Each requirement below has measurable obligation, method, acceptance rule, open dependency and responsible stage in the paired JSON file.

| ID | Classification | Gate disposition / owner |
|---|---|---|
| REQ-IO-01 | binding | S02 specification/S03 generator/S11 test |
| REQ-LFM-01 | binding | S02 freeze/S03 reference |
| REQ-SNR-01 | binding | S02 freeze/S03 statistical reference |
| REQ-RNG-01 | binding | S02 proof/S03 |
| REQ-MF-01 | binding | S02 convention/S03 proof |
| REQ-RNG-02 | design_target | S02 protocol/S03 feasibility |
| REQ-RNG-03 | binding_test | S02 protocol/S03 |
| REQ-MTI-01 | binding | S03/S04/S05 |
| REQ-DOP-01 | binding | S02 freeze/S03/S04 |
| REQ-CFAR-01 | binding | S02 freeze/S03 reference |
| REQ-CFAR-02 | design_target_with_binding_bound | S02 statistical protocol/S03 and S11 measurements |
| REQ-PD-01 | design_target | S03 analysis/S02 review if binding |
| REQ-SCR-01 | binding | S02 specification/S03 |
| REQ-DET-01 | binding | S02 spec/S04 bittrue |
| REQ-MATCH-01 | binding | S02 freeze/S03 |
| REQ-POWER-01 | binding | S02 interface/S04 |
| REQ-LIST-01 | binding | S02 behavior/S05 capacity |
| REQ-OBS-01 | binding | S02 interface/S05 design |
| REQ-UART-01 | binding | S02 protocol/S05/S11 |
| REQ-RES-01 | binding | S05 budget/S08 synthesis/S09 STA |
| REQ-TIME-01 | binding | S05/S11 |
| REQ-EVID-01 | binding | S06-S12 |

## Before S02 Gate: specification closure required, not hardware test results
1. Freeze discrete LFM sample/phase equation and linear matched-filter output index/peak-delay convention; define algorithmic valid range/CFAR CUT policy, or freeze precise deterministic derivation and checking method when S03 reference is needed.
2. Freeze IQ binary input layout and deterministic test vector manifest (endianness, signed numerical representation, seed, version, SHA-256); exact SNR and SCR measurement masks and calculation equations.
3. Freeze CA-CFAR training/guard/edge/CUT policies and Pfa CI estimator (CPI as cluster), one-sided 95% acceptance upper bound 1.5e-3, and predetermined trial stopping/power methodology; ensure 2D CUT correlation accounted for.
4. Freeze one-to-one truth assignment normalizers/gates/tie-breakers and conditional Doppler peak rule; freeze numerical test criteria or reference-based deterministic binding formulas.
5. Freeze UART CRC-32 variant/frame byte order, error/retry behavior, buffer semantics and negative test pass/fail oracle.
6. Provide traceable test owners, artifact and evidence checklist, documented deferral rules for any S03-S05 derived quantities, engineer review and explicit Gate-S02 approval.

## Allowed to derive in S03-S05 under a pre-approved test contract
- S03: MF valid range after agreed reference index, two-target separation reference behavior, noise range error distribution and detection/Pd feasibility, off-bin leakage, Pfa sample-size numeric determination under already-frozen stopping/confidence rules.
- S04: Bit-true internal word widths, overflow/saturation and rounding mapping, stage floating-point discrepancy bounds; exactly matching bit-true FPGA outputs remains binding.
- S05: BRAM vs optional SDRAM, bank ports/intermediate lifetime, time-sharing and RTL module architecture; per-resource headroom and physical list capacity/overflow selection, cycle counting.
- S08-S09: actual ISE synthesis and STA utilization/timing proof. S11: physical UART/readback and on-board implementation evidence. No unperformed result may be counted as achieved.

## Quantitative gate status and risks
S02 eight milestones remain open because acceptance oracle/test protocols require closure and no integrated acceptance has been formally reviewed. S02 progress 0/8=0%. Overall equal 12 stages 1/12=8.333%. No radar Python reference/RTL/board execution claimed.

# AX309-RDSP-001 — S02 Requirements and Acceptance, WORKING v0.3

**STATUS: working draft; engineer Gate-S02 OPEN; no tests executed.**
Historical v0.1 and v0.2 preserved; this document is a new immutable version for review.
Approved S01 baseline: see decisions/GATE-S01-approved-baseline.json.
Decision evidence: S02-D01..D09; source_index engineer_message_12 and engineer_message_13.

## Classification, traceability and evidence rules
- BINDING = functional or verification obligation explicitly endorsed by engineer.
- DESIGN_TARGET = quantitative aspiration; cannot be called statistically verified without a specified confidence/effective trials procedure.
- OPEN = unresolved numerical tolerance, estimator behavior, architecture or verification plan. Do not treat an OPEN value as approved.
- For each approved S02 acceptance row, record unique requirement ID, conditions, exact reference and metric formula, numerical pass/fail threshold, dataset and seed, number of trials / correlation policy, hardware/software method, log path, artifact version/hash and disposition.
- Seven FPGA DSP functions are mandatory FUNCTIONS, not seven required RTL modules.

## Binding requirement matrix (partial, pending acceptance metrics)

| ID | Class | Mandatory behavior, measurement and method | Open acceptance detail |
|---|---|---|---|
| S02-NUM-01 | BINDING | FPGA stage outputs bitwise identical to architecturally equivalent bit-true model under identical input and initial state. All deterministic output words must match exactly (zero mismatched bits). | Bit widths, arithmetic rounding/saturation/overflow and export formats defined in S04/S05; floating-point-stage error budgets still OPEN. |
| S02-RNG-01 | BINDING | Integer sample-index range estimates with matched-filter delay compensation, report bin-index and metre errors; range-bin spacing 150 m at fs=1MS/s; distinguish localization from nominal LFM range resolution ~600 m. | Matched-filter correlation/latency/valid CUT range and allowable single-target error OPEN. No sub-sample interpolation required. |
| S02-RNG-02 | BINDING | Independently test two-target resolution using separations around nominal 600 m in defined test environment. | Definition of resolvable pair, sidelobe/relative power and statistical acceptance OPEN. |
| S02-MTI-01 | BINDING | Compare zero-Doppler stationary clutter suppression and moving-target frequency response independently; quantify dB suppression and gain-vs-speed. | Exact MTI type, numeric attenuation and amplitude/phase error budgets OPEN. |
| S02-DOP-01 | BINDING | Check signed FFT bin index, signed velocity error m/s and leakage for both on-bin and off-bin signals (incl. -3,+1.5,+5 m/s). Approaching radial velocity is positive. | Window function, leakage metric, valid tolerance and peak-bin rule OPEN; no sub-bin interpolation required. |
| S02-CFAR-01 | DESIGN_TARGET | Noise-only zero-target zero-clutter complex Gaussian baseline; target Pfa=1e-3 per valid CUT after entire MF/MTI/FFT path. Empirical Pfa = false alarm count / valid tested CUT count, with uncertainty method qualifying correlated cells. | CFAR algorithm, guard/training, valid CUT/edge handling, independent trial count, confidence width, and Pd acceptance OPEN. Clutter tests separate; no universal Pfa guarantee. |
| S02-DET-01 | BINDING | Deterministic clustering and target-list bits match bit-true model exactly, separately evaluate radar-level correct/missed/false detections and range/velocity/power error against truth. | One-to-one association algorithm, match gates, error tolerances and Pd test sample size OPEN. No all-SNR guaranteed 3/3 target detection. |
| S02-RES-01 | BINDING | ISE resource and P&R/STA reports prove all mandatory FPGA functions fit device capacities and all defined clock constraints pass. | Numeric headroom by resource class OPEN; no blanket 90% cap. |
| S02-UART-01 | BINDING | USB-UART length, sequence ID, CRC-32; controlled faults must be detected (truncation, corruption, duplication, reordering); retransmission/recovery and full intermediate/final bytewise readback verified. | CRC-32 variant, framing/endianness, frame sizing, retry policy, speed and pass limits OPEN. |
| S02-TIM-01 | BINDING | Count actual board cycles per CPI with separately recorded link transfer time, report processor ms from proven clock. | Counter overflow handling, repetitions/reporting OPEN. |
| S02-VAL-01 | BINDING | Independent test for every FPGA DSP function plus entire integrated chain, with stored deterministic input and hardware evidence. | Corpus, repeated stochastic test count and numerical pass/fail rules OPEN. |

## Key statistical caveat
Cells of range-Doppler map are generally dependent because of pulse compression, MTI, FFT and CFAR windows; treating every CUT as an independent Bernoulli trial would understate uncertainty. Plan separate independent-CPI realizations, choose confidence interval procedure appropriate for clustered/correlated outcomes, and preserve seed and trial IDs.
Pfa=1e-3 is design target only for specified noise-only baseline, not measured compliance or a claim for heterogeneous clutter.
A moving-target off-bin Doppler velocity is not guaranteed to be accurate to less than half a bin when multiple targets, leakage or MTI distort the spectrum; quantitative tolerance needs a separate engineering decision.

## Progress and gate
S01 complete. S02 eight equal criteria exist in engineering/S02-progress.json. Because thresholds and approved test procedures remain incomplete, no S02 criterion is marked complete. S02=0%, project=100/12=8.3333% at 12 equal stage weights.
Gate-S02 OPEN. This document does not prove simulation, synthesized resource usage or operation on AX309.

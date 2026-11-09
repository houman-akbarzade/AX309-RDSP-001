# AX309-RDSP-001 — S02 Requirements and Acceptance — WORKING v0.4

STATUS: draft for engineering decisions; Gate-S02 OPEN. Earlier working drafts v0.1-v0.3 preserved. All decision histories are append-only in replay/events.jsonl.

## Decision classes
BINDING = approved obligation within stated conditions. DESIGN_TARGET = not yet unconditional pass/fail. OPEN = requires frozen measurement rule, dependent analysis or approval. No FPGA numerical, simulation, synthesis or board test is claimed.

| Requirement | Class | Quantitative acceptance rule or test | Open dependency |
|---|---|---|---|
| S02-NUM-01 | BINDING | FPGA deterministic outputs exactly match architecture-equivalent bit-true reference; zero bit mismatches at agreed exported interfaces and same reset/input state | Word widths, arithmetic order, exact state and reference validation |
| S02-RNG-01 | BINDING | In valid region, noise/clutter free single target at integer-sample delay: compensated peak index error exactly zero | Exact LFM sampled waveform, matched filter alignment, valid interval |
| S02-RNG-02 | DESIGN_TARGET | At input SNR=20 dB, range peak within one 150m sample; independently quantify two-target resolution (~600m theory) | Statistical confidence, number of trials, peak separation rule |
| S02-MTI-01 | BINDING | Separate fixed-clutter DC and moving-target frequency-response tests | Fixed-point attenuation tolerance and MTI realization |
| S02-DOP-01 | CONDITIONALLY BINDING | One dominant target with identifiable peak: nearest-bin velocity error <=0.234375m/s; test on-bin and off-bin plus boundary, leakage, MTI response | Peak-identifiability rule, FFT window and indexing/aliasing policy |
| S02-CFAR-01 | DESIGN_TARGET | Noise-only input complex Gaussian: Pfa=1e-3 per valid CUT, measured across independent seeded CPIs, report 95% CI with correlation-aware uncertainty | Exact CFAR, effective test size, acceptance tolerance and measured Pd |
| S02-CFAR-02 | DESIGN_TARGET | Single target no clutter, 20dB input SNR: Pd>=0.9 goal, subject to reference-model feasibility. Report Pd 0/10dB without minima | CFAR configuration, SNR, trials and confidence acceptance |
| S02-DET-01 | BINDING | One-to-one global minimum-cost truth association using normalized range/velocity, deterministic ties, never multiple assignment. Compare bit-true target list first, then radar truth confusion and range/velocity/power errors | Cost norm, match gate, power calibration/tolerance |
| S02-RES-01 | BINDING | Device capacity not exceeded, ISE implementation and STA meet constraints | Per-resource headroom, BRAM port/lifetime and data path |
| S02-UART-01 | BINDING | Length/sequence/CRC-32 framing; detect corruption/truncation/duplicate/reorder and controlled recovery; readback matches bitwise | Exact framing, CRC variant, timeout/retry policy |
| S02-VAL-01 | BINDING | Each of seven mandatory FPGA processing FUNCTIONS and full chain verified against independent references; no mandated number of RTL modules | Dataset counts, reproducibility schema, stagewise tolerances |

## Audit of outstanding topics
Independent potential policy decisions: phase-one LFM chirp waveform convention; noise power/SNR normalization and signal power definition; FFT window baseline; CFAR baseline family; CFAR statistical tolerance and confidence method; target-list capacity/overflow behavior; weak/strong clutter SCR baseline cases; debug stage-readback granularity; UART recovery acceptance policy; numerical proof treatment of CFD versus radar performance; range-validity convention; velocity aliasing test boundary handling; performance evidence format.
Engineering defaults without needing separate engineer decision: choose CRC-32/ISO-HDLC if CRC-32 variant unspecified, little-endian words when framing protocol frozen, fixed generator seed manifest and SHA-256 test-vector hashes; use 64-bit cycle counter unless design resource pressure dictates an equivalent overflow-safe solution; report all LUT/FF/DSP/BRAM utilization and STA with tool/version/hash.
Dependent items: exact valid range/CUT indices and MF delay require discrete LFM/matched filter definition; achieved noisy range and velocity statistics require reference runs; Pd goal feasibility and CFAR thresholds require CFAR/normalization plus reference model; margin percentages require architecture and map reports; timing closure requires implemented RTL; UART baud reliability requires board loopback; formal bit-true arithmetic tolerances require S04 bit-true specification and architecture.
None of above is falsely promoted to agreed numeric requirement. S02 remains 0/8 criteria closed; overall 1/12 completed.

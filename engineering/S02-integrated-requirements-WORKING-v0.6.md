# S02 Integrated Gate Review v0.6 | AX309-RDSP-001

Gate-S02 OPEN, new technical draft for engineer review. Earlier S02 versions preserved. All 22 requirements trace to the JSON matrix and six contract sections. No model execution, synthesis or board measurement performed.

| Domain | Frozen proposed contract | Test/acceptance overview |
|---|---|---|
| Signal/MF | 16 midpoint samples, centered complex chirp, linear MF p[k]=z[k+15] | Clean aligned peak exactly k; complete echo k=0..112 |
| IQ / SNR / SCR | signed int16 I,Q little-endian, pulse-major, pinned PCG64 generator, SNR complex variance | Source/hash replay; 0/10/20dB, SCR +10/-10dB |
| Doppler/association | 33->32 first difference; rectangular 32-point signed bins; unique 1:1 truth assignment | Half-bin criterion conditional, ambiguity separate |
| 2D CA-CFAR | 7x7 window excluding central 3x3, 40 training, 2782 valid CUT/CPI | 4096 independent CPIs, 10000 CPI bootstrap resamples, CI qualification, upper 95%<=1.5e-3 |
| UART | 529-byte max framing, CRC32 ISO-HDLC, 512 payload, stop-wait, up to 3 retries | Injected faults yield recovered or explicit error, full stage readback |
| Hardware and provenance | all seven FPGA functions; memory architecture optional, physical resource and STA limits hard | S05 resource plan, S08/09 proof, S11 board evidence |

## Acceptance and deferrals
S02 requirements are ready for engineering review, NOT formally approved. Methods and proposed oracles documented; statistical rare-event confidence procedure includes a required independent coverage-qualification gate. If this is not satisfied, no Pfa PASS may be claimed and a revised pre-approved CI procedure is required. S03 derives measured range/Pd/CFAR performance only after S02 approval; S04 determines bit-true numerical widths/error budgets; S05 determines memory allocation, RTL partitioning, target list capacity and resource-specific margins. Actual synthesis, STA and physical board execution occur later.

## Official milestone accounting
Seven technical criterion packages are drafted for review, but their wording requires approved requirements and the engineer has not approved the new contracts. Therefore 0/8 completed S02 acceptance milestones, overall project 1/12=8.3333% under accepted-gate weighting. Gate-S02 remains OPEN.

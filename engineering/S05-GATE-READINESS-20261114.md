# S05 architecture and interfaces Gate readiness — 2026-11-14

Status: READY_FOR_ENGINEER_GATE_DECISION, NOT YET APPROVED. Branch docs/fpga-engineering-repository-audit. This package evaluates the *design definition* of the selected laboratory FFT-IP configuration. It does not grant S06–S11 implementation or board acceptance.

| S05 design item | Disposition | Basis / boundary |
|---|---|---|
| S04 entry | PASS | GATE-S04-FINAL-ACCEPTANCE-20261114; no remaining S04 gate carryovers; original historical snapshots retained |
| Mission and FPGA/host allocation | PASS | S05-FINAL-FFT-IP-ARCHITECTURE-2026-11-14 and S01/S02 limited amendment; MF/MTI/FFT-IP/Power/CFAR/Grouping on FPGA, IQ source/GUI on PC |
| FFT numeric configuration/reference | PASS at specification level | Xilinx FFT v7.1 Radix-2 Lite/BRAM, 32-point, 25-bit I/O, convergent rounding, 10'h144 scale schedule; source XCO SHA256 58a4a71af573fc70ce6ba2a47662aa71dd22b7475e17cb4cf5b58d7fb15fb782, adapter SHA256 170642d68eb37794c86716eb6ac562964a7248e71df440e28f27b037ea3f5de7. IP-corresponding bit-true reference selected; C02 historical, no bitwise equivalence claim |
| Functional and stage interface mapping | PASS at specification level | S05-FFT-IP-AS-BUILT-TRACE-v1.0; six processing readbacks in separate Stage Lab images, IQ verified as input; range recomputation and target list mapping approved. Complete fixed comparisons and repeatability are S11 evidence obligations |
| UART frame and current CPI transaction | PASS at as-built design scope | S05-UART-AS-BUILT-ICD-v1.0 maps codec and RTL: S02 frame, R1 session SID, IQ verification, RESULT/COMMIT, full-chain Power readback; no real-time/Ethernet claim. Any R2/R1 broader proposal not embodied in RTL is not a feature of this baseline |
| Recovery and errors | PASS at approved limited design scope | S05-LAB-FAIL-CLOSED-RECOVERY-20261114; no automatic same-CPI recovery. Physical disconnect/reset response remains to be tested in S11 |
| Memory/list capacity and flow | PASS as design policy | 4096-cell Power memory; grouping backpressure and 0..702 record IDs; no silent truncation. Fit/STA and physical 702-case acceptance are S08/S09/S11 |
| Clock/pin/budget | DESIGN PINNED; physical proof deferred | 50 MHz, UCF SHA256 03bd52fedec6269c0b4e22c6e059fe83a4de296c5a4ca1720279ae74e1bde5fb; applied timing/resource reports exist but S08/S09 own their formal acceptance. Actual board pin/UART checks S11 |
| Gate authority | PENDING | Explicit system-engineer acceptance of this defined S05 scope and downstream ownership |

Remaining downstream obligations are concrete: independent FFT-IP model vs physical/full-chain comparison (including same-IQ Power and records), physical Pd/Pfa, REQ-RNG-03 on selected implementation if claimed, stage readback/repeated-run/bit-true evidence, full UART fault and reset behavior, overflow telemetry, resource/STA sign-off. None is silently treated as completed by S05.

Decision requested: approve Gate S05 for the laboratory as-built architecture and interfaces under this scope, without promoting S06–S11 tests. If approved, record final S05 decision and change Gate status; otherwise leave this candidate open with the specific blocking item.

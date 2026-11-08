# AX309-RDSP-001 — S02 Requirements & Acceptance WORKING v0.2
S02 Gate OPEN. Not an approved matrix. S01 v0.3 remains approved baseline. This revision preserves WORKING v0.1.
Classification: BINDING = required engineer-approved behavior; DESIGN TARGET = numerical target requiring measured/stated verification; OPEN = pending details. Seven FPGA functions are functional requirements and do not require seven RTL modules.

| ID | Class | Verification and pass criterion | Open details |
| --- | --- | --- | --- |
| S02-NUM-01 | Binding | Compare all deterministic FPGA output bits against architecture-exact bit-true reference for identical vectors/state: mismatch count MUST be zero. | Numeric scaling/rounding/saturation/overflow semantics and interface binary format pending |
| S02-NUM-02 | Binding | Compare stage outputs separately against floating Python reference with documented error budget. | Tolerances per stage OPEN |
| S02-MTI-01 | Binding | Independently test stationary clutter cancellation and moving targets against analytical frequency response. | Quantitative fixed-point attenuation/passband thresholds OPEN |
| S02-CFAR-01 | Design target | Goal Pfa=1e-3 per valid CUT in defined ensemble; measure empirical false-alarm fraction and confidence over adequate effective trials. | CFAR method/guard/train/edge, statistical pass bounds and Pd OPEN |
| S02-RES-01 | Binding | ISE utilization within XC6SLX9 physical limits and place-route/STA passes all constrained clocks. | Design-specific headroom OPEN; no 90% uniform ceiling |
| S02-UART-01 | Binding | Packet length + sequence ID + CRC-32; negative test corruption, truncation, duplication and reorder with controlled recovery; byte compare intermediate/final readback. | CRC variant, framing, retries, baud and throughput values OPEN |
| S02-RNG-01 | S01 carryover | Check matched-filter aligned output and valid range interval with edge tests. | Interval and range error bound OPEN |
| S02-DOP-01 | S01 carryover | Compare Doppler signed bins/velocity with known test target velocities. | Off-bin error/FFT window/tolerance OPEN |
| S02-DET-01 | S01 carryover | Compare detections/clusters/target parameters to reference. | Association and error bounds OPEN |
| S02-TIM-01 | S01 carryover | Measure FPGA-only CPI cycles and time separately from host link. | Counter/report reproducibility OPEN |
| S02-VAL-01 | S01 carryover | Verify each FPGA processing function and full chain with reproducible input corpus. | Test count, fixed seed manifest, statistically qualified thresholds OPEN |

S02 eight approved completion criteria remain in engineering/S02-progress.json: zero fully completed. S02 progress 0%, overall progress 8.333333% by equal weights of 12 stages. No Python model has been executed for this radar project, nor RTL simulation, synthesis, implementation or board testing.

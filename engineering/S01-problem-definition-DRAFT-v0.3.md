# AX309-RDSP-001: S01 Problem Definition
Draft v0.3. Gate-S01 OPEN. Not an approved baseline.
Basis: engineer messages 01-10; ALINX AX309 User Manual Rev 1.0, linked in evidence/source-index.json.
This document revises v0.2 and preserves the former revision as-is.

## 1. Problem statement and system boundary
The project shall demonstrate the complete radar processing chain executed on a *physical* AX309 board, with Python-generated deterministic test input and an independent Python reference for each output. Host-side computation of the reference outputs cannot be counted as execution of any mandatory radar processing stage on the FPGA. No real-time processing requirement applies during phase one, but processor cycles and duration must be measured independently of host communication.

### 1.1 Host PC (Python): test generation, control and verification, NOT radar hardware processing
- Generate seeded synthetic complex IQ for multiple targets, thermal noise, stationary and time-correlated clutter; record random seed, input model version, amplitudes and test parameters.
- Build CPI input vectors, transfer and verify received data over USB-UART (non-real-time, full CPI load before processing).
- Maintain Python floating-point functional reference and later bit-true fixed-point comparison model. Check FPGA intermediate and final outputs with stored tolerances; archive differences and logs.
- Use Python to display diagnostics, analyze hardware output and generate verification reports; these do not replace hardware stages.
- Define packet framing, retry/error detection, transfer speed and serial observation protocol in later stages; USB-UART physical suitability remains to be tested.

### 1.2 FPGA: seven mandatory radar processing functions
1. Pulse compression / LFM matched filtering on received IQ.
2. CPI range matrix construction and storage.
3. MTI clutter suppression.
4. Per-range Doppler FFT (32 points) and range-Doppler matrix.
5. 2D CFAR estimation and binary candidate detection.
6. Candidate grouping/clustering and target consolidation.
7. Generate target list with range, signed radial velocity and signal power.
All seven above must be implemented and executed on the FPGA in the completed project, not calculated on Python instead. Independent stage readback is mandatory. Data ingress, memory orchestration, telemetry and cycle count are ancillary hardware functions.
Original eight-function scope remains intact: synthetic IQ production is the one host-side function, while the seven listed processing functions are on-FPGA.

## 2. Engineer-approved preliminary parameters and test scenarios
- Board: AX309, XC6SLX9-2FTG256C, nominal oscillator 50 MHz.
- Candidate IQ input 16-bit signed I and 16-bit signed Q; sample rate 1 MS/s; nominal LFM B 250 kHz (provisional) and pulse duration 16 us; PRI 1 ms; 128 complex range samples per pulse; 33 input pulses per CPI; 32-point Doppler FFT after candidate first-difference MTI.
- Assume radar carrier 10 GHz for velocity model only, not for any physical RF source or FPGA ADC. Positive radial velocity means approaching; Doppler phase sign and FFT-bin mapping shall be consistent with this.
- Receive window sample n=0 coincides with LFM transmit start. Echo round-trip delay = 2R/c. 128 us corresponds to nominal 19.2-km range-equivalent time window, not a validated detection region. Matched filter delay, correlation definition and edge effects remain to be established.
- Three base targets: ranges 3, 6, 9 km and respective velocities -3, +1.5, +5 m/s; initial equal received echo power. Later unequal powers and optionally range-dependent attenuation.
- SNR test levels 0, 10, 20 dB; baseline 20 dB. Exact SNR average signal power, complex-noise variance and measurement point shall be determined quantitatively in S02.
- No-clutter baseline; stationary clutter with constant inter-pulse phase; weak/strong target-relative clutter levels; strong clutter test for MTI; later time-correlated extended clutter. Numeric SCR belongs in S02.
- Separate stationary-target MTI DC-null test, near-window-boundary tests, per-block verification and full-chain verification.
- Generator uses reproducible saved seeds; stable generator version/hashes and test vectors are required.

## 3. Hardware baseline and documentation evidence
Verified from AX309 User Manual Rev 1.0, 2019-04-26, in Google Drive:
- FPGA XC6SLX9-2FTG256C; nominal 9,152 logic cells, 16 DSP slices, 576 Kbit BRAM.
- SDRAM HY57V2562GTR, 256 Mbit, 16-bit bus.
- 50 MHz oscillator connects to FPGA T8.
- USB UART CP2102GM with FPGA RXD C11, TXD D12; dedicated JTAG interface.
These manual facts are not a test of a particular board revision, SDRAM operation, tool installation, UART baud limits or actual FPGA programming.

## 4. Mandatory feasibility constraints, explicitly unproven
Nominal BRAM=576 Kbit=73,728 bytes=72 KiB. For only three idealized 32-bit-per-element buffers:
- CPI input 33 x 128 x 4 = 16,896 bytes (16.5 KiB).
- 128 x 32 complex matrix x 4 = 16,384 bytes (16 KiB).
- 128 x 32 power matrix x 4 = 16,384 bytes (16 KiB).
Total 49,664 bytes (48.5 KiB), leaving a hypothetical 24,064 bytes (23.5 KiB). This is only a RAW CAPACITY comparison, not evidence of successful memory allocation.
Actual design must account for BRAM primitive size/aspect ratio, independent memory read/write ports, bank conflicts, simultaneous access demand, arithmetic bit growth, temporary buffers, FFT/twiddle needs, CFAR windows, clustering state, UART/debug buffers and appropriate margin. Actual memory placement, buffer lifetime, port-count scheduling and post-synthesis BRAM utilization are required evidence at later stages.
16 DSP slices and finite CLBs/LUTs impose further hard limits. Batch mode permits resource sharing, sequential passes and tiled operations, but no valid claim of fitting or clock closure is possible absent a scheduled architecture, ISE synthesis, place-and-route/STA and physical validation.
If resource limits are exceeded, an architectural redesign or engineer-approved scope change is mandatory. Python may never silently execute an FPGA-required function as a workaround.

## 5. Firm requirements vs open architecture choices
BINDING:
F01 All seven FPGA processing functions shall execute on physical AX309.
F02 Deterministic host-generated IQ plus independent Python reference.
F03 Batch CPI upload then FPGA execution, no real-time deadline for first phase.
F04 USB-UART input and intermediate/final results readback (communication parameters to be validated).
F05 Record FPGA processing cycles and actual milliseconds independently from UART transfer time.
F06 Signed velocity, range and power target list; modular input boundary for future ADC/SDR.
F07 Separate per-stage and full-chain verification, plus actual board proof with logged evidence.
F08 Document and obey hard resource constraints; report utilization, timing, failed tests and redesigns honestly.
OPEN ARCHITECTURE ALTERNATIVES:
A01 Whether external SDRAM is used at all; BRAM-only, SDRAM or hybrid are candidates. No final external memory choice approved.
A02 BRAM bank and port mapping, buffer overlap, tiling and data width growth.
A03 Sequential/parallel datapath scheduling and degree of DSP sharing.
A04 Exact MTI, FFT, 2D CFAR, clustering architecture and bit true formats.
A05 UART baud, packet format, error detection, retries and data ordering.
A06 Resource guardrails, algorithmic numerical thresholds and acceptance tolerances set in S02.
These open choices must not be treated as project acceptance criteria already met or as permission to reduce binding scope.

## 6. Feasibility risks and engineering gates
R1 HIGH: 2D CFAR and clustering logic, temporary state and debug readback on small XC6SLX9.
R2 HIGH: BRAM organization and multiport access may invalidate raw capacity assumption; SDRAM controller requires FPGA resources, timing analysis and independent testing if selected.
R3 MEDIUM: USB-UART transport throughput/error handling and practical intermediate output size; no real-time I/O requirement.
R4 MEDIUM: LFM BT=4, filter group delay/edge effects, finite achievable range resolution.
R5 MEDIUM: fixed-point rounding, overflow, detection threshold statistics and Doppler sign/MTI notch.
S01 acceptance is an approval of the DEFINED PROBLEM and acknowledged risks, not a demonstration of resource fit. S02 establishes measurable requirements and guardrails; S05 designs constrained architecture; S08 synthesis and S09 implementation/STA demonstrate actual fit/timing; S11 physical tests demonstrate board execution. If later feasibility fails, STOP relevant downstream Gate, document failure, redesign or obtain explicit engineer requirement change. The mandatory FPGA hardware boundary remains until engineer approves a formal change.

## 7. S01 exit criteria and evidence
- Requirement boundary identifies seven FPGA functions and Python-generated stimuli/reference, clearly distinguishing actual hardware output from host computation.
- Preliminary scenario, time/phase conventions and test families recorded with engineer decisions.
- AX309 hardware facts verified against manual, while board-specific unknowns explicitly marked.
- BRAM capacity AND organization, DSP/LUT limits, memory traffic and full-chain feasibility risks represented as constraints, with follow-on proof requirements.
- Binding functions separated from architectural choices, SDRAM optional pending analysis.
- Independent module tests, whole-chain validation and physical FPGA demonstration mandated.
- Versioned S01 document with preserved prior draft and reproducible provenance and review disposition.
- Engineer explicitly accepts document, approves final Gate-S01 and records artifact hash in Git/Replay.
Criteria for progress remain the already established eight equally weighted S01 milestones: 6 completed, 2 remaining (engineer accepted final document and explicit Gate approval).
S01 Gate OPEN, progress 75%, overall progress with equal 12 stages 6.25%.

## 8. Execution and evidence truth
No executed radar Python reference model, RTL simulation, ISE synthesis, bitstream implementation, static timing analysis, UART test or physical board test is claimed at this stage. All these statuses remain NOT EXECUTED. Draft v0.3 is ready for engineer review, not a signed baseline.

# S01 — Problem Definition (DRAFT v0.1)

Project: AX309-RDSP-001
Stage: S01 — Problem Definition
Status: ENGINEERING REVIEW REQUIRED; GATE OPEN
Source: Engineer decisions in current chat; hardware characteristics are engineer-supplied, not verified against AX309 manual.
No claim of Python simulation, RTL implementation, synthesis or FPGA board test is made.

## 1. Objective and scope
Demonstrate a full radar signal processing pipeline running on the real ALINX AX309 / XC6SLX9-2FTG256C using precomputed I/Q data loaded from a Python host. Pipeline: reproducible multi-target/noise/clutter I/Q generation; LFM matched filtering; CPI range matrix; MTI; 32-point Doppler FFT and range-Doppler map; 2D CFAR; detection and clustering; target list (range, signed radial velocity, signal power). Validate each block against a Python reference and then the end-to-end chain. This is an offline batch demonstrator; real-time throughput is not a phase-one requirement.

## 2. Preliminary system context
Engineer-reported: AX309, Spartan-6 XC6SLX9-2FTG256C, 9152 logic cells, 16 DSP48A1, 576 Kbit BRAM, 256 Mbit external SDRAM, 50 MHz board clock, ISE 14.7. Verify against original board manual and device documentation. Prefer assessing SDRAM first, but defer final allocation until bandwidth, BRAM port pressure and controller cost evaluation. USB-UART available per engineer report; baud capability and transfer protocol must be verified. No 10 GHz RF electronics are implied.

## 3. Parameter and time conventions
IQ signed complex 16+16 bit (candidate); fs=1 MS/s; nominal LFM B=250 kHz and pulse 16 us; PRI=1 ms; 128 received complex samples per pulse; 33 input pulses/CPI for candidate first-difference MTI followed by 32-point Doppler FFT (algorithmic ordering not yet approved); hypothetical fc=10 GHz. IQ receive window sample n=0 corresponds to transmit LFM start t=0, with t[n]=n/fs. Echo delay is 2R/c. Nominal window extent is 128 us or 19.2 km on range-equivalent scale, NOT a declaration that full interval is valid for detection. MF correlation, indexing, startup/ending effects and latency compensation must be defined in the Python reference.

## 4. Approved first-pass verification scenarios
Initial three targets at ranges [3,6,9] km, respectively radial velocities [-3,+1.5,+5] m/s with positive approaching. Python model must impose an internally consistent phase convention for positive Doppler, and report positive signed velocity accordingly. Input SNR cases [0,10,20] dB; 20 dB is the baseline. Define mean target echo power, noise circular complex variance and exact SNR measurement point in S02. Stationary clutter with constant slow-time phase for first test, then separate extended temporally correlated clutter. Include isolated stationary target to probe MTI DC notch, and targets near validity-window boundaries in separate tests. Independently check each DSP block and end-to-end processing. Use explicit RNG seed and record it with generated datasets.

## 5. Execution and timing
Load complete CPI through a host-to-board interface before processing. Record host transfer time separately from FPGA processing time. Count actual FPGA clock cycles and convert with confirmed effective clock to milliseconds. Keep modular input interface to facilitate later ADC/SDR substitution. No claim of meeting real-time operation until validated.

## 6. Constraints and provisional feasibility
Input storage: 33*128*4 = 16,896 bytes. An unscaled 128*32 complex 16+16-bit matrix: 16,384 bytes, but extra bit-growth, buffers, CFAR, intermediate results and memory fragmentation remain to be budgeted. Spartan-6 resources and SDRAM controller cost could dominate. Nominal LFM theoretical range resolution c/(2B) approx 600 m; this is provisionally accepted for proof of function, with measurable criterion pending S02. Doppler: PRF=1000 Hz and fc=10 GHz imply unambiguous speed approximately +/-7.5 m/s in centered convention, provided Doppler sign/alias conventions agree.

## 7. Unresolved S01 decisions and handoff to S02
- Confirm board pinout, actual clock, SDRAM interface, USB-UART and JTAG from primary AX309 manual; read-only evidence provenance required.
- Confirm treatment of external SDRAM as optional vs required for first demonstration.
- Decide the required hardware-visible output and readback/debug path for numerical FPGA/Python comparisons.
- Decide whether first demonstration must support all 8 blocks on FPGA or whether staged milestones are permitted while full final deliverable remains mandatory.
- Confirm proposed scope of clustered CFAR detections and numeric acceptance strategy; exact numerical thresholds and algorithms belong to S02/S03.
- For S02 define input signal normalization, noise variance, clutter amplitudes, target RCS/power, deterministic seed/precision, range-validity interval, MF delay and Doppler sign conventions.
- Establish board manual evidence, a measurable S01 exit checklist, draft revision/hash, and explicitly record engineer Gate-S01 disposition.

## 8. Gate and progress
Gate-S01 OPEN. Existing 8 equal-weight criteria: objective/scope approved; IQ source/Python model approved; batch timing approved; board manual verified OPEN; complete radar performance scenario approved OPEN pending power and acceptance context; preliminary resource/interface feasibility completed OPEN; S01 document completed and accepted OPEN; formal gate approval OPEN. Progress 3/8=37.5%; total project (equal-weight 12 stages) 3.125%. Writing this DRAFT does not complete acceptance criterion for approved S01 document.

## 9. Evidence and status
Approved parameters documented in decisions/S01-decisions.json (D01-D15) from cited real user chat messages. Replay append-only event records preserve source references. No testbench, RTL, synthesis, implementation, STA or hardware logs exist. On failure of gate review, revise draft and add a new decision event; never overwrite older replay events.

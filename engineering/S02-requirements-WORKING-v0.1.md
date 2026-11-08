# AX309-RDSP-001 — S02 Requirements & Acceptance, WORKING DRAFT v0.1
Status: S02 OPEN, awaiting engineer selections; no S02 requirement baseline approved.
Source baseline: engineering/S01-problem-definition-DRAFT-v0.3.md (content SHA-256 recorded in decisions/GATE-S01-approved-baseline.json).
Process: every requirement shall include ID, binding status, measured quantity, unit/reference point, test stimulus and repetitions, verification method, numerical acceptance rule, evidence artifact and owner; no unsupported blanket claims.

| ID | Required behavior / interface | Quantifiable metric and verification | Status |
| --- | --- | --- | --- |
| REQ-DAT-01 | Python-synthesized repeatable IQ, 128 complex samples x 33 pulses per CPI, fs=1 MS/s | Byte equality for fixed seed/config/version; inspect vector manifest and host/Fpga upload readback | metric/protocol pending |
| REQ-MF-01 | FPGA matched filter 250 kHz 16 us LFM | Compare aligned correlation output and peak range error vs Python bit-true reference at multiple ranges and edge positions | numeric tolerance and valid window pending |
| REQ-RNG-01 | Window n=0 at LFM TX origin, nominal 19.2 km span | Determine valid detection index interval from linear MF boundary response; verify guard cells and index-to-range map | interval pending MF reference |
| REQ-MTI-01 | FPGA MTI suppresses stationary clutter and preserves non-zero Doppler targets | Measure attenuation at fd=0 and passband response by amplitude/power relative to input, using isolated stationary and moving cases | thresholds pending |
| REQ-DOP-01 | FPGA 32-bin Doppler analysis, positive velocity approaching | Test signed Doppler bin index, velocity quantization and power leakage with known -3,+1.5,+5 m/s targets | tolerances and off-bin acceptance pending |
| REQ-CFAR-01 | FPGA two-dimensional CFAR | Estimate Pfa on noise-only trials, Pd for declared signal/clutter ensembles; define guard/train windows and edge policy | targets/iterations/statistical confidence pending |
| REQ-DET-01 | FPGA clustering and target list of range, velocity, power | Compare number of targets and errors with reference; specify missed/merged/duplicate handling, power conventions | thresholds pending |
| REQ-RES-01 | Full mandatory FPGA chain must fit XC6SLX9-2FTG256C | ISE map resource usage DSP <= 16, BRAM <= device capacity, LUT/FF usage <= device capacity; detailed margin/guardrails and congestion/timing closure required; staged synthesis evidence | guardrail margin pending |
| REQ-MEM-01 | BRAM allocation and optional SDRAM | Document all buffer size/lifetime and simultaneous access port requirements; verify no banking conflicts via RTL tests; SDRAM only if selected after resource trade | architecture selection pending |
| REQ-TIM-01 | Non-realtime CPI batch processing with separate host transfer and FPGA processing time | Read hardware cycle counter, measure valid clock frequency, compare wall-clock latency independently; repeat trials | repeatability/statistical summary pending |
| REQ-UART-01 | Non-realtime bidirectional CP2102GM interface | Send/recover full CPI and intermediate results, detect corrupt/truncated/reordered frames; record baud and throughput | CRC/packet policy and pass limit pending |
| REQ-VAL-01 | Software stage reference and hardware self-checks | For each of seven FPGA functions and end-to-end chain, independently compare to reference across SNR [0,10,20] dB, target/clutter test matrices | test-matrix counts and tolerances pending |
| REQ-EVD-01 | Actual FPGA implementation and hardware proof | Evidence from ISE build logs/STA, image hash, recorded board tests and replay audit chain; simulated-only results cannot satisfy | evidence format pending |

Important: Seven FPGA functions are requirements; this matrix does NOT prescribe RTL module count. CFAR/Pd/Pfa targets, bit-true rounding tolerances, memory architecture and UART packetization are not yet approved. Input 16+16-bit assumption is candidate and must be frozen. S02 Gate requires an explicitly approved complete numerical matrix. No executed tests exist.

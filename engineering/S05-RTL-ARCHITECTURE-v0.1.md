# AX309-RDSP-001 | S05 RTL Architecture Baseline v0.1

**Status:** DESIGN BASELINE IN PROGRESS; no S05 criterion is claimed complete by this document alone.
**Target:** ALINX AX309, XC6SLX9-2FTG256C. ISE 14.7 is installed on the development host; the board oscillator, pin map and timing constraints still require board-manual confirmation.
**Numeric baseline:** C02 selected architecture C, signed Q formats and FFT shifts [0,1,0,1,1]; unchanged.

## 1. Processing dimensions and order

- Input CPI: 33 pulses × 128 complex I/Q samples, pulse-major, signed 16-bit I and Q, little-endian at the host boundary.
- MF16: 16-tap linear convolution, delay-aligned output range 0..127 for each of 33 pulses. Out-of-support samples are zero.
- MTI2: MF[p+1,r] - MF[p,r], p=0..31, producing 32 slow-time samples for each of 128 ranges.
- FFT32: forward, unnormalised radix-2 DIT with negative-exponent twiddles; input order is bit-reversed and output order is natural. The frozen stage shifts are [0,1,0,1,1].
- Power: 128×32 stored U46.30 range-Doppler map.
- CA-CFAR: 7×7 window, central 3×3 excluded, 40 training cells; valid CUTs r=3..109 and b=3..28, exactly 2,782 per CPI; no wrap.
- Grouping: 8-connected components on the valid CUT mask, deterministic peak selection by stored U46.30 power and the frozen signed-Doppler/range tie order.

## 2. Numeric formats carried unchanged

| Boundary | Format |
|---|---|
| Input I/Q | signed Q16.15 |
| MF output I/Q | signed Q22.15 |
| MTI output I/Q | signed Q23.15 |
| FFT output I/Q | signed Q25.15 |
| Stored power | unsigned U46.30 |
| SUM40 | unsigned U52.30 |
| CFAR alpha | 490007/65536 |
| CFAR decision | 40*Pcut*65536 > 490007*SUM40; equality is no alarm |

MF coefficients and FFT twiddles are generated from the frozen C02 executable contract. RNE is applied only at the specified narrowing points. Signed wraparound is prohibited; saturation and pre-limit event telemetry remain mandatory.

## 3. Proposed dataflow and buffering

The first implementation uses a frame-buffered, time-multiplexed datapath rather than a fully parallel 16-tap FIR. This is a resource-conscious RTL organisation, not a change to the arithmetic contract.

1. **Pulse capture:** one 128×32-bit I/Q sample buffer. The input stream uses valid/ready; pulse and range indices are explicit.
2. **MF:** a serial 16-tap complex MAC processes each delay-aligned output range. Four real multipliers implement one complex multiply per tap; the 16 tap products are accumulated at full precision before the single Q30→Q15 RNE.
3. **Frame store:** 33×128 MF values are stored as sign-extended 50-bit complex slots. The physical memory depth is 4,224.
4. **MTI/FFT:** for each range, read all 33 MF values, form 32 full-width differences, load a 32-entry FFT scratch bank in bit-reversed order, execute 80 butterflies (16 per stage), then calculate power.
5. **In-place map reuse:** after a range's 33 MF values have been read, its 32 power values may overwrite the corresponding already-consumed frame-buffer address region. The address schedule must be verified in the integrated controller before use; no unread MF location may be overwritten.
6. **CFAR:** a sequential scan controller requests the CUT and 40 training powers through a synchronous-memory read interface, accumulates U52.30, and emits one ordered CUT decision.
7. **Grouping:** a streaming 8-neighbour labeler consumes every valid CUT in range-major/Doppler-minor order. It maintains current/previous row labels and a bounded union-find/statistics table. Target records are emitted through a back-pressured stream; no silent list truncation is allowed.

### Memory estimate (pre-synthesis)

The main 4,224×50-bit frame store contains 211,200 bits. A Spartan-6 BRAM18 geometry estimate is approximately 18 blocks for this width/depth organisation, before banking and port constraints are finalised. A 128×32-bit input buffer, 32×50-bit FFT scratch, row-label buffers and up to 702 cluster-stat entries add further memory. The 702 bound is the maximum independent-set count for a 107×26 grid under 8-neighbour connectivity: ceil(107/2)×ceil(26/2)=702. This is a capacity bound, not a measured resource result.

The design target is to keep the frame store in BRAM and avoid a second full-size power-map copy. Actual BRAM packing, dual-port scheduling, DSP48A1 use, LUT/FF count and timing are OPEN until XST/ISE reports are produced.

## 4. Clocking and throughput

The datapath clock is independent of the 1 MS/s sample-valid cadence. The first RTL does not hard-code a board oscillator. The controller must tolerate input back-pressure and must not assume a fixed clock ratio. A later timing budget will use the confirmed board clock and measured worst-case cycle counts for capture, MF, MTI/FFT, CFAR and grouping.

## 5. Internal module interfaces

All internal streaming boundaries use synchronous valid/ready handshakes. Data and metadata remain stable while valid && !ready.

| Module | Input | Output |
|---|---|---|
| mf16_serial_mac | start, tap_valid/index, signed I/Q sample, range tag | done, signed Q22.15 I/Q, saturation event |
| mti2_diff | two signed Q22.15 complex samples, valid | signed Q23.15 difference, valid |
| fft32_dit | 32 signed Q23.15 samples in bit-reversed order | 32 signed Q25.15 bins in natural order, overflow events |
| power_q25_u46 | signed Q25.15 I/Q | unsigned U46.30 power, saturation event |
| cfar_sum40 | 40 U46.30 training values | U52.30 sum, overflow event |
| cfar_compare | U46.30 CUT and U52.30 sum | strict alarm decision and exact comparison operands |
| grouping_8conn | ordered CUT coordinate, alarm and power | target-record stream and capacity/overflow flags |

The internal interfaces are implementation contracts only. They do not approve the physical UART/FPGA ICD, pin assignments or board-level transport.

## 6. Requirement impact and exclusions

- REQ-SCR-01 is PASS only within the engineer-approved 11-case scope. This does not silently admit other clutter, gain or source populations.
- REQ-RNG-03 remains technically FAIL: 4/8 mandatory scenarios passed. The 8/8 acceptance criterion is unchanged. By explicit system-engineer disposition dated 2026-11-12, this result is carried to final project evaluation and does not block S05 implementation. No S05 retest or retuning is authorized.
- S04-C02-RISK-PERFORMANCE remains OPEN: Fixed-Point statistical Pfa/Pd qualification is incomplete and is carried to final project evaluation. No statistical PASS is claimed.
- Target truth association remains host-side scoring; it is not substituted for hardware grouping.
- No changes are made to C01–C06 criteria, C02 formats, coefficients, alpha, RNE, saturation or FFT shifts.

## 7. Implementation sequence

1. Fixed-point arithmetic helper, MF16 and MTI2 RTL: implemented; local ISim smoke test PASS.
2. FFT32 DIT and power RTL: implemented; FFT zero/impulse smoke test and power arithmetic smoke test PASS.
3. SUM40 and strict CFAR comparator: implemented and locally tested. The 2-D CA-CFAR scan controller is now implemented, simulates all 2,782 valid CUTs in order, and synthesizes to the target Spartan-6 part. The 8-connected streaming grouping engine remains to be implemented.
4. Frame controller, memory schedule and top-level integration: not yet implemented. The 4,224-word MF frame-store to power-map overwrite schedule remains subject to explicit integrated-controller verification.
5. Continue block-level ISim and XST checks, then add common-vector oracle-driven RTL verification and full top-level synthesis/timing/resource review. The current unit tests are smoke tests, not C03–C05 end-to-end equivalence evidence.
6. Board-specific constraints and physical interface only after oscillator/pin/ICD confirmation.

**Current limitation:** this is the first S05 architecture baseline. No pre-existing S05 RTL or implementation was found in the repository at the start of this work.

# AX309-RDSP-001 | S05 CFAR Scanner to Grouping Interface/Verification Plan v0.1

**Status:** this is the pre-execution interface plan. The connected CFAR–Grouping RTL simulation and XST synthesis have now been performed and reported in engineering/S05-CFAR-GROUPING-INTEGRATION-REPORT-v0.1.md. Full radar-chain integration and board hardware qualification have NOT been performed.

## 1. Direct signal mapping

| cfar_2d_scan | grouping_8conn | Function |
|---|---|---|
| clk, rst | clk, rst | Common synchronous clock/reset |
| system controller start | start | Common new-CPI initialization while both engines idle |
| out_valid | in_valid | Ordered CUT record available |
| out_ready | in_ready | Back-pressure propagates to scanner |
| out_range[6:0] | in_range[6:0] | Range bin, 3..109 |
| out_bin[4:0] | in_bin[4:0] | Unsigned Doppler bin, 3..28 |
| out_power[45:0] | in_power[45:0] | Stored U46.30 CUT power |
| out_alarm | in_alarm | Strict CFAR alarm |
| out_equality | not consumed | Optional diagnostic, not grouping membership |

**Handshake invariants:** each CUT is accepted only when valid and ready are both high at the rising edge; while valid and not ready, coordinates, power and alarm must remain constant. Grouping checks the exact 2,782-CUT raster sequence. Neither engine may insert/delete CUTs.

## 2. Frame and control sequencing

1. Issue synchronous start to BOTH engines only after both previous frames are complete (not merely on scanner done). The grouping row banks initialize before the scanner finishes loading its 4,096 map words.
2. Feed the scanner a full range-major 128x32 power map through map_valid/map_ready. The scanner emits 2,782 ordered CUT records and pauses as required by grouping's in_ready.
3. The scanner's done pulse occurs after the last CUT handshake. It is NOT equivalent to end of grouping output; grouping may still be sorting and emitting records.
4. Grouping's out_valid/out_ready drives the downstream target-record sink; it remains stable on stalls.
5. Treat grouping done as the end-of-record-list indication for the CPI. Only then may a controller initiate the next frame. Any grouping frame_invalid, overflow_sticky or protocol_error invalidates that frame and must be reported to the host.
6. External host record limits, output-list selection/overflow behavior, and physical-unit record encoding remain subject to S05 engineer ICD decisions; do not silently impose a numerical cap.

## 3. Original verification plan (CFAR–Grouping ISim/XST executed; MAP/PAR remains pending)

- Drive one new synthetic 128x32 stored U46.30 map with deterministic spikes and zero/noise background; independently generate the exact 2,782 strict CFAR decisions and 8-connected grouping records from C03/C05 approved oracles. Do not use or reprocess historical REQ-RNG-03/C06 CPI files.
- Connect the actual scanner and grouping RTL ports; exercise pressure at map input, CUT stream, and target output.
- Assert monotonically ordered CUT coordinates, exactly 2,782 accepted records, no loss/duplication under back-pressure, correct final scanner done/grouping done sequencing, exact grouping records and repeated-frame reset.
- Run an all-zero map for zero-target completion and a dense/bridge mask case for late union and peak ties; avoid source modifications to the approved software oracles.
- Separately run integrated XST/MAP/PAR under confirmed board oscillator, physical interface, UCF and resource budget. Only post-route timing can establish timing closure.

**Gate:** The CFAR–Grouping subsystem simulation is now PASS for five synthetic maps with archived oracle comparisons. This does not establish PASS for the complete radar-chain MF/MTI/FFT/CFAR/Grouping integration.

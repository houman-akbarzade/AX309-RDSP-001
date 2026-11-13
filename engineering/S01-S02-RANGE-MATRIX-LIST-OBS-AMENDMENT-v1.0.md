# S01/S02 limited amendment v1.0: range data, target list and observability

**Status: APPROVED by the project system engineer on 2026-11-14.** Authority: decisions/S01-S02-RANGE-MATRIX-LIST-CLARIFICATION-20261114.json. This is a scoped overlay on S01 §1.2, REQ-OBS-01 and C-UART-01. Historical baseline files and results remain unchanged.

## S01 functional wording

Function 2: Form range-indexed data during the CPI and retain the values required for correct downstream processing. A complete persistent MF range matrix is not mandatory. Deterministic recomputation, buffer reuse or full storage are valid implementations, provided the logical MF output, indexing, dimensions and downstream values agree with the selected bit-true reference.

Function 7: Produce the complete FPGA target/cluster record list with ID, range cell, Doppler bin/sign, peak power and approved record fields. Transfer it without silent truncation, with an exact terminal count and valid CPI COMMIT. The host may convert range cells and Doppler bins to metres and metres per second under a recorded conversion/sign contract. No host-side Grouping substitutes for FPGA Grouping.

## REQ-OBS-01 / C-UART-01 mapping

The seven S01 functions do not require seven distinct physical output ports or seven simultaneous buffers. The selected six processing readbacks are MF, MTI, FFT-IP, Power, CFAR and Grouping/final records. Raw IQ readback is input verification, not a seventh processing output. Function 2 is checked through the complete logical MF sequence and the data consumed by MTI; Function 7 through the complete Grouping/final record stream and COMMIT. Separate deterministic stage configurations may be used with the same initial IQ and recorded build identity.

For every selected output, specify its ID, dimensions, ordering, signedness, binary point, validity/status flags, wire encoding and lifetime. Recover the complete binary output; compare equivalent same-input runs bitwise and compare to the corresponding FFT-IP bit-true reference under identical initial conditions. The finite stimulus matrix, seeds, tolerances where applicable, and evidence hashes shall be fixed before S11 acceptance. REQ-LIST-01 capacity and no-silent-drop policy are unchanged.

## Engineering trace

In the selected RTL, radar_cpi_core.v recomputes MF per slow-time pair and retains a prior result for MTI, cfar_2d_scan.v stores the 4096-cell Power map, grouping_8conn.v emits record fields, and uart_s05_dsp_top.v packs the 99-bit record for the reliable UART result transaction. The stage-lab application names six processing stages and separately echoes raw IQ. This establishes design mapping, not by itself full requirement PASS.

No Pd/Pfa criterion, range-resolution criterion, selected FFT-IP configuration, historical Gate disposition or S11 board acceptance changes under this amendment.

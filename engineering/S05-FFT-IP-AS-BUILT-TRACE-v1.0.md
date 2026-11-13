# S05 functional and interface trace for selected FFT-IP laboratory design

Status: REVIEW_CANDIDATE, Gate S05 decision pending. Source decisions: S05-FINAL-FFT-IP-ARCHITECTURE-2026-11-14, S01-S02-RANGE-MATRIX-LIST-CLARIFICATION-20261114 and S05-LAB-FAIL-CLOSED-RECOVERY-20261114. Normative wire proposal: S05-UART-AS-BUILT-ICD-v1.0.md. This trace describes designs and finite archived evidence, not S11 physical requirement acceptance.

| S01 function / interface | Selected FPGA implementation | Observable boundary | Reference and later acceptance |
|---|---|---|---|
| 1 MF compression | radar_cpi_core → mf16_serial_mac | Stage Lab MF signed22 F15, 33×128 logical output | Same quantized IQ, bit-true MF |
| 2 range data formation | per-range schedule and MF recomputation; prior MF pair held for MTI | complete logical MF sequence and tagged range/pulse order, no persistent full MF matrix | MF and MTI consumption equivalence under approved amendment |
| 3 MTI | mti2_diff | Stage Lab signed23 F15, 32×128 | bit-true first difference |
| 4 Doppler FFT/range-Doppler | Xilinx FFT v7.1 Radix-2 Lite/BRAM adapter with scale_sch=10'h144 | Stage Lab signed25 F15, 32×128 natural bins | corresponding vendor FFT-IP C-model plus independent Float functional reference; no C02 bitwise claim |
| 5 2-D CA-CFAR | power_q25_u46_serial and cfar_2d_scan, stored power_mem[4096] | Power U46.30 (full-chain stage4), Stage Lab CFAR valid-CUT mask and power | exact integer CFAR with 2782 valid CUTs; no PC-reconstructed mask substituted as actual FPGA mask |
| 6 Grouping | grouping_8conn, 8-neighbour | Stage Lab full records | independent grouping oracle, all valid groups |
| 7 target list | same Grouping record stream, UART RESULT/COMMIT | 99-bit record, contiguous IDs, count0..702, no silent drop | host validates fields/count/terminal transaction |
| Host IQ/GUI | synthetic IQ, PC UART and display | full-chain stage0 IQ readback; GUI may render actual Power/records | input bytewise identity; GUI truth and physical output distinct |

The six Stage Lab processing outputs have separate bitstreams and an operator GUI; raw IQ is an input witness, not a seventh FPGA processing output. Their finite archived tests are not proof of simultaneous full-chain stage readback. The as-built full-chain bitstream exposes IQ, Power and final records. The approved amendment allows deterministic staged rerun; a stage's selected image/configuration and exact input hash must be pinned for comparison. Whether the extant archives fully satisfy each REQ-OBS-01 repeated-run oracle is a S11 evidence question.

Other interfaces: UART framing/epoch/stop-and-wait and fail-closed reset policy in the ICD; internal valid/ready stream with no dropped records; 50 MHz clock and physical pins as captured in selected UCF/build. Resource fit and external timing are S08/S09; physical UART and FPGA results are S11. W5500 is excluded from this version. No continuous real-time throughput or physical RF input is claimed.

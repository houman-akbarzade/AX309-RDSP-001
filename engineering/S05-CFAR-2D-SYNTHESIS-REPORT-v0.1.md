# AX309-RDSP-001 | CFAR 2-D Scan Block Synthesis Report v0.1

**Tool:** Xilinx ISE 14.7 XST P.20131013
**Target:** XC6SLX9-2-FTG256 (Spartan-6 LX9, speed grade -2)
**Top module:** cfar_2d_scan
**Status:** XST synthesis PASS; block-level result only.

## Synthesized function

The block accepts one complete 128×32 U46.30 power map, stores 4,096 words, then scans the valid CUT region r=3..109 and b=3..28. For each CUT it reads the 7×7 window, excludes the central 3×3 guard region, accumulates the remaining 40 training cells in U52.30, and emits the strict CA-CFAR decision. The output stream is range-major/Doppler-minor and obeys valid/ready back-pressure.

## XST result

- HDL parsing/elaboration: PASS.
- Synthesis errors: 0.
- Synthesis warnings: 0.
- Inferred memory: one 4,096×46-bit dual-port block RAM.
- Physical BRAM mapping: 11 RAMB16BWER + 1 RAMB8BWER = 12 blocks.
- DSP48A1: 5.
- Slice LUTs: 464 / 5,720 (8%).
- Slice registers: 146 / 11,440 (1%).
- BUFG: 1 / 16 (6%).
- Reported I/O count: 170. This is the stand-alone block interface count, not a board-level pin assignment or integrated top-level I/O fit.

## Timing interpretation

XST reports a default synthesis-estimated minimum period of 7.152 ns (139.821 MHz). No board clock constraint/UCF, pin assignment, place-and-route or post-route timing analysis was applied. This estimate is not timing closure and must not be used as a board operating-frequency guarantee.

## Evidence

- Reproducible command: rtl/tools/run_xst_cfar_2d.sh
- RTL: rtl/power_cfar/cfar_2d_scan.v
- XST project and run script are generated under rtl/build/xst_cfar_2d/.
- NGC SHA-256: d2dccbf89701093b06ac27c3a099b04d066a9e3d2d91a82a41d52cb5cea0651e
- XST report archive: engineering/evidence/s05/CFAR-2D-XST-REPORT-v0.1.srp.gz
- Uncompressed XST report SHA-256: 7fb6991bd80e7d5b38180b39dd544a7d0900cd7b220e8b64861907f28f3240fc
Compressed archive SHA-256: cadbf806533a4646f83563ea7c214331423d15c99b7faaa3bb1cb43457a61320

**Scope limitation:** this is synthesis of cfar_2d_scan and cfar_compare only. It does not establish full radar-chain resource fit, integrated top-level synthesis, board I/O fit, placement, routing or timing closure.

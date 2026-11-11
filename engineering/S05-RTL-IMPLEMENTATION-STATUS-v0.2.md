# AX309-RDSP-001 | S05 RTL Implementation Status v0.2

**Status:** S05 implementation in progress. Block-level simulation and synthesis evidence now exists; no full-chain or FPGA qualification is claimed.
**Frozen design basis:** C02 architecture C, signed Q formats, RNE/saturation points and FFT shifts [0,1,0,1,1] remain unchanged.

## Implemented RTL blocks

- Signed RNE/saturate helper.
- C02 MF16 coefficient ROM and serial complex MAC.
- MTI2 difference.
- C02 FFT twiddle ROM and five-stage radix-2 DIT FFT32 controller/butterfly.
- Q25.15 to U46.30 power.
- SUM40 U52.30 and strict CFAR comparator.
- New 2-D CA-CFAR scan controller with a 4,096×46-bit power-map memory, synchronous read schedule, 7×7 window, central 3×3 guard exclusion, 40-cell accumulation and ordered 2,782-CUT output stream.

## ISim block-level verification

The complete local unit suite passes using Xilinx ISE 14.7 ISim:

| Testbench | Verified scope | Result |
|---|---|---|
| tb_mf_mti_rne | RNE ties, signed endpoints, MF complex MAC, MTI | PASS |
| tb_fft32 | Zero frame and impulse; 64 output bins checked | PASS |
| tb_power_cfar | Power saturation, SUM40 and strict CFAR boundary | PASS |
| tb_cfar_2d_scan | 4,096 map writes; all 2,782 valid CUT coordinates; 40 training cells; guard exclusion; equality boundary; output back-pressure | PASS |

The FFT32 controller was corrected after its unit test exposed a busy-state assignment conflict: the idle-state default branch cleared busy in the same cycle as start. The testbench also now holds ready through the handshake of the final output bin. Both corrections are covered by the passing zero-frame/impulse test.

The ISim compatibility helper redirects Fuse's hard-coded /usr/bin/gcc invocation to the bundled Xilinx GCC 6.2 compiler with the host multiarch include/startup paths. It does not modify the system compiler. Reproduce the unit suite with: bash rtl/tb/run_isim.sh

**Evidence:** engineering/evidence/s05/RTL-UNIT-SUITE-ISIM-v0.1.log and the four per-test logs in the same directory.

## XST synthesis

The 2-D CFAR scanner and strict comparator synthesize with XST 14.7 for XC6SLX9-2-FTG256:

- 0 errors, 0 warnings.
- 12 BRAM blocks: 11 RAMB16BWER + 1 RAMB8BWER.
- 5 DSP48A1.
- 464 LUT (8% of 5,720).
- 146 slice registers (1% of 11,440).
- 170 stand-alone module I/Os.
- Default synthesis estimate: 7.152 ns minimum period (139.821 MHz).

This is a block-level synthesis result only. There is no board UCF, integrated top-level, place-and-route or post-route timing report. The default period estimate is not timing closure. See engineering/S05-CFAR-2D-SYNTHESIS-REPORT-v0.1.md and the archived XST report.

Reproduce with: bash rtl/tools/run_xst_cfar_2d.sh

## Not yet implemented or qualified

- Streaming 8-connected component grouping and target-list/statistics output.
- Full CPI controller, input capture, MF frame-store schedule and top-level datapath integration.
- Integrated memory arbitration and proof that MF samples are not overwritten before consumption.
- Full-chain RTL comparison against the independent C03/C05 oracle on common, approved source vectors.
- Full top-level XST resource analysis, board constraints, place-and-route and timing closure.
- FPGA board programming and hardware verification.

The existing local testbenches are deterministic block smoke tests. They are not a replacement for C03–C05 oracle regression, C06R2 statistical qualification or system-level detection acceptance.

## S04 carryover

S04 is closed by explicit system-engineer disposition with open items transferred to final project evaluation. This is not a technical PASS for the carried items:

- REQ-RNG-03: FAIL, 4/8 mandatory cases; the 8/8 criterion is unchanged. No S05 retest is authorized.
- S04-C02-RISK-PERFORMANCE: OPEN; Fixed-Point statistical performance remains unqualified.

See engineering/S04-OPEN-ITEMS-CARRYOVER-v1.0.json and engineering/S04-C08-GATE-DISPOSITION-v1.2.md.

**S05 next implementation step:** implement the streaming 8-connected grouping block to consume the scanner's ordered CUT decisions, then integrate the CFAR/grouping output with the frame controller. Preserve the frozen numeric contract and the two S04 carryover dispositions.

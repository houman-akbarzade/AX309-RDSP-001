# AX309 Radar DSP — VHDL engineering project (ISE 14.7)

**Engineering status, 2026-11-16:** This is a separate VHDL derivative of the accepted Verilog RTL, NOT a replacement for the accepted design. All 20 VHDL design units compile in ISE 14.7. XST synthesis, Translate, MAP, Place & Route, and TRACE completed successfully; 4 focused GHDL tests passed. **Full cycle-accurate/bit-exact equivalence to the accepted Verilog has NOT been proved. No VHDL variant bitstream was generated or programmed.**

## Open in Project Navigator

File > Open Project:

    /home/houman/AX309-RDSP-001/rtl/vhdl_project/AX309_RadarDSP_VHDL.xise

The project targets **Spartan-6 XC6SLX9-2FTG256**. Its top is radar_ip_ax309_top, with the approved UART UCF and the original Xilinx FFT-IP netlist. The Source Hierarchy displays editable VHDL in src/: MF16, MTI, FFT adapter, Power, CA-CFAR, Grouping, CPI controller, UART, and board wrapper. Four VHDL testbenches in tb/ are associated with Behavioral Simulation only, not implementation.

There are 19 translated RTL modules and one additional **VHDL FFT-IP black-box declaration**. fft32_ip.vhd does NOT implement the proprietary IP butterfly; it uses the actual locally generated CoreGen fft32_ip.ngc.

## Actual tool results

| Check | Result |
|---|---|
| ISE VHDL analyzer | PASS: 20/20 units |
| Project Navigator open and hierarchy parsing | PASS |
| XST synthesis | PASS |
| Translate / vendor FFT netlist resolution | PASS |
| MAP | PASS: 3,904 registers; 4,839 LUTs; 1,421/1,430 occupied slices; 14/16 DSP48A1 |
| Place & Route | PASS |
| TRACE timing | PASS: all constraints met; minimum period 19.395 ns, Fmax 51.560 MHz at 50 MHz clock |
| Independent GHDL unit simulations | PASS: RNE+sat, MTI, threshold-exact CFAR comparator, 2-cell Grouping full-grid case |
| Whole-chain Verilog-VHDL input/output equivalence | NOT TESTED |
| FPGA hardware UART/CPI and Pd/Pfa gate with VHDL | NOT TESTED |
| VHDL bitstream or FPGA programming | NOT DONE |

**Important limitations:** Grouping simulation produced numerous IEEE numeric_std metavalue warnings from internal signals, despite passing its checked record and completion assertions. The VHDL mapping occupies 99% of available slices, so even a timing-passing VHDL design has much less headroom than desirable. Warnings require additional review. Do not treat these initial unit simulations as acceptance tests for the system.

## Critical FFT IP dependency

The XISE links to ../build/fft32_ip/fft32_ip.ngc relative to this folder, and to ../uart/AX309_UART_S05.ucf. The licensed binary NGC is present on the ASUS laptop but **not committed to GitHub**. On a fresh clone the existing RTL CoreGen configuration must be recreated first, with the accepted FFT v7.1 parameters (see rtl/ise_project/fft32_ip.xco and rtl/tools/prepare_radar_ip_build.py). Never silently replace it with another FFT.

## Run tests

    cd /home/houman/AX309-RDSP-001
    python3 rtl/vhdl_project/verify_ghdl.py --ghdl /usr/bin/ghdl

The test runner also accepts the path to any compatible GHDL binary. The original ISim fuse could not compile the generated simulation C on the current Linux/GCC installation (getcontext error); this is a simulator-host compatibility issue. Source VHDL successfully compiled with Xilinx ISE.

## Traceability and maintenance

The original accepted Verilog, bitstream and evidence were not modified. translation_report.json records the SHA-256 of each source. translate_verilog_to_vhdl.py is a **historical one-time translation helper**, based on a separately obtained FPGA Discovery non-commercial translator; it must NOT be rerun over delivered src/ because it overwrites later manual VHDL corrections. The delivered sources additionally fix VHDL memory indices, FSM choices, byte extraction, UART expressions, synthesis width handling and reset integration.

create_project.tcl reconstructs the independent XISE project only if that file does not already exist. compile_ise.py runs the ISE analyzer; verify_ghdl.py runs the 4 focused unit tests. The VHDL implementation must undergo **paired full-system regression and physical board validation** before any formal equivalence or acceptance claim.

Generated files (NGC/NCD, .bit, logs, ISim/GHDL outputs, temporary reports) are intentionally excluded from the Git repository. Save qualification evidence separately if this VHDL design is later promoted.

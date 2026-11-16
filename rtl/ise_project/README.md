# AX309 / Radar DSP — Xilinx ISE 14.7 graphical project

**This is an engineering-navigation convenience, not a new S01–S12 acceptance result.** All previously approved Verilog, UCF, testbenches and the selected SRAM bitstream remain unchanged.

## Open in Project Navigator

Open the following project through **File > Open Project** in ISE 14.7:

`/home/houman/AX309-RDSP-001/rtl/ise_project/AX309_RadarDSP.xise`

The project contains **19 implementation Verilog sources**, the **FFT-IP CoreGen configuration**, **one board UCF**, and **12 simulation-only Verilog testbenches**. Its explicit implementation top is `radar_ip_ax309_top`, for `xc6slx9-2-ftg256`. It uses the **Area** synthesis goal and `AX309_UART_S05.ucf` (50 MHz, 115200 baud). The legacy standalone `fft32_ip/ip_stub.v` is intentionally excluded from this GUI project to avoid duplicate design-unit warnings with the CoreGen configuration; it **remains unchanged on disk** and in the original command-line build.

In the **Design** pane, use the **Implementation** tab to explore the hardware hierarchy and the **Simulation** tab to select a `tb_*.v` simulation top. Testbenches have been explicitly removed from the Implementation source set. Selecting a testbench does not automatically supply the externally generated test vectors: consult the original RTL/test instructions and generate the needed vector files first.

## FFT-IP and rebuild boundaries

The editable IP configuration is `fft32_ip.xco` here (byte-for-byte copied from `rtl/experiments/fft_ip_20261112/configs/lite_bram.xco`); the actual previously built CoreGen output resides in `rtl/build/fft32_ip/`. An actual CoreGen run on this computer generated a netlist with a **different SHA-256** from the historic accepted netlist; examine CoreGen outputs, tool parameters, generated files, and hashes before treating the result as equivalent.

A local `fft32_ip_synth.v` is generated from the historical `ip_stub.v` as the ISE-required synthesis black-box declaration. The CoreGen implementation netlist produced in this GUI directory may have a different SHA-256 from the accepted historical NGC; it must not silently replace the approved NGC.

GUI **Synthesize - XST**, **Translate** and **Map** were executed successfully in this independent GUI project on 16 November 2026. This does **not** establish equivalence with the previously approved image, does not qualify placement/routing timing, and does not program the board. Synthesis emitted area-related warnings; do not interpret success as new Gate acceptance.

The accepted full-chain board image and reports remain under `rtl/build/ise_radar_ip_ax309/`; they were built with the **original CLI flow** `rtl/tools/run_ise_radar_ip_board.sh`, not from this newly created Project Navigator project. For faithful re-execution of that established build, use that script and its retained evidence manifest. In particular, opening this GUI project does **not** imply that a new GUI-built Bitstream will be byte-identical, timing-equivalent, or accepted under prior gates.

Do **not** overwrite an accepted bitstream, reprogram the FPGA, re-run all tests, or conflate fresh simulation/synthesis outputs with the approved S08–S11 evidence without a separate comparison. The project may generate its own `.ngc`, `.ncd`, reports and other temporary products, which should remain outside the tracked configuration files.

## Reproducible project generation

For a clean regenerated GUI project, keep source files frozen, remove or rename only the generated `.xise` in this directory, then run:

```bash
cd /home/houman/AX309-RDSP-001/rtl/ise_project
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
xtclsh create_project.tcl
```

The helper refuses to overwrite a present `.xise`, preserving edits made inside ISE. The source-selection postprocessor `finalize_project.py` fixes simulation-only associations and CoreGen path. Source, IP and UCF source files are referenced relative to this project and should not be copied into unrelated directories.

## Relevant original evidence

- `engineering/evidence/s10/full_ip_20261112/manifest.json`: accepted board configuration and source hashes.
- `decisions/GATE-S08-SYNTHESIS-MAP-APPROVED-20261114.json`: mapped resource disposition.
- `decisions/GATE-S09-ROUTED-TIMING-APPROVED-20261114.json`: implementation / timing disposition.
- `decisions/GATE-S10-INTEGRATION-BITSTREAM-APPROVED-20261114.json`: selected physical build.

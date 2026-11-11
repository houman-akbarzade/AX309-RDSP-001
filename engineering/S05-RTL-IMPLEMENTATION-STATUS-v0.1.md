# S05 Verilog implementation status v0.1

**Code present:** signed RNE+saturate, exact C02 MF16 coefficient ROM, serial MF16 MAC, MTI2 difference, exact C02 FFT twiddle ROM, 5-stage DIT FFT32 butterfly/controller (80 butterflies), Power U46.30, SUM40 U52.30, strict CFAR comparator, testbench sources for MF/MTI/RNE, FFT and Power/CFAR.

**Not implemented:** integrated CPI controller and memory scheduler, 2D CFAR window scanning, 8-neighbour grouping, end-to-end oracle comparison, board interface.

**Simulation:** Xilinx ISE 14.7 ISim Fuse successfully parses and elaborates the MF/MTI unit RTL and testbench. Compiling the Fuse-generated C main fails with the host GCC 15 environment; **no simulation PASS is claimed**. The temporary GCC-compat wrapper is diagnostic, not a verified simulator fix.

**Synthesis:** XST installed, but no accepted synthesis/resource/timing report for these new modules. BRAM, DSP, LUT and timing fit are unverified.

**Oracle linkage:** ROM generator reads frozen C02 executable JSON (SHA256 c7991b50a010a5646b6d2baa9b0eb86874fcc0d101fe9bb54c9ea575be06c856); 16 MF coefficients and 31 FFT twiddles. Testbenches are local deterministic smoke tests, **not** C03–C05 oracle regression or C06R2 reruns.

**Status:** preliminary, unverified RTL components; no S05 criterion PASS or claimed FPGA qualification.

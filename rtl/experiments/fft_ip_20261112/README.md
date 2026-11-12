# FFT IP laboratory benchmark — 2026-11-12

This experiment does not replace the approved C02 arithmetic, production RTL,
UART bitstream, or engineering acceptance. No new FPGA programming was done.

ISE 14.7 CORE Generator produced Xilinx FFT v7.1 for XC6SLX9-2FTG256:
32 points, one channel, fixed transform size, signed 25-bit input/output,
16-bit phase factors, scaled arithmetic, convergent rounding, natural output,
CE/reset/overflow ports enabled. The measurement wrapper sign-extends the
23-bit MTI input and fixes SCALE_SCH=0x144 ([0,1,0,1,1]), forward transform.
Complex multiplier option: use_mults_resources; butterfly option: use_luts.

All resource rows below are actual **MAP** results, including routing LUTs:

| Variant | LUT | FF | DSP48A1 | RAMB8BWER |
|---|---:|---:|---:|---:|
| Existing custom FFT, standalone diagnostic wrapper | 5589 | 1621 | 8 | 0 |
| Radix-2 Lite, data BRAM | 537 | 1040 | 4 | 2 |
| Radix-2 Lite, distributed data RAM | 665 | 1089 | 4 | 0 |
| Radix-2 Burst, data BRAM | 1043 | 1444 | 6 | 4 |

RAMB16BWER count is zero for all rows. RAMB8BWER are half-size RAM blocks;
do not confuse these counts with 18-kbit BRAM-site counts. The legacy XST
number was 5652 LUT; 5589 is the new comparable MAP number.
The Lite-BRAM MAP reduction is 5052 LUT (90.3918%).

Lite-BRAM completed PAR and TRCE with TS_clk=20 ns. Internal minimum
period 6.691 ns, slack +13.309 ns. External I/O delays/pins were not board
qualified; this is standalone-core timing, not full-radar timing or hardware.

Structural ISim tested Lite-BRAM and Radix-2-BRAM on the unchanged three
deterministic development CPI MTI/golden-FFT vectors: zero, single, multiple.
Each configuration produced 12288 ordered complex outputs without observed
overflow or unknown data. Lite output latency was 251 cycles to first and
282 to last; Radix-2 was 235/266. Lite-distributed was mapped, not simulated.

**Strict C02 bit-true equivalence FAIL** for both simulated configurations:
0/138/277 complex mismatches by CPI; max component differences 0/11/16 LSB.
Native C05 processing of those outputs changed 0/2/7 CFAR CUT decisions and
cluster counts 0->0, 12->10, 18->13. This is not statistical Pfa/Pd evidence
and does not justify accepting the differences automatically. IP overflow
wrap behavior also differs from C02 saturation. An IP-based experimental
numeric reference and explicit baseline-change disposition remain necessary.

Reproduction (generated vendor products stay in ignored rtl/build):

    bash rtl/experiments/fft_ip_20261112/run_trials.sh

The runner uses the same commands that were executed in temporary benchmark
directories. Its syntax and relocated vector paths were checked; it was not
rerun as a complete batch after packaging. compare_ip.py was executed on
both complete traces and reports the numeric FAIL separately from transport.

The first attempt to MAP a bare core netlist had no top-level PADs and was
trimmed entirely; those failed counts are never used. Resource reports use
the explicit ip_probe_top diagnostic wrapper. Vendor generated implementation
netlists are reproducible from the XCO; their hashes are retained in evidence.

Canonical benchmark evidence:
engineering/evidence/s05/fft_ip_20261112/manifest.json

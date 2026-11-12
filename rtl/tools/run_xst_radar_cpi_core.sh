#!/usr/bin/env bash
# DSP core only, with streaming external IQ read port; not a board bitstream.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/radar_cpi"
mkdir -p "$BUILD"
for path in common/rne_sat_signed common/rne_sat_fft43 mf16/mf16_coeff_rom mf16/mf16_serial_mac mti/mti2_diff fft32/fft32_twiddle_rom fft32/fft32_butterfly fft32/fft32_dit power_cfar/power_q25_u46_serial power_cfar/cfar_compare power_cfar/cfar_2d_scan grouping/grouping_8conn integration/cfar_grouping_subsystem integration/radar_cpi_core; do
 echo "verilog work $ROOT/rtl/$path.v"
done > "$BUILD/core.prj"
cat > "$BUILD/core.xst" <<EOF
run
-ifn $BUILD/core.prj
-ifmt mixed
-ofn $BUILD/core.ngc
-p xc6slx9-2-ftg256
-top radar_cpi_core
-opt_mode Area
-opt_level 2
-keep_hierarchy No
-rtlview No
EOF
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
cd "$BUILD"
xst -ifn core.xst -ofn core.srp > xst.log 2>&1
grep -A32 '^Device utilization summary' core.srp
echo 'A successful XST exit does NOT prove device fit; inspect resource limits.'

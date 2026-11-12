#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TB="$ROOT/rtl/tb"
BUILD="$ROOT/rtl/build/radar_cpi"
mkdir -p "$BUILD"
python3 "$ROOT/rtl/tools/generate_radar_cpi_vectors.py"
for path in common/rne_sat_signed common/rne_sat_fft43 mf16/mf16_coeff_rom mf16/mf16_serial_mac mti/mti2_diff fft32/fft32_twiddle_rom fft32/fft32_butterfly fft32/fft32_dit power_cfar/power_q25_u46_serial power_cfar/cfar_compare power_cfar/cfar_2d_scan grouping/grouping_8conn integration/cfar_grouping_subsystem integration/radar_cpi_core; do
 echo "verilog work $ROOT/rtl/$path.v"
done > "$BUILD/core.prj"
cp "$BUILD/core.prj" "$BUILD/tb.prj"
echo "verilog work $TB/tb_radar_cpi_core.v" >> "$BUILD/tb.prj"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
gcc -shared -fPIC -o "$ROOT/rtl/build/redirect_gcc_exec.so" "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl
export LD_PRELOAD="$ROOT/rtl/build/redirect_gcc_exec.so"
(cd "$TB" && fuse -mt off -prj "$BUILD/tb.prj" -o "$BUILD/tb_core" work.tb_radar_cpi_core)
unset LD_PRELOAD
(cd "$TB" && "$BUILD/tb_core" -tclbatch run_all.tcl) | tee "$BUILD/sim.log"
grep -q '^PASS tb_radar_cpi_core:' "$BUILD/sim.log"
if grep -q '^FAIL ' "$BUILD/sim.log"; then exit 1; fi

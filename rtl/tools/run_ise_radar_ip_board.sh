#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/ise_radar_ip_ax309"
TOP=radar_ip_ax309_top
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
python3 "$ROOT/rtl/tools/prepare_radar_ip_build.py"
if [ ! -s "$ROOT/rtl/build/fft32_ip/fft32_ip.ngc" ] || [ ! -s "$ROOT/rtl/build/fft32_ip/fft32_ip.v" ]; then
 (cd "$ROOT/rtl/build/fft32_ip" && coregen -b fft32_ip.xco -p coregen.cgp > coregen.log 2>&1)
fi
cd "$BUILD"
xst -ifn "$TOP.xst" -ofn "$TOP.srp" > xst.log 2>&1
echo XST_PASS
ngdbuild -sd "$ROOT/rtl/build/fft32_ip" -dd _ngo -nt timestamp -uc "$ROOT/rtl/uart/AX309_UART_S05.ucf" "$TOP.ngc" "$TOP.ngd" > ngdbuild.log 2>&1
echo NGDBUILD_PASS
map -p xc6slx9-2-ftg256 -w -o "${TOP}_map.ncd" "$TOP.ngd" "$TOP.pcf" > map.log 2>&1
echo MAP_PASS
par -w -ol high "${TOP}_map.ncd" "$TOP.ncd" "$TOP.pcf" > par.log 2>&1
echo PAR_PASS
trce -v 10 -s 2 -n 10 "$TOP.ncd" -o "$TOP.twr" "$TOP.pcf" > trce.log 2>&1
echo TRCE_COMPLETE
if ! grep -q 'All constraints were met' "$TOP.twr"; then echo TIMING_NOT_CLOSED;exit 2;fi
bitgen -w "$TOP.ncd" "$TOP.bit" > bitgen.log 2>&1
echo BITGEN_PASS_UNPROGRAMMED

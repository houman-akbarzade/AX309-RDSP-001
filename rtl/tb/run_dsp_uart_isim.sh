#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
python3 "$ROOT/rtl/tools/prepare_radar_ip_build.py"
if [ ! -s "$ROOT/rtl/build/fft32_ip/fft32_ip.v" ]; then
 (cd "$ROOT/rtl/build/fft32_ip" && coregen -b fft32_ip.xco -p coregen.cgp > coregen.log 2>&1)
fi
python3 "$ROOT/rtl/tools/generate_dsp_uart_vectors.py"
BUILD="$ROOT/rtl/build/dsp_uart_sim"
gcc -shared -fPIC -o "$ROOT/rtl/build/redirect_gcc_exec.so" "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl
cd "$BUILD"
LD_PRELOAD="$ROOT/rtl/build/redirect_gcc_exec.so" fuse -mt off -L unisims_ver -L xilinxcorelib_ver -prj sim.prj -o tb_dsp_uart work.tb_dsp_uart work.glbl > fuse.log 2>&1
./tb_dsp_uart -tclbatch "$ROOT/rtl/tb/run_all.tcl" > sim.log 2>&1
grep -q '^PASS tb_dsp_uart:' sim.log
if grep -q '^FAIL ' sim.log; then exit 1;fi
echo FULL_DSP_UART_ISIM_PASS

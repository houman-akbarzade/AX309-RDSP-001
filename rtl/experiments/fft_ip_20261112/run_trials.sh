#!/usr/bin/env bash
# Standalone resource/numeric experiments only. No FPGA programming.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
EXPERIMENT="$ROOT/rtl/experiments/fft_ip_20261112"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
BUILDROOT="$ROOT/rtl/build/fft_ip_trial"
mkdir -p "$BUILDROOT"
for trial in lite_bram lite_dist r2_bram; do
 BUILD="$BUILDROOT/$trial"
 mkdir -p "$BUILD"
 cp "$EXPERIMENT/configs/$trial.xco" "$BUILD/fft32_ip.xco"
 awk '/^SELECT/{exit} /^SET /{print}' "$BUILD/fft32_ip.xco" > "$BUILD/coregen.cgp"
 cd "$BUILD"
 coregen -b fft32_ip.xco -p coregen.cgp > coregen-run.log 2>&1
 test -s fft32_ip.ngc
 cp "$EXPERIMENT/ip_probe_top.v" .
 echo "verilog work $BUILD/ip_probe_top.v" > probe.prj
 cat > probe.xst <<EOF
run
-ifn $BUILD/probe.prj
-ifmt mixed
-ofn $BUILD/ip_probe_top.ngc
-p xc6slx9-2-ftg256
-top ip_probe_top
-opt_mode Area
-opt_level 2
-keep_hierarchy No
-rtlview No
EOF
 cat > probe.ucf <<EOF
NET "clk" TNM_NET = "clk_group";
TIMESPEC "TS_clk" = PERIOD "clk_group" 20 ns HIGH 50%;
EOF
 xst -ifn probe.xst -ofn probe.srp > xst-probe.log 2>&1
 ngdbuild -p xc6slx9-2-ftg256 -sd . -uc probe.ucf ip_probe_top.ngc probe.ngd > ngdbuild-probe.log 2>&1
 map -p xc6slx9-2-ftg256 -w -o probe_map.ncd probe.ngd probe.pcf > map-probe.log 2>&1
 test -s probe_map.ncd
 if [ "$trial" = lite_bram ]; then
  par -w -ol high probe_map.ncd probe.ncd probe.pcf > par.log 2>&1
  trce -v 3 -s 2 -n 3 probe.ncd -o probe.twr probe.pcf > trce.log 2>&1
 fi
 if [ "$trial" != lite_dist ]; then
  cat > sim.prj <<EOF
verilog work $BUILD/fft32_ip.v
verilog work /opt/Xilinx/14.7/ISE_DS/ISE/verilog/src/glbl.v
verilog work $EXPERIMENT/tb_fft_ip.v
EOF
  gcc -shared -fPIC -o "$BUILDROOT/redirect_gcc_exec.so" "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl
  export LD_PRELOAD="$BUILDROOT/redirect_gcc_exec.so"
  fuse -mt off -L unisims_ver -L xilinxcorelib_ver -prj sim.prj -o tb_fft_ip work.tb_fft_ip work.glbl > fuse.log 2>&1
  unset LD_PRELOAD
  ./tb_fft_ip -tclbatch "$ROOT/rtl/tb/run_all.tcl" > sim.log 2>&1
  grep -q '^PASS tb_fft_ip transport:' sim.log
  if grep -q '^FAIL ' sim.log; then exit 1; fi
  python3 "$EXPERIMENT/compare_ip.py" fft-ip-output.txt --out numeric-comparison.json
 fi
 echo "EXPERIMENT_COMPLETE $trial (not engineering acceptance)"
done

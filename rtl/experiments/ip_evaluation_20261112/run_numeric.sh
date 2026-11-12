#!/usr/bin/env bash
# Finite development comparison, not a Pfa/Pd acceptance run.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
EXP="$ROOT/rtl/experiments/ip_evaluation_20261112"
python3 "$EXP/build_numeric_vectors.py"
IPMODEL="$ROOT/rtl/build/fft_ip_trial/lite_bram/fft32_ip.v"
if [ ! -s "$IPMODEL" ]; then IPMODEL=/tmp/ax309-fft-ip-20261112/lite_bram/fft32_ip.v; fi
test -s "$IPMODEL"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
BUILD="$ROOT/rtl/build/ip_evaluation_numeric/sim"
mkdir -p "$BUILD"
cat > "$BUILD/sim.prj" <<EOF
verilog work $IPMODEL
verilog work /opt/Xilinx/14.7/ISE_DS/ISE/verilog/src/glbl.v
verilog work $EXP/tb_more_ip.v
EOF
export LD_PRELOAD="$ROOT/rtl/build/redirect_gcc_exec.so"
cd "$BUILD"
fuse -mt off -L unisims_ver -L xilinxcorelib_ver -prj sim.prj -o tb_more_ip work.tb_more_ip work.glbl > fuse.log 2>&1
unset LD_PRELOAD
./tb_more_ip -tclbatch "$ROOT/rtl/tb/run_all.tcl" > sim.log 2>&1
grep -q '^PASS tb_more_ip:' sim.log
if grep -q '^FAIL ' sim.log; then exit 1; fi
python3 "$EXP/analyze_float.py"

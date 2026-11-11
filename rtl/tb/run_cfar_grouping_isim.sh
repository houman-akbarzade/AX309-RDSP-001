#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TB="$ROOT/rtl/tb"
BUILD="$ROOT/rtl/build"
mkdir -p "$BUILD"
python3 "$ROOT/rtl/tools/generate_cfar_grouping_vectors.py" | tee "$BUILD/cfar_grouping_oracle.log"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
gcc -shared -fPIC -o "$BUILD/redirect_gcc_exec.so" \
 "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl
export LD_PRELOAD="$BUILD/redirect_gcc_exec.so"
(cd "$TB" && fuse -mt off -prj cfar_grouping_subsystem.prj \
 -o "$BUILD/tb_cfar_grouping_subsystem" work.tb_cfar_grouping_subsystem) | tee "$BUILD/cfar_grouping_compile.log"
unset LD_PRELOAD
(cd "$TB" && "$BUILD/tb_cfar_grouping_subsystem" -tclbatch run_all.tcl) | tee "$BUILD/cfar_grouping_sim.log"
grep -q '^PASS tb_cfar_grouping_subsystem:' "$BUILD/cfar_grouping_sim.log"
grep -q '^INTEGRATED RTL AND INDEPENDENT ORACLE PASS' "$BUILD/cfar_grouping_sim.log"
if grep -q '^FAIL ' "$BUILD/cfar_grouping_sim.log"; then exit 1; fi
echo "CONNECTED CFAR-GROUPING SIMULATION PASS"

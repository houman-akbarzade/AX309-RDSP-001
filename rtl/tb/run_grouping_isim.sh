#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TB="$ROOT/rtl/tb"
BUILD="$ROOT/rtl/build"
mkdir -p "$BUILD"
python3 "$ROOT/rtl/tools/generate_grouping_vectors.py" | tee "$BUILD/grouping_oracle.log"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
gcc -shared -fPIC -o "$BUILD/redirect_gcc_exec.so" \
  "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl
export LD_PRELOAD="$BUILD/redirect_gcc_exec.so"
(cd "$TB" && fuse -mt off -prj grouping_8conn.prj -o "$BUILD/tb_grouping_8conn" work.tb_grouping_8conn) | tee "$BUILD/grouping_compile.log"
unset LD_PRELOAD
(cd "$TB" && "$BUILD/tb_grouping_8conn" -tclbatch run_all.tcl) | tee "$BUILD/grouping_sim.log"
grep -q '^PASS tb_grouping_8conn:' "$BUILD/grouping_sim.log"
if grep -q '^FAIL ' "$BUILD/grouping_sim.log";then exit 1;fi
echo 'GROUPING RTL SIMULATION AND C05 ORACLE EQUIVALENCE PASS'

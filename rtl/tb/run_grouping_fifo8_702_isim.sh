#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TB="$ROOT/rtl/tb"
BUILD="$ROOT/rtl/build"
mkdir -p "$BUILD"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
gcc -shared -fPIC -o "$BUILD/redirect_gcc_exec.so" \
  "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl
export LD_PRELOAD="$BUILD/redirect_gcc_exec.so"
(cd "$TB" && fuse -mt off -prj grouping_fifo8_702.prj \
 -o "$BUILD/tb_grouping_fifo8_702" work.tb_grouping_fifo8_702) | tee "$BUILD/grouping_fifo8_702_compile.log"
unset LD_PRELOAD
(cd "$TB" && "$BUILD/tb_grouping_fifo8_702" -tclbatch run_all.tcl) | tee "$BUILD/grouping_fifo8_702_sim.log"
grep -q '^PASS tb_grouping_fifo8_702:' "$BUILD/grouping_fifo8_702_sim.log"
if grep -q '^FAIL ' "$BUILD/grouping_fifo8_702_sim.log"; then exit 1; fi
echo "GROUPING->FIFO LOSSLESS 702-RECORD SIMULATION PASS"

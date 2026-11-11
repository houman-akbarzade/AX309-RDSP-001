#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TB="$ROOT/rtl/tb"
BUILD="$ROOT/rtl/build"
mkdir -p "$BUILD"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
export PATH="$ROOT/rtl/tools/gcc-compat:$PATH"
cd "$TB"
run_one() {
  local project="$1" top="$2" name="$3"
  echo "=== ISim compile: $name ==="
  fuse -mt off -prj "$project" -o "$BUILD/$name" "work.$top"
  echo "=== ISim run: $name ==="
  "$BUILD/$name" -tclbatch "$TB/run_all.tcl" | tee "$BUILD/$name.log"
  grep -q "PASS " "$BUILD/$name.log"
}
run_one mf_mti.prj tb_mf_mti_rne tb_mf_mti_rne
run_one fft32.prj tb_fft32 tb_fft32
run_one power_cfar.prj tb_power_cfar tb_power_cfar
echo "ALL RTL UNIT TESTS PASS"

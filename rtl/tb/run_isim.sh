#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TB="$ROOT/rtl/tb"
BUILD="$ROOT/rtl/build"
mkdir -p "$BUILD"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh

# Fuse 14.7 calls /usr/bin/gcc by absolute path. Redirect that invocation to
# the bundled GCC 6.2 host compiler; do not alter the system compiler symlink.
gcc -shared -fPIC -o "$BUILD/redirect_gcc_exec.so" \
  "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl

run_one() {
  local project="$1" top="$2" name="$3"
  echo "=== ISim compile: $name ==="
  export LD_PRELOAD="$BUILD/redirect_gcc_exec.so"
  (cd "$TB" && fuse -mt off -prj "$project" -o "$BUILD/$name" "work.$top")
  unset LD_PRELOAD
  echo "=== ISim run: $name ==="
  (cd "$TB" && "$BUILD/$name" -tclbatch "$TB/run_all.tcl") | tee "$BUILD/$name.log"
  grep -q "PASS " "$BUILD/$name.log"
  if grep -q '^FAIL ' "$BUILD/$name.log"; then return 1; fi
}

run_one mf_mti.prj tb_mf_mti_rne tb_mf_mti_rne
run_one fft32.prj tb_fft32 tb_fft32
run_one power_cfar.prj tb_power_cfar tb_power_cfar
run_one cfar_2d_scan.prj tb_cfar_2d_scan tb_cfar_2d_scan
python3 "$ROOT/rtl/tools/generate_grouping_vectors.py" | tee "$BUILD/grouping_oracle.log"
run_one grouping_8conn.prj tb_grouping_8conn tb_grouping_8conn
grep -q '^PASS tb_grouping_8conn:' "$BUILD/tb_grouping_8conn.log"

echo "ALL 5 RTL UNIT TESTS PASS (MODULE-SCOPED ONLY)"

#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
for top in iq_cpi_store_probe mf_frame_store_probe iq_cpi_banked_probe mf_frame_banked_probe; do
  build="$ROOT/rtl/build/xst_${top}"
  mkdir -p "$build"
  printf 'verilog work %s/rtl/tools/resource_probe/%s.v\n' "$ROOT" "$top" > "$build/$top.prj"
  cat > "$build/$top.xst" <<EOT
run
-ifn $build/$top.prj
-ifmt mixed
-ofn $build/$top.ngc
-p xc6slx9-2-ftg256
-top $top
-opt_mode Speed
-opt_level 1
-keep_hierarchy No
-rtlview No
EOT
  (cd "$build" && xst -ifn "$build/$top.xst" -ofn "$build/$top.srp" > "$build/run.log" 2>&1)
  echo "XST_PROBE $top"
  grep -E 'Number of Slice LUTs|Number of Slice Registers|Number of bonded IOBs|Number of DSP48A1s|RAMB16BWER|RAMB8BWER|Number of errors|Number of warnings|Minimum period' "$build/$top.srp" | tail -15
 done

#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
for top in target_record_store8_probe target_record_store702_probe target_record_store8_distributed_probe; do
  build="$ROOT/rtl/build/xst_${top}"
  mkdir -p "$build"
  if [ "$top" != "target_record_store8_distributed_probe" ]; then
    printf 'verilog work %s/rtl/tools/resource_probe/target_record_store_probe.v\n' "$ROOT" > "$build/$top.prj"
  else
    : > "$build/$top.prj"
  fi
  printf 'verilog work %s/rtl/tools/resource_probe/%s.v\n' "$ROOT" "$top" >> "$build/$top.prj"
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
  grep -E 'Number of Slice LUTs|Number of Slice Registers|Number of Block RAM/FIFO|Number of bonded IOBs|Number of DSP48A1s|RAMB16BWER|RAMB8BWER|Number of errors|Number of warnings|WARNING:' "$build/$top.srp" | tail -20
 done

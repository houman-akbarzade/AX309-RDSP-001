#!/usr/bin/env bash
# Analysis runner: expected negative variants do not mean experiment failure.
# No board programming, bitgen, production RTL update, or acceptance change.
set -o pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
python3 "$ROOT/rtl/experiments/ip_evaluation_20261112/prepare_resource_probes.py" || exit 1
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
for variant in power cfar grouping cfar_pipelined grouping_ram_pipelined grouping_ram_globalclock; do
 cd "$ROOT/rtl/build/ip_evaluation_resources/$variant" || exit 1
 if ! xst -ifn probe.xst -ofn probe.srp > xst.log 2>&1; then echo "XST_FAILED $variant";continue;fi
 if ! ngdbuild -p xc6slx9-2-ftg256 -sd ../ip -uc probe.ucf ip_resource_top.ngc probe.ngd > ngdbuild.log 2>&1; then echo "NGDBUILD_FAILED $variant";continue;fi
 if ! map -p xc6slx9-2-ftg256 -w -o probe_map.ncd probe.ngd probe.pcf > map.log 2>&1; then echo "MAP_FAILED $variant";continue;fi
 if ! par -w -ol high probe_map.ncd probe.ncd probe.pcf > par.log 2>&1; then echo "PAR_REPORTED_FAILURE $variant";fi
 trce -v 3 -s 2 -n 3 probe.ncd -o probe.twr probe.pcf > trce.log 2>&1
 echo "PROBE_REPORTED $variant"
 grep -E 'timing errors detected|Minimum period is' probe.twr
done
echo "Read individual reports. This runner does not grant project acceptance."

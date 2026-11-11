#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/xst_cfar_grouping_subsystem"
mkdir -p "$BUILD"
cat > "$BUILD/cfar_grouping_subsystem.prj" <<EOF
verilog work $ROOT/rtl/power_cfar/cfar_compare.v
verilog work $ROOT/rtl/power_cfar/cfar_2d_scan.v
verilog work $ROOT/rtl/grouping/grouping_8conn.v
verilog work $ROOT/rtl/integration/cfar_grouping_subsystem.v
EOF
cat > "$BUILD/cfar_grouping_subsystem.xst" <<EOF
run
-ifn $BUILD/cfar_grouping_subsystem.prj
-ifmt mixed
-ofn $BUILD/cfar_grouping_subsystem.ngc
-p xc6slx9-2-ftg256
-top cfar_grouping_subsystem
-opt_mode Speed
-opt_level 1
-keep_hierarchy No
-rtlview No
EOF
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
cd "$BUILD"
xst -ifn "$BUILD/cfar_grouping_subsystem.xst" -ofn "$BUILD/cfar_grouping_subsystem.srp"
echo "XST_NGC=$BUILD/cfar_grouping_subsystem.ngc"
echo "XST_REPORT=$BUILD/cfar_grouping_subsystem.srp"
sha256sum "$BUILD/cfar_grouping_subsystem.ngc" "$BUILD/cfar_grouping_subsystem.srp"

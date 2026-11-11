#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/xst_cfar_2d"
mkdir -p "$BUILD"

cat > "$BUILD/cfar_2d_scan.prj" <<EOF
verilog work $ROOT/rtl/power_cfar/cfar_compare.v
verilog work $ROOT/rtl/power_cfar/cfar_2d_scan.v
EOF

cat > "$BUILD/cfar_2d_scan.xst" <<EOF
run
-ifn $BUILD/cfar_2d_scan.prj
-ifmt mixed
-ofn $BUILD/cfar_2d_scan.ngc
-p xc6slx9-2-ftg256
-top cfar_2d_scan
-opt_mode Speed
-opt_level 1
-keep_hierarchy No
-rtlview No
EOF

source /opt/Xilinx/14.7/ISE_DS/settings64.sh
cd "$BUILD"
xst -ifn "$BUILD/cfar_2d_scan.xst" -ofn "$BUILD/cfar_2d_scan.srp"
echo "XST_NGC=$BUILD/cfar_2d_scan.ngc"
echo "XST_REPORT=$BUILD/cfar_2d_scan.srp"
sha256sum "$BUILD/cfar_2d_scan.ngc" "$BUILD/cfar_2d_scan.srp"

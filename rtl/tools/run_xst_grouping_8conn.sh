#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/xst_grouping_8conn"
mkdir -p "$BUILD"

cat > "$BUILD/grouping_8conn.prj" <<EOF
verilog work $ROOT/rtl/grouping/grouping_8conn.v
EOF

cat > "$BUILD/grouping_8conn.xst" <<EOF
run
-ifn $BUILD/grouping_8conn.prj
-ifmt mixed
-ofn $BUILD/grouping_8conn.ngc
-p xc6slx9-2-ftg256
-top grouping_8conn
-opt_mode Speed
-opt_level 1
-keep_hierarchy No
-rtlview No
EOF
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
cd "$BUILD"
xst -ifn "$BUILD/grouping_8conn.xst" -ofn "$BUILD/grouping_8conn.srp"
echo "XST_NGC=$BUILD/grouping_8conn.ngc"
echo "XST_REPORT=$BUILD/grouping_8conn.srp"
if [ -s "$BUILD/grouping_8conn.ngc" ];then
  sha256sum "$BUILD/grouping_8conn.ngc" "$BUILD/grouping_8conn.srp"
fi

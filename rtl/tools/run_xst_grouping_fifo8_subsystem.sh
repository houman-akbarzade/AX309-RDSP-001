#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/xst_grouping_fifo8_subsystem"
mkdir -p "$BUILD"
cat > "$BUILD/grouping_fifo8_subsystem.prj" <<EOT
verilog work $ROOT/rtl/grouping/grouping_8conn.v
verilog work $ROOT/rtl/transport/record_fifo8.v
verilog work $ROOT/rtl/integration/grouping_fifo8_subsystem.v
EOT
cat > "$BUILD/grouping_fifo8_subsystem.xst" <<EOT
run
-ifn $BUILD/grouping_fifo8_subsystem.prj
-ifmt mixed
-ofn $BUILD/grouping_fifo8_subsystem.ngc
-p xc6slx9-2-ftg256
-top grouping_fifo8_subsystem
-opt_mode Speed
-opt_level 1
-keep_hierarchy No
-rtlview No
EOT
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
(cd "$BUILD" && xst -ifn grouping_fifo8_subsystem.xst -ofn grouping_fifo8_subsystem.srp)

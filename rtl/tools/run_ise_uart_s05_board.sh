#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/ise_uart_s05_ax309"
TOP="uart_s05_ax309_top"
mkdir -p "$BUILD"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
cat > "$BUILD/$TOP.prj" <<EOF
verilog work $ROOT/rtl/uart/uart_rx_8n1.v
verilog work $ROOT/rtl/uart/uart_tx_8n1.v
verilog work $ROOT/rtl/uart/s02_frame_echo.v
verilog work $ROOT/rtl/uart/s02_r1_reply_tx.v
verilog work $ROOT/rtl/uart/s05_iq_cpi_banked.v
verilog work $ROOT/rtl/uart/s05_session_arq.v
verilog work $ROOT/rtl/uart/uart_s05_session_top.v
verilog work $ROOT/rtl/uart/$TOP.v
EOF
cat > "$BUILD/$TOP.xst" <<EOF
run
-ifn $BUILD/$TOP.prj
-ifmt mixed
-ofn $BUILD/$TOP.ngc
-p xc6slx9-2-ftg256
-top $TOP
-opt_mode Speed
-opt_level 1
-keep_hierarchy No
-rtlview No
EOF
cd "$BUILD"
xst -ifn "$TOP.xst" -ofn "$TOP.srp" > "xst.log" 2>&1
test -s "$TOP.ngc"
echo "XST_BOARD_READY"
ngdbuild -dd _ngo -nt timestamp -uc "$ROOT/rtl/uart/AX309_UART_S05.ucf" \
    "$TOP.ngc" "$TOP.ngd" > ngdbuild.log 2>&1
test -s "$TOP.ngd"
echo "NGDBUILD_PASS"
map -p xc6slx9-2-ftg256 -w -o "$TOP_map.ncd" "$TOP.ngd" "$TOP.pcf" \
    > map.log 2>&1
test -s "$TOP_map.ncd"
echo "MAP_PASS"
par -w -ol high "$TOP_map.ncd" "$TOP.ncd" "$TOP.pcf" > par.log 2>&1
test -s "$TOP.ncd"
echo "PAR_PASS"
trce -v 3 -s 2 -n 3 "$TOP.ncd" -o "$TOP.twr" "$TOP.pcf" > trce.log 2>&1
test -s "$TOP.twr"
echo "TRCE_COMPLETE"
bitgen -w "$TOP.ncd" "$TOP.bit" > bitgen.log 2>&1
test -s "$TOP.bit"
echo "BITGEN_PASS_UNPROGRAMMED_BOARD_UNVERIFIED"
echo "BITSTREAM_PATH=$BUILD/$TOP.bit"
grep -E 'Minimum period|Number of Slice LUTs|Number of Slice Registers|#      RAMB|Number of bonded IOBs' "$TOP.srp" | tail -15 || true
grep -E 'All constraints were met|Timing errors|Timing constraint' "$TOP.twr" | tail -20 || true

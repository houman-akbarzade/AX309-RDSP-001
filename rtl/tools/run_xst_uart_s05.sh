#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/xst_uart_s05"
mkdir -p "$BUILD"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
for top in s05_iq_cpi_banked s05_session_arq s02_r1_reply_tx; do
    d="$BUILD/$top"
    mkdir -p "$d"
    cat > "$d/$top.prj" <<EOF
verilog work $ROOT/rtl/uart/uart_rx_8n1.v
verilog work $ROOT/rtl/uart/uart_tx_8n1.v
verilog work $ROOT/rtl/uart/s02_frame_echo.v
verilog work $ROOT/rtl/uart/s02_r1_reply_tx.v
verilog work $ROOT/rtl/uart/s05_iq_cpi_banked.v
verilog work $ROOT/rtl/uart/s05_session_arq.v
verilog work $ROOT/rtl/uart/uart_s05_session_top.v
EOF
    cat > "$d/$top.xst" <<EOF
run
-ifn $d/$top.prj
-ifmt mixed
-ofn $d/$top.ngc
-p xc6slx9-2-ftg256
-top $top
-opt_mode Speed
-opt_level 1
-keep_hierarchy No
-rtlview No
EOF
    echo "XST_START $top"
    (cd "$d" && xst -ifn "$d/$top.xst" -ofn "$d/$top.srp") > "$d/run.log" 2>&1
    test -s "$d/$top.srp"
    if grep -E 'ERROR:|ERROR\s*:' "$d/$top.srp" "$d/run.log"; then
        echo "XST_FAILED $top"
        exit 1
    fi
    echo "XST_NO_ERRORS $top"
    grep -E 'Number of Slice LUTs|Number of Slice Registers|#      RAMB|#      DSP48A1|Minimum period|Number of bonded IOBs' "$d/$top.srp" | tail -16 || true
done
echo "XST_UART_S05_THREE_STANDALONE_TOPS_COMPLETE"

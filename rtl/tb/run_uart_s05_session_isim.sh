#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TB="$ROOT/rtl/tb"
BUILD="$ROOT/rtl/build/uart_s05_session"
mkdir -p "$BUILD"
python3 "$ROOT/rtl/tools/generate_uart_r1_vectors.py" | tee "$BUILD/pc_golden.log"
source /opt/Xilinx/14.7/ISE_DS/settings64.sh
gcc -shared -fPIC -o "$BUILD/redirect_gcc_exec.so" \
    "$ROOT/rtl/tools/gcc-compat/redirect_gcc_exec.c" -ldl
export LD_PRELOAD="$BUILD/redirect_gcc_exec.so"
(cd "$TB" && fuse -mt off -prj uart_s05_session.prj -o "$BUILD/tb_uart_s05_session" \
    work.tb_uart_s05_session) 2>&1 | tee "$BUILD/compile.log"
unset LD_PRELOAD
(cd "$TB" && "$BUILD/tb_uart_s05_session" -tclbatch run_all.tcl) 2>&1 | tee "$BUILD/isim.log"
grep -q '^PASS tb_uart_s05_session:' "$BUILD/isim.log"
if grep -q '^FAIL tb_uart_s05_session:' "$BUILD/isim.log"; then exit 1; fi
echo "UART_S05_SESSION_ISIM_PASS"

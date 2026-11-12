#!/usr/bin/env bash
# Icarus fallback: ISim 14.7 crashes internally while compiling this full TB.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/rtl/build/radar_cpi"
mkdir -p "$BUILD"
python3 "$ROOT/rtl/tools/generate_radar_cpi_vectors.py"
IVL="${IVERILOG:-$HOME/.local/opt/ax309-sim/usr/bin/iverilog}"
VVP="${VVP:-$HOME/.local/opt/ax309-sim/usr/bin/vvp}"
IVLBASE="${IVERILOG_BASE:-$HOME/.local/opt/ax309-sim/usr/lib/x86_64-linux-gnu/ivl}"
ARGS=()
if [ -d "$IVLBASE" ]; then ARGS=(-B "$IVLBASE"); fi
SOURCES=()
for path in common/rne_sat_signed common/rne_sat_fft43 mf16/mf16_coeff_rom mf16/mf16_serial_mac mti/mti2_diff fft32/fft32_twiddle_rom fft32/fft32_butterfly fft32/fft32_dit power_cfar/power_q25_u46_serial power_cfar/cfar_compare power_cfar/cfar_2d_scan grouping/grouping_8conn integration/cfar_grouping_subsystem integration/radar_cpi_core; do
 SOURCES+=("$ROOT/rtl/$path.v")
done
"$IVL" "${ARGS[@]}" -g2005 -s tb_fft_rne_equivalence -o "$BUILD/tb_rne" "$ROOT/rtl/common/rne_sat_signed.v" "$ROOT/rtl/common/rne_sat_fft43.v" "$ROOT/rtl/tb/tb_fft_rne_equivalence.v"
"$VVP" "$BUILD/tb_rne" | tee "$BUILD/rne-equivalence.log"
grep -q '^PASS tb_fft_rne_equivalence:' "$BUILD/rne-equivalence.log"
"$IVL" "${ARGS[@]}" -g2005 -s tb_radar_cpi_core -o "$BUILD/tb_icarus" "${SOURCES[@]}" "$ROOT/rtl/tb/tb_radar_cpi_core.v"
(cd "$ROOT/rtl/tb" && "$VVP" "$BUILD/tb_icarus") | tee "$BUILD/icarus.log"
grep -q '^PASS tb_radar_cpi_core:' "$BUILD/icarus.log"
if grep -q '^FAIL ' "$BUILD/icarus.log" "$BUILD/rne-equivalence.log"; then exit 1; fi

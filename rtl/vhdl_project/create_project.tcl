# Xilinx ISE 14.7 Project Navigator — VHDL architectural counterpart of AX309 RTL.
# A distinct, unqualified engineering implementation. Never overwrite Verilog build.
set here [file dirname [file normalize [info script]]]
set rtl [file normalize [file join $here ..]]
set proj [file join $here AX309_RadarDSP_VHDL.xise]
if {[file exists $proj]} {
 puts stderr "REFUSING to replace existing VHDL project $proj"
 exit 2
}
project new $proj
project set family "Spartan6"
project set device "xc6slx9"
project set package "ftg256"
project set speed "-2"
project set "Preferred Language" "VHDL"
project set "Synthesis Tool" "XST (VHDL/Verilog)"
project set "Simulator" "ISim (VHDL/Verilog)"
project set "Optimization Goal" "Area"
set sources {
 common/rne_sat_signed.vhd
 mf16/mf16_coeff_rom.vhd
 mf16/mf16_serial_mac.vhd
 mti/mti2_diff.vhd
 power_cfar/cfar_compare.vhd
 power_cfar/power_q25_u46_serial.vhd
 power_cfar/cfar_2d_scan.vhd
 grouping/grouping_8conn.vhd
 integration/cfar_grouping_subsystem.vhd
 fft32_ip/fft32_ip.vhd
 fft32_ip/fft32_ip_adapter.vhd
 integration/radar_cpi_core.vhd
 uart/uart_rx_8n1.vhd
 uart/uart_tx_8n1.vhd
 uart/s02_frame_echo.vhd
 uart/s05_iq_cpi_banked.vhd
 uart/s05_dsp_session_arq.vhd
 uart/s05_dsp_reply_tx.vhd
 uart/uart_s05_dsp_top.vhd
 uart/radar_ip_ax309_top.vhd
}
foreach f $sources {
 set path [file normalize [file join $here src $f]]
 if {![file exists $path]} {error "Missing VHDL RTL source $path"}
 xfile add $path
}
set ucf [file normalize [file join $rtl uart AX309_UART_S05.ucf]]
xfile add $ucf
# The vendor 7.1 FFT generated NGC is provided by frozen local CoreGen build,
# rather than committing licensed generated netlists to the public GitHub repo.
# xfile add ensures NGDBuild searches for this unmodified IP implementation.
set ngc [file normalize [file join $rtl build fft32_ip fft32_ip.ngc]]
if {![file exists $ngc]} {error "Missing licensed Xilinx FFT NGC: $ngc"}
xfile add $ngc
foreach f [lsort [glob -nocomplain -directory [file join $here tb] *.vhd]] {
 xfile add $f
}
project set "Auto Implementation Top" "false"
project set "Implementation Top" "Entity|radar_ip_ax309_top"
project save
puts "VHDL_PROJECT_CREATED=$proj SOURCES=[llength $sources]"
project close
exec python3 [file join $here finalize_project.py]

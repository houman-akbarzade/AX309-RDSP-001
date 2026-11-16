# Creates a separate GUI ISE project, leaving frozen RTL and bitstream untouched.
set here [file dirname [file normalize [info script]]]
set rtl [file normalize [file join $here ..]]
set project_file [file join $here AX309_RadarDSP.xise]
if {[file exists $project_file]} {error "Refusing to overwrite existing .xise"}
file copy -force [file join $rtl fft32_ip ip_stub.v] [file join $here fft32_ip_synth.v]
project new $project_file
project set family "Spartan6"
project set device "xc6slx9"
project set package "ftg256"
project set speed "-2"
project set "Preferred Language" "Verilog"
project set "Synthesis Tool" "XST (VHDL/Verilog)"
project set "Optimization Goal" "Area"
project set "Simulator" "ISim (VHDL/Verilog)"
set sources {
common/rne_sat_signed.v mf16/mf16_coeff_rom.v mf16/mf16_serial_mac.v
mti/mti2_diff.v fft32_ip/fft32_ip_adapter.v
power_cfar/power_q25_u46_serial.v power_cfar/cfar_compare.v
power_cfar/cfar_2d_scan.v grouping/grouping_8conn.v
integration/cfar_grouping_subsystem.v integration/radar_cpi_core.v
uart/uart_rx_8n1.v uart/uart_tx_8n1.v uart/s02_frame_echo.v
uart/s05_iq_cpi_banked.v uart/s05_dsp_session_arq.v
uart/s05_dsp_reply_tx.v uart/uart_s05_dsp_top.v
uart/radar_ip_ax309_top.v
}
foreach f $sources {
 set p [file normalize [file join $rtl $f]]
 if {![file exists $p]} {error "Missing source $p"}
 xfile add $p
}
xfile add [file normalize [file join $rtl uart AX309_UART_S05.ucf]]
xfile add [file join $here fft32_ip.xco]
set count 0
foreach p [lsort [glob -nocomplain -directory [file join $rtl tb] tb_*.v]] {
 xfile add $p
 incr count
}
project set "Auto Implementation Top" "false"
project set "Implementation Top" "Module|radar_ip_ax309_top"
project save
puts "PROJECT_CREATED=$project_file RTL_COUNT=[llength $sources] TB_COUNT=$count"
project close
exec python3 [file join $here finalize_project.py]

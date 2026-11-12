// Resource probe, NOT a deployable UART result protocol.
// Diagnostic output buses keep all processing observable.
// DSP starts only after uploaded IQ has been fully read back and ACKed.
// Host must remain quiescent during DSP: busy-NACK/RESULT integration absent.
module ip_resource_top(input clk,rst,uart_rxd,start,out_ready,
 output uart_txd,active_session,busy,done,error,saturation_sticky,
 output out_valid,output [9:0] out_record_id,output [6:0] out_range,
 output [4:0] out_bin,output signed [5:0] out_signed_bin,
 output [45:0] out_peak_power,output [11:0] out_cluster_cells,
 output out_tie_flag,output [11:0] out_equal_power_cells,
 output power_valid,output [45:0] power_value,
 output [6:0] power_range,output [4:0] power_bin);
 wire [12:0] addr;wire [31:0] word;
 wire [14:0] uploaded,readback;
 wire launch=start && active_session && uploaded==16896 && readback==16896 && !busy;
 uart_s05_shared_resource_probe u_link(.clk(clk),.rst(rst),
 .uart_rxd(uart_rxd),.uart_txd(uart_txd),.active_session(active_session),
 .expected_seq(),.activation_count(),.accepted_count(),.duplicate_count(),
 .stale_count(),.nack_count(),.good_frames(),.crc_errors(),.header_errors(),
 .length_errors(),.partial_timeouts(),.uart_errors(),.cpi_open(),.cpi_id(),
 .iq_uploaded_bytes(uploaded),.iq_readback_acked_bytes(readback),
 .tx_next_seq(),.tx_retry_exhausted(),.dsp_mem_active(busy),
 .dsp_read_addr(addr),.dsp_read_word(word));
 radar_cpi_core u_core(.clk(clk),.rst(rst),.start(launch),
 .iq_read_addr(addr),.iq_read_word(word),.out_valid(out_valid),.out_ready(out_ready),
 .out_record_id(out_record_id),.out_range(out_range),.out_bin(out_bin),
 .out_signed_bin(out_signed_bin),.out_peak_power(out_peak_power),
 .out_cluster_cells(out_cluster_cells),.out_tie_flag(out_tie_flag),
 .out_equal_power_cells(out_equal_power_cells),.busy(busy),.done(done),
 .error(error),.saturation_sticky(saturation_sticky),
 .power_valid(power_valid),.power_value(power_value),
 .power_range(power_range),.power_bin(power_bin));endmodule

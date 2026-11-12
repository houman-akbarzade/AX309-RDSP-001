// S05 synthesizable CFAR scanner -> 8-neighbour grouping integration.
// S02/S04 numeric and CUT contracts unchanged. Start both engines on the
// same rising edge; grouping done is the final frame completion.
module cfar_grouping_subsystem #(
 parameter integer GROUP_MAX_LABELS = 702
) (
 input wire clk, rst, start,
 input wire debug_read, input wire [11:0] debug_addr, output wire [45:0] debug_power,
 input wire map_valid,
 input wire cut_pause, // optional safe throttling from a future frame controller
 output wire map_ready,
 input wire [45:0] map_power,
 output wire out_valid,
 input wire out_ready,
 output wire [9:0] out_record_id,
 output wire [6:0] out_range,
 output wire [4:0] out_bin,
 output wire signed [5:0] out_signed_bin,
 output wire [45:0] out_peak_power,
 output wire [11:0] out_cluster_cells,
 output wire out_tie_flag,
 output wire [11:0] out_equal_power_cells,
 output wire busy, done, scanner_done,
 output wire overflow_sticky, protocol_error, frame_invalid
);
 wire cut_valid, cut_ready, cut_alarm;
 wire group_ready;
 wire group_valid;
 assign cut_ready = group_ready & ~cut_pause;
 assign group_valid = cut_valid & ~cut_pause;
 wire [6:0] cut_range;
 wire [4:0] cut_bin;
 wire [45:0] cut_power;
 wire scan_busy, group_busy;
 wire scan_overflow, scan_proto;
 wire group_overflow, group_proto, group_invalid;

 assign busy=scan_busy | group_busy;
 assign overflow_sticky=scan_overflow | group_overflow;
 assign protocol_error=scan_proto | group_proto;
 assign frame_invalid=group_invalid | scan_overflow | scan_proto;

 cfar_2d_scan u_scanner(
  .clk(clk), .rst(rst), .start(start),
  .debug_read(debug_read),.debug_addr(debug_addr),.debug_power(debug_power),
  .map_valid(map_valid), .map_ready(map_ready), .map_power(map_power),
  .out_valid(cut_valid), .out_ready(cut_ready),
  .out_range(cut_range), .out_bin(cut_bin), .out_power(cut_power),
  .out_sum40(), .out_alarm(cut_alarm), .out_equality(),
  .busy(scan_busy), .done(scanner_done), .overflow_event(),
  .overflow_sticky(scan_overflow), .protocol_error(scan_proto)
 );
 grouping_8conn #(.MAX_LABELS(GROUP_MAX_LABELS)) u_grouping(
  .clk(clk), .rst(rst), .start(start),
  .in_valid(group_valid), .in_ready(group_ready),
  .in_range(cut_range), .in_bin(cut_bin),
  .in_power(cut_power), .in_alarm(cut_alarm),
  .out_valid(out_valid), .out_ready(out_ready),
  .out_record_id(out_record_id), .out_range(out_range),
  .out_bin(out_bin), .out_signed_bin(out_signed_bin),
  .out_peak_power(out_peak_power),
  .out_cluster_cells(out_cluster_cells), .out_tie_flag(out_tie_flag),
  .out_equal_power_cells(out_equal_power_cells),
  .busy(group_busy), .done(done),
  .overflow_sticky(group_overflow), .protocol_error(group_proto),
  .frame_invalid(group_invalid)
 );
endmodule

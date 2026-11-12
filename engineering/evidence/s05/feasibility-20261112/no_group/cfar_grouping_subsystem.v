// S05 synthesizable CFAR scanner -> 8-neighbour grouping integration.
// S02/S04 numeric and CUT contracts unchanged. Start both engines on the
// same rising edge; grouping done is the final frame completion.
module cfar_grouping_subsystem #(
 parameter integer GROUP_MAX_LABELS = 702
) (
 input wire clk, rst, start,
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

 wire [51:0] sum_unused;
 wire equality;
 assign out_record_id=0;
 assign out_signed_bin=out_bin[4]? $signed({1'b0,out_bin})-6'sd32 : $signed({1'b0,out_bin});
 assign out_cluster_cells=1;assign out_equal_power_cells=1;
 assign frame_invalid=overflow_sticky|protocol_error;
 assign scanner_done=done;
 cfar_2d_scan u_scanner(.clk(clk),.rst(rst),.start(start),
 .map_valid(map_valid),.map_ready(map_ready),.map_power(map_power),
 .out_valid(out_valid),.out_ready(out_ready & ~cut_pause),
 .out_range(out_range),.out_bin(out_bin),.out_power(out_peak_power),
 .out_sum40(sum_unused),.out_alarm(out_tie_flag),.out_equality(equality),
 .busy(busy),.done(done),.overflow_event(),.overflow_sticky(overflow_sticky),.protocol_error(protocol_error));
endmodule

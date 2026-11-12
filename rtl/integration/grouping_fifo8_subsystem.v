// S05 executable lossless-stream proof of principle. This is NOT a UART
// serializer, transactional packet engine or complete CPI controller.
// Source is the frozen grouping_8conn; sink is a valid/ready mock host.
// CPI commit/abort packet TYPE codes remain unapproved/unused here.
module grouping_fifo8_subsystem(
    input wire clk, rst, start,
    input wire cut_valid,
    output wire cut_ready,
    input wire [6:0] cut_range,
    input wire [4:0] cut_bin,
    input wire [45:0] cut_power,
    input wire cut_alarm,
    output wire record_valid,
    input wire record_ready,
    output wire [98:0] record_data,
    output wire [3:0] fifo_occupancy,
    output wire group_done,
    output wire group_busy,
    output wire overflow_sticky,
    output wire protocol_error,
    output wire frame_invalid,
    output wire [9:0] produced_count,
    output wire [9:0] delivered_count,
    output wire frame_drained
);
    wire group_out_valid, group_out_ready;
    wire [9:0] record_id;
    wire [6:0] peak_range;
    wire [4:0] peak_bin;
    wire signed [5:0] signed_bin;
    wire [45:0] peak_power;
    wire [11:0] cluster_cells, equal_power_cells;
    wire tie_flag;
    wire [98:0] packed_record = {
      record_id, peak_range, peak_bin, signed_bin,
      peak_power, cluster_cells, tie_flag, equal_power_cells
    };

    grouping_8conn u_grouping(
      .clk(clk),.rst(rst),.start(start),
      .in_valid(cut_valid),.in_ready(cut_ready),
      .in_range(cut_range),.in_bin(cut_bin),
      .in_power(cut_power),.in_alarm(cut_alarm),
      .out_valid(group_out_valid),.out_ready(group_out_ready),
      .out_record_id(record_id),.out_range(peak_range),
      .out_bin(peak_bin),.out_signed_bin(signed_bin),
      .out_peak_power(peak_power),.out_cluster_cells(cluster_cells),
      .out_tie_flag(tie_flag),.out_equal_power_cells(equal_power_cells),
      .busy(group_busy),.done(group_done),
      .overflow_sticky(overflow_sticky),
      .protocol_error(protocol_error),.frame_invalid(frame_invalid)
    );

    record_fifo8 u_fifo(
      .clk(clk),.rst(rst),
      .in_valid(group_out_valid),.in_ready(group_out_ready),
      .in_data(packed_record),
      .out_valid(record_valid),.out_ready(record_ready),
      .out_data(record_data),.occupancy(fifo_occupancy)
    );

    reg [9:0] produced,delivered;
    reg generation_done;
    assign produced_count=produced;
    assign delivered_count=delivered;
    assign frame_drained = generation_done &&
       (fifo_occupancy==4'd0) && (produced==delivered) &&
       !frame_invalid && !protocol_error && !overflow_sticky;

    always @(posedge clk) begin
      if (rst || start) begin
        produced<=10'd0;
        delivered<=10'd0;
        generation_done<=1'b0;
      end else begin
        if (group_out_valid && group_out_ready)
          produced<=produced+10'd1;
        if (record_valid && record_ready)
          delivered<=delivered+10'd1;
        if (group_done)
          generation_done<=1'b1;
      end
    end
endmodule

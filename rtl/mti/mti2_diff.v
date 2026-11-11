// Exact MTI two-pulse difference. Q22.15 - Q22.15 -> Q23.15.
module mti2_diff (
    input wire clk,
    input wire rst,
    input wire in_valid,
    input wire signed [21:0] pulse_next_re,
    input wire signed [21:0] pulse_next_im,
    input wire signed [21:0] pulse_prev_re,
    input wire signed [21:0] pulse_prev_im,
    input wire [6:0] range_in,
    input wire [4:0] pulse_in,
    output reg out_valid,
    output reg signed [22:0] diff_re,
    output reg signed [22:0] diff_im,
    output reg [6:0] range_out,
    output reg [4:0] pulse_out
);
    wire signed [22:0] next_re_ext = {pulse_next_re[21],pulse_next_re};
    wire signed [22:0] next_im_ext = {pulse_next_im[21],pulse_next_im};
    wire signed [22:0] prev_re_ext = {pulse_prev_re[21],pulse_prev_re};
    wire signed [22:0] prev_im_ext = {pulse_prev_im[21],pulse_prev_im};

    always @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            diff_re <= 23'sd0;
            diff_im <= 23'sd0;
            range_out <= 7'd0;
            pulse_out <= 5'd0;
        end else begin
            out_valid <= in_valid;
            if (in_valid) begin
                diff_re <= next_re_ext - prev_re_ext;
                diff_im <= next_im_ext - prev_im_ext;
                range_out <= range_in;
                pulse_out <= pulse_in;
            end
        end
    end
endmodule

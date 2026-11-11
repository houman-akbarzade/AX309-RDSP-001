// Serial complex 16-tap MF MAC. One tap is accepted per clk.
module mf16_serial_mac (
    input wire clk,
    input wire rst,
    input wire start,
    input wire [6:0] range_in,
    input wire tap_valid,
    input wire [3:0] tap_index,
    input wire signed [15:0] sample_re,
    input wire signed [15:0] sample_im,
    output reg busy,
    output reg done,
    output reg [6:0] range_out,
    output reg signed [21:0] result_re,
    output reg signed [21:0] result_im,
    output reg saturation_event,
    output reg [1:0] saturation_mask,
    output reg signed [63:0] prelimit_re,
    output reg signed [63:0] prelimit_im,
    output reg protocol_error
);
    wire signed [15:0] coeff_re;
    wire signed [15:0] coeff_im;
    reg [3:0] expected_tap;
    reg signed [36:0] accum_re;
    reg signed [36:0] accum_im;

    mf16_coeff_rom u_coeff (
        .index(tap_index), .coeff_re(coeff_re), .coeff_im(coeff_im)
    );

    wire signed [31:0] p_rr = sample_re * coeff_re;
    wire signed [31:0] p_ii = sample_im * coeff_im;
    wire signed [31:0] p_ri = sample_re * coeff_im;
    wire signed [31:0] p_ir = sample_im * coeff_re;

    wire signed [32:0] pair_re =
        $signed({p_rr[31],p_rr}) - $signed({p_ii[31],p_ii});
    wire signed [32:0] pair_im =
        $signed({p_ri[31],p_ri}) + $signed({p_ir[31],p_ir});

    wire signed [36:0] accum_re_next =
        accum_re + {{4{pair_re[32]}},pair_re};
    wire signed [36:0] accum_im_next =
        accum_im + {{4{pair_im[32]}},pair_im};

    wire signed [21:0] rounded_re;
    wire signed [21:0] rounded_im;
    wire ov_re, ov_im;
    wire signed [63:0] pre_re, pre_im;

    rne_sat_signed #(.IN_W(37),.OUT_W(22)) u_rne_re (
        .in_value(accum_re_next), .shift_amt(6'd15),
        .out_value(rounded_re), .overflow(ov_re), .prelimit(pre_re)
    );
    rne_sat_signed #(.IN_W(37),.OUT_W(22)) u_rne_im (
        .in_value(accum_im_next), .shift_amt(6'd15),
        .out_value(rounded_im), .overflow(ov_im), .prelimit(pre_im)
    );

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            done <= 1'b0;
            range_out <= 7'd0;
            result_re <= 22'sd0;
            result_im <= 22'sd0;
            accum_re <= 37'sd0;
            accum_im <= 37'sd0;
            expected_tap <= 4'd0;
            saturation_event <= 1'b0;
            saturation_mask <= 2'b00;
            prelimit_re <= 64'sd0;
            prelimit_im <= 64'sd0;
            protocol_error <= 1'b0;
        end else begin
            done <= 1'b0;
            saturation_event <= 1'b0;
            saturation_mask <= 2'b00;

            if (start) begin
                if (busy) begin
                    protocol_error <= 1'b1;
                end else begin
                    busy <= 1'b1;
                    accum_re <= 37'sd0;
                    accum_im <= 37'sd0;
                    expected_tap <= 4'd0;
                    range_out <= range_in;
                end
            end

            if (tap_valid && busy) begin
                if (tap_index != expected_tap) begin
                    protocol_error <= 1'b1;
                    busy <= 1'b0;
                end else begin
                    accum_re <= accum_re_next;
                    accum_im <= accum_im_next;
                    expected_tap <= expected_tap + 4'd1;
                    if (tap_index == 4'd15) begin
                        result_re <= rounded_re;
                        result_im <= rounded_im;
                        prelimit_re <= pre_re;
                        prelimit_im <= pre_im;
                        saturation_mask <= {ov_im,ov_re};
                        saturation_event <= ov_re | ov_im;
                        done <= 1'b1;
                        busy <= 1'b0;
                    end
                end
            end
        end
    end
endmodule

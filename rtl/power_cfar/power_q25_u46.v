// Complex Q25.15 to stored unsigned U46.30 power with saturation.
module power_q25_u46 (
    input wire clk,
    input wire rst,
    input wire in_valid,
    input wire signed [24:0] in_re,
    input wire signed [24:0] in_im,
    input wire [6:0] range_in,
    input wire [4:0] bin_in,
    output reg out_valid,
    output reg [45:0] power_out,
    output reg [6:0] range_out,
    output reg [4:0] bin_out,
    output reg saturation_event,
    output reg signed [63:0] prelimit,
    output reg overflow_sticky
);
    wire signed [49:0] re_ext = {{25{in_re[24]}},in_re};
    wire signed [49:0] im_ext = {{25{in_im[24]}},in_im};
    wire signed [49:0] re_square = re_ext * re_ext;
    wire signed [49:0] im_square = im_ext * im_ext;
    wire [50:0] raw_power =
        {1'b0,re_square[49:0]} + {1'b0,im_square[49:0]};
    wire raw_overflow = |raw_power[50:46];

    always @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            power_out <= 46'd0;
            range_out <= 7'd0;
            bin_out <= 5'd0;
            saturation_event <= 1'b0;
            prelimit <= 64'sd0;
            overflow_sticky <= 1'b0;
        end else begin
            out_valid <= in_valid;
            saturation_event <= 1'b0;
            if (in_valid) begin
                range_out <= range_in;
                bin_out <= bin_in;
                prelimit <= $signed({13'd0,raw_power});
                if (raw_overflow) begin
                    power_out <= {46{1'b1}};
                    saturation_event <= 1'b1;
                    overflow_sticky <= 1'b1;
                end else begin
                    power_out <= raw_power[45:0];
                end
            end
        end
    end
endmodule

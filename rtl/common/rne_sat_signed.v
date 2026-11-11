// Signed integer RNE followed by saturation. Verilog-2001, combinational.
// shift_amt is the number of binary places removed; negative values are
// rounded by magnitude, so this is not an arithmetic-right-shift shortcut.
module rne_sat_signed #(parameter IN_W=43, parameter OUT_W=25) (
    input  wire signed [IN_W-1:0] in_value,
    input  wire [5:0] shift_amt,
    output reg  signed [OUT_W-1:0] out_value,
    output reg  overflow,
    output reg  signed [63:0] prelimit
);
    reg signed [63:0] x64;
    reg signed [63:0] y64;
    reg [63:0] magnitude;
    reg [63:0] quotient;
    reg [63:0] remainder;
    reg [63:0] half_lsb;
    reg [63:0] mask;
    reg signed [63:0] maximum;
    reg signed [63:0] minimum;

    always @* begin
        x64 = {{(64-IN_W){in_value[IN_W-1]}}, in_value};
        magnitude = 64'd0;
        quotient = 64'd0;
        remainder = 64'd0;
        half_lsb = 64'd0;
        mask = 64'd0;
        y64 = 64'sd0;
        maximum = (64'sd1 << (OUT_W-1)) - 64'sd1;
        minimum = -(64'sd1 << (OUT_W-1));

        if (shift_amt == 0) begin
            y64 = x64;
        end else begin
            magnitude = (x64 < 0) ? $unsigned(-x64) : $unsigned(x64);
            quotient = magnitude >> shift_amt;
            mask = (64'd1 << shift_amt) - 64'd1;
            remainder = magnitude & mask;
            half_lsb = 64'd1 << (shift_amt-1);
            if ((remainder > half_lsb) ||
                ((remainder == half_lsb) && quotient[0]))
                quotient = quotient + 64'd1;
            y64 = (x64 < 0) ? -$signed(quotient) : $signed(quotient);
        end

        prelimit = y64;
        overflow = (y64 > maximum) || (y64 < minimum);
        if (y64 > maximum)
            out_value = maximum[OUT_W-1:0];
        else if (y64 < minimum)
            out_value = minimum[OUT_W-1:0];
        else
            out_value = y64[OUT_W-1:0];
    end
endmodule

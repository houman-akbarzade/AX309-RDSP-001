// Exact signed nearest-even for the frozen FFT shifts 15 or 16 only.
// Arithmetic-floor quotient plus positive two's-complement remainder
// works for both signs. Avoids a general 64-bit barrel shifter.
module rne_sat_fft43(
 input wire signed [42:0] in_value,input wire [5:0] shift_amt,
 output wire signed [24:0] out_value,output wire overflow,
 output wire signed [63:0] prelimit);
 wire inc15=(in_value[14:0]>15'd16384) ||
            ((in_value[14:0]==15'd16384)&&in_value[15]);
 wire inc16=(in_value[15:0]>16'd32768) ||
            ((in_value[15:0]==16'd32768)&&in_value[16]);
 wire signed [28:0] q15=$signed({in_value[42],in_value[42:15]})+$signed({28'd0,inc15});
 wire signed [28:0] q16=$signed({{2{in_value[42]}},in_value[42:16]})+$signed({28'd0,inc16});
 wire signed [28:0] rounded=(shift_amt==16)?q16:q15;
 wire positive=rounded>29'sd16777215;
 wire negative=rounded< -29'sd16777216;
 assign prelimit={{35{rounded[28]}},rounded};
 assign overflow=positive|negative;
 assign out_value=positive?25'sh0ffffff:negative?25'sh1000000:rounded[24:0];
endmodule

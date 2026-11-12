// Exact U46.30 power, one shared 17x17 multiply (DSP48A1).
// Absolute 25-bit operand = lo16 + hi9*2^16; square has three terms.
module power_q25_u46_serial(
 input wire clk,rst,in_valid, output wire in_ready,
 input wire signed [24:0] in_re,in_im,
 input wire [6:0] range_in,input wire [4:0] bin_in,
 output wire out_valid,input wire out_ready,
 output wire [45:0] power_out,output reg [6:0] range_out,
 output reg [4:0] bin_out,output reg overflow_sticky);
 reg [3:0] state;
 reg [24:0] ar,ai;
 reg [50:0] acc;
 reg [16:0] a,b;
 wire [33:0] product=a*b;
 wire [24:0] operand=(state<4)?ar:ai;
 assign in_ready=(state==0);
 assign out_valid=(state==7);
 assign power_out=(|acc[50:46])?{46{1'b1}}:acc[45:0];
 always @* begin
  a=0;b=0;
  case(state)
   1,4:begin a={1'b0,operand[15:0]};b={1'b0,operand[15:0]};end
   2,5:begin a={1'b0,operand[15:0]};b={8'd0,operand[24:16]};end
   3,6:begin a={8'd0,operand[24:16]};b={8'd0,operand[24:16]};end
  endcase
 end
 always @(posedge clk) begin
  if(rst)begin state<=0;ar<=0;ai<=0;acc<=0;range_out<=0;bin_out<=0;overflow_sticky<=0;end
  else case(state)
   0:if(in_valid)begin
    ar<=in_re[24]?(~in_re+25'd1):in_re;
    ai<=in_im[24]?(~in_im+25'd1):in_im;
    acc<=0;range_out<=range_in;bin_out<=bin_in;state<=1;
   end
   1,4:begin acc<=acc+{17'd0,product};state<=state+1'b1;end
   2,5:begin acc<=acc+({17'd0,product}<<17);state<=state+1'b1;end
   3,6:begin acc<=acc+({17'd0,product}<<32);state<=state+1'b1;end
   7:begin
    if(|acc[50:46])overflow_sticky<=1;
    if(out_ready)state<=0;
   end
  endcase
 end
endmodule

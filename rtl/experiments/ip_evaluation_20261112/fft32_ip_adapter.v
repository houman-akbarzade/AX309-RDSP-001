// Experimental adapter: old bit-reversed MTI input -> natural-order FFT IP.
// Not a C02 bit-true replacement. IP numerical/overflow policy is unchanged.
module fft32_dit(
 input wire clk,rst,start,input wire [6:0] range_in,
 input wire in_valid,output wire in_ready,input wire signed [22:0] in_re,in_im,
 output wire out_valid,input wire out_ready,output wire out_last,
 output wire signed [24:0] out_re,out_im,output reg [6:0] range_out,
 output wire busy,output reg done,output wire overflow_event,
 output reg overflow_sticky,output wire [2:0] overflow_stage,
 output wire [3:0] overflow_butterfly,overflow_mask,
 output wire signed [63:0] overflow_pre_plus_re,overflow_pre_plus_im,
 output wire signed [63:0] overflow_pre_minus_re,overflow_pre_minus_im,
 output reg protocol_error);
 localparam IDLE=0,LOAD=1,START_IP=2,RUN_IP=3;
 reg [1:0] state;
 reg [4:0] load_index;
 (* ram_style="distributed" *) reg [45:0] samples[0:31];
 wire [4:0] write_index={load_index[0],load_index[1],load_index[2],load_index[3],load_index[4]};
 wire [4:0] ip_xn,ip_xk;
 wire [45:0] input_sample=samples[ip_xn];
 wire ip_dv,ip_overflow;
 wire ip_ce=!(state==RUN_IP && ip_dv && !out_ready);
 assign in_ready=(state==LOAD);
 assign out_valid=(state==RUN_IP)&&ip_dv;
 assign out_last=out_valid && ip_xk==31;
 assign busy=(state!=IDLE);
 assign overflow_event=(state==RUN_IP)&&ip_overflow;
 // IP does not expose C02's internal per-butterfly prelimit trace.
 assign overflow_stage=0;assign overflow_butterfly=0;
 assign overflow_mask=ip_overflow?4'b1111:4'b0000;
 assign overflow_pre_plus_re=0;assign overflow_pre_plus_im=0;
 assign overflow_pre_minus_re=0;assign overflow_pre_minus_im=0;
 fft32_ip u_ip(.clk(clk),.ce(ip_ce),.sclr(rst),.start(state==START_IP),
 .unload(1'b1),.fwd_inv(1'b1),.fwd_inv_we(1'b1),
 .scale_sch(10'h144),.scale_sch_we(1'b1),
 .xn_re({{2{input_sample[22]}},input_sample[22:0]}),
 .xn_im({{2{input_sample[45]}},input_sample[45:23]}),
 .rfd(),.xn_index(ip_xn),.busy(),.edone(),.done(),.dv(ip_dv),
 .ovflo(ip_overflow),.xk_index(ip_xk),.xk_re(out_re),.xk_im(out_im));
 always @(posedge clk)begin
  if(rst)begin state<=IDLE;load_index<=0;range_out<=0;done<=0;
   overflow_sticky<=0;protocol_error<=0;end
  else begin
   done<=0;
   if(start && state!=IDLE)protocol_error<=1;
   if(in_valid && !in_ready)protocol_error<=1;
   if(state==RUN_IP && ip_overflow)overflow_sticky<=1;
   case(state)
    IDLE:if(start)begin state<=LOAD;load_index<=0;range_out<=range_in;overflow_sticky<=0;end
    LOAD:if(in_valid)begin
     samples[write_index]<={in_im,in_re};
     if(load_index==31)state<=START_IP;else load_index<=load_index+1'b1;
    end
    START_IP:state<=RUN_IP;
    RUN_IP:if(out_last && out_ready)begin done<=1;state<=IDLE;end
   endcase
  end
 end
endmodule

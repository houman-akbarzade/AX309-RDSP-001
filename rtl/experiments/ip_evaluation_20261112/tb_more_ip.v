`timescale 1ns/1ps
module tb_more_ip;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,start=0;wire dv,ovflo;wire [4:0] xi,ki;wire [24:0] yr,yi;
 reg [45:0] all_samples[0:32767];
 integer scenario,range_index=0,cycles=0,seen=0,fd,start_cycle;
 wire [45:0] sample=all_samples[(scenario-3)*4096+xi*128+range_index];
 fft32_ip dut(.clk(clk),.ce(1'b1),.sclr(rst),.start(start),.unload(1'b1),
 .fwd_inv(1'b1),.fwd_inv_we(1'b1),.scale_sch(10'h144),.scale_sch_we(1'b1),
 .xn_re({{2{sample[22]}},sample[22:0]}),.xn_im({{2{sample[45]}},sample[45:23]}),
 .rfd(),.xn_index(xi),.busy(),.edone(),.done(),.dv(dv),.ovflo(ovflo),
 .xk_index(ki),.xk_re(yr),.xk_im(yi));
 always @(posedge clk)begin
  cycles=cycles+1;
  if(!rst && dv)begin
   if((^yr===1'bx)||(^yi===1'bx)||ovflo||ki!==seen)begin $display("FAIL IP sequence/data/overflow");$finish;end
   $fdisplay(fd,"%0d %0d %0d %h",scenario,range_index,ki,{yi,yr});seen=seen+1;
  end
 end
 initial begin
  $readmemh("/home/houman/AX309-RDSP-001/rtl/build/ip_evaluation_numeric/all_new_mti.hex",all_samples);
  fd=$fopen("more-ip-output.txt","w");
  for(scenario=3;scenario<11;scenario=scenario+1)begin
   for(range_index=0;range_index<128;range_index=range_index+1)begin
    rst=1;start=0;repeat(10)@(negedge clk);rst=0;
    repeat(4)@(negedge clk);seen=0;start_cycle=cycles;start=1;
    @(negedge clk);start=0;
    while(seen<32 && cycles-start_cycle<3000)@(negedge clk);
    if(seen!=32)begin $display("FAIL IP timeout");$finish;end
    repeat(5)@(negedge clk);
   end
   $display("EXECUTED development scenario=%d",scenario);
  end
  $fclose(fd);$display("PASS tb_more_ip: 32768 ordered complex outputs, no observed overflow");$finish;
 end
 initial begin #100000000;$display("FAIL global timeout");$finish;end
endmodule

`timescale 1ns/1ps
module tb_fft_ip;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,start=0;wire rfd,busy,done,dv,ovflo;
 wire [4:0] xi,ki;wire signed [24:0] yr,yi;
 reg [45:0] samples[0:4095];reg [49:0] golden[0:4095];
 integer scenario,range_index=0,cycles=0,seen=0,fd,errors=0;
 integer start_cycle,first_cycle,last_cycle;reg first_seen;
 wire [45:0] sample=samples[xi*128+range_index];
 fft32_ip dut(.clk(clk),.ce(1'b1),.sclr(rst),.start(start),.unload(1'b1),
 .fwd_inv(1'b1),.fwd_inv_we(1'b1),.scale_sch(10'h144),.scale_sch_we(1'b1),
 .xn_re({{2{sample[22]}},sample[22:0]}),.xn_im({{2{sample[45]}},sample[45:23]}),
 .rfd(rfd),.xn_index(xi),.busy(busy),.edone(),.done(done),.dv(dv),.ovflo(ovflo),
 .xk_index(ki),.xk_re(yr),.xk_im(yi));
 always @(posedge clk)begin
  cycles=cycles+1;
  if(!rst && dv)begin
   if((^yr===1'bx)||(^yi===1'bx))begin $display("FAIL unknown FFT output");$finish;end
   if(ki!==seen)begin $display("FAIL FFT output order got=%d expected=%d",ki,seen);$finish;end
   if(ovflo)begin $display("FAIL IP overflow scenario=%d range=%d",scenario,range_index);$finish;end
   if(!first_seen)begin first_cycle=cycles;first_seen=1;end
   last_cycle=cycles;
   $fdisplay(fd,"%0d %0d %0d %h",scenario,range_index,ki,{yi,yr});
   if({yi,yr}!==golden[range_index*32+ki])errors=errors+1;
   seen=seen+1;
  end
 end
 initial begin
  fd=$fopen("fft-ip-output.txt","w");
  for(scenario=0;scenario<3;scenario=scenario+1)begin
   if(scenario==0)begin
    $readmemh("../../../tb/vectors/radar_cpi/0_mti.hex",samples);
    $readmemh("../../../tb/vectors/radar_cpi/0_rd.hex",golden);
   end else if(scenario==1)begin
    $readmemh("../../../tb/vectors/radar_cpi/1_mti.hex",samples);
    $readmemh("../../../tb/vectors/radar_cpi/1_rd.hex",golden);
   end else begin
    $readmemh("../../../tb/vectors/radar_cpi/2_mti.hex",samples);
    $readmemh("../../../tb/vectors/radar_cpi/2_rd.hex",golden);
   end
   for(range_index=0;range_index<128;range_index=range_index+1)begin
    rst=1;start=0;repeat(10)@(negedge clk);rst=0;
    repeat(4)@(negedge clk);seen=0;first_seen=0;start_cycle=cycles;
    start=1;@(negedge clk);start=0;
    while(seen<32 && cycles-start_cycle<3000)@(negedge clk);
    if(seen!=32)begin $display("FAIL timeout count=%d range=%d",seen,range_index);$finish;end
    if(range_index==0)$display("TIMING scenario=%d first=%d last=%d",scenario,first_cycle-start_cycle,last_cycle-start_cycle);
    repeat(5)@(negedge clk);
   end
   $display("EXECUTED IP scenario=%d cumulative_bittrue_mismatched_complex_words=%d",scenario,errors);
  end
  $fclose(fd);$display("PASS tb_fft_ip transport: 12288 complex outputs; numeric mismatch count=%d",errors);$finish;
 end
 initial begin #100000000;$display("FAIL global timeout");$finish;end
endmodule

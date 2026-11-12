`timescale 1ns/1ps
module tb_adapter;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,start=0,in_valid=0,out_ready=0;
 reg signed [22:0] ir=0,ii=0;
 reg [6:0] rtag=0;
 wire in_ready,out_valid,out_last,done,ov,proto;
 wire signed [24:0] yr,yi;wire [6:0] rout;
 reg [45:0] mt[0:4095];reg [49:0] expected[0:4095];
 integer c,rn,i,j,r,cycles=0,seen=0,begin_cycle,frames=0;
 reg held=0;reg [49:0] held_word;reg [6:0] held_range;reg held_last;
 function [4:0] reverse5;input [4:0] v;begin reverse5={v[0],v[1],v[2],v[3],v[4]};end endfunction
 fft32_dit dut(.clk(clk),.rst(rst),.start(start),.range_in(rtag),
 .in_valid(in_valid),.in_ready(in_ready),.in_re(ir),.in_im(ii),
 .out_valid(out_valid),.out_ready(out_ready),.out_last(out_last),
 .out_re(yr),.out_im(yi),.range_out(rout),.busy(),.done(done),
 .overflow_event(),.overflow_sticky(ov),.overflow_stage(),.overflow_butterfly(),
 .overflow_mask(),.overflow_pre_plus_re(),.overflow_pre_plus_im(),
 .overflow_pre_minus_re(),.overflow_pre_minus_im(),.protocol_error(proto));
 always @(posedge clk)begin
  cycles=cycles+1;out_ready<=(cycles%5!=0 && cycles%7!=0);
  if(rst)held=0;
  else begin
   if(ov||proto)begin $display("FAIL adapter overflow/protocol");$finish;end
   if(held && (!out_valid || {yi,yr}!==held_word || rout!==held_range || out_last!==held_last))begin
    $display("FAIL adapter stalled data changed");$finish;end
   held=out_valid && !out_ready;held_word={yi,yr};held_range=rout;held_last=out_last;
   if(out_valid&&out_ready)begin
    if({yi,yr}!==expected[r*32+seen] || rout!==rtag || out_last!==(seen==31))begin
     $display("FAIL adapter c=%d r=%d b=%d got=%h expected=%h",c,r,seen,{yi,yr},expected[r*32+seen]);$finish;end
    seen=seen+1;
   end
  end
 end
 initial begin
  repeat(10)@(negedge clk);rst=0;
  for(c=0;c<3;c=c+1)begin
   if(c==0)begin
    $readmemh("/home/houman/AX309-RDSP-001/rtl/tb/vectors/radar_cpi/0_mti.hex",mt);
    $readmemh("/home/houman/AX309-RDSP-001/rtl/build/ip_evaluation_units/0_ip_rd.hex",expected);
   end else if(c==1)begin
    $readmemh("/home/houman/AX309-RDSP-001/rtl/tb/vectors/radar_cpi/1_mti.hex",mt);
    $readmemh("/home/houman/AX309-RDSP-001/rtl/build/ip_evaluation_units/1_ip_rd.hex",expected);
   end else begin
    $readmemh("/home/houman/AX309-RDSP-001/rtl/tb/vectors/radar_cpi/2_mti.hex",mt);
    $readmemh("/home/houman/AX309-RDSP-001/rtl/build/ip_evaluation_units/2_ip_rd.hex",expected);
   end
   for(rn=0;rn<5;rn=rn+1)begin
    case(rn)0:r=0;1:r=35;2:r=40;3:r=80;4:r=127;endcase
    seen=0;rtag=r;start=1;@(negedge clk);start=0;
    for(i=0;i<32;i=i+1)begin
     while(!in_ready)@(negedge clk);
     ir=mt[reverse5(i)*128+r][22:0];ii=mt[reverse5(i)*128+r][45:23];
     in_valid=1;@(negedge clk);in_valid=0;
     for(j=0;j<(i%4);j=j+1)@(negedge clk);
    end
    begin_cycle=cycles;
    while(seen<32 && cycles-begin_cycle<3000)@(negedge clk);
    if(seen!=32||!done)begin $display("FAIL adapter completion");$finish;end
    frames=frames+1;repeat(6)@(negedge clk);
   end
  end
  $display("PASS tb_adapter: 15 frames, 480 exact outputs, sparse inputs, continuous reuse and backpressure");$finish;
 end
 initial begin #1000000;$display("FAIL adapter global timeout");$finish;end
endmodule

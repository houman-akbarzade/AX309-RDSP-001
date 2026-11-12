`timescale 1ns/1ps
module tb_mf_pipeline;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,start=0,valid=0;reg [3:0] tap=0;reg [6:0] tag=0;
 reg signed [15:0] ir=0,ii=0;
 wire done,busy,sat,proto;wire [1:0] mask;wire [6:0] out_tag;
 wire signed [21:0] yr,yi;wire signed [63:0] pr,pi;
 reg [31:0] samples[0:1023];reg [43:0] expected[0:63];reg [127:0] prelimit[0:63];
 integer c,k,waits;
 mf16_serial_mac dut(.clk(clk),.rst(rst),.start(start),.range_in(tag),
 .tap_valid(valid),.tap_index(tap),.sample_re(ir),.sample_im(ii),
 .busy(busy),.done(done),.range_out(out_tag),.result_re(yr),.result_im(yi),
 .saturation_event(sat),.saturation_mask(mask),.prelimit_re(pr),.prelimit_im(pi),
 .protocol_error(proto));
 initial begin
  $readmemh("mf_full_samples.hex",samples);
  $readmemh("mf_full_outputs.hex",expected);
  $readmemh("mf_full_prelimit.hex",prelimit);
  repeat(4)@(negedge clk);rst=0;
  for(c=0;c<64;c=c+1)begin
   tag=c;start=1;@(negedge clk);start=0;
   for(k=0;k<16;k=k+1)begin
    valid=1;tap=k;ir=samples[c*16+k][15:0];ii=samples[c*16+k][31:16];
    @(negedge clk);
   end
   valid=0;waits=0;
   while(!done && waits<5)begin @(negedge clk);waits=waits+1;end
   if(!done||busy||proto||sat||mask||out_tag!==tag||{yi,yr}!==expected[c]||{pi,pr}!==prelimit[c])begin
    $display("FAIL MF pipeline case=%d output=%h expected=%h",c,{yi,yr},expected[c]);$finish;end
   repeat(2)@(negedge clk);
  end
  $display("PASS tb_mf_pipeline: 64 full 16-tap complex MAC frames exact against frozen integer oracle, prelimit and tags checked");$finish;
 end
endmodule

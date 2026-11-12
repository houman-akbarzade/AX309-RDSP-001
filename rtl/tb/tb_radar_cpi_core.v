`timescale 1ns/1ps
module tb_radar_cpi_core;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,start=0;
 wire [12:0] addr;reg [31:0] word;
 reg [31:0] iq[0:4223];reg [43:0] mf[0:4223];
 reg [45:0] mti[0:4095];reg [49:0] rd[0:4095];
 reg [45:0] power[0:4095];reg [98:0] records[0:701];
 reg [9:0] count[0:0];
 wire valid,busy,done,error,sat,pvalid;
 reg ready=0;integer cycles=0,seen=0,pseen=0,mseen=0,tseen=0,fseen=0;
 wire [9:0] rid;wire [6:0] rr,pr;wire [4:0] rb,pb;wire signed [5:0] sb;
 wire [45:0] peak,pvalue;wire [11:0] cells,equals;wire tie;
 integer k,j;
 reg [511:0] filename;
 radar_cpi_core dut(.clk(clk),.rst(rst),.start(start),
 .iq_read_addr(addr),.iq_read_word(word),.out_valid(valid),.out_ready(ready),
 .out_record_id(rid),.out_range(rr),.out_bin(rb),.out_signed_bin(sb),
 .out_peak_power(peak),.out_cluster_cells(cells),
 .out_tie_flag(tie),.out_equal_power_cells(equals),
 .busy(busy),.done(done),.error(error),.saturation_sticky(sat),
 .power_valid(pvalid),.power_value(pvalue),.power_range(pr),.power_bin(pb));
 always @(posedge clk)begin
  word<=iq[addr];
  if(!rst)begin
   cycles<=cycles+1;ready<=(cycles%7!=0);
   if(error||sat)begin $display("FAIL core error/saturation state=%d",dut.state);$finish;end
   if(dut.mf_done)begin
    if({dut.mf_im,dut.mf_re}!==mf[dut.pulse*128+dut.range_index])begin
     $display("FAIL MF p=%d r=%d",dut.pulse,dut.range_index);$finish;end
    mseen<=mseen+1;
   end
   if(dut.mti_valid)begin
    if({dut.diff_im,dut.diff_re}!==mti[dut.reversed_pulse*128+dut.range_index])begin
     $display("FAIL MTI");$finish;end
    tseen<=tseen+1;
   end
   if(dut.fft_valid&&dut.pow_ready)begin
    if({dut.fft_im,dut.fft_re}!==rd[dut.range_index*32+dut.bin_index])begin
     $display("FAIL FFT r=%d b=%d",dut.range_index,dut.bin_index);$finish;end
    fseen<=fseen+1;
   end
   if(pvalid&&dut.map_ready)begin
    if(pvalue!==power[pseen] || pr!==pseen/32 || pb!==pseen%32)begin
     $display("FAIL POWER index=%d got=%h expected=%h",pseen,pvalue,power[pseen]);$finish;end
    pseen<=pseen+1;
   end
   if(valid&&ready)begin
    if(seen>=count[0]||rid!==seen || {16'd0,equals,tie,cells,peak,rb,rr}!==records[seen])begin
     $display("FAIL RECORD case=%d index=%d r=%d b=%d",k,seen,rr,rb);$finish;end
    seen<=seen+1;
   end
  end
 end
 initial begin
  for(k=0;k<3;k=k+1)begin
   rst=1;start=0;repeat(5)@(negedge clk);
   $sformat(filename,"vectors/radar_cpi/%0d_iq.hex",k);$readmemh(filename,iq);
   $sformat(filename,"vectors/radar_cpi/%0d_mf.hex",k);$readmemh(filename,mf);
   $sformat(filename,"vectors/radar_cpi/%0d_mti.hex",k);$readmemh(filename,mti);
   $sformat(filename,"vectors/radar_cpi/%0d_rd.hex",k);$readmemh(filename,rd);
   $sformat(filename,"vectors/radar_cpi/%0d_power.hex",k);$readmemh(filename,power);
   $sformat(filename,"vectors/radar_cpi/%0d_count.hex",k);$readmemh(filename,count);
   $sformat(filename,"vectors/radar_cpi/%0d_records.hex",k);$readmemh(filename,records,0,(count[0]?count[0]-1:0));
   cycles=0;seen=0;pseen=0;mseen=0;tseen=0;fseen=0;rst=0;
   start=1;@(negedge clk);start=0;
   while(!done&&cycles<3000000)@(negedge clk);
   if(!done||seen!=count[0]||pseen!=4096||mseen!=8192||tseen!=4096||fseen!=4096)begin
    $display("FAIL completion case=%d state=%d cycles=%d counts=%d %d %d %d %d",k,dut.state,cycles,seen,pseen,mseen,tseen,fseen);$finish;end
   $display("PASS full CPI case=%d cycles=%d records=%d MF=%d MTI=%d FFT=%d POWER=%d",k,cycles,seen,mseen,tseen,fseen,pseen);
  end
  $display("PASS tb_radar_cpi_core: 3 exact full-chain CPIs and record backpressure");$finish;
 end
endmodule

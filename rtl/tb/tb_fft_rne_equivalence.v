`timescale 1ns/1ps
module tb_fft_rne_equivalence;
 reg signed [42:0] x;reg [5:0] shift;
 wire signed [24:0] a,b;wire oa,ob;wire signed [63:0] pa,pb;
 integer i,j,k;reg [63:0] rng=64'h123456789abcdef0;
 rne_sat_signed #(.IN_W(43),.OUT_W(25)) old(x,shift,a,oa,pa);
 rne_sat_fft43 opt(x,shift,b,ob,pb);
 task check;
 begin #1;if(a!==b||oa!==ob||pa!==pb)begin
  $display("FAIL RNE x=%d shift=%d old=%d new=%d",x,shift,a,b);$finish;end end
 endtask
 initial begin
  for(j=15;j<=16;j=j+1)begin
   shift=j;
   for(i=0;i<4000;i=i+1)begin
    rng=rng^(rng<<13);rng=rng^(rng>>7);rng=rng^(rng<<17);x=rng[42:0];check;
   end
   for(i=-6;i<=6;i=i+1)
    for(k=-1;k<=1;k=k+1)begin x=($signed(i)*64'sd65536)+(64'sd1<<(j-1))+k;check;end
   x=43'sh3ffffffffff;check;x=43'sh40000000000;check;
   x=(64'sd16777215<<j);check;
   x=(-64'sd16777216<<j);check;
  end
  $display("PASS tb_fft_rne_equivalence: 8086 signed/rounding/saturation cases");$finish;
 end
endmodule

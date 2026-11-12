module ip_probe_top(input clk,rst,ce,start,unload,input signed [22:0] in_re,in_im,output rfd,busy,done,dv,ovflo,output [4:0] xn_index,xk_index,output signed [24:0] out_re,out_im);
 fft32_ip u(.clk(clk),.ce(ce),.sclr(rst),.start(start),.unload(unload),
 .xn_re({{2{in_re[22]}},in_re}),.xn_im({{2{in_im[22]}},in_im}),
 .fwd_inv(1'b1),.fwd_inv_we(1'b1),.scale_sch(10'h144),.scale_sch_we(1'b1),
 .rfd(rfd),.xn_index(xn_index),.busy(busy),.edone(),.done(done),.dv(dv),
 .xk_index(xk_index),.xk_re(out_re),.xk_im(out_im),.ovflo(ovflo));endmodule
(* box_type="black_box" *) module fft32_ip(input clk,ce,sclr,start,unload,fwd_inv,fwd_inv_we,scale_sch_we,input [24:0] xn_re,xn_im,input [9:0] scale_sch,output rfd,busy,edone,done,dv,ovflo,output [4:0] xn_index,xk_index,output [24:0] xk_re,xk_im);endmodule

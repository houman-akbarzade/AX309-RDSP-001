// Banking/mapping experiment only. Separate 4096+128 words, 50-bit MF.
module mf_frame_banked_probe(input wire clk,en,write_en,
 input wire [12:0] addr,input wire [49:0] din,
 output wire [49:0] dout);
 (* ram_style="block" *) reg [49:0] main_mem[0:4095];
 (* ram_style="block" *) reg [49:0] tail_mem[0:127];
 reg [49:0] main_q,tail_q;
 reg tail_sel;
 // Unconditional synchronous reads on both banks avoid a distributed-LUT
 // mapping caused by the first conditional-read experiment.
 always @(posedge clk) begin
  if (en) tail_sel <= addr[12];
 end
 always @(posedge clk) begin
  if (en && write_en && !addr[12]) main_mem[addr[11:0]] <= din;
  main_q <= main_mem[addr[11:0]];
 end
 always @(posedge clk) begin
  if (en && write_en && addr[12]) tail_mem[addr[6:0]] <= din;
  tail_q <= tail_mem[addr[6:0]];
 end
 assign dout=tail_sel ? tail_q : main_q;
endmodule

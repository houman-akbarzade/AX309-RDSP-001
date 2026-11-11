// Resource estimation probe only; NOT an approved frame-controller datapath.
// 33*128 words, 50-bit sign-extended complex MF slots.
module mf_frame_store_probe (
 input wire clk,
 input wire en, input wire write_en,
 input wire [12:0] addr,
 input wire [49:0] din,
 output reg [49:0] dout
);
 (* ram_style = "block" *) reg [49:0] ram[0:4223];
 always @(posedge clk) if(en) begin
   if(write_en) ram[addr] <= din;
   dout <= ram[addr];
 end
endmodule

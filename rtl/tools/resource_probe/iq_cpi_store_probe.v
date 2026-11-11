// Resource estimation probe only; NOT an approved CPI controller.
// 33*128 words, 32-bit complex Q1.15 I/Q. Synchronous read/write.
module iq_cpi_store_probe (
 input wire clk,
 input wire en, input wire write_en,
 input wire [12:0] addr,
 input wire [31:0] din,
 output reg [31:0] dout
);
 (* ram_style = "block" *) reg [31:0] ram[0:4223];
 always @(posedge clk) if(en) begin
   if(write_en) ram[addr] <= din;
   dout <= ram[addr];
 end
endmodule

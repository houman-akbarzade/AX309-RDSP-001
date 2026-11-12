// RESOURCE PROBE ONLY. 99-bit serialized record payload, independently
// addressed synchronous read/write ports. Not a functional FIFO/serializer.
module target_record_store_probe #(parameter integer DEPTH=8, parameter integer ADDR_W=3)(
 input wire clk, input wire wr_en, input wire [ADDR_W-1:0] wr_addr,
 input wire [98:0] wr_data, input wire rd_en,
 input wire [ADDR_W-1:0] rd_addr, output reg [98:0] rd_data
);
 (* ram_style="block" *) reg [98:0] mem[0:DEPTH-1];
 always @(posedge clk) begin
  if(wr_en) mem[wr_addr] <= wr_data;
  if(rd_en) rd_data <= mem[rd_addr];
 end
endmodule

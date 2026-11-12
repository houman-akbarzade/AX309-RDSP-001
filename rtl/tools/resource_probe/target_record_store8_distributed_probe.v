// RESOURCE PROBE ONLY: 8 x 99 bits as distributed RAM, not a FIFO protocol.
module target_record_store8_distributed_probe(input wire clk,
 input wire wr_en,rd_en, input wire [2:0] wr_addr,rd_addr,
 input wire [98:0] wr_data, output reg [98:0] rd_data);
 (* ram_style="distributed" *) reg [98:0] mem[0:7];
 always @(posedge clk) begin
  if (wr_en) mem[wr_addr] <= wr_data;
  if (rd_en) rd_data <= mem[rd_addr];
 end
endmodule

module target_record_store8_probe(input wire clk,wr_en,rd_en,
 input wire [2:0] wr_addr,rd_addr,input wire [98:0] wr_data,
 output wire [98:0] rd_data);
 target_record_store_probe #(.DEPTH(8),.ADDR_W(3)) u(
 .clk(clk),.wr_en(wr_en),.wr_addr(wr_addr),.wr_data(wr_data),
 .rd_en(rd_en),.rd_addr(rd_addr),.rd_data(rd_data));
endmodule

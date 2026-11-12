module stage_lab_ax309_top #(parameter integer TARGET=4,FIRST=TARGET)(
 input clk50,reset_n,uart_rxd,output uart_txd);
 wire clk_g;BUFG u_global_clock(.I(clk50),.O(clk_g));
 reg [2:0] reset_pipe=3'b111;
 always @(posedge clk_g or negedge reset_n)if(!reset_n)reset_pipe<=3'b111;else reset_pipe<={reset_pipe[1:0],1'b0};
 stage_lab_top #(.TARGET(TARGET),.FIRST(FIRST)) u(.clk(clk_g),.rst(reset_pipe[2]),.uart_rxd(uart_rxd),.uart_txd(uart_txd));
endmodule

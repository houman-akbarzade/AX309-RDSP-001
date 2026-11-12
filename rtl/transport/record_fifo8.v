// S05 eight-entry 99-bit streaming queue prototype; FIFO depth is NOT final
// REQ-LIST-01 approval. Only valid/ready transfers advance either pointer.
// Distributed RAM is an FPGA inference preference, not numeric datapath change.
module record_fifo8 (
    input wire clk,
    input wire rst,
    input wire in_valid,
    output wire in_ready,
    input wire [98:0] in_data,
    output wire out_valid,
    input wire out_ready,
    output wire [98:0] out_data,
    output wire [3:0] occupancy
);
    (* ram_style = "distributed" *) reg [98:0] mem [0:7];
    reg [2:0] rd_ptr;
    reg [2:0] wr_ptr;
    reg [3:0] count;
    wire pop = out_valid && out_ready;
    wire push = in_valid && in_ready;

    assign out_valid = (count != 4'd0);
    assign in_ready = (count != 4'd8) || pop;
    assign out_data = mem[rd_ptr];
    assign occupancy = count;

    always @(posedge clk) begin
        if (rst) begin
            rd_ptr <= 3'd0;
            wr_ptr <= 3'd0;
            count <= 4'd0;
        end else begin
            if (push) begin
                mem[wr_ptr] <= in_data;
                wr_ptr <= wr_ptr + 3'd1;
            end
            if (pop)
                rd_ptr <= rd_ptr + 3'd1;
            if (push && !pop)
                count <= count + 4'd1;
            else if (pop && !push)
                count <= count - 4'd1;
        end
    end
endmodule

// AX309 S05: synthesizable 8N1 UART transmitter.
// valid/ready handshake accepts one byte when idle; idle TX line high.
module uart_tx_8n1 #(
    parameter integer CLOCK_HZ = 50000000,
    parameter integer BAUD = 115200
)(
    input wire clk,
    input wire rst,
    input wire [7:0] data_in,
    input wire data_valid,
    output wire data_ready,
    output reg tx_pin,
    output reg byte_done
);
    localparam integer TICKS = CLOCK_HZ / BAUD;
    localparam [1:0] IDLE=0, START=1, DATA=2, STOP=3;
    reg [1:0] state;
    reg [15:0] timer;
    reg [2:0] bit_index;
    reg [7:0] byte_latched;
    assign data_ready = (state == IDLE);

    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            timer <= 0;
            bit_index <= 0;
            byte_latched <= 0;
            tx_pin <= 1'b1;
            byte_done <= 1'b0;
        end else begin
            byte_done <= 1'b0;
            case (state)
                IDLE: begin
                    tx_pin <= 1'b1;
                    if (data_valid) begin
                        byte_latched <= data_in;
                        timer <= TICKS - 1;
                        tx_pin <= 1'b0;
                        state <= START;
                    end
                end
                START: if (timer == 0) begin
                    tx_pin <= byte_latched[0];
                    bit_index <= 0;
                    timer <= TICKS - 1;
                    state <= DATA;
                end else timer <= timer - 1'b1;
                DATA: if (timer == 0) begin
                    timer <= TICKS - 1;
                    if (bit_index == 7) begin
                        tx_pin <= 1'b1;
                        state <= STOP;
                    end else begin
                        bit_index <= bit_index + 1'b1;
                        tx_pin <= byte_latched[bit_index + 1'b1];
                    end
                end else timer <= timer - 1'b1;
                STOP: if (timer == 0) begin
                    byte_done <= 1'b1;
                    state <= IDLE;
                end else timer <= timer - 1'b1;
                default: state <= IDLE;
            endcase
        end
    end
endmodule

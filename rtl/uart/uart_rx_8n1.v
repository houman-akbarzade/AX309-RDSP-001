// AX309 S05: synthesizable 8N1 UART receiver.
// Nominal clock=50MHz, baud=115200; bit period=floor(50e6/115200)=434.
// Asynchronous RX passes through a two-register synchronizer.
module uart_rx_8n1 #(
    parameter integer CLOCK_HZ = 50000000,
    parameter integer BAUD = 115200
)(
    input wire clk,
    input wire rst,
    input wire rx_pin,
    output reg [7:0] data_out,
    output reg data_valid,
    output reg framing_error,
    output wire busy
);
    localparam integer TICKS = CLOCK_HZ / BAUD;
    localparam integer HALF = TICKS / 2;
    localparam [1:0] IDLE=0, START=1, DATA=2, STOP=3;
    reg [1:0] state;
    reg sync_a, sync_b;
    reg [15:0] timer;
    reg [2:0] bit_index;
    reg [7:0] shifting;
    assign busy = (state != IDLE);

    always @(posedge clk) begin
        sync_a <= rx_pin;
        sync_b <= sync_a;
        if (rst) begin
            state <= IDLE;
            sync_a <= 1'b1;
            sync_b <= 1'b1;
            timer <= 16'd0;
            bit_index <= 3'd0;
            shifting <= 8'd0;
            data_valid <= 1'b0;
            framing_error <= 1'b0;
            data_out <= 8'd0;
        end else begin
            data_valid <= 1'b0;
            framing_error <= 1'b0;
            case (state)
                IDLE: if (!sync_b) begin
                    timer <= HALF - 1;
                    state <= START;
                end
                START: if (timer == 0) begin
                    if (!sync_b) begin
                        timer <= TICKS - 1;
                        bit_index <= 0;
                        state <= DATA;
                    end else state <= IDLE; // Start glitch.
                end else timer <= timer - 1'b1;
                DATA: if (timer == 0) begin
                    shifting[bit_index] <= sync_b;
                    timer <= TICKS - 1;
                    if (bit_index == 7) state <= STOP;
                    else bit_index <= bit_index + 1'b1;
                end else timer <= timer - 1'b1;
                STOP: if (timer == 0) begin
                    if (sync_b) begin
                        data_out <= shifting;
                        data_valid <= 1'b1;
                    end else framing_error <= 1'b1;
                    state <= IDLE;
                end else timer <= timer - 1'b1;
                default: state <= IDLE;
            endcase
        end
    end
endmodule

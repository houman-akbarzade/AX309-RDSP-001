// AX309 S05 RTL-only UART/Parser bring-up echo top.
// Laboratory echo of entire CRC-accepted S02 frame, not real UART ACK/ARQ.
// Board pin assignment and 50MHz oscillator verification deferred to board tests.
module uart_s02_echo_top #(
    parameter integer CLOCK_HZ = 50000000,
    parameter integer BAUD = 115200,
    parameter integer TIMEOUT_CLKS = 86800
)(
    input wire clk,
    input wire rst,
    input wire uart_rxd,
    output wire uart_txd,
    output wire [15:0] good_count,
    output wire [15:0] crc_error_count,
    output wire [15:0] header_error_count,
    output wire [15:0] length_error_count,
    output wire [15:0] partial_timeout_count,
    output wire [15:0] uart_error_count,
    output wire [15:0] busy_drop_count,
    output wire response_busy
);
    wire [7:0] rx_byte, tx_byte;
    wire rx_byte_valid, rx_framing_error;
    wire tx_byte_valid, tx_byte_ready;

    uart_rx_8n1 #(.CLOCK_HZ(CLOCK_HZ), .BAUD(BAUD)) u_rx (
        .clk(clk), .rst(rst), .rx_pin(uart_rxd),
        .data_out(rx_byte), .data_valid(rx_byte_valid),
        .framing_error(rx_framing_error), .busy()
    );

    s02_frame_echo #(.TIMEOUT_CLKS(TIMEOUT_CLKS)) u_parser (
        .clk(clk), .rst(rst),
        .rx_data(rx_byte), .rx_valid(rx_byte_valid),
        .rx_framing_error(rx_framing_error),
        .tx_data(tx_byte), .tx_valid(tx_byte_valid),
        .tx_ready(tx_byte_ready),
        .good_count(good_count), .crc_error_count(crc_error_count),
        .header_error_count(header_error_count),
        .length_error_count(length_error_count),
        .partial_timeout_count(partial_timeout_count),
        .uart_error_count(uart_error_count),
        .busy_drop_count(busy_drop_count),
        .response_busy(response_busy)
    );

    uart_tx_8n1 #(.CLOCK_HZ(CLOCK_HZ), .BAUD(BAUD)) u_tx (
        .clk(clk), .rst(rst), .data_in(tx_byte),
        .data_valid(tx_byte_valid), .data_ready(tx_byte_ready),
        .tx_pin(uart_txd), .byte_done()
    );
endmodule

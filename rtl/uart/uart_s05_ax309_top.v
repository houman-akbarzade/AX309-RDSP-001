// AX309 Rev1.0-manual-based 4-pin UART lab application wrapper.
// FPGA USER RESET button: L3, active low (manual Table 13-1).
// Synchronous release of asynchronous reset. INIT values are implemented
// by Spartan-6 configuration (not a simulation-only $initial task).
module uart_s05_ax309_top (
    input wire clk50,
    input wire reset_n,
    input wire uart_rxd,
    output wire uart_txd
);
    reg [2:0] reset_pipe = 3'b111;
    always @(posedge clk50 or negedge reset_n) begin
        if (!reset_n) reset_pipe <= 3'b111;
        else reset_pipe <= {reset_pipe[1:0],1'b0};
    end
    wire rst = reset_pipe[2];

    uart_s05_session_top #(
        .CLOCK_HZ(50000000),.BAUD(115200),
        .TIMEOUT_CLKS(86800),
        .TX_ACK_TIMEOUT_CLKS(100000000)
    ) u_link (
        .clk(clk50),.rst(rst),.uart_rxd(uart_rxd),.uart_txd(uart_txd),
        .active_session(),.expected_seq(),.activation_count(),
        .accepted_count(),.duplicate_count(),.stale_count(),
        .nack_count(),.good_frames(),.crc_errors(),.header_errors(),
        .length_errors(),.partial_timeouts(),.uart_errors(),
        .cpi_open(),.cpi_id(),.iq_uploaded_bytes(),
        .iq_readback_acked_bytes(),.tx_next_seq(),.tx_retry_exhausted()
    );
endmodule

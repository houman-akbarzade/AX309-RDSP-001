// AX309 S05 actual UART/R1 session-control bring-up top.
// Reuses the validated S02 parser as a frame-holding receive engine.
// Banked CPI memory and raw-IQ StageData are included; no DSP RUN.
module uart_s05_session_top #(
    parameter integer CLOCK_HZ=50000000,
    parameter integer BAUD=115200,
    parameter integer TIMEOUT_CLKS=86800,
    parameter integer TX_ACK_TIMEOUT_CLKS=100000000
)(
    input wire clk,
    input wire rst,
    input wire uart_rxd,
    output wire uart_txd,
    output wire active_session,
    output wire [31:0] expected_seq,
    output wire [31:0] activation_count,
    output wire [31:0] accepted_count,
    output wire [31:0] duplicate_count,
    output wire [31:0] stale_count,
    output wire [31:0] nack_count,
    output wire [15:0] good_frames,
    output wire [15:0] crc_errors,
    output wire [15:0] header_errors,
    output wire [15:0] length_errors,
    output wire [15:0] partial_timeouts,
    output wire [15:0] uart_errors,
    output wire cpi_open,
    output wire [31:0] cpi_id,
    output wire [14:0] iq_uploaded_bytes,
    output wire [14:0] iq_readback_acked_bytes,
    output wire [31:0] tx_next_seq,
    output wire tx_retry_exhausted
);
    wire [7:0] rx_byte,tx_byte,rd_byte;
    wire rx_valid,rx_framing_error;
    wire tx_valid,tx_ready;
    wire frame_ready,frame_done;
    wire [7:0] frame_type,frame_flags;
    wire [31:0] frame_seq,frame_crc;
    wire [15:0] frame_length;
    wire [9:0] rd_index;
    wire reply_valid,reply_ready;
    wire [7:0] reply_type,reply_opcode;
    wire [127:0] reply_sid;
    wire [31:0] reply_seq,reply_number;
    wire iq_write_en;
    wire [12:0] iq_write_addr,iq_read_addr;
    wire [31:0] iq_write_data,iq_read_word;
    wire [31:0] stage_cpi_id,stage_offset;
    wire [15:0] stage_count;
    uart_rx_8n1 #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD)) u_rx (
       .clk(clk),.rst(rst),.rx_pin(uart_rxd),
       .data_out(rx_byte),.data_valid(rx_valid),
       .framing_error(rx_framing_error),.busy()
    );
    s02_frame_echo #(.TIMEOUT_CLKS(TIMEOUT_CLKS),.ECHO_MODE(0)) u_parser (
       .clk(clk),.rst(rst),.rx_data(rx_byte),.rx_valid(rx_valid),
       .rx_framing_error(rx_framing_error),
       .tx_data(),.tx_valid(),.tx_ready(1'b0),
       .good_count(good_frames),.crc_error_count(crc_errors),
       .header_error_count(header_errors),.length_error_count(length_errors),
       .partial_timeout_count(partial_timeouts),.uart_error_count(uart_errors),
       .busy_drop_count(),.response_busy(),
       .frame_ready(frame_ready),.frame_done(frame_done),
       .frame_type(frame_type),.frame_flags(frame_flags),.frame_seq(frame_seq),
       .frame_length(frame_length),.frame_crc(frame_crc),
       .frame_rd_index(rd_index),.frame_rd_byte(rd_byte)
    );
    s05_session_arq #(.TX_ACK_TIMEOUT_CLKS(TX_ACK_TIMEOUT_CLKS)) u_session (
       .clk(clk),.rst(rst),.frame_ready(frame_ready),.frame_done(frame_done),
       .frame_type(frame_type),.frame_flags(frame_flags),
       .frame_seq(frame_seq),.frame_length(frame_length),.frame_crc(frame_crc),
       .rd_index(rd_index),.rd_byte(rd_byte),
       .reply_ready(reply_ready),.reply_valid(reply_valid),
       .reply_type(reply_type),.reply_opcode(reply_opcode),
       .reply_sid(reply_sid),.reply_seq(reply_seq),
       .reply_number(reply_number),
       .active_session(active_session),
       .rx_expected_seq(expected_seq),.activation_count(activation_count),
       .accepted_count(accepted_count),.duplicate_count(duplicate_count),
       .stale_count(stale_count),.nack_count(nack_count),
       .cpi_id(cpi_id),.cpi_open(cpi_open),
       .iq_uploaded_bytes(iq_uploaded_bytes),
       .iq_write_en(iq_write_en),.iq_write_addr(iq_write_addr),
       .iq_write_data(iq_write_data),
       .iq_readback_acked_bytes(iq_readback_acked_bytes),
       .stage_cpi_id(stage_cpi_id),.stage_offset(stage_offset),
       .stage_count(stage_count),.tx_next_seq(tx_next_seq),
       .tx_retry_exhausted(tx_retry_exhausted)
    );
    s02_r1_reply_tx u_reply (
       .clk(clk),.rst(rst),.send_valid(reply_valid),.send_ready(reply_ready),
       .response_type(reply_type),.response_opcode(reply_opcode),
       .response_sid(reply_sid),.response_seq(reply_seq),
       .response_number(reply_number),
       .stage_cpi_id(stage_cpi_id),.stage_offset(stage_offset),
       .stage_count(stage_count),
       .iq_read_addr(iq_read_addr),.iq_read_word(iq_read_word),
       .tx_data(tx_byte),.tx_valid(tx_valid),.tx_ready(tx_ready),.busy()
    );
    s05_iq_cpi_banked u_iq_store (
       .clk(clk),.write_en(iq_write_en),.write_addr(iq_write_addr),
       .write_word(iq_write_data),.read_addr(iq_read_addr),
       .read_word(iq_read_word)
    );
    uart_tx_8n1 #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD)) u_tx (
       .clk(clk),.rst(rst),.data_in(tx_byte),.data_valid(tx_valid),
       .data_ready(tx_ready),.tx_pin(uart_txd),.byte_done()
    );
endmodule

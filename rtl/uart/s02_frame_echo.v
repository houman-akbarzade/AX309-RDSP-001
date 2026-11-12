// AX309 S05 S02 framing parser and ECHO test responder.
// Synthesizable Spartan-6 Verilog-2001, no $readmemh/initial/delay in RTL.
// Serializes exactly the validated input frame, including original CRC.
// Standalone laboratory loopback; NO session FSM, ARQ, IQ DSP or CPI controller.
// Only ONE frame buffered; bytes arriving during echo are counted and dropped.
// Back-pressure through the host Stop-and-Wait protocol is REQUIRED.
module s02_frame_echo #(
    parameter integer TIMEOUT_CLKS = 86800
)(
    input  wire       clk,
    input  wire       rst,
    input  wire [7:0] rx_data,
    input  wire       rx_valid,
    input  wire       rx_framing_error,
    output wire [7:0] tx_data,
    output wire       tx_valid,
    input  wire       tx_ready,
    output reg  [15:0] good_count,
    output reg  [15:0] crc_error_count,
    output reg  [15:0] header_error_count,
    output reg  [15:0] length_error_count,
    output reg  [15:0] partial_timeout_count,
    output reg  [15:0] uart_error_count,
    output reg  [15:0] busy_drop_count,
    output wire        response_busy
);
    localparam [2:0] SEARCH=0, HEADER=1, PAYLOAD=2,
                     CRC_BYTES=3, ECHO_FETCH=4, ECHO_SEND=5;
    reg [2:0] state;
    reg [1:0] sof_seen;
    reg [9:0] write_pos;
    reg [9:0] read_pos;
    reg [9:0] frame_bytes;
    reg [15:0] declared_length;
    reg [15:0] remaining;
    reg [1:0] crc_pos;
    reg [31:0] crc_value;
    reg [31:0] rx_crc;
    reg [7:0] header_type;
    reg [31:0] header_sequence;
    reg [31:0] idle_cycles;
    // 529 bytes: SOF + nine header bytes + 512 data + four CRC bytes.
    // Registered read enables block RAM inference on Xilinx Spartan-6.
    reg [7:0] frame_ram [0:524];
    reg [7:0] ram_read_q;
    // First four wire octets are fixed SOF; do not multi-write into BRAM.
    assign tx_data = (read_pos == 0) ? 8'hA5 :
                     (read_pos == 1) ? 8'h5A :
                     (read_pos == 2) ? 8'hC3 :
                     (read_pos == 3) ? 8'h3C : ram_read_q;

    assign tx_valid = (state == ECHO_SEND);
    assign response_busy = (state == ECHO_FETCH) || (state == ECHO_SEND);

    function [31:0] crc32_byte;
        input [31:0] old_crc;
        input [7:0] data;
        reg [31:0] x;
        integer i;
        begin
            x = old_crc ^ {24'd0, data};
            for (i = 0; i < 8; i = i + 1)
                if (x[0]) x = (x >> 1) ^ 32'hEDB88320;
                else x = x >> 1;
            crc32_byte = x;
        end
    endfunction

    always @(posedge clk) begin
        if (rst) begin
            state <= SEARCH;
            sof_seen <= 0;
            write_pos <= 0;
            read_pos <= 0;
            frame_bytes <= 0;
            declared_length <= 0;
            remaining <= 0;
            crc_pos <= 0;
            crc_value <= 32'hFFFFFFFF;
            rx_crc <= 0;
            header_type <= 0;
            header_sequence <= 0;
            idle_cycles <= 0;
            ram_read_q <= 0;
            good_count <= 0;
            crc_error_count <= 0;
            header_error_count <= 0;
            length_error_count <= 0;
            partial_timeout_count <= 0;
            uart_error_count <= 0;
            busy_drop_count <= 0;
        end else begin
            // One synchronous BRAM read port: registered data, registered read enable.
            if (state == ECHO_FETCH) begin
                if (read_pos >= 4) ram_read_q <= frame_ram[read_pos - 4];
                state <= ECHO_SEND;
            end else if (state == ECHO_SEND && tx_ready) begin
                if (read_pos == frame_bytes - 1'b1) begin
                    state <= SEARCH;
                    sof_seen <= 0;
                end else begin
                    read_pos <= read_pos + 1'b1;
                    state <= ECHO_FETCH;
                end
            end

            if (state == HEADER || state == PAYLOAD || state == CRC_BYTES) begin
                if (rx_valid || rx_framing_error)
                    idle_cycles <= 0;
                else if (idle_cycles >= TIMEOUT_CLKS - 1) begin
                    state <= SEARCH;
                    sof_seen <= 0;
                    idle_cycles <= 0;
                    partial_timeout_count <= partial_timeout_count + 1'b1;
                end else
                    idle_cycles <= idle_cycles + 1'b1;
            end else idle_cycles <= 0;

            // Single indexed write port enables block-RAM inference.
            // Position 4..528 corresponds to RAM index 0..524.
            // Writing a rejected header is harmless: only a CRC-valid frame
            // can ever enter the echo state.
            if (rx_valid && (state == HEADER || state == PAYLOAD || state == CRC_BYTES))
                frame_ram[write_pos - 4] <= rx_data;

            if (rx_framing_error) begin
                uart_error_count <= uart_error_count + 1'b1;
                if (state == HEADER || state == PAYLOAD || state == CRC_BYTES) begin
                    state <= SEARCH;
                    sof_seen <= 0;
                end
            end else if (rx_valid) begin
                case (state)
                    SEARCH: begin
                        case (sof_seen)
                            2'd0: sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            2'd1: begin
                                if (rx_data == 8'h5A) sof_seen <= 2'd2;
                                else sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            end
                            2'd2: begin
                                if (rx_data == 8'hC3) sof_seen <= 2'd3;
                                else sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            end
                            2'd3: begin
                                if (rx_data == 8'h3C) begin
                                    state <= HEADER;
                                    write_pos <= 10'd4;
                                    crc_value <= 32'hFFFFFFFF;
                                    declared_length <= 0;
                                    header_sequence <= 0;
                                    sof_seen <= 0;
                                    idle_cycles <= 0;
                                end else
                                    sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            end
                        endcase
                    end
                    HEADER: begin
                        if (write_pos == 4 && rx_data != 8'd1) begin
                            state <= SEARCH;
                            sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            header_error_count <= header_error_count + 1'b1;
                        end else if (write_pos == 5 &&
                                     (rx_data < 8'd1 || rx_data > 8'd9)) begin
                            state <= SEARCH;
                            sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            header_error_count <= header_error_count + 1'b1;
                        end else if (write_pos == 6 &&
                                     ((header_type == 8'd9 && rx_data != 0) ||
                                      (header_type != 8'd9 && rx_data != 1))) begin
                            state <= SEARCH;
                            sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            header_error_count <= header_error_count + 1'b1;
                        end else if (write_pos == 12 &&
                                     {rx_data,declared_length[7:0]} > 16'd512) begin
                            state <= SEARCH;
                            sof_seen <= (rx_data == 8'hA5) ? 2'd1 : 2'd0;
                            length_error_count <= length_error_count + 1'b1;
                        end else if (write_pos == 12 &&
                                     header_type == 8'd9 && header_sequence != 0) begin
                            state <= SEARCH;
                            sof_seen <= 0;
                            header_error_count <= header_error_count + 1'b1;
                        end else begin
                            crc_value <= crc32_byte(crc_value, rx_data);
                            write_pos <= write_pos + 1'b1;
                            if (write_pos == 5) header_type <= rx_data;
                            if (write_pos >= 7 && write_pos <= 10)
                                header_sequence[8*(write_pos-7) +: 8] <= rx_data;
                            if (write_pos == 11)
                                declared_length[7:0] <= rx_data;
                            if (write_pos == 12) begin
                                declared_length[15:8] <= rx_data;
                                remaining <= {rx_data,declared_length[7:0]};
                                crc_pos <= 0;
                                if ({rx_data,declared_length[7:0]} == 0)
                                    state <= CRC_BYTES;
                                else state <= PAYLOAD;
                            end
                        end
                    end
                    PAYLOAD: begin
                        crc_value <= crc32_byte(crc_value, rx_data);
                        write_pos <= write_pos + 1'b1;
                        if (remaining == 1) begin
                            remaining <= 0;
                            crc_pos <= 0;
                            state <= CRC_BYTES;
                        end else remaining <= remaining - 1'b1;
                    end
                    CRC_BYTES: begin
                        write_pos <= write_pos + 1'b1;
                        rx_crc[8*crc_pos +: 8] <= rx_data;
                        if (crc_pos == 3) begin
                            if ({rx_data,rx_crc[23:0]} == ~crc_value) begin
                                good_count <= good_count + 1'b1;
                                frame_bytes <= write_pos + 1'b1;
                                read_pos <= 0;
                                state <= ECHO_FETCH;
                            end else begin
                                crc_error_count <= crc_error_count + 1'b1;
                                state <= SEARCH;
                                sof_seen <= 0;
                            end
                        end else crc_pos <= crc_pos + 1'b1;
                    end
                    default: begin
                        // No second receive buffer. A host MUST await the
                        // echo/ACK before sending a subsequent frame.
                        busy_drop_count <= busy_drop_count + 1'b1;
                    end
                endcase
            end
        end
    end
endmodule

`timescale 1ns / 1ps
// ISim real serial 50MHz/115200 8N1 stimulus; gold byte frames generated
// INDEPENDENTLY by pc_link.codec.Frame.encode (not by this testbench).
// DUT returns exact accepted frame bytes; monitor independently bit-samples TX.
module tb_uart_s02_echo;
    parameter integer CLOCK_HZ=50000000;
    parameter integer BAUD=115200;
    localparam integer CPB=CLOCK_HZ/BAUD;
    reg clk=0, rst=1, uart_rxd=1;
    always #10 clk = ~clk; // Actual nominal 50MHz.
    wire uart_txd;
    wire [15:0] good_count, crc_error_count, header_error_count;
    wire [15:0] length_error_count, partial_timeout_count;
    wire [15:0] uart_error_count, busy_drop_count;
    wire response_busy;

    uart_s02_echo_top #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD),
                         .TIMEOUT_CLKS(16000)) dut(
        .clk(clk),.rst(rst),.uart_rxd(uart_rxd),.uart_txd(uart_txd),
        .good_count(good_count),.crc_error_count(crc_error_count),
        .header_error_count(header_error_count),
        .length_error_count(length_error_count),
        .partial_timeout_count(partial_timeout_count),
        .uart_error_count(uart_error_count),.busy_drop_count(busy_drop_count),
        .response_busy(response_busy)
    );
    reg [7:0] hello [0:40];
    reg [7:0] iq_529 [0:528];
    reg [7:0] after [0:36];
    reg [7:0] bad_crc [0:40];
    reg [7:0] bad_version [0:40];
    reg [7:0] bad_flags [0:40];
    reg [7:0] bad_length [0:12];
    reg [7:0] truncated [0:19];
    reg [7:0] noise [0:12];
    reg [7:0] expected_echo [0:606];

    integer tx_seen=0;
    integer tx_bit_errors=0;
    integer tindex;
    reg [7:0] decoded;
    integer i, bitno;
    integer validations=0;
    integer error_tests=0;
    reg [7:0] next_byte;

    task fail;
        input [1023:0] reason;
        begin
            $display("FAIL tb_uart_s02_echo: %0s t=%0t rx_ok=%0d tx_seen=%0d crc=%0d hdr=%0d len=%0d trunc=%0d uart=%0d busy=%0d",
             reason,$time,good_count,tx_seen,crc_error_count,
             header_error_count,length_error_count,partial_timeout_count,
             uart_error_count,busy_drop_count);
            $finish;
        end
    endtask

    // Host-side physical serial writer independent of RTL UART TX/RX.
    task serial_byte;
        input [7:0] value;
        input good_stop;
        integer k;
        begin
            @(negedge clk); uart_rxd=1'b0;
            repeat(CPB) @(negedge clk);
            for(k=0;k<8;k=k+1) begin
                uart_rxd=value[k];
                repeat(CPB) @(negedge clk);
            end
            uart_rxd=good_stop;
            repeat(CPB) @(negedge clk);
            uart_rxd=1'b1;
        end
    endtask

    task send_vector;
        input integer vector_id;
        input integer length;
        integer k;
        reg [7:0] value;
        begin
            for(k=0;k<length;k=k+1) begin
                case(vector_id)
                    0: value=hello[k];
                    1: value=iq_529[k];
                    2: value=after[k];
                    3: value=bad_crc[k];
                    4: value=bad_version[k];
                    5: value=bad_flags[k];
                    6: value=bad_length[k];
                    7: value=truncated[k];
                    8: value=noise[k];
                    default: fail("invalid vector id");
                endcase
                serial_byte(value, 1'b1);
            end
        end
    endtask

    task await_tx_count;
        input integer target;
        begin
            while(tx_seen < target) @(posedge clk);
            repeat(CPB*2) @(posedge clk);
            if(tx_seen != target)
                fail("TX byte count mismatch");
        end
    endtask

    // Independent bit-level UART TX observer. Does NOT instantiate uart_rx.
    initial begin : tx_monitor
        forever begin
            @(negedge uart_txd);
            repeat(CPB/2) @(posedge clk);
            if(uart_txd !== 1'b0) fail("TX start bit error");
            decoded=0;
            for(tindex=0;tindex<8;tindex=tindex+1) begin
                repeat(CPB) @(posedge clk);
                decoded[tindex]=uart_txd;
            end
            repeat(CPB) @(posedge clk);
            if(uart_txd !== 1'b1) fail("TX stop bit error");
            if(tx_seen>=607) fail("unexpected extra TX byte");
            if(decoded !== expected_echo[tx_seen]) begin
                $display("TX_MISMATCH index=%0d actual=%02h expected=%02h",
                         tx_seen, decoded, expected_echo[tx_seen]);
                fail("independent byte-for-byte TX scoreboard mismatch");
            end
            tx_seen=tx_seen+1;
        end
    end

    initial begin
        // Fail closed if UART framing/parser stalls or echo times out.
        #2000000000;
        fail("global ISim watchdog");
    end

    initial begin
        $readmemh("vectors/uart_pc/hello.mem", hello);
        $readmemh("vectors/uart_pc/iq_529.mem", iq_529);
        $readmemh("vectors/uart_pc/after.mem", after);
        $readmemh("vectors/uart_pc/bad_crc.mem", bad_crc);
        $readmemh("vectors/uart_pc/bad_version.mem", bad_version);
        $readmemh("vectors/uart_pc/bad_flags.mem", bad_flags);
        $readmemh("vectors/uart_pc/bad_length.mem", bad_length);
        $readmemh("vectors/uart_pc/truncated.mem", truncated);
        $readmemh("vectors/uart_pc/noise.mem", noise);
        $readmemh("vectors/uart_pc/expected_echo.mem", expected_echo);
        repeat(12) @(negedge clk);
        rst=0;
        repeat(CPB*2) @(posedge clk);
        if(CPB!==434) fail("expected real 50MHz 115200 baud ticks");
        $display("CHECK nominal 50MHz 115200 baud CPB=%0d",CPB);
        validations=validations+1;

        // 41-B SESSION_HELLO golden PC frame and full bytewise TX echo.
        send_vector(0,41);
        await_tx_count(41);
        if(good_count!=1 || crc_error_count!=0 || busy_drop_count!=0)
            fail("41-byte SESSION_HELLO path");
        $display("CHECK PC_HELLO_41_RX_TX exact 41 bytes CRC accepted");
        validations=validations+1;

        // Maximum legal 512-byte payload / 529-byte wire IQ_UPLOAD.
        // Includes deliberate internal SOF sequence inside IQ data.
        send_vector(1,529);
        await_tx_count(570);
        if(good_count!=2 || busy_drop_count!=0)
            fail("529-byte IQ frame path");
        $display("CHECK PC_IQ_UPLOAD_529_RX_TX exact 529 bytes (SOF within payload)");
        validations=validations+1;

        send_vector(3,41);
        repeat(CPB*3) @(posedge clk);
        if(crc_error_count!=1 || good_count!=2 || tx_seen!=570)
            fail("bad CRC not rejected");
        $display("CHECK BAD_CRC reject, no TX");
        error_tests=error_tests+1;

        send_vector(6,13);
        repeat(CPB*3) @(posedge clk);
        if(length_error_count!=1 || good_count!=2 || tx_seen!=570)
            fail("513-byte declared payload not rejected");
        $display("CHECK OVER_LENGTH_513 reject");
        error_tests=error_tests+1;

        send_vector(4,41);
        send_vector(5,41);
        repeat(CPB*3) @(posedge clk);
        if(header_error_count<2 || good_count!=2 || tx_seen!=570)
            fail("bad version / flags not rejected");
        $display("CHECK BAD_VERSION and BAD_FLAGS reject");
        error_tests=error_tests+2;

        send_vector(7,20);
        repeat(18000) @(posedge clk);
        if(partial_timeout_count<1 || good_count!=2 || tx_seen!=570)
            fail("truncated frame timeout not detected");
        $display("CHECK TRUNCATED_FRAME timeout and parser reset");
        error_tests=error_tests+1;

        serial_byte(8'h55,1'b0);
        repeat(CPB*3) @(posedge clk);
        if(uart_error_count<1 || good_count!=2 || tx_seen!=570)
            fail("UART bad stop bit not detected");
        $display("CHECK UART_FRAMING_ERROR bad stop bit reject");
        error_tests=error_tests+1;

        send_vector(8,13);
        repeat(CPB*2) @(posedge clk);
        if(good_count!=2 || tx_seen!=570)
            fail("noise spuriously accepted");
        $display("CHECK SERIAL_NOISE no spurious frame");
        error_tests=error_tests+1;

        // 37-B PC codec ACK is a valid framed S02 TYPE; echo as test data.
        // Note: NOT real ACK generation or session/ARQ validation.
        send_vector(2,37);
        await_tx_count(607);
        if(good_count!=3 || tx_seen!=607 || crc_error_count!=1 ||
           length_error_count!=1 || header_error_count<2 ||
           partial_timeout_count<1 || uart_error_count<1 ||
           busy_drop_count!=0)
            fail("post-fault recovery counters or data mismatch");
        $display("CHECK POST_FAULT_RECOVERY_37 exact bytewise UART TX");
        validations=validations+1;

        $display("PASS tb_uart_s02_echo: valid_frames=3 tx_bytes=607 good_checks=%0d rejected_fault_cases=%0d crc=%0d hdr=%0d len=%0d trunc=%0d uart=%0d busy=%0d CPB=%0d",
         validations,error_tests,crc_error_count,header_error_count,
         length_error_count,partial_timeout_count,uart_error_count,busy_drop_count,CPB);
        $finish;
    end
endmodule

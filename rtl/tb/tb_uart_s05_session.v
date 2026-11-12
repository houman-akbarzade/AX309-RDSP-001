`timescale 1ns/1ps
// Independent PC codec R1 frame vectors are serially transmitted at
// 50MHz clock and 115200 8N1. TX is monitored bit-by-bit independently.
module tb_uart_s05_session;
    localparam integer CLOCK_HZ=50000000;
    localparam integer BAUD=115200;
    localparam integer CPB=CLOCK_HZ/BAUD;
    reg clk=0, rst=1,uart_rxd=1;
    always #10 clk=~clk;
    wire uart_txd,active_session,cpi_open;
    wire [31:0] expected_seq,activation_count,accepted_count,
                duplicate_count,stale_count,nack_count,cpi_id;
    wire [15:0] good_frames,crc_errors,header_errors,length_errors,
                partial_timeouts,uart_errors;
    uart_s05_session_top #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD),
                             .TIMEOUT_CLKS(16000)) dut(
        .clk(clk),.rst(rst),.uart_rxd(uart_rxd),.uart_txd(uart_txd),
        .active_session(active_session),.expected_seq(expected_seq),
        .activation_count(activation_count),.accepted_count(accepted_count),
        .duplicate_count(duplicate_count),.stale_count(stale_count),
        .nack_count(nack_count),.good_frames(good_frames),
        .crc_errors(crc_errors),.header_errors(header_errors),
        .length_errors(length_errors),.partial_timeouts(partial_timeouts),
        .uart_errors(uart_errors),.cpi_open(cpi_open),.cpi_id(cpi_id)
    );
    reg [7:0] hello_a[0:40],activate_a[0:43];
    reg [7:0] hello_b[0:40],activate_b[0:43];
    reg [7:0] old_a[0:37],open_b[0:37],future_b[0:37],
              new_bad_b[0:37],old_seq_b[0:37],bad_crc[0:37];
    reg [7:0] inbound_ack_b[0:36],truncated[0:17];
    reg [7:0] expected_responses[0:626];
    integer tx_seen=0;
    integer test_checks=0;
    integer i,mon_bit;
    reg [7:0] decoded;
    task fail;
        input [1023:0] why;
        begin
            $display("FAIL tb_uart_s05_session: %0s at t=%0t tx=%0d act=%0d seq=%0d acc=%0d dup=%0d stale=%0d nack=%0d crc=%0d partial=%0d",
              why,$time,tx_seen,activation_count,expected_seq,
              accepted_count,duplicate_count,stale_count,nack_count,
              crc_errors,partial_timeouts);
            $finish;
        end
    endtask
    task serial_byte;
        input [7:0] data;
        integer b;
        begin
            @(negedge clk);uart_rxd=0;
            repeat(CPB) @(negedge clk);
            for(b=0;b<8;b=b+1) begin
                uart_rxd=data[b];
                repeat(CPB) @(negedge clk);
            end
            uart_rxd=1;
            repeat(CPB) @(negedge clk);
        end
    endtask
    task send_vec;
        input integer v;
        input integer len;
        integer j;
        reg [7:0] next_byte;
        begin
            for(j=0;j<len;j=j+1) begin
                case(v)
                    0:next_byte=hello_a[j];
                    1:next_byte=activate_a[j];
                    2:next_byte=hello_b[j];
                    3:next_byte=activate_b[j];
                    4:next_byte=old_a[j];
                    5:next_byte=open_b[j];
                    6:next_byte=future_b[j];
                    7:next_byte=new_bad_b[j];
                    8:next_byte=old_seq_b[j];
                    9:next_byte=bad_crc[j];
                    10:next_byte=inbound_ack_b[j];
                    11:next_byte=truncated[j];
                    default:fail("invalid test vector");
                endcase
                serial_byte(next_byte);
            end
        end
    endtask
    task await_count;
        input integer target;
        begin
            while(tx_seen<target) @(posedge clk);
            repeat(CPB*2) @(posedge clk);
            if(tx_seen!=target) fail("unexpected TX bytes");
        end
    endtask
    task expect_no_tx;
        input integer before;
        begin
            repeat(CPB*4) @(posedge clk);
            if(tx_seen!=before) fail("unexpected reply to stale/invalid frame");
        end
    endtask

    // Independent TX bit sampler, not instantiated FPGA UART receiver.
    initial begin
        forever begin
            @(negedge uart_txd);
            repeat(CPB/2) @(posedge clk);
            if(uart_txd!==0)fail("TX start-bit error");
            decoded=0;
            for(mon_bit=0;mon_bit<8;mon_bit=mon_bit+1) begin
                repeat(CPB) @(posedge clk);
                decoded[mon_bit]=uart_txd;
            end
            repeat(CPB) @(posedge clk);
            if(uart_txd!==1)fail("TX stop-bit error");
            if(tx_seen>=627)fail("spurious extra response byte");
            if(decoded!==expected_responses[tx_seen])begin
                $display("MISMATCH at TX index %0d expected=%02x got=%02x",
                   tx_seen,expected_responses[tx_seen],decoded);
                fail("PC codec golden byte mismatch");
            end
            tx_seen=tx_seen+1;
        end
    end
    initial begin
        #1000000000;
        fail("ISim global watchdog");
    end

    initial begin
        $readmemh("vectors/uart_r1/hello_a.mem",hello_a);
        $readmemh("vectors/uart_r1/activate_a.mem",activate_a);
        $readmemh("vectors/uart_r1/hello_b.mem",hello_b);
        $readmemh("vectors/uart_r1/activate_b.mem",activate_b);
        $readmemh("vectors/uart_r1/old_a.mem",old_a);
        $readmemh("vectors/uart_r1/open_b.mem",open_b);
        $readmemh("vectors/uart_r1/future_b.mem",future_b);
        $readmemh("vectors/uart_r1/new_bad_b.mem",new_bad_b);
        $readmemh("vectors/uart_r1/old_seq_b.mem",old_seq_b);
        $readmemh("vectors/uart_r1/bad_crc.mem",bad_crc);
        $readmemh("vectors/uart_r1/inbound_ack_b.mem",inbound_ack_b);
        $readmemh("vectors/uart_r1/truncated.mem",truncated);
        $readmemh("vectors/uart_r1/expected_responses.mem",expected_responses);
        repeat(12) @(negedge clk);
        rst=0;
        repeat(CPB*2) @(posedge clk);

        send_vec(0,41);await_count(43);
        if(active_session!==0 || activation_count!==0)fail("HELLO wrongly activates");
        $display("CHECK HELLO_A->OFFER_A 43 byte exact");
        test_checks=test_checks+1;

        send_vec(1,44);await_count(87);
        if(active_session!==1 || activation_count!==1 || expected_seq!==0)
            fail("first ACTIVATE failed");
        $display("CHECK ACTIVATE_A->READY_A 44 byte exact, seq0");
        test_checks=test_checks+1;

        send_vec(1,44);await_count(131);
        if(activation_count!==1 || expected_seq!==0)
            fail("duplicate ACTIVATE reset seq or activated twice");
        $display("CHECK LOST_READY replay READY exact once-only activation");
        test_checks=test_checks+1;

        send_vec(2,41);await_count(174);
        if(active_session!==0)fail("new epoch did not quarantine old session");
        send_vec(3,44);await_count(218);
        if(active_session!==1 || activation_count!==2 || expected_seq!==0)
            fail("new epoch handshake");
        $display("CHECK NEW_EPOCH SID_B full 4-way, seq resets only once");
        test_checks=test_checks+1;

        send_vec(4,38);expect_no_tx(218);
        if(stale_count<1)fail("old SID not rejected");
        $display("CHECK STALE_SID_A rejected without ACK");
        test_checks=test_checks+1;

        send_vec(5,38);await_count(255);
        if(expected_seq!==1 || accepted_count!==1 || cpi_id!==23 || !cpi_open)
            fail("OPEN_CPI ACK/seq mismatch");
        $display("CHECK valid OPEN_CPI ACK0 byte-exact and CPI_ID=23");
        test_checks=test_checks+1;

        send_vec(5,38);await_count(292);
        if(expected_seq!==1 || accepted_count!==1 || duplicate_count!==1)
            fail("duplicate OPEN_CPI applied again");
        $display("CHECK ACK_LOST exact retry ACK0 no reapply");
        test_checks=test_checks+1;

        send_vec(3,44);await_count(336);
        if(expected_seq!==1 || accepted_count!==1 || activation_count!==2)
            fail("ACTIVATE after data reset active sequence");
        $display("CHECK repeated ACTIVATE after accepted data no seq reset");
        test_checks=test_checks+1;

        send_vec(6,38);await_count(373);
        if(expected_seq!==1 || nack_count!==1)
            fail("out-of-order seq did not NACK(expected=1)");
        $display("CHECK FUTURE_SEQ2 -> NACK2(expected_seq1)");
        test_checks=test_checks+1;

        send_vec(7,38);await_count(410);
        if(expected_seq!==1 || nack_count!==2 || cpi_id!==23)
            fail("illegal command advanced seq or CPI");
        $display("CHECK invalid OPEN_CPI at seq1 -> NACK1, CPI unchanged");
        test_checks=test_checks+1;

        send_vec(10,37);expect_no_tx(410);
        $display("CHECK inbound ACK is not ACKed (no ACK-of-ACK)");
        test_checks=test_checks+1;

        send_vec(8,38);expect_no_tx(410);
        if(stale_count<2)fail("old SID seq1 not rejected");
        $display("CHECK stale old SID seq1 no reply");
        test_checks=test_checks+1;

        send_vec(9,38);expect_no_tx(410);
        if(crc_errors!=1 || expected_seq!==1)fail("CRC corruption bypass");
        $display("CHECK bad CRC rejected before ARQ");
        test_checks=test_checks+1;

        send_vec(11,18);
        repeat(17000) @(posedge clk);
        if(partial_timeouts!=1 || expected_seq!==1)
            fail("partial timeout did not protect state");
        $display("CHECK partial frame timeout preserves seq/CPI");
        test_checks=test_checks+1;

        // Global reset wipes volatile session and cpi information.
        // Must start a completely new handshake, cannot invent COMMIT.
        rst=1;
        repeat(8) @(negedge clk);
        rst=0;
        repeat(CPB*2) @(posedge clk);
        if(active_session!==0 || cpi_open!==0 || expected_seq!==0 ||
           activation_count!==0) fail("global reset did not clear volatile session");
        send_vec(0,41);await_count(453);
        send_vec(1,44);await_count(497);
        if(active_session!==1 || activation_count!==1 || expected_seq!==0 ||
           cpi_open!==0)fail("post-reset new handshake error");
        $display("CHECK after RESET new HELLO/OFFER ACTIVATE/READY and fresh seq0");
        test_checks=test_checks+1;

        // Reset after HELLO but before ACTIVATE; a stale ACTIVATE may not
        // activate or reset a new session without a fresh HELLO.
        rst=1;
        repeat(8) @(negedge clk);
        rst=0;
        repeat(CPB*2) @(posedge clk);
        send_vec(0,41);await_count(540);
        if(active_session!==0 || activation_count!==0)
            fail("HELLO before reset must only negotiate");
        $display("CHECK reset after HELLO/OFFER: negotiation pending only");
        test_checks=test_checks+1;
        rst=1;
        repeat(8) @(negedge clk);
        rst=0;
        repeat(CPB*2) @(posedge clk);
        send_vec(1,44);expect_no_tx(540);
        if(active_session!==0 || activation_count!==0)
            fail("stale ACTIVATE accepted after global reset");
        $display("CHECK stale ACTIVATE after reset rejected without READY");
        test_checks=test_checks+1;
        send_vec(0,41);await_count(583);
        send_vec(1,44);await_count(627);
        if(active_session!==1 || activation_count!==1 || expected_seq!==0)
            fail("fresh post-reset four-message handshake failed");
        $display("CHECK new HELLO/ACTIVATE after reset, no phantom prior CPI");
        test_checks=test_checks+1;
        $display("PASS tb_uart_s05_session: test_checks=%0d response_frames=15 TX_bytes=627 cpi_id=0(after reset) 115200_8N1=434CPB independent_pc_codec_oracle=YES",
                test_checks);
        $finish;
    end
endmodule

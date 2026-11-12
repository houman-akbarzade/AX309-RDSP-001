`timescale 1ns/1ps
// Real ISim 8N1 serial test using independently PC codec-generated vectors.
// Full 35 IQ_UPLOAD packets => 16896B stored in banked BRAM, followed by
// 35 STAGE_REQUEST/StageData frames and byte-for-byte UART readback oracle.
// Outbound ACK lost once -> same STAGE_DATA seq & bytes replayed on timeout.
module tb_uart_s05_iq_full;
    // Accelerated full-CPI regression: 10 clocks/bit to avoid hundreds of
    // millions of simulator cycles. The separate session/echo TBs use the
    // actual nominal 50MHz/115200 = 434 clocks/bit.
    localparam integer CPB=10;
    reg clk=0,rst=1,uart_rxd=1;
    always #10 clk=~clk;
    wire uart_txd,active_session,cpi_open,tx_retry_exhausted;
    wire [31:0] expected_seq,activation_count,accepted_count,
                 duplicate_count,stale_count,nack_count,cpi_id,tx_next_seq;
    wire [15:0] good_frames,crc_errors,header_errors,length_errors,
                 partial_timeouts,uart_errors;
    wire [14:0] iq_uploaded_bytes,iq_readback_acked_bytes;

    uart_s05_session_top #(.CLOCK_HZ(1152000),.BAUD(115200),
                          .TIMEOUT_CLKS(16000),
                          .TX_ACK_TIMEOUT_CLKS(6000)) dut(
        .clk(clk),.rst(rst),.uart_rxd(uart_rxd),.uart_txd(uart_txd),
        .active_session(active_session),.expected_seq(expected_seq),
        .activation_count(activation_count),.accepted_count(accepted_count),
        .duplicate_count(duplicate_count),.stale_count(stale_count),
        .nack_count(nack_count),.good_frames(good_frames),
        .crc_errors(crc_errors),.header_errors(header_errors),
        .length_errors(length_errors),.partial_timeouts(partial_timeouts),
        .uart_errors(uart_errors),.cpi_open(cpi_open),.cpi_id(cpi_id),
        .iq_uploaded_bytes(iq_uploaded_bytes),
        .iq_readback_acked_bytes(iq_readback_acked_bytes),
        .tx_next_seq(tx_next_seq),.tx_retry_exhausted(tx_retry_exhausted)
    );
    reg [7:0] hello[0:40],activate[0:43],open_cpi[0:37];
    reg [7:0] uploads_flat[0:18330];
    reg [7:0] requests_flat[0:1539];
    reg [7:0] stage_acks_flat[0:1294];
    reg [7:0] wrong_offset[0:528],future[0:37],
              bad_crc[0:528],old_sid[0:528],truncated[0:33],
              bad_stage[0:43];
    reg [7:0] expected_responses[0:21753];
    reg [7:0] response_lengths[0:225];

    integer tx_seen=0,reply_seen=0,expected_cursor=0;
    integer test_checks=0;
    integer mon_bit;
    integer j;
    reg [7:0] decoded;
    task fail;
        input [1023:0] message;
        begin
            $display("FAIL tb_uart_s05_iq_full: %0s t=%0t TX=%0d replies=%0d rx_seq=%0d tx_seq=%0d upload=%0d readbackACK=%0d dup=%0d stale=%0d nack=%0d CRCerr=%0d timeout=%0d",
                     message,$time,tx_seen,reply_seen,expected_seq,tx_next_seq,
                     iq_uploaded_bytes,iq_readback_acked_bytes,
                     duplicate_count,stale_count,nack_count,crc_errors,
                     partial_timeouts);
            $finish;
        end
    endtask
    task serial_byte;
        input [7:0] value;
        integer k;
        begin
            @(negedge clk);uart_rxd=1'b0;
            repeat(CPB) @(negedge clk);
            for(k=0;k<8;k=k+1) begin
                uart_rxd=value[k];
                repeat(CPB) @(negedge clk);
            end
            uart_rxd=1'b1;
            repeat(CPB) @(negedge clk);
        end
    endtask
    task send_constant;
        input integer which;
        input integer bytes;
        integer k;
        reg [7:0] octet;
        begin
            for(k=0;k<bytes;k=k+1) begin
                case(which)
                    0:octet=hello[k];
                    1:octet=activate[k];
                    2:octet=open_cpi[k];
                    3:octet=wrong_offset[k];
                    4:octet=future[k];
                    5:octet=bad_crc[k];
                    6:octet=old_sid[k];
                    7:octet=truncated[k];
                    8:octet=bad_stage[k];
                    default:fail("bad constant frame selection");
                endcase
                serial_byte(octet);
            end
        end
    endtask
    task send_upload;
        input integer packet_id;
        integer start_at,frame_len,k;
        begin
            start_at=packet_id*529;
            frame_len=(packet_id<34)?529:345;
            for(k=0;k<frame_len;k=k+1)
                serial_byte(uploads_flat[start_at+k]);
        end
    endtask
    task send_stage_request;
        input integer packet_id;
        integer k;
        begin
            for(k=0;k<44;k=k+1)
                serial_byte(requests_flat[packet_id*44+k]);
        end
    endtask
    task send_stage_ack;
        input integer packet_id;
        integer k;
        begin
            for(k=0;k<37;k=k+1)
                serial_byte(stage_acks_flat[packet_id*37+k]);
        end
    endtask
    task next_reply;
        integer frame_size;
        begin
            if(reply_seen>=113)fail("reply counter exceeded golden count");
            frame_size=response_lengths[2*reply_seen] +
                         (256*response_lengths[2*reply_seen+1]);
            expected_cursor=expected_cursor+frame_size;
            while(tx_seen<expected_cursor) @(posedge clk);
            reply_seen=reply_seen+1;
            repeat(CPB) @(posedge clk);
            if(tx_seen>expected_cursor)fail("unexpected extra TX before next request");
        end
    endtask
    task no_response;
        begin
            // Controller validates the held frame over up to 27 SRAM
            // reads (3 clocks each); do not inspect it mid-decision.
            repeat(CPB*40) @(posedge clk);
            if(tx_seen!=expected_cursor)fail("unexpected TX for invalid frame");
        end
    endtask
    initial begin : tx_monitor
        forever begin
            @(negedge uart_txd);
            repeat(CPB/2) @(posedge clk);
            if(uart_txd!==0)fail("TX start bit");
            decoded=0;
            for(mon_bit=0;mon_bit<8;mon_bit=mon_bit+1) begin
                repeat(CPB) @(posedge clk);
                decoded[mon_bit]=uart_txd;
            end
            repeat(CPB) @(posedge clk);
            if(uart_txd!==1)fail("TX stop bit");
            if(tx_seen>=21754)fail("excess TX byte");
            if(decoded!==expected_responses[tx_seen])begin
                $display("IQ_TX_MISMATCH index=%0d expected=%02x actual=%02x",
                  tx_seen,expected_responses[tx_seen],decoded);
                fail("PC codec complete byte stream mismatch");
            end
            tx_seen=tx_seen+1;
        end
    end
    initial begin
        #1500000000;
        fail("global watchdog full CPI");
    end
    initial begin
        $readmemh("vectors/uart_iq_full/hello.mem",hello);
        $readmemh("vectors/uart_iq_full/activate.mem",activate);
        $readmemh("vectors/uart_iq_full/open_cpi.mem",open_cpi);
        $readmemh("vectors/uart_iq_full/uploads_flat.mem",uploads_flat);
        $readmemh("vectors/uart_iq_full/requests_flat.mem",requests_flat);
        $readmemh("vectors/uart_iq_full/stage_acks_flat.mem",stage_acks_flat);
        $readmemh("vectors/uart_iq_full/bad_offset.mem",wrong_offset);
        $readmemh("vectors/uart_iq_full/future.mem",future);
        $readmemh("vectors/uart_iq_full/bad_crc.mem",bad_crc);
        $readmemh("vectors/uart_iq_full/old_sid.mem",old_sid);
        $readmemh("vectors/uart_iq_full/truncated.mem",truncated);
        $readmemh("vectors/uart_iq_full/bad_stage.mem",bad_stage);
        $readmemh("vectors/uart_iq_full/expected_responses.mem",expected_responses);
        $readmemh("vectors/uart_iq_full/response_lengths.mem",response_lengths);
        repeat(16) @(negedge clk);
        rst=0;
        repeat(CPB*2) @(posedge clk);

        send_constant(0,41);next_reply();
        send_constant(1,44);next_reply();
        if(!active_session || expected_seq!=0)fail("handshake activation");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL SESSION_HELLO/OFFER ACTIVATE/READY");

        send_constant(2,38);next_reply();
        if(expected_seq!=1 || !cpi_open || cpi_id!=23)
            fail("OPEN_CPI no ACK");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL OPEN_CPI ACK0");

        send_constant(3,529);next_reply();
        if(nack_count!=1 || iq_uploaded_bytes!=0 || expected_seq!=1)
            fail("wrong offset NACK");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL wrong offset 488 at seq1 -> NACK");

        send_constant(4,38);next_reply();
        if(nack_count!=2 || iq_uploaded_bytes!=0)
            fail("future seq NACK");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL future seq3 -> NACK1");

        send_upload(0);next_reply();
        if(iq_uploaded_bytes!=488 || expected_seq!=2)
            fail("first IQ chunk not written before ACK");
        send_upload(0);next_reply();
        if(iq_uploaded_bytes!=488 || expected_seq!=2 || duplicate_count!=1)
            fail("duplicate IQ consumed twice");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL seq1 accepted then duplicate ACK without overwrite");

        send_constant(6,529);no_response();
        if(stale_count<1 || iq_uploaded_bytes!=488)
            fail("stale SID changed IQ");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL stale SID old epoch rejected");

        send_constant(5,529);no_response();
        if(crc_errors!=1 || expected_seq!=2)
            fail("bad CRC write advanced sequence");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL CRC corrupt packet rejected");

        send_constant(7,34);
        repeat(17000) @(posedge clk);
        if(partial_timeouts!=1 || iq_uploaded_bytes!=488)
            fail("truncated upload was accepted");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL truncated frame timeout with no mutation");

        for(j=1;j<35;j=j+1) begin
            send_upload(j);
            next_reply();
            if(expected_seq!=(j+2))
                fail("IQ upload seq mismatch");
        end
        if(iq_uploaded_bytes!=16896 || accepted_count!=36 ||
           expected_seq!=36 || cpi_id!=23)
            fail("full CPI not assembled exactly");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL 35 packets 16896 bytes complete and ACKed");

        send_constant(8,44);next_reply();
        if(expected_seq!=36 || nack_count!=3)
            fail("bad STAGE_REQUEST stage id not NACKed");
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL readback unsupported stage NACK36");

        for(j=0;j<35;j=j+1)begin
            send_stage_request(j);
            next_reply(); // inbound ACK of request seq 36+j
            next_reply(); // full STAGE_DATA with FPGA seq j and CRC
            if(j==0)begin
                // Host drops first STAGE_DATA ACK. After short test
                // timeout, FPGA retransmits the SAME bytes and sequence.
                next_reply();
                if(tx_next_seq!=0 || iq_readback_acked_bytes!=0)
                    fail("dropped first STAGE_DATA ACK advanced FPGA seq");
                test_checks=test_checks+1;
                $display("CHECK IQ_FULL FPGA STAGE_DATA retry after lost ACK 526B exact");
            end
            send_stage_ack(j);
            no_response();
            if(iq_readback_acked_bytes!=((j<34)?((j+1)*484):16896) ||
               tx_next_seq!=(j+1))
                fail("readback ACK count or outgoing seq mismatch");
            if(tx_retry_exhausted)fail("unexpected FPGA retry exhaustion");
        end
        test_checks=test_checks+1;
        $display("CHECK IQ_FULL 35 STAGE_DATA packets, full 16896 byte PC golden readback");

        if(tx_seen!=21754 || reply_seen!=113 ||
           iq_uploaded_bytes!=16896 || iq_readback_acked_bytes!=16896 ||
           expected_seq!=71 || tx_next_seq!=35 || accepted_count!=71 ||
           good_frames<71 || crc_errors!=1 || partial_timeouts!=1 ||
           duplicate_count!=1 || nack_count!=3 || stale_count<1)
            fail("final full CPI counters");
        $display("PASS tb_uart_s05_iq_full: test_checks=%0d RX_upload_frames=35 IQ_bytes=16896 TX_readback_frames=35 exact_TX_bytes=21754 responses=113 FPGA_outbound_retry=1 PC_codec_byte_oracle=YES ACCELERATED_CPB10",
                 test_checks);
        $finish;
    end
endmodule

// New integrated grouping->8-record FIFO back-pressure experiment.
// Reuses *archived unchanged* C05+independent-union-find golden vectors.
// This is not a UART protocol/ACK/commit verification.
module tb_grouping_fifo8_702;
    reg clk=0; always #5 clk=~clk;
    reg rst=1,start=0,cut_valid=0,cut_alarm=0,record_ready=0;
    reg [6:0] cut_range=0;
    reg [4:0] cut_bin=0;
    reg [45:0] cut_power=0;
    wire cut_ready,record_valid,group_done,group_busy;
    wire overflow_sticky,protocol_error,frame_invalid,frame_drained;
    wire [98:0] record_data;
    wire [3:0] fifo_occupancy;
    wire [9:0] produced_count,delivered_count;

    reg [46:0] input_words[0:30601];
    reg [88:0] golden[0:2047];
    reg [11:0] counts[0:10];
    integer expected_offset=0,src_count=0,record_count=0;
    integer stalls=0,full_cycles=0,high_water=0;
    integer source_stalls=0;
    integer clock_cycles=0, last_producer_cycle=-1;
    integer fastest_producer_interval=2147483647;
    integer slowest_producer_interval=0, producer_interval;
    integer k,j;
    reg [98:0] held_src,held_output;
    reg held_src_active=0;

    grouping_fifo8_subsystem dut(
      .clk(clk),.rst(rst),.start(start),
      .cut_valid(cut_valid),.cut_ready(cut_ready),
      .cut_range(cut_range),.cut_bin(cut_bin),
      .cut_power(cut_power),.cut_alarm(cut_alarm),
      .record_valid(record_valid),.record_ready(record_ready),
      .record_data(record_data),.fifo_occupancy(fifo_occupancy),
      .group_done(group_done),.group_busy(group_busy),
      .overflow_sticky(overflow_sticky),
      .protocol_error(protocol_error),.frame_invalid(frame_invalid),
      .produced_count(produced_count),.delivered_count(delivered_count),
      .frame_drained(frame_drained)
    );

    task fail;
      input [8*140-1:0] reason;
      begin
        $display("FAIL tb_grouping_fifo8_702: %0s src=%0d recv=%0d fifo=%0d produced=%0d delivered=%0d group_state=%0d",
          reason,src_count,record_count,fifo_occupancy,
          produced_count,delivered_count,dut.u_grouping.state);
        $finish;
      end
    endtask

    always @(posedge clk) if(!rst) begin
      clock_cycles=clock_cycles+1;
      if(dut.u_grouping.out_valid && dut.u_grouping.out_ready) begin
        if(last_producer_cycle>=0) begin
          producer_interval=clock_cycles-last_producer_cycle;
          if(producer_interval<fastest_producer_interval)
            fastest_producer_interval=producer_interval;
          if(producer_interval>slowest_producer_interval)
            slowest_producer_interval=producer_interval;
        end
        last_producer_cycle=clock_cycles;
      end
      if(fifo_occupancy>8) fail("occupancy exceeded 8");
      if(fifo_occupancy>high_water)
        high_water=fifo_occupancy;
      if(fifo_occupancy==8) full_cycles=full_cycles+1;
      if(dut.u_grouping.out_valid && !dut.u_grouping.out_ready)
        source_stalls=source_stalls+1;
      if(record_valid && !record_ready)
        stalls=stalls+1;
      if(overflow_sticky || protocol_error || frame_invalid)
        fail("grouping error during legal backpressure");
    end

    task start_case;
      begin
        @(negedge clk);start=1;
        @(negedge clk);start=0;
      end
    endtask

    task send_case;
      input integer case_id;
      integer w;
      begin
        for(w=0;w<2782;w=w+1) begin
          @(negedge clk);
          cut_valid=0;
          while(!cut_ready) @(negedge clk);
          cut_range=7'd3+w/26;
          cut_bin=5'd3+w%26;
          cut_alarm=input_words[case_id*2782+w][46];
          cut_power=input_words[case_id*2782+w][45:0];
          cut_valid=1;
          @(posedge clk);
          src_count=src_count+1;
        end
        @(negedge clk);cut_valid=0;
      end
    endtask

    task receive_702;
      integer rec;
      begin
        // No host output consumption until the full 8-entry FIFO is reached.
        wait(fifo_occupancy==8);
        wait(dut.u_grouping.out_valid && !dut.u_grouping.out_ready);
        @(negedge clk);
        held_src={dut.u_grouping.out_record_id,
          dut.u_grouping.out_range,dut.u_grouping.out_bin,
          dut.u_grouping.out_signed_bin,dut.u_grouping.out_peak_power,
          dut.u_grouping.out_cluster_cells,dut.u_grouping.out_tie_flag,
          dut.u_grouping.out_equal_power_cells};
        held_output=record_data;
        // 60,000 clock cycles exceeds one 13-byte record airtime
        // at an *illustrative* 50 MHz / 115200 8N1. Mock sink, not UART.
        for(j=0;j<60000;j=j+1) begin
          @(negedge clk);
          if(fifo_occupancy!==8 || !record_valid ||
             dut.u_grouping.out_ready || !dut.u_grouping.out_valid)
            fail("full FIFO did not halt producer");
          if(held_src!=={dut.u_grouping.out_record_id,
            dut.u_grouping.out_range,dut.u_grouping.out_bin,
            dut.u_grouping.out_signed_bin,dut.u_grouping.out_peak_power,
            dut.u_grouping.out_cluster_cells,dut.u_grouping.out_tie_flag,
            dut.u_grouping.out_equal_power_cells} ||
            held_output!==record_data)
            fail("source/FIFO data changed during full pause");
        end
        // Drain every provisional record with additional intermittent stalls.
        for(rec=0;rec<702;rec=rec+1) begin
          wait(record_valid);
          @(negedge clk);
          if ((rec%31)==0) begin
            held_output=record_data;
            repeat(13) begin
              @(negedge clk);
              if(!record_valid || held_output!==record_data)
                fail("record changed under downstream stall");
            end
          end
          if(!record_valid ||
             record_data[98:89] !== rec ||
             record_data[88:0] !== golden[expected_offset+rec]) begin
            $display("ORACLE record=%0d expected=%023x observed=%023x id=%0d",
              rec,golden[expected_offset+rec],record_data[88:0],record_data[98:89]);
            fail("record loss, duplicate, reordering or data corruption");
          end
          record_ready=1;
          @(posedge clk);
          @(negedge clk);
          record_ready=0;
          record_count=record_count+1;
        end
        wait(frame_drained);
        @(negedge clk);
        if(fifo_occupancy!==0 || record_valid || group_busy ||
           produced_count!==702 || delivered_count!==702 || !frame_drained)
          fail("702-record frame not fully drained");
        if(src_count!=2782 || record_count!=702)
          fail("unexpected input/output count");
        if(full_cycles==0 || source_stalls==0 || stalls==0 || high_water!=8)
          fail("actual FIFO full and source/consumer backpressure not exercised");
        $display("PASS GROUPING_FIFO_702: source_CUTs=%0d accepted_records=%0d produced=%0d delivered=%0d FIFO_high_water=%0d full_cycles=%0d source_stalls=%0d consumer_stalls=%0d",
         src_count,record_count,produced_count,delivered_count,
         high_water,full_cycles,source_stalls,stalls);
        $display("PRODUCER_RATE_EVIDENCE fastest_record_interval_cycles=%0d slowest_record_interval_cycles=%0d mock_sink_not_uart",
          fastest_producer_interval,slowest_producer_interval);
      end
    endtask

    initial begin
      $readmemh("vectors/grouping/input.mem",input_words);
      $readmemh("vectors/grouping/expected.mem",golden);
      $readmemh("vectors/grouping/counts.mem",counts);
      if(counts[8]!==702) fail("archived approved case 8 is not 702 clusters");
      for(k=0;k<8;k=k+1) expected_offset=expected_offset+counts[k];
      if(expected_offset!=181) fail("unexpected reference output offset");
      repeat(5) @(negedge clk);rst=0;
      start_case;
      fork
        send_case(8);
        receive_702;
      join
      if(!frame_drained)
        fail("committable status lost");
      $display("PASS tb_grouping_fifo8_702: 702/702 independently certified C05 records through 8-slot lossless FIFO, no producer drop, hard-full stall, valid-ready persistence, complete drain; NO UART COMMIT/ACK CLAIM");
      $finish;
    end
    initial begin
      #35000000;
      $display("FAIL tb_grouping_fifo8_702 TIMEOUT produced=%0d delivered=%0d fifo=%0d group_state=%0d",
        produced_count,delivered_count,fifo_occupancy,dut.u_grouping.state);
      $finish;
    end
endmodule

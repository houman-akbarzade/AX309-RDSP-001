// Connected RTL self-checker: 5 new synthetic U46.30 power maps.
// Every scanner CUT triple {alarm,Pcut,SUM40} and final grouping record
// is checked against independently constructed S04-C05 integer oracles.
// No historical CPI is loaded or run.
module tb_cfar_grouping_subsystem;
 reg clk=0;
 always #5 clk=~clk;
 reg rst=1, start=0, map_valid=0, out_ready=0, cut_pause=0;
 reg [45:0] map_power=0;
 wire map_ready;
 wire out_valid;
 wire [9:0] out_record_id;
 wire [6:0] out_range;
 wire [4:0] out_bin;
 wire signed [5:0] out_signed_bin;
 wire [45:0] out_peak_power;
 wire [11:0] out_cluster_cells;
 wire out_tie_flag;
 wire [11:0] out_equal_power_cells;
 wire busy,done,scanner_done,overflow_sticky,protocol_error,frame_invalid;

 reg cap_start=0,cap_map_valid=0;
 reg [45:0] cap_map_power=0;
 wire cap_map_ready,cap_out_valid,cap_busy,cap_done,cap_scanner_done;
 wire cap_overflow,cap_protocol,cap_invalid;

 reg [45:0] map_words [0:20479];
 reg [98:0] cut_gold [0:13909];
 reg [88:0] record_gold [0:255];
 reg [11:0] record_count [0:4];

 reg [98:0] observed_cut;
 reg [110:0] held_cut;
 reg hold_cut_active=0;
 reg [88:0] observed_record;
 reg [88:0] held_record;
 integer frame_id=-1;
 integer cut_count=0;
 integer scanner_done_count=0;
 integer group_done_count=0;
 integer stalled_cut_cycles=0;
 integer stalled_output_cycles=0;
 integer record_total=0;
 integer offset=0;
 integer i,j,k,idx;

 cfar_grouping_subsystem dut (
   .clk(clk),.rst(rst),.start(start),
   .map_valid(map_valid),.cut_pause(cut_pause),.map_ready(map_ready),.map_power(map_power),
   .out_valid(out_valid),.out_ready(out_ready),
   .out_record_id(out_record_id),.out_range(out_range),.out_bin(out_bin),
   .out_signed_bin(out_signed_bin),.out_peak_power(out_peak_power),
   .out_cluster_cells(out_cluster_cells),.out_tie_flag(out_tie_flag),
   .out_equal_power_cells(out_equal_power_cells),
   .busy(busy),.done(done),.scanner_done(scanner_done),
   .overflow_sticky(overflow_sticky),.protocol_error(protocol_error),
   .frame_invalid(frame_invalid)
 );

 // Reduced label capacity exercises explicit fatal overflow propagation
 // through the SAME connected scanner/grouping RTL, not silent truncation.
 cfar_grouping_subsystem #(.GROUP_MAX_LABELS(1)) cap (
   .clk(clk),.rst(rst),.start(cap_start),
   .map_valid(cap_map_valid),.cut_pause(1'b0),.map_ready(cap_map_ready),.map_power(cap_map_power),
   .out_valid(cap_out_valid),.out_ready(1'b1),
   .out_record_id(),.out_range(),.out_bin(),.out_signed_bin(),
   .out_peak_power(),.out_cluster_cells(),.out_tie_flag(),
   .out_equal_power_cells(),.busy(cap_busy),.done(cap_done),
   .scanner_done(cap_scanner_done),.overflow_sticky(cap_overflow),
   .protocol_error(cap_protocol),.frame_invalid(cap_invalid)
 );

 task fail;
   input [8*140-1:0] reason;
   begin
     $display("FAIL connected frame=%0d CUT=%0d reason=%0s",frame_id,cut_count,reason);
     $finish;
   end
 endtask

 // Check every accepted scanner->grouping interface record at the
 // synchronous handshake boundary; preserves the approved 2782 sequence.
 always @(posedge clk) begin
   if (!rst && frame_id>=0 && frame_id<5) begin
     if (dut.cut_valid && !dut.cut_ready) begin
       stalled_cut_cycles=stalled_cut_cycles+1;
       if (hold_cut_active &&
           held_cut !== {dut.cut_range,dut.cut_bin,dut.cut_alarm,
             dut.cut_power,dut.u_scanner.out_sum40})
         fail("scanner output changed while CUT valid and not ready");
       held_cut={dut.cut_range,dut.cut_bin,dut.cut_alarm,
         dut.cut_power,dut.u_scanner.out_sum40};
       hold_cut_active=1;
     end else begin
       if (hold_cut_active && dut.cut_valid && dut.cut_ready &&
           held_cut !== {dut.cut_range,dut.cut_bin,dut.cut_alarm,
             dut.cut_power,dut.u_scanner.out_sum40})
         fail("scanner output changed at delayed CUT handshake");
       hold_cut_active=0;
     end
     if (out_valid && !out_ready)
       stalled_output_cycles=stalled_output_cycles+1;
     if (scanner_done)
       scanner_done_count=scanner_done_count+1;
     if (done)
       group_done_count=group_done_count+1;
     if (dut.cut_valid && dut.cut_ready) begin
       if (cut_count>=2782)
         fail("duplicate CUT beyond valid raster");
       if (dut.cut_range !== (3+cut_count/26) ||
           dut.cut_bin !== (3+cut_count%26))
         fail("incorrect CUT range-major Doppler-minor address");
       observed_cut={dut.cut_alarm,dut.cut_power,dut.u_scanner.out_sum40};
       if (observed_cut !== cut_gold[frame_id*2782+cut_count]) begin
         $display("CUT MISMATCH expected=%025x got=%025x",
           cut_gold[frame_id*2782+cut_count],observed_cut);
         fail("CFAR CUT triple differs from independent oracle");
       end
       cut_count=cut_count+1;
     end
   end
 end

 task begin_frame;
   input integer test_id;
   begin
     @(negedge clk);
     frame_id=test_id;
     cut_count=0;
     scanner_done_count=0;
     group_done_count=0;
     start=1;
     @(negedge clk);
     start=0;
   end
 endtask

 task send_map;
   input integer test_id;
   integer w;
   begin
     for(w=0;w<4096;w=w+1) begin
       @(negedge clk);
       map_valid=0;
       if ((w%257)==0) repeat(2) @(negedge clk);
       map_valid=1;
       map_power=map_words[test_id*4096+w];
       while(!map_ready) @(negedge clk);
       @(posedge clk);
     end
     @(negedge clk);
     map_valid=0;
     map_power=0;
   end
 endtask

 task check_records;
   input integer expected_count;
   integer rec,hold_n;
   begin
     for(rec=0;rec<expected_count;rec=rec+1) begin
       wait(out_valid);
       @(negedge clk);
       observed_record={out_range,out_bin,out_signed_bin,
         out_peak_power,out_cluster_cells,out_tie_flag,out_equal_power_cells};
       if (!out_valid || out_record_id !== rec ||
           observed_record !== record_gold[offset+rec]) begin
         $display("RECORD expected %023x actual %023x id=%0d",
           record_gold[offset+rec],observed_record,out_record_id);
         fail("record differs from independent software oracle");
       end
       held_record=observed_record;
       // Deliberately stall the record; all fields and valid must hold.
       if ((rec%2)==0) begin
         for(hold_n=0;hold_n<4;hold_n=hold_n+1) begin
           @(negedge clk);
           observed_record={out_range,out_bin,out_signed_bin,
             out_peak_power,out_cluster_cells,out_tie_flag,out_equal_power_cells};
           if (!out_valid || out_record_id !== rec || observed_record !== held_record)
             fail("output data changed while valid and not ready");
         end
       end
       out_ready=1;
       @(posedge clk);
       @(negedge clk);
       out_ready=0;
       record_total=record_total+1;
     end
     wait(done);
     // Allow the synchronous done-pulse observer to sample this event.
     @(posedge clk);
     @(negedge clk);
     if(out_valid || busy || overflow_sticky || protocol_error || frame_invalid)
       fail("unexpected end-state error/partial record");
     if(cut_count != 2782 || scanner_done_count != 1)
       fail("CUT loss/duplication or wrong scanner frame boundary");
     if(group_done_count != 1)
       fail("grouping frame completion pulse mismatch");
     $display("PASS integrated_case_%0d: CUTs=%0d clusters=%0d scanner_done=%0d",
         frame_id,cut_count,expected_count,scanner_done_count);
     offset=offset+expected_count;
   end
 endtask

 task run_capacity_overflow;
   integer w;
   begin
     // Case 1 contains four isolated approved CUT detections.
     @(negedge clk); cap_start=1;
     @(negedge clk); cap_start=0;
     for(w=0;w<4096;w=w+1) begin
       @(negedge clk);
       cap_map_valid=1;
       cap_map_power=map_words[4096+w];
       while(!cap_map_ready) @(negedge clk);
       @(posedge clk);
     end
     @(negedge clk); cap_map_valid=0;
     wait(cap_done);
     @(negedge clk);
     if(!cap_overflow || !cap_invalid || cap_out_valid || cap_protocol)
       fail("connected capacity overflow not propagated or silent loss detected");
     $display("PASS integrated_capacity_overflow: sticky overflow and invalid frame; no truncated target list");
     // Explicit system reset is the recovery path after a fatal overflow.
     @(negedge clk); rst=1;
     repeat(3) @(negedge clk);
     if (cap_overflow || cap_invalid || cap_busy || cap_out_valid)
       fail("reset did not clear fatal grouping overflow");
     rst=0;
     $display("PASS integrated_overflow_reset_recovery");
   end
 endtask

 // Apply a real, handshake-safe pause to the CUT stream once in frame 1.
 // Both scanner ready and grouping valid are gated simultaneously.
 initial begin
   wait(frame_id==1);
   wait(dut.cut_valid);
   @(negedge clk); cut_pause=1;
   repeat(8) @(negedge clk);
   cut_pause=0;
 end

 initial begin
   $readmemh("vectors/cfar_grouping/map.mem",map_words);
   $readmemh("vectors/cfar_grouping/cut.mem",cut_gold);
   $readmemh("vectors/cfar_grouping/expected.mem",record_gold);
   $readmemh("vectors/cfar_grouping/counts.mem",record_count);
   repeat(5) @(negedge clk);
   rst=0;
   for(i=0;i<5;i=i+1) begin
     begin_frame(i);
     send_map(i);
     check_records(record_count[i]);
   end
   if (record_total!=14 || offset!=14)
     fail("integrated golden output count mismatch");
   if (stalled_cut_cycles==0 || stalled_output_cycles==0)
     fail("CUT or record back-pressure was not exercised");
   $display("HANDSHAKE cut_stall_cycles=%0d record_stall_cycles=%0d",
     stalled_cut_cycles,stalled_output_cycles);
   frame_id=5;  // stop monitoring the nominal DUT
   run_capacity_overflow;
   $display("PASS tb_cfar_grouping_subsystem: 5 maps, 20480 power words, 13910 CUTs, 14 C05 records, independent CFAR+union-find oracle, held output, 8-connect late unions, equality boundary, frame replay, explicit overflow");
   $display("INTEGRATED RTL AND INDEPENDENT ORACLE PASS");
   $finish;
 end

 initial begin
   #100000000;
   $display("FAIL tb_cfar_grouping_subsystem TIMEOUT frame=%0d CUT=%0d scanner_state=%0d group_state=%0d",
      frame_id,cut_count,dut.u_scanner.state,dut.u_grouping.state);
   $finish;
 end
endmodule

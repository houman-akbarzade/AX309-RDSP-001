// Independent RTL checker: 11 synthetic full 2782-CUT frames.
// The expected records are generated from the UNMODIFIED approved C05
// native BFS and cross-checked with a distinct union-find implementation.
// No previous CPI is processed or reused.
module tb_grouping_8conn;
    reg clk=0;
    always #5 clk=~clk;
    reg rst=1;
    reg start=0;
    reg in_valid=0;
    wire in_ready;
    reg [6:0] in_range=7'd0;
    reg [4:0] in_bin=5'd0;
    reg [45:0] in_power=46'd0;
    reg in_alarm=0;
    wire out_valid;
    reg out_ready=0;
    wire [9:0] out_record_id;
    wire [6:0] out_range;
    wire [4:0] out_bin;
    wire signed [5:0] out_signed_bin;
    wire [45:0] out_peak_power;
    wire [11:0] out_cluster_cells;
    wire out_tie_flag;
    wire [11:0] out_equal_power_cells;
    wire busy,done,overflow_sticky,protocol_error,frame_invalid;

    reg cap_start=0,cap_valid=0,cap_alarm=0;
    wire cap_ready,cap_out_valid,cap_busy,cap_done,cap_overflow,cap_protocol,cap_invalid;
    reg [6:0] cap_range=7'd0;
    reg [4:0] cap_bin=5'd0;
    reg [45:0] cap_power=46'd0;

    reg [46:0] frame_words [0:30601];
    reg [88:0] golden [0:2047];
    reg [11:0] counts [0:10];
    reg [88:0] actual;
    reg [88:0] held;
    integer testcase,index,offset,expected_offset,record_idx,cycles;
    integer total_seen;
    integer i;

    grouping_8conn uut(
        .clk(clk),.rst(rst),.start(start),
        .in_valid(in_valid),.in_ready(in_ready),
        .in_range(in_range),.in_bin(in_bin),
        .in_power(in_power),.in_alarm(in_alarm),
        .out_valid(out_valid),.out_ready(out_ready),
        .out_record_id(out_record_id),
        .out_range(out_range),.out_bin(out_bin),
        .out_signed_bin(out_signed_bin),
        .out_peak_power(out_peak_power),
        .out_cluster_cells(out_cluster_cells),
        .out_tie_flag(out_tie_flag),
        .out_equal_power_cells(out_equal_power_cells),
        .busy(busy),.done(done),.overflow_sticky(overflow_sticky),
        .protocol_error(protocol_error),.frame_invalid(frame_invalid)
    );

    // Reduced internal allocation capacity for explicit overflow test.
    // It is not a claim about the approved REQ-LIST-01 list limit.
    grouping_8conn #(.MAX_LABELS(1)) cap(
        .clk(clk),.rst(rst),.start(cap_start),
        .in_valid(cap_valid),.in_ready(cap_ready),
        .in_range(cap_range),.in_bin(cap_bin),
        .in_power(cap_power),.in_alarm(cap_alarm),
        .out_valid(cap_out_valid),.out_ready(1'b1),
        .out_record_id(),.out_range(),.out_bin(),
        .out_signed_bin(),.out_peak_power(),.out_cluster_cells(),
        .out_tie_flag(),.out_equal_power_cells(),
        .busy(cap_busy),.done(cap_done),.overflow_sticky(cap_overflow),
        .protocol_error(cap_protocol),.frame_invalid(cap_invalid)
    );

    task fail;
        input [8*120-1:0] message;
        begin
            $display("FAIL tb_grouping_8conn case=%0d idx=%0d: %0s",testcase,index,message);
            $finish;
        end
    endtask

    task send_start;
        begin
            @(negedge clk); start=1;
            @(negedge clk); start=0;
        end
    endtask

    task send_frame;
        input integer test_id;
        integer k;
        begin
            for(k=0;k<2782;k=k+1) begin
                @(negedge clk);
                in_valid=0;
                if (k%211 == 0) repeat(3) @(negedge clk);
                while (!in_ready) @(negedge clk);
                index=k;
                in_range=7'd3+(k/26);
                in_bin=5'd3+(k%26);
                in_alarm=frame_words[test_id*2782+k][46];
                in_power=frame_words[test_id*2782+k][45:0];
                in_valid=1;
                @(posedge clk);
            end
            @(negedge clk);
            in_valid=0;
        end
    endtask

    task check_output_frame;
        input integer expected_count;
        integer k,j;
        begin
            for(k=0;k<expected_count;k=k+1) begin
                wait(out_valid);
                @(negedge clk);
                index=k;
                if (!out_valid)
                    fail("output valid disappeared before handshake");
                actual={out_range,out_bin,out_signed_bin,
                        out_peak_power,out_cluster_cells,
                        out_tie_flag,out_equal_power_cells};
                if (out_record_id !== k || actual !== golden[expected_offset+k]) begin
                    $display("FAIL record case=%0d idx=%0d id=%0d actual=%023x expected=%023x",
                             testcase,k,out_record_id,actual,golden[expected_offset+k]);
                    $finish;
                end
                // Check stable metadata and data while downstream not ready.
                held=actual;
                if ((k%7)==0) begin
                    for(j=0;j<4;j=j+1) begin
                        @(negedge clk);
                        actual={out_range,out_bin,out_signed_bin,
                                out_peak_power,out_cluster_cells,
                                out_tie_flag,out_equal_power_cells};
                        if (!out_valid || held!==actual || out_record_id!==k)
                            fail("back-pressure changed output");
                    end
                end
                out_ready=1;
                @(posedge clk);
                @(negedge clk);
                out_ready=0;
                total_seen=total_seen+1;
            end
            wait(done);
            @(negedge clk);
            if (out_valid || busy || overflow_sticky || protocol_error || frame_invalid)
                fail("normal frame completion or telemetry failed");
        end
    endtask

    initial begin
        $readmemh("vectors/grouping/input.mem",frame_words);
        $readmemh("vectors/grouping/expected.mem",golden);
        $readmemh("vectors/grouping/counts.mem",counts);
        total_seen=0;
        repeat(5) @(negedge clk);
        rst=0;
        expected_offset=0;
        for(testcase=0;testcase<11;testcase=testcase+1) begin
            send_start;
            send_frame(testcase);
            check_output_frame(counts[testcase]);
            $display("PASS grouping_case_%0d: records=%0d",testcase,counts[testcase]);
            expected_offset=expected_offset+counts[testcase];
        end
        if (total_seen!=887 || expected_offset!=887)
            fail("expected oracle record count mismatch");

        // Test capacity overflow: label 1 is created at (3,3), and
        // isolated label 2 at (3,28) must ABORT, never silently truncate.
        @(negedge clk);cap_start=1;
        @(negedge clk);cap_start=0;
        for(i=0;i<26;i=i+1) begin
            @(negedge clk);
            cap_valid=0;
            while(!cap_ready) @(negedge clk);
            cap_range=7'd3;
            cap_bin=5'd3+i;
            cap_power=46'd500+i;
            cap_alarm=(i==0 || i==25);
            cap_valid=1;
            @(posedge clk);
        end
        @(negedge clk);cap_valid=0;
        wait(cap_done);
        @(negedge clk);
        if (!cap_overflow || !cap_invalid || cap_busy || cap_out_valid)
            fail("capacity overflow was not explicitly aborted");

        // Fault state must be recoverable with a new start and reject
        // a wrong coordinate without inventing an output record.
        @(negedge clk);cap_start=1;
        @(negedge clk);cap_start=0;
        wait(cap_ready);
        @(negedge clk);
        cap_range=7'd3;cap_bin=5'd4;cap_alarm=0;cap_valid=1;
        @(posedge clk);
        @(negedge clk);cap_valid=0;
        if(!cap_protocol || !cap_invalid || cap_out_valid || cap_busy)
            fail("ordered input violation not detected");

        $display("PASS tb_grouping_8conn: 11 cases, 30602 CUTs, 887 records, independent C05 oracle+union-find, 702 clusters, late merges, exact ties, back-pressure, overflow and protocol guard");
        $finish;
    end

    initial begin
        #30000000;
        $display("FAIL tb_grouping_8conn TIMEOUT state=%0d case=%0d idx=%0d roots=%0d labels=%0d emitted=%0d",
           uut.state,testcase,index,uut.root_count,uut.label_count,uut.emitted_count);
        $finish;
    end
endmodule

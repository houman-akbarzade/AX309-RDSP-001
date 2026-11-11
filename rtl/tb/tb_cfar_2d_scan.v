// Smoke test for 2-D CA-CFAR map loading, 7x7/3x3 geometry,
// exact 40-cell sum, synchronous memory read and output back-pressure.
module tb_cfar_2d_scan;
    reg clk=0;
    always #5 clk=~clk;

    reg rst=1;
    reg start=0;
    reg map_valid=0;
    reg [45:0] map_power=0;
    wire map_ready;

    wire out_valid;
    reg out_ready=0;
    wire [6:0] out_range;
    wire [4:0] out_bin;
    wire [45:0] out_power;
    wire [51:0] out_sum40;
    wire out_alarm;
    wire out_equality;
    wire busy,done,overflow_event,overflow_sticky,protocol_error;

    reg [45:0] frame [0:4095];
    integer i,r,b;
    integer held_cycles;
    integer cut_index;
    integer expected_range;
    integer expected_bin;

    cfar_2d_scan dut(
        .clk(clk),.rst(rst),.start(start),
        .map_valid(map_valid),.map_ready(map_ready),.map_power(map_power),
        .out_valid(out_valid),.out_ready(out_ready),
        .out_range(out_range),.out_bin(out_bin),
        .out_power(out_power),.out_sum40(out_sum40),
        .out_alarm(out_alarm),.out_equality(out_equality),
        .busy(busy),.done(done),
        .overflow_event(overflow_event),.overflow_sticky(overflow_sticky),
        .protocol_error(protocol_error)
    );

    initial begin
        for(i=0;i<4096;i=i+1)
            frame[i]=46'd0;

        // Forty training cells are exactly 65536 each.
        // Guard cells are deliberately large and must not enter SUM40.
        for(r=0;r<=6;r=r+1) begin
            for(b=0;b<=6;b=b+1) begin
                if ((r>=2 && r<=4) && (b>=2 && b<=4))
                    frame[r*32+b]=46'd100000000;
                else
                    frame[r*32+b]=46'd65536;
            end
        end
        // CUT (3,3) is the centre of the excluded 3x3 guard region.
        frame[3*32+3]=46'd490007;

        repeat(4) @(negedge clk);
        rst=0;
        @(negedge clk); start=1;
        @(negedge clk); start=0;

        for(i=0;i<4096;i=i+1) begin
            @(negedge clk);
            map_valid=1;
            map_power=frame[i];
            @(posedge clk);
        end
        @(negedge clk);
        map_valid=0;
        map_power=0;

        wait(out_valid);
        #1; // Allow the combinational strict-CFAR comparator to settle after the final SUM40 register update.
        if (out_range!==7'd3 || out_bin!==5'd3 ||
            out_power!==46'd490007 ||
            out_sum40!==52'd2621440 ||
            !out_equality || out_alarm ||
            overflow_sticky || protocol_error) begin
            $display("FAIL CFAR scan r=%0d b=%0d p=%0d sum=%0d eq=%b alarm=%b ov=%b err=%b",
                out_range,out_bin,out_power,out_sum40,out_equality,out_alarm,
                overflow_sticky,protocol_error);
            $finish;
        end

        // The output record must remain stable under back-pressure.
        for(held_cycles=0;held_cycles<5;held_cycles=held_cycles+1) begin
            @(negedge clk);
            if (!out_valid || out_range!==7'd3 || out_bin!==5'd3 ||
                out_power!==46'd490007 || out_sum40!==52'd2621440 ||
                !out_equality || out_alarm) begin
                $display("FAIL CFAR output stability under back-pressure");
                $finish;
            end
        end

        @(negedge clk); out_ready=1;
        @(posedge clk);
        @(negedge clk); out_ready=0;
        if (out_valid || done) begin
            $display("FAIL CFAR output handshake");
            $finish;
        end

        // Drain the rest of the frame and verify all valid CUT coordinates.
        for(cut_index=1;cut_index<2782;cut_index=cut_index+1) begin
            wait(out_valid);
            @(negedge clk);
            expected_range=3+(cut_index/26);
            expected_bin=3+(cut_index%26);
            if (out_range!==expected_range[6:0] || out_bin!==expected_bin[4:0]) begin
                $display("FAIL CFAR scan order index=%0d got=(%0d,%0d) expected=(%0d,%0d)",
                    cut_index,out_range,out_bin,expected_range,expected_bin);
                $finish;
            end
            out_ready=1;
            @(posedge clk);
            @(negedge clk); out_ready=0;
        end

        if (out_valid || !done || busy || overflow_sticky || protocol_error) begin
            $display("FAIL CFAR frame completion done=%b busy=%b overflow=%b protocol=%b",
                done,busy,overflow_sticky,protocol_error);
            $finish;
        end

        $display("PASS tb_cfar_2d_scan: 4096 map writes, 2782 ordered CUTs, 40 training cells, guard exclusion, exact equality, output back-pressure");
        $finish;
    end

    initial begin
        #5000000;
        $display("FAIL timeout");
        $finish;
    end
endmodule

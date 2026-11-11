// Deterministic FFT32 bit-true smoke: zero frame and unit impulse.
module tb_fft32;
    reg clk=0; always #5 clk=~clk;
    reg rst=1, start=0, in_valid=0, out_ready=0;
    reg [6:0] range_in=7'd0;
    reg signed [22:0] in_re=23'sd0, in_im=23'sd0;
    wire in_ready, out_valid, out_last, busy, done;
    wire signed [24:0] out_re, out_im;
    wire [6:0] range_out;
    wire overflow_event, overflow_sticky, protocol_error;
    wire [2:0] overflow_stage;
    wire [3:0] overflow_butterfly, overflow_mask;
    wire signed [63:0] ppr, ppi, pmr, pmi;
    integer i, count;

    fft32_dit dut(
        .clk(clk),.rst(rst),.start(start),.range_in(range_in),
        .in_valid(in_valid),.in_ready(in_ready),.in_re(in_re),.in_im(in_im),
        .out_valid(out_valid),.out_ready(out_ready),.out_last(out_last),
        .out_re(out_re),.out_im(out_im),.range_out(range_out),
        .busy(busy),.done(done),.overflow_event(overflow_event),
        .overflow_sticky(overflow_sticky),.overflow_stage(overflow_stage),
        .overflow_butterfly(overflow_butterfly),.overflow_mask(overflow_mask),
        .overflow_pre_plus_re(ppr),.overflow_pre_plus_im(ppi),
        .overflow_pre_minus_re(pmr),.overflow_pre_minus_im(pmi),
        .protocol_error(protocol_error)
    );

    task send_frame;
        input integer impulse;
        begin
            @(negedge clk); start=1; range_in=7'd23;
            @(negedge clk); start=0;
            for(i=0;i<32;i=i+1) begin
                while(!in_ready) @(negedge clk);
                in_valid=1;
                in_re=(impulse && i==0) ? 23'sd32768 : 23'sd0;
                in_im=23'sd0;
                @(negedge clk);
            end
            in_valid=0; in_re=0;
        end
    endtask

    task collect_frame;
        input integer expected_re;
        begin
            count=0; out_ready=0;
            @(negedge clk);
            if(!out_valid || out_re !== expected_re || out_im !== 25'sd0) begin
                $display("FAIL FFT bin=0 re=%0d im=%0d expected_re=%0d",out_re,out_im,expected_re);
                $finish;
            end
            if(range_out !== 7'd23) begin $display("FAIL FFT range tag"); $finish; end
            count=1; out_ready=1;
            while(count<32) begin
                @(negedge clk);
                if(out_valid) begin
                    if(out_re !== expected_re || out_im !== 25'sd0) begin
                        $display("FAIL FFT bin=%0d re=%0d im=%0d expected_re=%0d",
                                 count,out_re,out_im,expected_re);
                        $finish;
                    end
                    if(range_out !== 7'd23) begin
                        $display("FAIL FFT range tag"); $finish;
                    end
                    count=count+1;
                end
            end
            out_ready=0;
            if(overflow_sticky || protocol_error) begin
                $display("FAIL FFT unexpected overflow/protocol error");
                $finish;
            end
        end
    endtask

    initial begin
        repeat(4) @(negedge clk); rst=0;
        send_frame(0);
        wait(out_valid);
        collect_frame(25'sd0);
        wait(!busy);
        send_frame(1);
        wait(out_valid);
        collect_frame(25'sd4096);
        wait(!busy);
        $display("PASS tb_fft32: zero frame and impulse; 64 bins checked");
        $finish;
    end
endmodule

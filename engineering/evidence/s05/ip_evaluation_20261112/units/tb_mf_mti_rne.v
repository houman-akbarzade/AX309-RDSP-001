module tb_mf_mti_rne;
    reg clk=0; always #5 clk=~clk;
    reg rst=1,start=0,tap_valid=0;
    reg [6:0] range_in=0;
    reg [3:0] tap_index=0;
    reg signed [15:0] sample_re=0,sample_im=0;
    wire busy,done;
    wire [6:0] range_out;
    wire signed [21:0] result_re,result_im;
    wire saturation_event;
    wire [1:0] saturation_mask;
    wire signed [63:0] prelimit_re,prelimit_im;
    wire protocol_error;

    reg signed [7:0] rne_in=0;
    wire signed [4:0] rne_out;
    wire rne_overflow;
    wire signed [63:0] rne_pre;
    rne_sat_signed #(.IN_W(8),.OUT_W(5)) u_rne(
        .in_value(rne_in),.shift_amt(6'd1),.out_value(rne_out),
        .overflow(rne_overflow),.prelimit(rne_pre)
    );

    reg mti_valid=0;
    reg signed [21:0] nre=0,nim=0,pre=0,pim=0;
    reg [6:0] mti_range=0;
    reg [4:0] mti_pulse=0;
    wire mti_out_valid;
    wire signed [22:0] mti_re,mti_im;
    wire [6:0] mti_range_out;
    wire [4:0] mti_pulse_out;

    mf16_serial_mac u_mf(
        .clk(clk),.rst(rst),.start(start),.range_in(range_in),
        .tap_valid(tap_valid),.tap_index(tap_index),
        .sample_re(sample_re),.sample_im(sample_im),
        .busy(busy),.done(done),.range_out(range_out),
        .result_re(result_re),.result_im(result_im),
        .saturation_event(saturation_event),.saturation_mask(saturation_mask),
        .prelimit_re(prelimit_re),.prelimit_im(prelimit_im),
        .protocol_error(protocol_error)
    );
    mti2_diff u_mti(
        .clk(clk),.rst(rst),.in_valid(mti_valid),
        .pulse_next_re(nre),.pulse_next_im(nim),
        .pulse_prev_re(pre),.pulse_prev_im(pim),
        .range_in(mti_range),.pulse_in(mti_pulse),
        .out_valid(mti_out_valid),.diff_re(mti_re),.diff_im(mti_im),
        .range_out(mti_range_out),.pulse_out(mti_pulse_out)
    );

    integer i,mf_wait;
    task run_mf;
        input signed [15:0] first_re;
        input signed [15:0] first_im;
        input signed [21:0] expected_re;
        input signed [21:0] expected_im;
        begin
            @(negedge clk); start=1; range_in=7'd17;
            @(negedge clk); start=0;
            for(i=0;i<16;i=i+1) begin
                tap_index=i[3:0];
                sample_re=(i==0)?first_re:16'sd0;
                sample_im=(i==0)?first_im:16'sd0;
                tap_valid=1;
                @(negedge clk);
            end
            tap_valid=0; sample_re=0; sample_im=0;
            mf_wait=0;
            while(!done && mf_wait<4)begin @(negedge clk);mf_wait=mf_wait+1;end
            if(!done || result_re!==expected_re || result_im!==expected_im ||
               saturation_event || protocol_error || range_out!==7'd17) begin
                $display("FAIL MF got=(%0d,%0d) expected=(%0d,%0d) done=%b sat=%b err=%b",
                    result_re,result_im,expected_re,expected_im,done,saturation_event,protocol_error);
                $finish;
            end
        end
    endtask

    initial begin
        repeat(3) @(negedge clk); rst=0;
        rne_in=8'sd5; #1; if(rne_out!==5'sd2) begin $display("FAIL RNE +2.5"); $finish; end
        rne_in=8'sd7; #1; if(rne_out!==5'sd4) begin $display("FAIL RNE +3.5"); $finish; end
        rne_in=-8'sd5; #1; if(rne_out!==-5'sd2) begin $display("FAIL RNE -2.5"); $finish; end
        rne_in=-8'sd7; #1; if(rne_out!==-5'sd4) begin $display("FAIL RNE -3.5"); $finish; end
        rne_in=8'sd31; #1; if(rne_out!==5'sd15 || !rne_overflow) begin $display("FAIL RNE positive saturation"); $finish; end
        rne_in=-8'sd32; #1; if(rne_out!==-5'sd16 || rne_overflow) begin $display("FAIL RNE negative endpoint"); $finish; end

        run_mf(-16'sd32768,16'sd0,-22'sd30425,-22'sd12167);
        run_mf(16'sd0,-16'sd32768,22'sd12167,-22'sd30425);

        @(negedge clk);
        mti_valid=1; nre=22'sd2097151; pre=-22'sd2097152;
        nim=-22'sd2097152; pim=22'sd2097151;
        mti_range=7'd9; mti_pulse=5'd12;
        @(negedge clk); mti_valid=0;
        if(!mti_out_valid || mti_re!==23'sd4194303 ||
           mti_im!==-23'sd4194303 || mti_range_out!==7'd9 ||
           mti_pulse_out!==5'd12) begin
            $display("FAIL MTI exact signed difference"); $finish;
        end
        $display("PASS tb_mf_mti_rne: RNE ties, signed endpoints, MF complex MAC, MTI");
        $finish;
    end
endmodule

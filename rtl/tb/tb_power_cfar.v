module tb_power_cfar;
    reg clk=0; always #5 clk=~clk;
    reg rst=1, in_valid=0;
    reg signed [24:0] in_re=0,in_im=0;
    reg [6:0] range_in=0;
    reg [4:0] bin_in=0;
    wire out_valid;
    wire [45:0] power_out;
    wire [6:0] range_out;
    wire [4:0] bin_out;
    wire saturation_event, overflow_sticky;
    wire signed [63:0] prelimit;

    reg start=0, training_valid=0;
    reg [45:0] training_power=0;
    wire busy, sum_done, sum_overflow, sum_protocol_error;
    wire [51:0] sum40;
    reg [45:0] p_cut=0;
    reg [51:0] cmp_sum=0;
    wire alarm,equality;
    wire [71:0] lhs,rhs;
    integer i;

    power_q25_u46 u_power(
        .clk(clk),.rst(rst),.in_valid(in_valid),
        .in_re(in_re),.in_im(in_im),.range_in(range_in),.bin_in(bin_in),
        .out_valid(out_valid),.power_out(power_out),.range_out(range_out),
        .bin_out(bin_out),.saturation_event(saturation_event),
        .prelimit(prelimit),.overflow_sticky(overflow_sticky)
    );
    cfar_sum40 u_sum(
        .clk(clk),.rst(rst),.start(start),.training_valid(training_valid),
        .training_power(training_power),.busy(busy),.done(sum_done),
        .sum40(sum40),.overflow_event(sum_overflow),
        .protocol_error(sum_protocol_error)
    );
    cfar_compare u_cmp(
        .p_cut(p_cut),.sum40(cmp_sum),.alarm(alarm),
        .equality(equality),.lhs(lhs),.rhs(rhs)
    );

    task send_power;
        input signed [24:0] re;
        input signed [24:0] im;
        input [45:0] expected;
        input expected_sat;
        begin
            @(negedge clk); in_re=re; in_im=im; in_valid=1;
            @(negedge clk); in_valid=0;
            if(!out_valid || power_out!==expected || saturation_event!==expected_sat) begin
                $display("FAIL power re=%0d im=%0d got=%0d sat=%b expected=%0d/%b",
                         re,im,power_out,saturation_event,expected,expected_sat);
                $finish;
            end
        end
    endtask

    initial begin
        repeat(3) @(negedge clk); rst=0;
        send_power(25'sd32768,25'sd0,46'd1073741824,1'b0);
        send_power(-25'sd32768,25'sd0,46'd1073741824,1'b0);
        send_power(-25'sd16777216,25'sd0,{46{1'b1}},1'b1);

        @(negedge clk); start=1;
        @(negedge clk); start=0;
        for(i=0;i<40;i=i+1) begin
            training_valid=1; training_power=46'd1;
            @(negedge clk);
        end
        training_valid=0;
        if(!sum_done || sum40!==52'd40 || sum_overflow || sum_protocol_error) begin
            $display("FAIL SUM40 basic"); $finish;
        end

        // Maximum possible 40-cell sum fits U52.30 without overflow.
        @(negedge clk); start=1;
        @(negedge clk); start=0;
        for(i=0;i<40;i=i+1) begin
            training_valid=1; training_power={46{1'b1}};
            @(negedge clk);
        end
        training_valid=0;
        if(!sum_done || sum40!==52'd2814749767106520 || sum_overflow || sum_protocol_error) begin
            $display("FAIL SUM40 maximum"); $finish;
        end

        // Exact equality: strict comparison must not alarm.
        p_cut=46'd490007; cmp_sum=52'd2621440; #1;
        if(!equality || alarm) begin $display("FAIL CFAR equality"); $finish; end
        p_cut=46'd490008; #1;
        if(equality || !alarm) begin $display("FAIL CFAR above"); $finish; end
        p_cut=46'd490006; #1;
        if(equality || alarm) begin $display("FAIL CFAR below"); $finish; end

        $display("PASS tb_power_cfar: power saturation, SUM40, strict CFAR boundary");
        $finish;
    end
endmodule

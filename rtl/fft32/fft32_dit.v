// Sequential 32-point forward DIT FFT.
// Input samples are presented in bit-reversed order; output bins are natural order.
// C02 shifts [0,1,0,1,1], one butterfly/cycle, exact full-width arithmetic.
module fft32_dit (
    input wire clk,
    input wire rst,
    input wire start,
    input wire [6:0] range_in,
    input wire in_valid,
    output wire in_ready,
    input wire signed [22:0] in_re,
    input wire signed [22:0] in_im,
    output wire out_valid,
    input wire out_ready,
    output wire out_last,
    output wire signed [24:0] out_re,
    output wire signed [24:0] out_im,
    output wire [6:0] range_out,
    output reg busy,
    output reg done,
    output reg overflow_event,
    output reg overflow_sticky,
    output reg [2:0] overflow_stage,
    output reg [3:0] overflow_butterfly,
    output reg [3:0] overflow_mask,
    output reg signed [63:0] overflow_pre_plus_re,
    output reg signed [63:0] overflow_pre_plus_im,
    output reg signed [63:0] overflow_pre_minus_re,
    output reg signed [63:0] overflow_pre_minus_im,
    output reg protocol_error
);
    localparam ST_IDLE=2'd0, ST_LOAD=2'd1, ST_CALC=2'd2, ST_OUTPUT=2'd3;
    reg [1:0] state;
    reg signed [24:0] mem_re [0:31];
    reg signed [24:0] mem_im [0:31];
    reg [4:0] load_index;
    reg [3:0] butterfly_index;
    reg [2:0] stage;
    reg [4:0] output_index;
    reg [6:0] range_tag;

    reg [4:0] half_span;
    reg [4:0] group_index;
    reg [4:0] j_index;
    reg [4:0] addr_a;
    reg [4:0] addr_b;
    reg stage_shift;
    reg [5:0] shift_amt;

    wire signed [15:0] tw_re;
    wire signed [15:0] tw_im;
    wire signed [24:0] plus_re, plus_im, minus_re, minus_im;
    wire [3:0] sat_mask;
    wire signed [63:0] pre_pr, pre_pi, pre_mr, pre_mi;

    assign in_ready = (state == ST_LOAD);
    assign out_valid = (state == ST_OUTPUT);
    assign out_last = (state == ST_OUTPUT) && (output_index == 5'd31);
    assign out_re = mem_re[output_index];
    assign out_im = mem_im[output_index];
    assign range_out = range_tag;

    always @* begin
        half_span = 5'd1 << (stage-1'b1);
        j_index = {1'b0,butterfly_index} & (half_span-5'd1);
        group_index = {1'b0,butterfly_index} >> (stage-1'b1);
        addr_a = (group_index << stage) + j_index;
        addr_b = addr_a + half_span;
        stage_shift = (stage==3'd2) || (stage==3'd4) || (stage==3'd5);
        shift_amt = 6'd15 + stage_shift;
    end

    fft32_twiddle_rom u_twiddle (
        .stage(stage), .index(j_index[3:0]), .tw_re(tw_re), .tw_im(tw_im)
    );

    fft32_butterfly u_butterfly (
        .u_re(mem_re[addr_a]), .u_im(mem_im[addr_a]),
        .v_re(mem_re[addr_b]), .v_im(mem_im[addr_b]),
        .tw_re(tw_re), .tw_im(tw_im), .shift_amt(shift_amt),
        .plus_re(plus_re), .plus_im(plus_im),
        .minus_re(minus_re), .minus_im(minus_im),
        .saturation_mask(sat_mask),
        .pre_plus_re(pre_pr), .pre_plus_im(pre_pi),
        .pre_minus_re(pre_mr), .pre_minus_im(pre_mi)
    );

    integer i;
    always @(posedge clk) begin
        if (rst) begin
            state <= ST_IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            load_index <= 5'd0;
            butterfly_index <= 4'd0;
            stage <= 3'd1;
            output_index <= 5'd0;
            range_tag <= 7'd0;
            overflow_event <= 1'b0;
            overflow_sticky <= 1'b0;
            overflow_stage <= 3'd0;
            overflow_butterfly <= 4'd0;
            overflow_mask <= 4'd0;
            overflow_pre_plus_re <= 64'sd0;
            overflow_pre_plus_im <= 64'sd0;
            overflow_pre_minus_re <= 64'sd0;
            overflow_pre_minus_im <= 64'sd0;
            protocol_error <= 1'b0;
            for (i=0;i<32;i=i+1) begin
                mem_re[i] <= 25'sd0;
                mem_im[i] <= 25'sd0;
            end
        end else begin
            done <= 1'b0;
            overflow_event <= 1'b0;

            if (start) begin
                if (state != ST_IDLE) begin
                    protocol_error <= 1'b1;
                end else begin
                    state <= ST_LOAD;
                    busy <= 1'b1;
                    load_index <= 5'd0;
                    range_tag <= range_in;
                    overflow_sticky <= 1'b0;
                end
            end

            if (in_valid && !in_ready)
                protocol_error <= 1'b1;

            case (state)
                ST_LOAD: begin
                    if (in_valid) begin
                        mem_re[load_index] <= {{2{in_re[22]}},in_re};
                        mem_im[load_index] <= {{2{in_im[22]}},in_im};
                        if (load_index == 5'd31) begin
                            stage <= 3'd1;
                            butterfly_index <= 4'd0;
                            state <= ST_CALC;
                        end else begin
                            load_index <= load_index + 5'd1;
                        end
                    end
                end

                ST_CALC: begin
                    mem_re[addr_a] <= plus_re;
                    mem_im[addr_a] <= plus_im;
                    mem_re[addr_b] <= minus_re;
                    mem_im[addr_b] <= minus_im;
                    if (sat_mask != 4'b0000) begin
                        overflow_event <= 1'b1;
                        overflow_sticky <= 1'b1;
                        overflow_stage <= stage;
                        overflow_butterfly <= butterfly_index;
                        overflow_mask <= sat_mask;
                        overflow_pre_plus_re <= pre_pr;
                        overflow_pre_plus_im <= pre_pi;
                        overflow_pre_minus_re <= pre_mr;
                        overflow_pre_minus_im <= pre_mi;
                    end
                    if (butterfly_index == 4'd15) begin
                        butterfly_index <= 4'd0;
                        if (stage == 3'd5) begin
                            output_index <= 5'd0;
                            state <= ST_OUTPUT;
                        end else begin
                            stage <= stage + 3'd1;
                        end
                    end else begin
                        butterfly_index <= butterfly_index + 4'd1;
                    end
                end

                ST_OUTPUT: begin
                    if (out_valid && out_ready) begin
                        if (output_index == 5'd31) begin
                            state <= ST_IDLE;
                            busy <= 1'b0;
                            done <= 1'b1;
                        end else begin
                            output_index <= output_index + 5'd1;
                        end
                    end
                end

                default: begin
                    busy <= 1'b0;
                end
            endcase
        end
    end
endmodule

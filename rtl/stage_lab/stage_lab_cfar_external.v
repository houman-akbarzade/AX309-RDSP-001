// Sequential 2-D CA-CFAR scanner for a stored 128x32 U46.30 map.
// The map is loaded once, then scanned range-major over valid CUTs
// r=3..109, b=3..28. Each CUT uses exactly 40 cells from its 7x7
// window after excluding the central 3x3 guard region.
// The synchronous single-port map read is time-multiplexed between CUT
// capture and training-cell reads so the 4096x46 array can infer BRAM.
module stage_lab_cfar_external (
    input wire [45:0] external_power,
    output wire [11:0] external_addr,
    input wire clk,
    input wire rst,
    input wire start,

    input wire debug_read,
    input wire [11:0] debug_addr,
    output wire [45:0] debug_power,
    input wire map_valid,
    output wire map_ready,
    input wire [45:0] map_power,

    output wire out_valid,
    input wire out_ready,
    output wire [6:0] out_range,
    output wire [4:0] out_bin,
    output wire [45:0] out_power,
    output wire [51:0] out_sum40,
    output wire out_alarm,
    output wire out_equality,

    output reg busy,
    output reg done,
    output reg overflow_event,
    output reg overflow_sticky,
    output reg protocol_error
);
    localparam ST_IDLE      = 3'd0;
    localparam ST_LOAD      = 3'd1;
    localparam ST_SCAN_INIT = 3'd2;
    localparam ST_READ      = 3'd3;
    localparam ST_ACCUM     = 3'd4;
    localparam ST_EMIT      = 3'd5;

    reg [2:0] state;

    reg [11:0] load_addr;

    reg [6:0] cut_range;
    reg [4:0] cut_bin;
    reg [2:0] win_row;
    reg [2:0] win_col;
    reg [5:0] training_count;

    wire [45:0] mem_q=external_power;
    reg [45:0] cut_power;
    reg [51:0] sum40;

    wire [11:0] cut_addr =
        {cut_range,5'b00000} + {7'd0,cut_bin};

    wire [8:0] train_range_ext =
        {2'b00,cut_range} + {6'd0,win_row} - 9'd3;
    wire [7:0] train_bin_ext =
        {3'b000,cut_bin} + {5'd0,win_col} - 8'd3;
    wire [11:0] train_range_12 = {3'b000,train_range_ext};
    wire [11:0] train_addr =
        (train_range_12 << 5) + {4'd0,train_bin_ext};

    wire guard_cell =
        (win_row >= 3'd2) && (win_row <= 3'd4) &&
        (win_col >= 3'd2) && (win_col <= 3'd4);

    wire [52:0] sum_next =
        {1'b0,sum40} + {7'd0,mem_q};

    wire cmp_alarm;
    wire cmp_equality;
    wire ram_read_enable=(state==ST_SCAN_INIT) || (state==ST_READ && !guard_cell) || (state==ST_IDLE && debug_read);
    wire [11:0] ram_read_addr=(state==ST_IDLE)?debug_addr:(state==ST_SCAN_INIT)?cut_addr:train_addr;
    assign external_addr=ram_read_addr;
    assign debug_power=mem_q;
    assign map_ready = (state == ST_LOAD);
    assign out_valid = (state == ST_EMIT);
    assign out_range = cut_range;
    assign out_bin = cut_bin;
    assign out_power = cut_power;
    assign out_sum40 = sum40;
    assign out_alarm = cmp_alarm;
    assign out_equality = cmp_equality;

    cfar_compare u_cfar_compare (
        .p_cut(cut_power),
        .sum40(sum40),
        .alarm(cmp_alarm),
        .equality(cmp_equality),
        .lhs(),
        .rhs()
    );

    always @(posedge clk) begin
        if (rst) begin
            state <= ST_IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            overflow_event <= 1'b0;
            overflow_sticky <= 1'b0;
            protocol_error <= 1'b0;
            load_addr <= 12'd0;
            cut_range <= 7'd3;
            cut_bin <= 5'd3;
            win_row <= 3'd0;
            win_col <= 3'd0;
            training_count <= 6'd0;

            cut_power <= 46'd0;
            sum40 <= 52'd0;
        end else begin
            done <= 1'b0;
            overflow_event <= 1'b0;

            if (start) begin
                if (state != ST_IDLE) begin
                    protocol_error <= 1'b1;
                end else begin
                    state <= ST_SCAN_INIT;
                    cut_range<=7'd3;cut_bin<=5'd3;
                    busy <= 1'b1;
                    load_addr <= 12'd0;
                    overflow_sticky <= 1'b0;
                    protocol_error <= 1'b0;
                end
            end

            case (state)
                ST_IDLE: begin

                end

                ST_LOAD: begin
                    if (map_valid && map_ready) begin
                        // Preloaded shared test memory; no second map RAM.
                        if (load_addr == 12'd4095) begin
                            cut_range <= 7'd3;
                            cut_bin <= 5'd3;
                            state <= ST_SCAN_INIT;
                        end else begin
                            load_addr <= load_addr + 12'd1;
                        end
                    end
                end

                ST_SCAN_INIT: begin
                    win_row <= 3'd0;
                    win_col <= 3'd0;
                    training_count <= 6'd0;
                    sum40 <= 52'd0;

                    state <= ST_READ;
                end

                ST_READ: begin
                    if (guard_cell) begin
                        if (win_col == 3'd6) begin
                            win_col <= 3'd0;
                            win_row <= win_row + 3'd1;
                        end else begin
                            win_col <= win_col + 3'd1;
                        end
                    end else begin
                        if ((win_row == 3'd0) && (win_col == 3'd0))
                            cut_power <= mem_q;

                        state <= ST_ACCUM;
                    end
                end

                ST_ACCUM: begin
                    sum40 <= sum_next[51:0];
                    if (sum_next[52]) begin
                        overflow_event <= 1'b1;
                        overflow_sticky <= 1'b1;
                    end

                    if (training_count == 6'd39) begin
                        state <= ST_EMIT;
                    end else begin
                        training_count <= training_count + 6'd1;
                        if (win_col == 3'd6) begin
                            win_col <= 3'd0;
                            win_row <= win_row + 3'd1;
                        end else begin
                            win_col <= win_col + 3'd1;
                        end
                        state <= ST_READ;
                    end
                end

                ST_EMIT: begin
                    if (out_valid && out_ready) begin
                        if ((cut_range == 7'd109) && (cut_bin == 5'd28)) begin
                            state <= ST_IDLE;
                            busy <= 1'b0;
                            done <= 1'b1;
                        end else begin
                            if (cut_bin == 5'd28) begin
                                cut_bin <= 5'd3;
                                cut_range <= cut_range + 7'd1;
                            end else begin
                                cut_bin <= cut_bin + 5'd1;
                            end
                            state <= ST_SCAN_INIT;
                        end
                    end
                end

                default: begin
                    state <= ST_IDLE;
                    busy <= 1'b0;
                end
            endcase
        end
    end
endmodule

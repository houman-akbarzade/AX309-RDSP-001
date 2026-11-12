// 8-connected streaming grouping of the 2-D CA-CFAR valid CUT raster.
// Approved behavior: nonwrapping 107x26 mask, stored U46.30 power,
// maximum power, signed-bin/range/unsigned-bin exact tie priority,
// and target records sorted by peak range and signed Doppler.
// Local safe-fail policy: on exceeded internal label allocation capacity,
// abort the frame with an explicit sticky overflow flag and NO partial list.
// S02 REQ-LIST-01's external output-list capacity/selection policy is OPEN.
module grouping_8conn #(
    parameter integer MAX_LABELS = 702
)(
    input wire clk,
    input wire rst,
    input wire start,
    input wire in_valid,
    output wire in_ready,
    input wire [6:0] in_range,
    input wire [4:0] in_bin,
    input wire [45:0] in_power,
    input wire in_alarm,

    output wire out_valid,
    input wire out_ready,
    output wire [9:0] out_record_id,
    output wire [6:0] out_range,
    output wire [4:0] out_bin,
    output wire signed [5:0] out_signed_bin,
    output wire [45:0] out_peak_power,
    output wire [11:0] out_cluster_cells,
    output wire out_tie_flag,
    output wire [11:0] out_equal_power_cells,

    output reg busy,
    output reg done,
    output reg overflow_sticky,
    output reg protocol_error,
    output reg frame_invalid
);
    // 702 is the independent-set bound on the 107x26 king graph.
    // The parameter is an internal allocation limit, not a signed-off
    // REQ-LIST-01 target-list capacity or overflow selection rule.
    localparam integer PHYSICAL_LABELS = 702;
    // 10-bit table addresses are physically padded to a power of two.
    // Allocation still stops at the proven 702 valid-grid label bound.
    localparam integer RAM_LAST_ADDRESS = 1023;
    localparam [5:0] S_IDLE       = 6'd0;
    localparam [5:0] S_INIT_ROW   = 6'd1;
    localparam [5:0] S_ACCEPT     = 6'd2;
    localparam [5:0] S_NEIGH      = 6'd3;
    localparam [5:0] S_FIND       = 6'd4;
    localparam [5:0] S_FIND_READ  = 6'd17;
    localparam [5:0] S_UNION_A    = 6'd5;
    localparam [5:0] S_UNION_B    = 6'd6;
    localparam [5:0] S_UNION_WR   = 6'd7;
    localparam [5:0] S_PROCESS    = 6'd8;
    localparam [5:0] S_ADD_READ   = 6'd9;
    localparam [5:0] S_ADD_WRITE  = 6'd10;
    localparam [5:0] S_STEP       = 6'd11;
    localparam [5:0] S_SHIFT_ROW  = 6'd12;
    localparam [5:0] S_SORT_INIT  = 6'd13;
    localparam [5:0] S_SORT_READ  = 6'd14;
    localparam [5:0] S_SORT_CHECK = 6'd15;
    localparam [5:0] S_OUTPUT     = 6'd16;

    // Packed root statistics: {power[45:0],range[6:0],bin[4:0],
    //                         cells[11:0],equal_max_cells[11:0]}.
    localparam integer STAT_W = 82;
    (* ram_style = "block" *) reg [STAT_W-1:0] stat_mem [0:RAM_LAST_ADDRESS];
    reg [STAT_W-1:0] stat_q;
    reg [STAT_W-1:0] stat_a;
    (* ram_style = "block" *) reg [9:0] parent [0:RAM_LAST_ADDRESS];
    reg [9:0] parent_q;
    (* ram_style="distributed" *) reg emitted [0:RAM_LAST_ADDRESS];
    (* ram_style="distributed" *) reg [9:0] prev_row [0:31];
    (* ram_style="distributed" *) reg [9:0] curr_row [0:31];

    reg [5:0] state;
    reg [6:0] expected_range;
    reg [4:0] expected_bin;
    reg [4:0] row_index;
    reg [2:0] neighbor_index;
    reg [9:0] neighbor0,neighbor1,neighbor2,neighbor3;
    reg [9:0] find_ptr;
    reg [9:0] selected_root;
    reg [9:0] label_count;
    reg [9:0] root_count;
    reg [9:0] emitted_count;
    reg [9:0] scan_index;
    reg [9:0] best_index;
    reg best_found;
    reg [STAT_W-1:0] best_stat;
    reg [45:0] current_power;

    function signed [5:0] signed_bin;
        input [4:0] b;
        begin
            if (b <= 5'd15)
                signed_bin = {1'b0,b};
            else
                signed_bin = $signed({1'b0,b}) - 6'sd32;
        end
    endfunction

    // 1 means the first peak is higher priority than the second.
    function better_peak;
        input [45:0] power_a, power_b;
        input [6:0] range_a, range_b;
        input [4:0] bin_a, bin_b;
        begin
            if (power_a != power_b)
                better_peak = power_a > power_b;
            else if (signed_bin(bin_a) != signed_bin(bin_b))
                better_peak = signed_bin(bin_a) < signed_bin(bin_b);
            else if (range_a != range_b)
                better_peak = range_a < range_b;
            else
                better_peak = bin_a < bin_b;
        end
    endfunction

    function better_record;
        input [STAT_W-1:0] a,b;
        begin
            if (a[35:29] != b[35:29])
                better_record = a[35:29] < b[35:29];
            else if (signed_bin(a[28:24]) != signed_bin(b[28:24]))
                better_record = signed_bin(a[28:24]) < signed_bin(b[28:24]);
            else
                better_record = a[28:24] < b[28:24];
        end
    endfunction

    wire [9:0] next_label = label_count + 10'd1;
    wire [9:0] union_lo =
        (selected_root < find_ptr) ? selected_root : find_ptr;
    wire [9:0] union_hi =
        (selected_root < find_ptr) ? find_ptr : selected_root;

    wire choose_a = better_peak(
        stat_a[81:36], stat_q[81:36],
        stat_a[35:29], stat_q[35:29],
        stat_a[28:24], stat_q[28:24]);
    wire equal_union_power = (stat_a[81:36] == stat_q[81:36]);
    wire [12:0] merged_cells =
        {1'b0,stat_a[23:12]} + {1'b0,stat_q[23:12]};
    wire [12:0] merged_equal =
        {1'b0,stat_a[11:0]} + {1'b0,stat_q[11:0]};

    wire [STAT_W-1:0] merged_stat = {
        (choose_a ? stat_a[81:36] : stat_q[81:36]),
        (choose_a ? stat_a[35:29] : stat_q[35:29]),
        (choose_a ? stat_a[28:24] : stat_q[28:24]),
        merged_cells[11:0],
        (equal_union_power ? merged_equal[11:0] :
            (choose_a ? stat_a[11:0] : stat_q[11:0]))
    };

    wire choose_current = better_peak(
        current_power, stat_q[81:36],
        expected_range, stat_q[35:29],
        expected_bin, stat_q[28:24]);

    wire [STAT_W-1:0] added_stat = {
        (choose_current ? current_power : stat_q[81:36]),
        (choose_current ? expected_range : stat_q[35:29]),
        (choose_current ? expected_bin : stat_q[28:24]),
        (stat_q[23:12] + 12'd1),
        ((current_power == stat_q[81:36]) ?
            (stat_q[11:0] + 12'd1) :
            (choose_current ? 12'd1 : stat_q[11:0]))
    };

    reg [9:0] next_neighbor;
    always @* begin
        case (neighbor_index)
            3'd0: next_neighbor = neighbor0;
            3'd1: next_neighbor = neighbor1;
            3'd2: next_neighbor = neighbor2;
            default: next_neighbor = neighbor3;
        endcase
    end

    // A single synchronous BRAM read port for per-root statistics.
    reg [9:0] stats_read_addr;
    always @* begin
        case (state)
            S_UNION_A: stats_read_addr = selected_root;
            S_UNION_B: stats_read_addr = find_ptr;
            S_ADD_READ: stats_read_addr = selected_root;
            S_SORT_READ: stats_read_addr =
                (scan_index <= label_count) ? scan_index : 10'd0;
            default: stats_read_addr = 10'd0;
        endcase
    end
    // Exactly one synchronous write port and one synchronous read port.
    // Unified addresses are required for Spartan-6 XST BRAM inference:
    // multiple conditional indexed writes would synthesize into 57k FFs.
    reg stat_write_en;
    reg [9:0] stat_write_addr;
    reg [STAT_W-1:0] stat_write_data;
    always @* begin
        stat_write_en = 1'b0;
        stat_write_addr = 10'd0;
        stat_write_data = {STAT_W{1'b0}};
        case (state)
            S_UNION_WR: begin
                stat_write_en = 1'b1;
                stat_write_addr = union_lo;
                stat_write_data = merged_stat;
            end
            S_PROCESS: begin
                if (selected_root == 10'd0 &&
                    (label_count < MAX_LABELS) &&
                    (label_count < PHYSICAL_LABELS)) begin
                    stat_write_en = 1'b1;
                    stat_write_addr = next_label;
                    stat_write_data = {
                        current_power,expected_range,expected_bin,
                        12'd1,12'd1
                    };
                end
            end
            S_ADD_WRITE: begin
                stat_write_en = 1'b1;
                stat_write_addr = selected_root;
                stat_write_data = added_stat;
            end
            default: begin end
        endcase
    end
    always @(posedge clk) begin
        if (stat_write_en)
            stat_mem[stat_write_addr] <= stat_write_data;
        stat_q <= stat_mem[stats_read_addr];
    end

    // Sequential parent-pointer RAM, shared by union-find traversals
    // and final root enumeration; no 703x10 multi-read-port LUT table.
    reg parent_write_en;
    reg [9:0] parent_write_addr;
    reg [9:0] parent_write_data;
    reg [9:0] parent_read_addr;
    always @* begin
        parent_write_en = 1'b0;
        parent_write_addr = 10'd0;
        parent_write_data = 10'd0;
        parent_read_addr = 10'd0;
        case (state)
            S_UNION_WR: begin
                parent_write_en = 1'b1;
                parent_write_addr = union_hi;
                parent_write_data = union_lo;
            end
            S_PROCESS: begin
                if (selected_root == 10'd0 &&
                    (label_count < MAX_LABELS) &&
                    (label_count < PHYSICAL_LABELS)) begin
                    parent_write_en = 1'b1;
                    parent_write_addr = next_label;
                    parent_write_data = next_label;
                end
            end
            default: begin end
        endcase
        case (state)
            S_FIND_READ: parent_read_addr = find_ptr;
            S_SORT_READ: parent_read_addr =
                (scan_index <= label_count) ? scan_index : 10'd0;
            default: parent_read_addr = 10'd0;
        endcase
    end
    always @(posedge clk) begin
        if (parent_write_en)
            parent[parent_write_addr] <= parent_write_data;
        parent_q <= parent[parent_read_addr];
    end



    // Experimental equivalent single-write-port table inference.
    reg emitted_we,emitted_data;
    reg [9:0] emitted_addr;
    reg curr_we,prev_we;
    reg [4:0] curr_addr;
    reg [9:0] curr_data,prev_data;
    always @* begin
        emitted_we=0;emitted_addr=0;emitted_data=0;
        curr_we=0;curr_addr=0;curr_data=0;
        prev_we=0;prev_data=0;
        if(state==S_PROCESS && selected_root==0 && label_count<MAX_LABELS && label_count<PHYSICAL_LABELS) begin
            emitted_we=1;emitted_addr=next_label;emitted_data=0;
            curr_we=1;curr_addr=expected_bin-5'd3;curr_data=next_label;
        end
        if(state==S_OUTPUT && out_ready) begin
            emitted_we=1;emitted_addr=best_index;emitted_data=1;
        end
        if(state==S_INIT_ROW) begin
            curr_we=1;curr_addr=row_index;curr_data=0;prev_we=1;prev_data=0;
        end
        if(state==S_SHIFT_ROW) begin
            curr_we=1;curr_addr=row_index;curr_data=0;prev_we=1;prev_data=curr_row[row_index];
        end
        if(state==S_ACCEPT && in_valid && in_range==expected_range && in_bin==expected_bin && !in_alarm) begin
            curr_we=1;curr_addr=expected_bin-5'd3;curr_data=0;
        end
        if(state==S_ADD_WRITE) begin
            curr_we=1;curr_addr=expected_bin-5'd3;curr_data=selected_root;
        end
    end
    always @(posedge clk)begin
        if(!rst)begin
            if(emitted_we)emitted[emitted_addr]<=emitted_data;
            if(curr_we)curr_row[curr_addr]<=curr_data;
            if(prev_we)prev_row[row_index]<=prev_data;
        end
    end

    assign in_ready = (state == S_ACCEPT);
    assign out_valid = (state == S_OUTPUT);
    assign out_record_id = emitted_count;
    assign out_range = best_stat[35:29];
    assign out_bin = best_stat[28:24];
    assign out_signed_bin = signed_bin(best_stat[28:24]);
    assign out_peak_power = best_stat[81:36];
    assign out_cluster_cells = best_stat[23:12];
    assign out_tie_flag = (best_stat[11:0] > 12'd1);
    assign out_equal_power_cells = best_stat[11:0];

    always @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            overflow_sticky <= 1'b0;
            protocol_error <= 1'b0;
            frame_invalid <= 1'b0;
            expected_range <= 7'd3;
            expected_bin <= 5'd3;
            row_index <= 5'd0;
            neighbor_index <= 3'd0;
            neighbor0 <= 10'd0;
            neighbor1 <= 10'd0;
            neighbor2 <= 10'd0;
            neighbor3 <= 10'd0;
            find_ptr <= 10'd0;
            selected_root <= 10'd0;
            label_count <= 10'd0;
            root_count <= 10'd0;
            emitted_count <= 10'd0;
            scan_index <= 10'd0;
            best_index <= 10'd0;
            best_found <= 1'b0;
            best_stat <= {STAT_W{1'b0}};
            current_power <= 46'd0;
            stat_a <= {STAT_W{1'b0}};
        end else begin
            done <= 1'b0;
            if (start && state != S_IDLE)
                protocol_error <= 1'b1;

            case (state)
                S_IDLE: begin
                    if (start) begin
                        busy <= 1'b1;
                        overflow_sticky <= 1'b0;
                        protocol_error <= 1'b0;
                        frame_invalid <= 1'b0;
                        expected_range <= 7'd3;
                        expected_bin <= 5'd3;
                        row_index <= 5'd0;
                        label_count <= 10'd0;
                        root_count <= 10'd0;
                        emitted_count <= 10'd0;
                        state <= S_INIT_ROW;
                    end
                end

                S_INIT_ROW: begin
                    if (row_index == 5'd31)
                        state <= S_ACCEPT;
                    else
                        row_index <= row_index + 5'd1;
                end

                S_ACCEPT: begin
                    if (in_valid) begin
                        if ((in_range != expected_range) ||
                            (in_bin != expected_bin)) begin
                            protocol_error <= 1'b1;
                            frame_invalid <= 1'b1;
                            busy <= 1'b0;
                            done <= 1'b1;
                            state <= S_IDLE;
                        end else if (!in_alarm) begin
                            state <= S_STEP;
                        end else begin
                            current_power <= in_power;
                            neighbor0 <= (expected_bin == 5'd3) ? 10'd0 :
                                curr_row[expected_bin-5'd4];
                            neighbor1 <= (expected_bin == 5'd3) ? 10'd0 :
                                prev_row[expected_bin-5'd4];
                            neighbor2 <= prev_row[expected_bin-5'd3];
                            neighbor3 <= (expected_bin == 5'd28) ? 10'd0 :
                                prev_row[expected_bin-5'd2];
                            neighbor_index <= 3'd0;
                            selected_root <= 10'd0;
                            state <= S_NEIGH;
                        end
                    end
                end

                S_NEIGH: begin
                    if (neighbor_index == 3'd4)
                        state <= S_PROCESS;
                    else if (next_neighbor == 10'd0)
                        neighbor_index <= neighbor_index + 3'd1;
                    else begin
                        find_ptr <= next_neighbor;
                        state <= S_FIND_READ;
                    end
                end

                S_FIND_READ: state <= S_FIND;

                S_FIND: begin
                    if (parent_q != find_ptr) begin
                        find_ptr <= parent_q;
                        state <= S_FIND_READ;
                    end
                    else if (selected_root == 10'd0) begin
                        selected_root <= find_ptr;
                        neighbor_index <= neighbor_index + 3'd1;
                        state <= S_NEIGH;
                    end else if (selected_root == find_ptr) begin
                        neighbor_index <= neighbor_index + 3'd1;
                        state <= S_NEIGH;
                    end else
                        state <= S_UNION_A;
                end

                S_UNION_A: state <= S_UNION_B;
                S_UNION_B: begin
                    stat_a <= stat_q;
                    state <= S_UNION_WR;
                end

                S_UNION_WR: begin
                    selected_root <= union_lo;
                    root_count <= root_count - 10'd1;
                    neighbor_index <= neighbor_index + 3'd1;
                    state <= S_NEIGH;
                end

                S_PROCESS: begin
                    if (selected_root == 10'd0) begin
                        if ((label_count >= MAX_LABELS) ||
                            (label_count >= PHYSICAL_LABELS)) begin
                            overflow_sticky <= 1'b1;
                            frame_invalid <= 1'b1;
                            busy <= 1'b0;
                            done <= 1'b1;
                            state <= S_IDLE;
                        end else begin
                            label_count <= next_label;
                            root_count <= root_count + 10'd1;
                            state <= S_STEP;
                        end
                    end else
                        state <= S_ADD_READ;
                end

                S_ADD_READ: state <= S_ADD_WRITE;
                S_ADD_WRITE: begin
                    state <= S_STEP;
                end

                S_STEP: begin
                    if (expected_bin == 5'd28) begin
                        if (expected_range == 7'd109)
                            state <= S_SORT_INIT;
                        else begin
                            row_index <= 5'd0;
                            state <= S_SHIFT_ROW;
                        end
                    end else begin
                        expected_bin <= expected_bin + 5'd1;
                        state <= S_ACCEPT;
                    end
                end

                S_SHIFT_ROW: begin
                    if (row_index == 5'd31) begin
                        expected_range <= expected_range + 7'd1;
                        expected_bin <= 5'd3;
                        state <= S_ACCEPT;
                    end else
                        row_index <= row_index + 5'd1;
                end

                S_SORT_INIT: begin
                    if (emitted_count == root_count) begin
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= S_IDLE;
                    end else begin
                        scan_index <= 10'd1;
                        best_found <= 1'b0;
                        state <= S_SORT_READ;
                    end
                end

                S_SORT_READ: begin
                    if (scan_index > label_count)
                        state <= S_OUTPUT;
                    else
                        state <= S_SORT_CHECK;
                end

                S_SORT_CHECK: begin
                    if (parent_q == scan_index &&
                        !emitted[scan_index]) begin
                        if (!best_found ||
                            better_record(stat_q,best_stat)) begin
                            best_stat <= stat_q;
                            best_index <= scan_index;
                            best_found <= 1'b1;
                        end
                    end
                    scan_index <= scan_index + 10'd1;
                    state <= S_SORT_READ;
                end

                S_OUTPUT: begin
                    if (out_ready) begin
                        emitted_count <= emitted_count + 10'd1;
                        state <= S_SORT_INIT;
                    end
                end

                default: begin
                    protocol_error <= 1'b1;
                    frame_invalid <= 1'b1;
                    busy <= 1'b0;
                    done <= 1'b1;
                    state <= S_IDLE;
                end
            endcase
        end
    end
endmodule

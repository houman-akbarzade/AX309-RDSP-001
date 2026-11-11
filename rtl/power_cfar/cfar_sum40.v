// Exact U46.30 training-cell accumulation: exactly 40 accepted values.
module cfar_sum40 (
    input wire clk,
    input wire rst,
    input wire start,
    input wire training_valid,
    input wire [45:0] training_power,
    output reg busy,
    output reg done,
    output reg [51:0] sum40,
    output reg overflow_event,
    output reg protocol_error
);
    reg [5:0] count;
    reg [52:0] sum_next;

    always @* begin
        sum_next = {1'b0,sum40} + {7'd0,training_power};
    end

    always @(posedge clk) begin
        if (rst) begin
            busy <= 1'b0;
            done <= 1'b0;
            sum40 <= 52'd0;
            count <= 6'd0;
            overflow_event <= 1'b0;
            protocol_error <= 1'b0;
        end else begin
            done <= 1'b0;
            overflow_event <= 1'b0;
            if (start) begin
                if (busy) protocol_error <= 1'b1;
                else begin
                    busy <= 1'b1;
                    count <= 6'd0;
                    sum40 <= 52'd0;
                end
            end
            if (training_valid) begin
                if (!busy || count >= 6'd40) begin
                    protocol_error <= 1'b1;
                end else begin
                    if (sum_next[52]) begin
                        overflow_event <= 1'b1;
                        protocol_error <= 1'b1;
                    end
                    sum40 <= sum_next[51:0];
                    if (count == 6'd39) begin
                        busy <= 1'b0;
                        done <= 1'b1;
                    end
                    count <= count + 6'd1;
                end
            end
        end
    end
endmodule

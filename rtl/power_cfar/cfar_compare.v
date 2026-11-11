// Exact strict CFAR comparison with frozen alpha = 490007/65536.
// Alarm iff 40*Pcut*65536 > 490007*SUM40. Equality is no alarm.
module cfar_compare (
    input wire [45:0] p_cut,
    input wire [51:0] sum40,
    output wire alarm,
    output wire equality,
    output wire [71:0] lhs,
    output wire [71:0] rhs
);
    wire [51:0] p_cut_ext = {6'd0,p_cut};
    wire [51:0] forty_p = (p_cut_ext << 5) + (p_cut_ext << 3);
    wire [70:0] sum_ext = {19'd0,sum40};
    wire [70:0] rhs_product = sum_ext * 71'd490007;
    assign lhs = {4'd0,forty_p,16'd0};
    assign rhs = {1'b0,rhs_product};
    assign alarm = (lhs > rhs);
    assign equality = (lhs == rhs);
endmodule

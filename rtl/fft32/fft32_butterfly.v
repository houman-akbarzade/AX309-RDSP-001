// One radix-2 DIT butterfly. C02 widths are retained through exact
// product, complex pair and pre-shift butterfly; RNE occurs once per output.
module fft32_butterfly (
    input wire signed [24:0] u_re,
    input wire signed [24:0] u_im,
    input wire signed [24:0] v_re,
    input wire signed [24:0] v_im,
    input wire signed [15:0] tw_re,
    input wire signed [15:0] tw_im,
    input wire [5:0] shift_amt,
    output wire signed [24:0] plus_re,
    output wire signed [24:0] plus_im,
    output wire signed [24:0] minus_re,
    output wire signed [24:0] minus_im,
    output wire [3:0] saturation_mask,
    output wire signed [63:0] pre_plus_re,
    output wire signed [63:0] pre_plus_im,
    output wire signed [63:0] pre_minus_re,
    output wire signed [63:0] pre_minus_im
);
    // Sign extension makes the full 25x16 signed products explicit.
    // Synthesis may trim redundant sign bits; no product bits are discarded.
    wire signed [40:0] v_re_ext = {{16{v_re[24]}},v_re};
    wire signed [40:0] v_im_ext = {{16{v_im[24]}},v_im};
    wire signed [40:0] tw_re_ext = {{25{tw_re[15]}},tw_re};
    wire signed [40:0] tw_im_ext = {{25{tw_im[15]}},tw_im};

    wire signed [40:0] p_rr = v_re_ext * tw_re_ext;
    wire signed [40:0] p_ii = v_im_ext * tw_im_ext;
    wire signed [40:0] p_ri = v_re_ext * tw_im_ext;
    wire signed [40:0] p_ir = v_im_ext * tw_re_ext;

    wire signed [41:0] pair_re =
        $signed({p_rr[40],p_rr}) - $signed({p_ii[40],p_ii});
    wire signed [41:0] pair_im =
        $signed({p_ri[40],p_ri}) + $signed({p_ir[40],p_ir});

    wire signed [39:0] aligned_u_re = {u_re,15'b0};
    wire signed [39:0] aligned_u_im = {u_im,15'b0};

    wire signed [42:0] plus_raw_re =
        {{3{aligned_u_re[39]}},aligned_u_re} + {{1{pair_re[41]}},pair_re};
    wire signed [42:0] minus_raw_re =
        {{3{aligned_u_re[39]}},aligned_u_re} - {{1{pair_re[41]}},pair_re};
    wire signed [42:0] plus_raw_im =
        {{3{aligned_u_im[39]}},aligned_u_im} + {{1{pair_im[41]}},pair_im};
    wire signed [42:0] minus_raw_im =
        {{3{aligned_u_im[39]}},aligned_u_im} - {{1{pair_im[41]}},pair_im};

    wire ov_pr, ov_pi, ov_mr, ov_mi;
    rne_sat_signed #(.IN_W(43),.OUT_W(25)) r_pr
        (plus_raw_re,shift_amt,plus_re,ov_pr,pre_plus_re);
    rne_sat_signed #(.IN_W(43),.OUT_W(25)) r_pi
        (plus_raw_im,shift_amt,plus_im,ov_pi,pre_plus_im);
    rne_sat_signed #(.IN_W(43),.OUT_W(25)) r_mr
        (minus_raw_re,shift_amt,minus_re,ov_mr,pre_minus_re);
    rne_sat_signed #(.IN_W(43),.OUT_W(25)) r_mi
        (minus_raw_im,shift_amt,minus_im,ov_mi,pre_minus_im);

    assign saturation_mask = {ov_mi,ov_mr,ov_pi,ov_pr};
endmodule

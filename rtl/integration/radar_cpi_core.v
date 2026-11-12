// Full C02 DSP chain using the existing raw IQ RAM read port.
// Recompute MF for each slow-time pair instead of allocating a full MF frame.
// This preserves exact arithmetic; no mandatory stage is moved to the host.
module radar_cpi_core(
 input wire clk,rst,start,
 input wire debug_read,input wire [11:0] debug_addr,output wire [45:0] debug_power,
 output reg [12:0] iq_read_addr,input wire [31:0] iq_read_word,
 output wire out_valid,input wire out_ready,
 output wire [9:0] out_record_id,output wire [6:0] out_range,
 output wire [4:0] out_bin,output wire signed [5:0] out_signed_bin,
 output wire [45:0] out_peak_power,output wire [11:0] out_cluster_cells,
 output wire out_tie_flag,output wire [11:0] out_equal_power_cells,
 output reg busy,output reg done,output wire error,
 output reg saturation_sticky,
 output wire power_valid,output wire [45:0] power_value,
 output wire [6:0] power_range,output wire [4:0] power_bin);
 localparam IDLE=0,BEGIN_RANGE=1,MF_BEGIN=2,TAP_ADDR=3,TAP_WAIT=4,
 TAP_SEND=5,MF_WAIT=6,MTI_SEND=7,FFT_SEND=8,FFT_WAIT=9,WAIT_GROUP=10;
 reg [3:0] state;
 reg [6:0] range_index;
 reg [4:0] load_index,bin_index;
 reg second_pulse;
 reg [3:0] tap;
 reg zero_sample;
 reg signed [21:0] previous_re,previous_im;
 wire [4:0] reversed_pulse={load_index[0],load_index[1],load_index[2],load_index[3],load_index[4]};
 wire [5:0] pulse={1'b0,reversed_pulse}+second_pulse;
 wire [8:0] sample_index={2'b0,range_index}+9'd15-{5'd0,tap};
 wire mf_start=(state==MF_BEGIN);
 wire mf_done,mf_sat,mf_error;
 wire signed [21:0] mf_re,mf_im;
 wire signed [15:0] sample_re_selected=zero_sample?16'sd0:iq_read_word[15:0];
 wire signed [15:0] sample_im_selected=zero_sample?16'sd0:iq_read_word[31:16];
 mf16_serial_mac u_mf(.clk(clk),.rst(rst),.start(mf_start),
 .range_in(range_index),.tap_valid(state==TAP_SEND),.tap_index(tap),
 .sample_re(sample_re_selected),
 .sample_im(sample_im_selected),
 .busy(),.done(mf_done),.range_out(),.result_re(mf_re),.result_im(mf_im),
 .saturation_event(mf_sat),.saturation_mask(),.prelimit_re(),.prelimit_im(),
 .protocol_error(mf_error));
 wire mti_valid;
 wire signed [22:0] diff_re,diff_im;
 mti2_diff u_mti(.clk(clk),.rst(rst),.in_valid(state==MTI_SEND),
 .pulse_next_re(mf_re),.pulse_next_im(mf_im),
 .pulse_prev_re(previous_re),.pulse_prev_im(previous_im),
 .range_in(range_index),.pulse_in(reversed_pulse),.out_valid(mti_valid),
 .diff_re(diff_re),.diff_im(diff_im),.range_out(),.pulse_out());
 wire fft_ready,fft_valid,fft_done,fft_last,fft_sat,fft_error;
 wire signed [24:0] fft_re,fft_im;
 wire pow_ready,map_ready,group_done,group_error,group_overflow,group_invalid;
 fft32_dit u_fft(.clk(clk),.rst(rst),.start(state==BEGIN_RANGE),
 .range_in(range_index),.in_valid(mti_valid),.in_ready(fft_ready),
 .in_re(diff_re),.in_im(diff_im),.out_valid(fft_valid),
 .out_ready(pow_ready),.out_last(fft_last),.out_re(fft_re),.out_im(fft_im),
 .range_out(),.busy(),.done(fft_done),.overflow_event(),
 .overflow_sticky(fft_sat),.overflow_stage(),.overflow_butterfly(),
 .overflow_mask(),.overflow_pre_plus_re(),.overflow_pre_plus_im(),
 .overflow_pre_minus_re(),.overflow_pre_minus_im(),.protocol_error(fft_error));
 wire pow_sat;
 power_q25_u46_serial u_power(.clk(clk),.rst(rst),.in_valid(fft_valid),
 .in_ready(pow_ready),.in_re(fft_re),.in_im(fft_im),
 .range_in(range_index),.bin_in(bin_index),
 .out_valid(power_valid),.out_ready(map_ready),.power_out(power_value),
 .range_out(power_range),.bin_out(power_bin),.overflow_sticky(pow_sat));
 cfar_grouping_subsystem u_detect(.clk(clk),.rst(rst),
 .start(start && !busy),.debug_read(debug_read),.debug_addr(debug_addr),.debug_power(debug_power),.map_valid(power_valid),.map_ready(map_ready),
 .map_power(power_value),.cut_pause(1'b0),
 .out_valid(out_valid),.out_ready(out_ready),
 .out_record_id(out_record_id),.out_range(out_range),.out_bin(out_bin),
 .out_signed_bin(out_signed_bin),.out_peak_power(out_peak_power),
 .out_cluster_cells(out_cluster_cells),.out_tie_flag(out_tie_flag),
 .out_equal_power_cells(out_equal_power_cells),.busy(),.done(group_done),
 .scanner_done(),.overflow_sticky(group_overflow),
 .protocol_error(group_error),.frame_invalid(group_invalid));
 assign error=mf_error|fft_error|group_error|group_overflow|group_invalid;
 always @(posedge clk) begin
  if(rst)begin
   state<=IDLE;busy<=0;done<=0;range_index<=0;load_index<=0;
   bin_index<=0;second_pulse<=0;tap<=0;zero_sample<=0;
   previous_re<=0;previous_im<=0;iq_read_addr<=0;saturation_sticky<=0;
  end else begin
   done<=0;
   if(mf_sat|fft_sat|pow_sat)saturation_sticky<=1;
   if(fft_valid && pow_ready)bin_index<=bin_index+1'b1;
   case(state)
    IDLE:if(start)begin busy<=1;range_index<=0;state<=BEGIN_RANGE;end
    BEGIN_RANGE:begin load_index<=0;bin_index<=0;second_pulse<=0;state<=MF_BEGIN;end
    MF_BEGIN:begin tap<=0;state<=TAP_ADDR;end
    TAP_ADDR:begin
     iq_read_addr<={pulse,7'b0}+sample_index;
     zero_sample<=sample_index>=128;state<=TAP_WAIT;
    end
    TAP_WAIT:state<=TAP_SEND;
    TAP_SEND:if(tap==15)state<=MF_WAIT;else begin tap<=tap+1'b1;state<=TAP_ADDR;end
    MF_WAIT:if(mf_done)begin
     if(!second_pulse)begin
      previous_re<=mf_re;previous_im<=mf_im;second_pulse<=1;state<=MF_BEGIN;
     end else state<=MTI_SEND;
    end
    MTI_SEND:state<=FFT_SEND;
    FFT_SEND:begin
     second_pulse<=0;
     if(load_index==31)state<=FFT_WAIT;
     else begin load_index<=load_index+1'b1;state<=MF_BEGIN;end
    end
    FFT_WAIT:if(power_valid && map_ready && power_bin==31)begin
     if(range_index==127)state<=WAIT_GROUP;
     else begin range_index<=range_index+1'b1;state<=BEGIN_RANGE;end
    end
    WAIT_GROUP:if(group_done)begin busy<=0;done<=1;state<=IDLE;end
   endcase
  end
 end
endmodule

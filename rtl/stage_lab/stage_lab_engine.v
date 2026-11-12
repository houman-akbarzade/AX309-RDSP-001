// Test-only sequential stage controller. Original arithmetic modules unchanged.
// Canonical memory: 64-bit words, I signed32 low / Q signed32 high;
// slow-time (or FFT-bin) major, 128 range cells. Power low46; CFAR alarm bit63.
module stage_lab_engine #(parameter integer TARGET=4, FIRST=TARGET)(
 input clk,rst,start,input [2:0] input_stage,input [12:0] input_words,
 output wire [12:0] read_addr,input [63:0] read_data,
 output reg write_en,output reg [12:0] write_addr,output reg [63:0] write_data,
 output reg busy,done,output reg [12:0] output_words,output reg [15:0] flags);
 localparam DISPATCH=1,ADV1=2,ADV2=3,FINISH=4,
 MSTART=10,MADDR=11,MWAIT=12,MSEND=13,MDONE=14,
 TA=20,TAW=21,TAS=22,TB=23,TBW=24,TSEND=25,TWAIT=26,
 FSTART=30,FADDR=31,FW=32,FSEND=33,FWAIT=34,
 PA=40,PW=41,PSEND=42,PWAIT=43,
 CSTART=50,CRUN=51,GSTART=60,GA=61,GW=62,GSEND=63,GWAIT=64,GSECOND=65;
 reg [6:0] state;reg [2:0] stage;reg [12:0] index,words;
 reg [3:0] tap;reg zero_sample;reg [63:0] previous;
 reg [6:0] range_index;reg [4:0] load_index,output_bin;
 reg [34:0] upper_record;reg [9:0] record_count;reg group_finished;
 wire [8:0] sample_index={2'd0,index[6:0]}+9'd15-{5'd0,tap};
 wire mf_done,mf_error,mf_sat;wire signed [21:0] mf_re,mf_im;
 wire signed [15:0] ms_re=zero_sample?16'sd0:read_data[15:0];
 wire signed [15:0] ms_im=zero_sample?16'sd0:read_data[47:32];
 generate if(TARGET>=1 && FIRST<=1)begin:MF
 mf16_serial_mac u(.clk(clk),.rst(rst),.start(state==MSTART),.range_in(index[6:0]),
 .tap_valid(state==MSEND),.tap_index(tap),.sample_re(ms_re),.sample_im(ms_im),
 .busy(),.done(mf_done),.range_out(),.result_re(mf_re),.result_im(mf_im),
 .saturation_event(mf_sat),.saturation_mask(),.prelimit_re(),.prelimit_im(),.protocol_error(mf_error));
 end else begin assign mf_done=0;assign mf_error=0;assign mf_sat=0;assign mf_re=0;assign mf_im=0;end endgenerate
 wire mt_valid;wire signed [22:0] mt_re,mt_im;
 generate if(TARGET>=2 && FIRST<=2)begin:MTI
 mti2_diff u(.clk(clk),.rst(rst),.in_valid(state==TSEND),
 .pulse_next_re(read_data[21:0]),.pulse_next_im(read_data[53:32]),
 .pulse_prev_re(previous[21:0]),.pulse_prev_im(previous[53:32]),
 .range_in(index[6:0]),.pulse_in(index[11:7]),
 .out_valid(mt_valid),.diff_re(mt_re),.diff_im(mt_im),.range_out(),.pulse_out());
 end else begin assign mt_valid=0;assign mt_re=0;assign mt_im=0;end endgenerate
 wire fr, fv,fl,fe,fo;wire signed [24:0] fy_re,fy_im;
 wire [4:0] reverse_load={load_index[0],load_index[1],load_index[2],load_index[3],load_index[4]};
 generate if(TARGET>=3 && FIRST<=3)begin:FFT
 fft32_dit u(.clk(clk),.rst(rst),.start(state==FSTART),.range_in(range_index),
 .in_valid(state==FSEND),.in_ready(fr),.in_re(read_data[22:0]),.in_im(read_data[54:32]),
 .out_valid(fv),.out_ready(1'b1),.out_last(fl),.out_re(fy_re),.out_im(fy_im),
 .range_out(),.busy(),.done(),.overflow_event(),.overflow_sticky(fo),
 .overflow_stage(),.overflow_butterfly(),.overflow_mask(),.overflow_pre_plus_re(),
 .overflow_pre_plus_im(),.overflow_pre_minus_re(),.overflow_pre_minus_im(),.protocol_error(fe));
 end else begin assign fr=0;assign fv=0;assign fl=0;assign fe=0;assign fo=0;assign fy_re=0;assign fy_im=0;end endgenerate
 wire pr,pv,po;wire [45:0] power_value;
 generate if(TARGET>=4 && FIRST<=4)begin:POWER
 power_q25_u46_serial u(.clk(clk),.rst(rst),.in_valid(state==PSEND),.in_ready(pr),
 .in_re(read_data[24:0]),.in_im(read_data[56:32]),.range_in(index[6:0]),.bin_in(index[11:7]),
 .out_valid(pv),.out_ready(1'b1),.power_out(power_value),.range_out(),.bin_out(),.overflow_sticky(po));
 end else begin assign pr=0;assign pv=0;assign po=0;assign power_value=0;end endgenerate
 wire cv,cd,ce,co,ca;wire [6:0] cr;wire [4:0] cb;wire [45:0] cp;wire [11:0] caddr;
 generate if(TARGET>=5 && FIRST<=5)begin:CFAR
 stage_lab_cfar_external u(.clk(clk),.rst(rst),.start(state==CSTART),
 .external_power(read_data[45:0]),.external_addr(caddr),.debug_read(1'b0),.debug_addr(12'd0),.debug_power(),
 .map_valid(1'b0),.map_ready(),.map_power(46'd0),.out_valid(cv),.out_ready(1'b1),
 .out_range(cr),.out_bin(cb),.out_power(cp),.out_sum40(),.out_alarm(ca),.out_equality(),
 .busy(),.done(cd),.overflow_event(),.overflow_sticky(co),.protocol_error(ce));
 end else begin assign cv=0;assign cd=0;assign ce=0;assign co=0;assign ca=0;assign cr=0;assign cb=0;assign cp=0;assign caddr=0;end endgenerate
 wire gr,gv,gd,ge,go,gi;wire [9:0] gid;wire [6:0] g_range;wire [4:0] g_bin;
 wire signed [5:0] g_signed;wire [45:0] g_power;wire [11:0] g_cells,g_equals;wire g_tie;
 wire [98:0] g_record={gid,g_range,g_bin,g_signed,g_power,g_cells,g_tie,g_equals};
 generate if(TARGET>=6 && FIRST<=6)begin:GROUP
 grouping_8conn u(.clk(clk),.rst(rst),.start(state==GSTART),
 .in_valid(state==GSEND),.in_ready(gr),.in_range(range_index),.in_bin(load_index),
 .in_power(read_data[45:0]),.in_alarm(read_data[63]),.out_valid(gv),.out_ready(state==GWAIT),
 .out_record_id(gid),.out_range(g_range),.out_bin(g_bin),.out_signed_bin(g_signed),
 .out_peak_power(g_power),.out_cluster_cells(g_cells),.out_tie_flag(g_tie),.out_equal_power_cells(g_equals),
 .busy(),.done(gd),.overflow_sticky(go),.protocol_error(ge),.frame_invalid(gi));
 end else begin assign gr=0;assign gv=0;assign gd=0;assign ge=0;assign go=0;assign gi=0;assign gid=0;assign g_range=0;assign g_bin=0;assign g_signed=0;assign g_power=0;assign g_cells=0;assign g_equals=0;assign g_tie=0;end endgenerate
 reg [12:0] internal_read;reg [12:0] ordinary_read;
 always @* begin
  if(stage==5)internal_read={1'b0,caddr[4:0],caddr[11:5]};
  else internal_read=ordinary_read;
 end
 // read_addr is registered for ordinary stages; CFAR supplies the shared RAM address.
 assign read_addr=internal_read;
 always @(posedge clk)begin
  if(rst)begin state<=0;stage<=0;index<=0;words<=0;ordinary_read<=0;
   write_en<=0;write_addr<=0;write_data<=0;busy<=0;done<=0;output_words<=0;flags<=0;
   tap<=0;zero_sample<=0;previous<=0;range_index<=0;load_index<=0;output_bin<=0;
   upper_record<=0;record_count<=0;group_finished<=0;end
  else begin
   write_en<=0;done<=0;
   if(mf_sat)flags[0]<=1;if(mf_error)flags[8]<=1;
   if(fo)flags[1]<=1;if(fe)flags[9]<=1;
   if(po)flags[2]<=1;if(ce|co)flags[10]<=1;
   if(ge|go|gi)flags[11]<=1;if(gd)group_finished<=1;
   if(fv)begin
    write_en<=1;write_addr<={1'b0,output_bin,range_index};
    write_data<={ {7{fy_im[24]}},fy_im,{7{fy_re[24]}},fy_re};
    output_bin<=output_bin+1'b1;
   end
   case(state)
    0:if(start)begin busy<=1;done<=0;flags<=0;stage<=input_stage+1'b1;
      words<=input_words;output_words<=input_words;index<=0;range_index<=0;state<=DISPATCH;end
    DISPATCH:begin
     index<=0;range_index<=0;
     case(stage)
      1:state<=MSTART;2:state<=TA;3:state<=FSTART;
      4:state<=PA;5:state<=CSTART;6:state<=GSTART;
      default:state<=FINISH;
     endcase
    end
    ADV1:state<=ADV2;
    ADV2:if(stage==TARGET)state<=FINISH;else begin stage<=stage+1'b1;state<=DISPATCH;end
    FINISH:begin busy<=0;done<=1;state<=0;end
    MSTART:begin tap<=0;state<=MADDR;end
    MADDR:begin ordinary_read<={index[12:7],7'd0}+sample_index;zero_sample<=sample_index>=128;state<=MWAIT;end
    MWAIT:state<=MSEND;
    MSEND:if(tap==15)state<=MDONE;else begin tap<=tap+1'b1;state<=MADDR;end
    MDONE:if(mf_done)begin
     write_en<=1;write_addr<=index;write_data<={{10{mf_im[21]}},mf_im,{10{mf_re[21]}},mf_re};
     if(index==words-1'b1)state<=ADV1;else begin index<=index+1'b1;state<=MSTART;end
    end
    TA:begin ordinary_read<=index;state<=TAW;end
    TAW:state<=TAS;
    TAS:begin previous<=read_data;state<=TB;end
    TB:begin ordinary_read<=index+13'd128;state<=TBW;end
    TBW:state<=TSEND;
    TSEND:state<=TWAIT;
    TWAIT:if(mt_valid)begin
     write_en<=1;write_addr<=index;write_data<={{9{mt_im[22]}},mt_im,{9{mt_re[22]}},mt_re};
     if(index==words-13'd129)begin words<=words-13'd128;output_words<=words-13'd128;state<=ADV1;end
     else begin index<=index+1'b1;state<=TA;end
    end
    FSTART:begin load_index<=0;output_bin<=0;state<=FADDR;end
    FADDR:begin ordinary_read<={1'b0,reverse_load,range_index};state<=FW;end
    FW:state<=FSEND;
    FSEND:if(fr)begin
     if(load_index==31)state<=FWAIT;else begin load_index<=load_index+1'b1;state<=FADDR;end
    end
    FWAIT:if(fv && fl)begin
     if(range_index==127)state<=ADV1;else begin range_index<=range_index+1'b1;state<=FSTART;end
    end
    PA:begin ordinary_read<=index;state<=PW;end
    PW:state<=PSEND;
    PSEND:if(pr)state<=PWAIT;
    PWAIT:if(pv)begin
     write_en<=1;write_addr<=index;write_data<={18'd0,power_value};
     if(index==words-1'b1)state<=ADV1;else begin index<=index+1'b1;state<=PA;end
    end
    CSTART:state<=CRUN;
    CRUN:begin
     if(cv)begin write_en<=1;write_addr<={1'b0,cb,cr};write_data<={ca,1'b1,16'd0,cp};end
     if(cd)state<=ADV1;
    end
    GSTART:begin range_index<=3;load_index<=3;record_count<=0;group_finished<=0;output_words<=0;state<=GA;end
    GA:begin ordinary_read<={1'b0,load_index,range_index};state<=GW;end
    GW:state<=GSEND;
    GSEND:if(gr)begin
     if(range_index==109 && load_index==28)state<=GWAIT;
     else begin
      if(load_index==28)begin load_index<=3;range_index<=range_index+1'b1;end
      else load_index<=load_index+1'b1;
      state<=GA;
     end
    end
    GWAIT:if(gv)begin
     write_en<=1;write_addr<={2'd0,record_count,1'b0};write_data<=g_record[63:0];
     upper_record<=g_record[98:64];record_count<=record_count+1'b1;
     output_words<=output_words+13'd2;state<=GSECOND;
    end else if(group_finished)state<=ADV1;
    GSECOND:begin write_en<=1;write_addr<=({2'd0,record_count,1'b0}-1'b1);write_data<={29'd0,upper_record};state<=GWAIT;end
   endcase
  end
 end
endmodule

// Stage Lab v0.2. Test-only firmware; distinct protocol from stable full radar.
// CRC-verified request/response ARQ. One request in flight, same-sequence retries.
// Input/output share one RAM, input echo must be completed before VERIFY/RUN.
module stage_lab_top #(parameter integer TARGET=4,FIRST=TARGET,CLOCK_HZ=50000000,BAUD=115200)(
 input clk,rst,uart_rxd,output uart_txd);
 wire [7:0] rx;wire rxv,rxe;wire txready;
 uart_rx_8n1 #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD)) ur(.clk(clk),.rst(rst),.rx_pin(uart_rxd),.data_out(rx),.data_valid(rxv),.framing_error(rxe),.busy());
 wire frame_ready;reg frame_done;wire [7:0] ftype,fflags,rdbyte;
 wire [31:0] fseq,fcrc;wire [15:0] flen;reg [9:0] rdindex;
 s02_frame_echo #(.ECHO_MODE(0),.TIMEOUT_CLKS(CLOCK_HZ/100)) parser(.clk(clk),.rst(rst),
 .rx_data(rx),.rx_valid(rxv),.rx_framing_error(rxe),.tx_data(),.tx_valid(),.tx_ready(1'b0),
 .good_count(),.crc_error_count(),.header_error_count(),.length_error_count(),.partial_timeout_count(),
 .uart_error_count(),.busy_drop_count(),.response_busy(),.frame_ready(frame_ready),.frame_done(frame_done),
 .frame_type(ftype),.frame_flags(fflags),.frame_seq(fseq),.frame_length(flen),.frame_crc(fcrc),
 .frame_rd_index(rdindex),.frame_rd_byte(rdbyte));
 reg [63:0] bank0[0:4095];reg [63:0] bank1[0:127];reg [63:0] q0,q1;reg read_bank;wire [63:0] mem_q=read_bank?q1:q0;
 wire engine_busy,engine_done;reg run_engine,clear_engine;
 wire [12:0] eraddr,ewaddr,eowords;wire [63:0] ewdata;wire ewen;wire [15:0] eflags;
 reg [12:0] words;reg [2:0] entry;
 reg [12:0] host_addr;reg host_we;reg [63:0] host_data;reg [12:0] host_waddr;
 wire [12:0] maddr=engine_busy?eraddr:host_addr;
 wire mw=ewen|host_we;wire [12:0] mwa=ewen?ewaddr:host_waddr;wire [63:0] mwd=ewen?ewdata:host_data;
 always @(posedge clk)begin
  read_bank<=maddr[12];q0<=bank0[maddr[11:0]];q1<=bank1[maddr[6:0]];
  if(mw && !mwa[12])bank0[mwa[11:0]]<=mwd;
  if(mw && mwa[12] && mwa[11:7]==0)bank1[mwa[6:0]]<=mwd;
 end
 stage_lab_engine #(.TARGET(TARGET),.FIRST(FIRST)) engine(.clk(clk),.rst(rst|clear_engine),.start(run_engine),
 .input_stage(entry),.input_words(words),.read_addr(eraddr),.read_data(mem_q),
 .write_en(ewen),.write_addr(ewaddr),.write_data(ewdata),.busy(engine_busy),.done(engine_done),.output_words(eowords),.flags(eflags));
 localparam IDLE=0,RSET=1,RWAIT=2,RSTORE=3,DECIDE=4,CSET=5,CWAIT=6,CSTORE=7,
 TXSTART=8,TXWAIT=9,RELEASE=10,RELEASE_WAIT=11;
 reg [3:0] state;
 reg [5:0] field_index,field_count;reg [255:0] fields;
 reg [127:0] sid;reg [31:0] case_id,expected_seq,last_seq,last_crc;
 reg [15:0] uploaded,echoed;reg active,verified,started,complete,last_valid;
 reg [7:0] last_type;reg [15:0] last_length;
 reg [9:0] copy_index;reg [63:0] upload_word;
 reg send_start;wire send_ready;
 reg [7:0] response_type;reg [15:0] response_length;
 reg [31:0] response_seq,response_offset;reg [7:0] response_stage;
 reg [15:0] response_count;
 wire [127:0] incoming_sid=fields[127:0];
 wire [7:0] opcode=fields[135:128];
 wire [31:0] command_case=fields[167:136];
 wire [31:0] data_case=fields[159:128];
 wire [31:0] data_offset=fields[191:160];
 wire [31:0] read_offset=fields[199:168];
 wire [15:0] read_count=fields[215:200];
 wire [15:0] input_bytes={words,3'b000};
 wire [15:0] output_bytes={eowords,3'b000};
 wire [7:0] device_state=engine_busy?8'd2:complete?8'd3:verified?8'd1:8'd0;
 wire txvalid;wire [7:0] txbyte;wire [12:0] tx_mem_addr;
 wire txbusy;
 stage_lab_tx #(.TARGET(TARGET),.FIRST(FIRST)) reply(.clk(clk),.rst(rst),.send(send_start),
 .ready(send_ready),.kind(response_type),.length(response_length),.sequence(response_seq),
 .sid(sid),.case_id(case_id),.device_state(device_state),.flags(eflags),
 .input_words(words),.output_words(eowords),.stage(response_stage),.offset(response_offset),
 .count(response_count),.memory_addr(tx_mem_addr),.memory_word(mem_q),
 .tx_data(txbyte),.tx_valid(txvalid),.tx_ready(txready),.busy(txbusy));
 uart_tx_8n1 #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD)) ut(.clk(clk),.rst(rst),.data_in(txbyte),.data_valid(txvalid),.data_ready(txready),.tx_pin(uart_txd),.byte_done());
 always @(posedge clk)begin
  if(rst)begin
   state<=IDLE;frame_done<=0;rdindex<=0;field_index<=0;field_count<=0;fields<=0;
   sid<=0;case_id<=0;expected_seq<=0;last_seq<=0;last_crc<=0;last_type<=0;last_length<=0;last_valid<=0;
   words<=0;entry<=0;uploaded<=0;echoed<=0;active<=0;verified<=0;started<=0;complete<=0;
   host_addr<=0;host_we<=0;host_data<=0;host_waddr<=0;run_engine<=0;clear_engine<=0;
   copy_index<=0;upload_word<=0;send_start<=0;response_type<=0;response_length<=0;response_seq<=0;
   response_offset<=0;response_stage<=0;response_count<=0;
  end else begin
   frame_done<=0;host_we<=0;run_engine<=0;clear_engine<=0;send_start<=0;
   if(engine_done)complete<=1;
   if(txbusy)host_addr<=tx_mem_addr;
   case(state)
    IDLE:if(frame_ready)begin
     fields<=0;field_index<=0;field_count<=(flen>32)?32:flen[5:0];state<=(flen<16)?RELEASE:RSET;
    end
    RSET:begin rdindex<=9+field_index;state<=RWAIT;end
    RWAIT:state<=RSTORE;
    RSTORE:begin fields[8*field_index+:8]<=rdbyte;
     if(field_index+1'b1==field_count)state<=DECIDE;
     else begin field_index<=field_index+1'b1;state<=RSET;end
    end
    DECIDE:begin
     response_seq<=fseq;response_type<=7;response_length<=32;state<=TXSTART;
     if(fflags!=1 || flen<16)state<=RELEASE;
     else if(active && incoming_sid==sid && last_valid && fseq==last_seq && fcrc==last_crc && ftype==last_type && flen==last_length)begin
      response_type<=(ftype==3)?4:6;response_length<=(ftype==3)?(25+response_count):32;
     end else if(ftype==1 && opcode==8'h40 && fseq==0 && flen==24 && incoming_sid!=0 && !engine_busy &&
        fields[175:168]==FIRST-1 &&
        ((TARGET==1 && fields[191:176]>=128 && fields[191:176]<=4224 && fields[182:176]==0) ||
         (TARGET==2 && fields[191:176]>=256 && fields[191:176]<=4224 && fields[182:176]==0) || (TARGET>=3 && fields[191:176]==4096)))begin
      sid<=incoming_sid;case_id<=command_case;entry<=fields[170:168];words<=fields[188:176];
      uploaded<=0;echoed<=0;verified<=0;started<=0;complete<=0;clear_engine<=1;active<=1;
      expected_seq<=1;last_seq<=0;last_crc<=fcrc;last_type<=ftype;last_length<=flen;last_valid<=1;response_type<=6;
     end else if(!active || incoming_sid!=sid)state<=RELEASE;
     else if(fseq==expected_seq && fseq!=32'hffffffff)begin
      if(ftype==2 && !verified && !started && flen>=32 && data_case==case_id &&
         data_offset==uploaded && data_offset+flen-24<=input_bytes &&
         flen==24+((input_bytes-uploaded>480)?480:(input_bytes-uploaded)))begin
       copy_index<=24;upload_word<=0;state<=CSET;
      end else if(ftype==3 && flen==27 && data_case==case_id && !engine_busy &&
         read_offset[2:0]==0 && read_count>0 && read_count<=480 && read_count[2:0]==0 &&
         ((fields[167:160]==0 && !started && read_offset==echoed && read_offset+read_count<=input_bytes) ||
          (fields[167:160]==1 && complete && read_offset+read_count<=output_bytes)))begin
       response_type<=4;response_length<=25+read_count;response_offset<=read_offset;
       response_count<=read_count;response_stage<=fields[167:160];
       if(fields[167:160]==0)echoed<=echoed+read_count;
       expected_seq<=expected_seq+1'b1;last_valid<=1;last_seq<=fseq;last_crc<=fcrc;last_type<=ftype;last_length<=flen;
      end else if(ftype==1 && flen==21 && command_case==case_id &&
          ((opcode==3 && !started && uploaded==input_bytes && echoed==input_bytes) ||
           (opcode==4 && verified && !started) || opcode==5))begin
       if(opcode==3)verified<=1;
       if(opcode==4)begin started<=1;run_engine<=1;end
       response_type<=6;expected_seq<=expected_seq+1'b1;last_valid<=1;last_seq<=fseq;last_crc<=fcrc;last_type<=ftype;last_length<=flen;
      end
     end
    end
    CSET:begin rdindex<=9+copy_index;state<=CWAIT;end
    CWAIT:state<=CSTORE;
    CSTORE:begin
     upload_word[8*copy_index[2:0]+:8]<=rdbyte;
     if(copy_index[2:0]==7)begin
      host_we<=1;host_waddr<=(uploaded+copy_index-24)>>3;host_data<={rdbyte,upload_word[55:0]};
     end
     if(copy_index+1'b1==flen)begin
      uploaded<=uploaded+flen-24;expected_seq<=expected_seq+1'b1;
      last_valid<=1;last_seq<=fseq;last_crc<=fcrc;last_type<=ftype;last_length<=flen;
      response_type<=6;response_length<=32;state<=TXSTART;
     end else begin copy_index<=copy_index+1'b1;state<=CSET;end
    end
    TXSTART:if(send_ready)begin send_start<=1;state<=TXWAIT;end
    TXWAIT:if(txbusy)state<=RELEASE;
    RELEASE:if(!txbusy && !send_start)begin frame_done<=1;state<=RELEASE_WAIT;end
    RELEASE_WAIT:if(!frame_ready)state<=IDLE;
   endcase
  end
 end
endmodule

module stage_lab_tx #(parameter integer TARGET=4,FIRST=TARGET)(
 input clk,rst,send,output ready,input [7:0] kind,input [15:0] length,input [31:0] sequence,
 input [127:0] sid,input [31:0] case_id,input [7:0] device_state,input [15:0] flags,
 input [12:0] input_words,output_words,input [7:0] stage,input [31:0] offset,input [15:0] count,
 output [12:0] memory_addr,input [63:0] memory_word,
 output reg [7:0] tx_data,output tx_valid,input tx_ready,output reg busy);
 reg [9:0] pos;reg [31:0] crc;wire [31:0] final_crc=~crc;
 wire [31:0] byte_offset=offset+((pos>=38)?(pos-38):0);
 assign memory_addr=byte_offset[15:3];assign ready=!busy;assign tx_valid=busy;
 reg [9:0] n;
 function [31:0] crc_byte;input [31:0] c;input [7:0] v;integer j;reg [31:0] x;
 begin x=c^v;for(j=0;j<8;j=j+1)x=x[0]?((x>>1)^32'hedb88320):(x>>1);crc_byte=x;end endfunction
 always @*begin
  n=pos-13;tx_data=0;
  case(pos)
   0:tx_data=8'ha5;1:tx_data=8'h5a;2:tx_data=8'hc3;3:tx_data=8'h3c;
   4:tx_data=1;5:tx_data=kind;6:tx_data=1;
   7:tx_data=sequence[7:0];8:tx_data=sequence[15:8];9:tx_data=sequence[23:16];10:tx_data=sequence[31:24];
   11:tx_data=length[7:0];12:tx_data=length[15:8];
   default:begin
    if(pos>=13 && pos<13+length)begin
     if(n<16)tx_data=sid>>(8*n);
     else if(kind==4)begin
      if(n<20)tx_data=case_id>>(8*(n-16));
      else if(n==20)tx_data=stage;
      else if(n<25)tx_data=offset>>(8*(n-21));
      else tx_data=memory_word>>(8*byte_offset[2:0]);
     end else begin
      case(n)
       16,17,18,19:tx_data=sequence>>(8*(n-16));
       20:tx_data=TARGET;21:tx_data=device_state;22:tx_data=flags[7:0];23:tx_data=flags[15:8];
       24,25,26,27:tx_data=case_id>>(8*(n-24));
       28:tx_data=input_words[7:0];29:tx_data={3'd0,input_words[12:8]};
       30:tx_data=output_words[7:0];31:tx_data={3'd0,output_words[12:8]};
      endcase
     end
    end else if(pos>=13+length && pos<17+length)tx_data=final_crc>>(8*(pos-13-length));
   end
  endcase
 end
 always @(posedge clk)begin
  if(rst)begin busy<=0;pos<=0;crc<=32'hffffffff;end
  else if(!busy && send)begin busy<=1;pos<=0;crc<=32'hffffffff;end
  else if(busy && tx_ready)begin
   if(pos>=4 && pos<13+length)crc<=crc_byte(crc,tx_data);
   if(pos==16+length)begin busy<=0;pos<=0;end else pos<=pos+1'b1;
  end
 end
endmodule

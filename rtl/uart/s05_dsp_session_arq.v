// S05 R1 FPGA inbound session/stop-and-wait ARQ controller.
// Receives CRC-verified frames from s02_frame_echo(ECHO_MODE=0).
// Implements HELLO/OFFER, ACTIVATE/READY and inbound ACK/NACK.
// Full lab path: verified IQ, RUN, one reliable record per RESULT,
// COMMIT/ABORT, stage-4 Power readback and RELEASE.
// Missing/invalid CRC, old session, or incomplete frame never cause ACK.
// No terminal CPI decision/release or host journal is fabricated.
module s05_dsp_session_arq #(
    parameter integer TX_ACK_TIMEOUT_CLKS = 100000000,
    parameter integer TX_MAX_RETRIES = 3
)(
    input wire clk,
    input wire rst,
    output reg dsp_start, output reg dsp_clear,
    input wire dsp_busy,dsp_done,dsp_error,dsp_saturation,
    input wire result_valid,output wire result_ready,
    input wire [98:0] result_data,
    output reg [98:0] result_record,
    output reg [7:0] stage_kind,
    output reg [11:0] map_base,
    output reg [15:0] terminal_count,
    output wire map_read_enable,
    input wire frame_ready,
    output reg frame_done,
    input wire [7:0] frame_type,
    input wire [7:0] frame_flags,
    input wire [31:0] frame_seq,
    input wire [15:0] frame_length,
    input wire [31:0] frame_crc,
    output reg [9:0] rd_index,
    input wire [7:0] rd_byte,
    input wire reply_ready,
    output wire reply_valid,
    output reg [7:0] reply_type,
    output reg [7:0] reply_opcode,
    output reg [127:0] reply_sid,
    output reg [31:0] reply_seq,
    output reg [31:0] reply_number,
    output reg active_session,
    output reg [31:0] rx_expected_seq,
    output reg [31:0] activation_count,
    output reg [31:0] accepted_count,
    output reg [31:0] duplicate_count,
    output reg [31:0] stale_count,
    output reg [31:0] nack_count,
    output reg [31:0] cpi_id,
    output reg cpi_open,
    output reg [14:0] iq_uploaded_bytes,
    output reg iq_write_en,
    output reg [12:0] iq_write_addr,
    output reg [31:0] iq_write_data,
    output reg [14:0] iq_readback_acked_bytes,
    output reg [31:0] stage_cpi_id,
    output reg [31:0] stage_offset,
    output reg [15:0] stage_count,
    output reg [31:0] tx_next_seq,
    output reg tx_retry_exhausted
);
    localparam [3:0] IDLE=0, READ_SETUP=1, READ_WAIT=2,
                     READ_STORE=3, DECIDE=4, REPLY_START=5,
                     REPLY_BUSY=6, REPLY_DONE=7, RELEASE=8,
                     COPY_SETUP=9, COPY_WAIT=10, COPY_STORE=11,
                     COPY_END=12, STAGE_START=13, STAGE_BUSY=14;
    reg input_verified,running,finished,terminal_sent,terminal_acked,failed;
    reg [7:0] outbound_kind;
    reg [15:0] map_acked_bytes;
    reg [11:0] map_acked_words;
    reg [25:0] watchdog;
    wire [15:0] map_expected_count=(map_acked_bytes<16'd24480)?16'd480:16'd96;
    assign result_ready=running && !stage_pending && !stage_outstanding && !tx_retry_exhausted;
    assign map_read_enable=finished && !running;
    reg [3:0] state;
    reg [5:0] read_idx;
    reg [5:0] read_target;
    reg [215:0] fields;
    reg [127:0] sid;
    reg [127:0] retired_sid;
    reg retired_valid;
    reg pending;
    reg [31:0] last_seq;
    reg [31:0] last_crc;
    reg [15:0] last_length;
    reg [7:0] last_type;
    reg last_valid;
    reg reply_started;
    reg [9:0] copy_idx;
    reg [31:0] sample_word;
    reg [15:0] current_iq_size;
    reg stage_pending;
    reg stage_outstanding;
    reg [31:0] tx_ack_ticks;
    reg [2:0] tx_retries;
    wire [15:0] expected_read_count =
         (iq_readback_acked_bytes < 15'd16456) ? 16'd484 : 16'd440;
    wire [31:0] incoming_read_offset=fields[168 +: 32];
    wire [15:0] incoming_read_count=fields[200 +: 16];
    wire [31:0] incoming_cpi = fields[128 +: 32];
    wire [31:0] incoming_offset = fields[160 +: 32];
    wire [15:0] expected_chunk =
         (iq_uploaded_bytes < 15'd16592) ? 16'd488 : 16'd304;
    assign reply_valid=(state==REPLY_START) || (state==STAGE_START);

    // Embedded little-endian PC application payload: sid[0..15], opcode,
    // then CPI_ID at bytes 17..20. Header seq is already decoded by parser.
    wire [127:0] boot_sid = fields[16 +: 128];
    wire [127:0] active_sid = fields[0 +: 128];
    wire [7:0] app_opcode = fields[128 +: 8];
    wire [31:0] app_cpi_id = fields[136 +: 32];

    always @(posedge clk) begin
        if (rst) begin
            dsp_start<=0;dsp_clear<=0;input_verified<=0;running<=0;finished<=0;
            terminal_sent<=0;terminal_acked<=0;failed<=0;outbound_kind<=4;
            terminal_count<=0;result_record<=0;stage_kind<=0;map_base<=0;
            map_acked_bytes<=0;map_acked_words<=0;watchdog<=0;
            state<=IDLE;
            read_idx<=0;
            read_target<=0;
            rd_index<=0;
            fields<=0;
            frame_done<=0;
            reply_started<=0;
            reply_type<=0;
            reply_opcode<=0;
            reply_sid<=0;
            reply_seq<=0;
            reply_number<=0;
            active_session<=0;
            rx_expected_seq<=0;
            activation_count<=0;
            accepted_count<=0;
            duplicate_count<=0;
            stale_count<=0;
            nack_count<=0;
            cpi_id<=0;
            cpi_open<=0;
            iq_uploaded_bytes<=0;
            iq_write_en<=0;
            iq_write_addr<=0;
            iq_write_data<=0;
            copy_idx<=0;
            sample_word<=0;
            current_iq_size<=0;
            iq_readback_acked_bytes<=0;
            stage_cpi_id<=0;
            stage_offset<=0;
            stage_count<=0;
            tx_next_seq<=0;
            tx_retry_exhausted<=0;
            stage_pending<=0;
            stage_outstanding<=0;
            tx_ack_ticks<=0;
            tx_retries<=0;
            pending<=0;
            sid<=0;
            retired_sid<=0;
            retired_valid<=0;
            last_seq<=0;
            last_crc<=0;
            last_length<=0;
            last_type<=0;
            last_valid<=0;
        end else begin
            frame_done<=0;
            dsp_start<=0;dsp_clear<=0;
            iq_write_en<=0;
            if(running)begin
                if(!stage_pending && !stage_outstanding)watchdog<=watchdog+1'b1;
                if(dsp_error || dsp_saturation || watchdog==26'd49999999)begin
                    failed<=1;running<=0;finished<=1;dsp_clear<=1;
                end else if(dsp_done)begin running<=0;finished<=1;end
            end
            if(result_valid && result_ready)begin
                result_record<=result_data;terminal_count<=terminal_count+1'b1;
                outbound_kind<=5;stage_pending<=1;tx_retries<=0;tx_ack_ticks<=0;
            end
            if(finished && !terminal_sent && !stage_pending && !stage_outstanding)begin
                outbound_kind<=8;stage_pending<=1;terminal_sent<=1;
                tx_retries<=0;tx_ack_ticks<=0;
            end
            case(state)
                IDLE: if(frame_ready) begin
                    fields<=0;
                    read_idx<=0;
                    if(frame_length>27) read_target<=27;
                    else read_target<=frame_length[5:0];
                    if(frame_length==0) state<=DECIDE;
                    else state<=READ_SETUP;
                end else if(stage_pending && !stage_outstanding && reply_ready &&
                            !tx_retry_exhausted) begin
                    reply_type<=outbound_kind;
                    reply_sid<=sid;
                    reply_seq<=tx_next_seq;
                    reply_opcode<=failed?8'd7:8'd6;
                    reply_number<=0;
                    state<=STAGE_START;
                end else if(stage_outstanding && !tx_retry_exhausted) begin
                    if(tx_ack_ticks >= TX_ACK_TIMEOUT_CLKS-1) begin
                        tx_ack_ticks<=0;
                        if(tx_retries < TX_MAX_RETRIES) begin
                            tx_retries<=tx_retries+1'b1;
                            stage_outstanding<=0;
                            reply_type<=outbound_kind;
                            reply_opcode<=failed?8'd7:8'd6;
                            reply_sid<=sid;
                            reply_seq<=tx_next_seq;
                            state<=STAGE_START;
                        end else tx_retry_exhausted<=1;
                    end else tx_ack_ticks<=tx_ack_ticks+1'b1;
                end
                READ_SETUP: begin
                    rd_index<=10'd9+read_idx;
                    state<=READ_WAIT;
                end
                READ_WAIT: state<=READ_STORE;
                READ_STORE: begin
                    fields[8*read_idx +:8]<=rd_byte;
                    if(read_idx+1'b1==read_target)
                        state<=DECIDE;
                    else begin
                        read_idx<=read_idx+1'b1;
                        state<=READ_SETUP;
                    end
                end
                DECIDE: begin
                    // HELLO: 24B payload. Snapshot NO_RETAINED_STATE=0.
                    if(frame_type==9 && frame_flags==0 && frame_seq==0 &&
                       frame_length==24 && fields[7:0]==8'd1 &&
                       fields[15:8]==8'd1 && boot_sid!=0 &&
                       fields[151:144]==0 && fields[159:152]==0 &&
                       fields[191:160]==0) begin
                        if ((sid==boot_sid && (pending||active_session)) ||
                            (!cpi_open && (!retired_valid || boot_sid!=retired_sid))) begin
                            if(sid!=boot_sid) begin
                                if(sid!=0) begin
                                    retired_sid<=sid;
                                    retired_valid<=1;
                                end
                                sid<=boot_sid;
                                pending<=1;
                                active_session<=0;
                            end
                            reply_type<=9;
                            reply_opcode<=2;
                            reply_sid<=boot_sid;
                            reply_seq<=0;
                            reply_number<=0;
                            state<=REPLY_START;
                        end else begin
                            stale_count<=stale_count+1'b1;
                            state<=RELEASE;
                        end
                    end
                    // ACTIVATE: exact echoed OFFER snapshot, cpi_valid=0;
                    // same bytes can be repeated indefinitely after READY.
                    else if(frame_type==9 && frame_flags==0 && frame_seq==0 &&
                            frame_length==27 && fields[7:0]==8'd3 &&
                            fields[15:8]==8'd1 && boot_sid==sid && sid!=0 &&
                            fields[151:144]==0 &&
                            fields[215:152]==0 && (pending||active_session)) begin
                        if(pending && !active_session) begin
                            active_session<=1;
                            pending<=0;
                            rx_expected_seq<=0;
                            tx_next_seq<=0;
                            activation_count<=activation_count+1'b1;
                            accepted_count<=0;
                            last_valid<=0;
                        end
                        // No mutation of counters or CPI on duplicate.
                        reply_type<=9;
                        reply_opcode<=4;
                        reply_sid<=sid;
                        reply_seq<=0;
                        reply_number<=0;
                        state<=REPLY_START;
                    end
                    else if(frame_type==9) begin
                        stale_count<=stale_count+1'b1;
                        state<=RELEASE;
                    end
                    // Active application frame: first compare full epoch.
                    else if(!active_session || frame_flags!=1 ||
                            frame_length<16 || active_sid!=sid) begin
                        stale_count<=stale_count+1'b1;
                        state<=RELEASE;
                    end
                    else if(frame_type==6 || frame_type==7) begin
                        // Never acknowledge an ACK/NACK (no ACK-of-ACK).
                        // Only exact current outbound STAGE_DATA may clear
                        // replay reservation or trigger a bounded replay.
                        if(frame_length==20 && stage_outstanding &&
                           frame_seq==tx_next_seq &&
                           fields[128 +: 32]==tx_next_seq) begin
                            if(frame_type==6) begin
                                stage_outstanding<=0;
                                stage_pending<=0;
                                tx_next_seq<=tx_next_seq+1'b1;
                                if(outbound_kind==4)begin
                                    if(stage_kind==0)iq_readback_acked_bytes<=iq_readback_acked_bytes+stage_count;
                                    else begin
                                        map_acked_bytes<=map_acked_bytes+stage_count;
                                        map_acked_words<=map_acked_words+((stage_count==480)?12'd80:12'd16);
                                    end
                                end
                                if(outbound_kind==8)terminal_acked<=1;
                                tx_retries<=0;
                                tx_ack_ticks<=0;
                                tx_retry_exhausted<=0;
                            end else if(tx_retries<TX_MAX_RETRIES) begin
                                stage_outstanding<=0;
                                tx_retries<=tx_retries+1'b1;
                                tx_ack_ticks<=0;
                            end else tx_retry_exhausted<=1;
                        end
                        state<=RELEASE;
                    end else begin
                        reply_type<=7; // Default is explicit NACK.
                        reply_opcode<=0;
                        reply_sid<=sid;
                        reply_seq<=frame_seq;
                        reply_number<=rx_expected_seq;
                        state<=REPLY_START;
                        if(frame_seq==rx_expected_seq && frame_seq!=32'hFFFFFFFF &&
                           frame_type==3 && frame_length==27 &&
                           cpi_open && !running && iq_uploaded_bytes==15'd16896 &&
                           !stage_pending && !stage_outstanding &&
                           incoming_cpi==cpi_id &&
                           ((fields[167:160]==8'd0 && !input_verified &&
                             iq_readback_acked_bytes<16896 &&
                             incoming_read_offset=={17'd0,iq_readback_acked_bytes} &&
                             incoming_read_count==expected_read_count) ||
                            (fields[167:160]==8'd4 && terminal_acked && !failed &&
                             map_acked_bytes<24576 &&
                             incoming_read_offset=={16'd0,map_acked_bytes} &&
                             incoming_read_count==map_expected_count))) begin
                            stage_cpi_id<=cpi_id;
                            stage_offset<=incoming_read_offset;
                            stage_count<=incoming_read_count;
                            stage_kind<=fields[167:160];map_base<=map_acked_words;
                            outbound_kind<=4;
                            stage_pending<=1;
                            tx_retries<=0;
                            tx_ack_ticks<=0;
                            rx_expected_seq<=rx_expected_seq+1'b1;
                            accepted_count<=accepted_count+1'b1;
                            last_valid<=1;
                            last_seq<=frame_seq;
                            last_crc<=frame_crc;
                            last_type<=frame_type;
                            last_length<=frame_length;
                            reply_type<=6;
                            reply_number<=frame_seq;
                        end else if(frame_seq==rx_expected_seq && frame_seq!=32'hFFFFFFFF &&
                           frame_type==2 && cpi_open && !input_verified && !running &&
                           iq_uploaded_bytes<15'd16896 &&
                           incoming_cpi==cpi_id &&
                           incoming_offset=={17'd0,iq_uploaded_bytes} &&
                           frame_length==(16'd24+expected_chunk)) begin
                            // CRC is already verified. Copy to CPI memory
                            // before acknowledging or advancing seq.
                            copy_idx<=10'd24;
                            sample_word<=0;
                            current_iq_size<=expected_chunk;
                            state<=COPY_SETUP;
                        end else if(frame_seq==rx_expected_seq && frame_seq!=32'hFFFFFFFF &&
                           frame_type==1 && frame_length==21 &&
                           app_opcode==8'd1 && !cpi_open) begin
                            cpi_open<=1;
                            cpi_id<=app_cpi_id;
                            rx_expected_seq<=rx_expected_seq+1'b1;
                            accepted_count<=accepted_count+1'b1;
                            last_valid<=1;
                            last_seq<=frame_seq;
                            last_crc<=frame_crc;
                            last_type<=frame_type;
                            last_length<=frame_length;
                            reply_type<=6;
                            reply_number<=frame_seq;
                        end else if(frame_seq==rx_expected_seq && frame_seq!=32'hFFFFFFFF &&
                           frame_type==1 && frame_length==21 && cpi_open &&
                           app_cpi_id==cpi_id &&
                           ((app_opcode==3 && !input_verified && iq_readback_acked_bytes==16896) ||
                            (app_opcode==4 && input_verified && !running && !finished) ||
                            (app_opcode==5 && terminal_acked && !stage_pending && !stage_outstanding) ||
                            (app_opcode==6 && terminal_acked && !stage_pending && !stage_outstanding)))begin
                            if(app_opcode==3)input_verified<=1;
                            if(app_opcode==4)begin
                                running<=1;dsp_start<=1;watchdog<=0;
                            end
                            if(app_opcode==5)begin
                                outbound_kind<=8;stage_pending<=1;tx_retries<=0;tx_ack_ticks<=0;
                            end
                            if(app_opcode==6)begin
                                cpi_open<=0;input_verified<=0;finished<=0;terminal_sent<=0;
                                terminal_acked<=0;failed<=0;terminal_count<=0;dsp_clear<=1;
                                iq_uploaded_bytes<=0;iq_readback_acked_bytes<=0;
                                map_acked_bytes<=0;map_acked_words<=0;
                            end
                            rx_expected_seq<=rx_expected_seq+1'b1;
                            accepted_count<=accepted_count+1'b1;
                            last_valid<=1;last_seq<=frame_seq;last_crc<=frame_crc;
                            last_type<=frame_type;last_length<=frame_length;
                            reply_type<=6;reply_number<=frame_seq;
                        end else if(last_valid && frame_seq==last_seq &&
                                    frame_crc==last_crc && frame_length==last_length &&
                                    frame_type==last_type) begin
                            duplicate_count<=duplicate_count+1'b1;
                            reply_type<=6;
                            reply_number<=frame_seq;
                        end else nack_count<=nack_count+1'b1;
                    end
                end
                COPY_SETUP: begin
                    rd_index<=10'd9+copy_idx;
                    state<=COPY_WAIT;
                end
                COPY_WAIT: state<=COPY_STORE;
                COPY_STORE: begin
                    case ((copy_idx-10'd24) & 10'd3)
                        0: sample_word[7:0]<=rd_byte;
                        1: sample_word[15:8]<=rd_byte;
                        2: sample_word[23:16]<=rd_byte;
                        3: begin
                            iq_write_en<=1;
                            iq_write_addr<=
                               (iq_uploaded_bytes+(copy_idx-10'd24)) >> 2;
                            iq_write_data<={rd_byte,sample_word[23:0]};
                        end
                    endcase
                    if(copy_idx+1'b1==frame_length) state<=COPY_END;
                    else begin
                        copy_idx<=copy_idx+1'b1;
                        state<=COPY_SETUP;
                    end
                end
                COPY_END: begin
                    iq_uploaded_bytes<=iq_uploaded_bytes+current_iq_size;
                    rx_expected_seq<=rx_expected_seq+1'b1;
                    accepted_count<=accepted_count+1'b1;
                    last_valid<=1;
                    last_seq<=frame_seq;
                    last_crc<=frame_crc;
                    last_type<=frame_type;
                    last_length<=frame_length;
                    reply_type<=6;
                    reply_seq<=frame_seq;
                    reply_number<=frame_seq;
                    state<=REPLY_START;
                end
                REPLY_START: if(reply_ready) begin
                    reply_started<=0;
                    state<=REPLY_BUSY;
                end
                REPLY_BUSY: begin
                    if(!reply_ready) reply_started<=1;
                    else if(reply_started) state<=RELEASE;
                end
                RELEASE: begin
                    frame_done<=1;
                    state<=REPLY_DONE;
                end
                REPLY_DONE: if(!frame_ready) state<=IDLE;
                STAGE_START: if(reply_ready) begin
                    reply_started<=0;
                    state<=STAGE_BUSY;
                end
                STAGE_BUSY: begin
                    if(!reply_ready) reply_started<=1;
                    else if(reply_started) begin
                        stage_outstanding<=1;
                        tx_ack_ticks<=0;
                        state<=IDLE;
                    end
                end
                default: state<=IDLE;
            endcase
        end
    end
endmodule

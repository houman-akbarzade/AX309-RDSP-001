// AX309 S05: sends an S02/R1 OFFER, READY, ACK or NACK wire frame.
// All 8N1 byte pacing uses the existing uart_tx_8n1. CRC-32/ISO-HDLC:
// init FFFFFFFF, reflected poly EDB88320, final ones' complement.
// No RAM, simulation tasks, or inferred latch.
module s05_dsp_reply_tx (
    input wire clk,
    input wire rst,
    input wire send_valid,
    output wire send_ready,
    input wire [7:0] response_type, // 9 SESSION_CONTROL, 6 ACK, 7 NACK
    input wire [7:0] response_opcode, // 2 OFFER, 4 READY
    input wire [127:0] response_sid,
    input wire [31:0] response_seq,
    input wire [31:0] response_number,
    // STAGE_DATA=4: raw-IQ bytewise readback from banked CPI RAM.
    input wire [31:0] stage_cpi_id,
    input wire [31:0] stage_offset,
    input wire [15:0] stage_count,
    input wire [7:0] stage_kind,
    input wire [11:0] map_base,
    output reg [11:0] map_read_addr,
    input wire [45:0] map_read_power,
    input wire [98:0] result_record,
    input wire [15:0] terminal_count,
    output wire [12:0] iq_read_addr,
    input wire [31:0] iq_read_word,
    output wire [7:0] tx_data,
    output wire tx_valid,
    input wire tx_ready,
    output wire busy
);
    reg [7:0] stage_kind_q;
    reg [2:0] map_lane;
    reg [98:0] record_q;
    reg [15:0] count_q;
    wire [47:0] map_word={2'b0,map_read_power};
    wire [7:0] stage_byte=(stage_kind_q==0)?iq_byte:(map_word >> (8*map_lane));
    reg active;
    reg [9:0] pos;
    reg [15:0] payload_length;
    reg [7:0] kind;
    reg [7:0] opcode;
    reg [127:0] sid;
    reg [31:0] seq;
    reg [31:0] number;
    reg [31:0] stage_id_latched;
    reg [31:0] stage_offset_latched;
    reg [15:0] stage_count_latched;
    reg [31:0] crc_state;
    wire [31:0] iq_byte_offset = stage_offset_latched +
                     ((pos>=10'd38) ? {22'd0,(pos-10'd38)} : 32'd0);
    assign iq_read_addr=iq_byte_offset[14:2];
    wire [7:0] iq_byte = (iq_read_word >> (8*iq_byte_offset[1:0])) & 8'hff;
    wire [9:0] frame_len = 10'd17 + payload_length[9:0];
    wire [7:0] current_byte;
    assign send_ready = !active;
    assign busy = active;
    assign tx_valid = active;

    function [31:0] crc32_byte;
        input [31:0] crc_in;
        input [7:0] value;
        reg [31:0] x;
        integer j;
        begin
            x = crc_in ^ {24'd0,value};
            for (j=0;j<8;j=j+1)
                if (x[0]) x = (x >> 1) ^ 32'hEDB88320;
                else x = x >> 1;
            crc32_byte=x;
        end
    endfunction
    function [7:0] payload_octet;
        input [9:0] n;
        input [7:0] t;
        input [7:0] op;
        input [127:0] s;
        input [31:0] serial;
        input [31:0] stage_id;
        input [31:0] stage_base;
        input [7:0] data_octet;
        input [7:0] sk;
        input [98:0] rec;
        input [15:0] cnt;
        begin
            payload_octet=0;
            if (t == 9) begin
                case(n)
                    0: payload_octet=op;
                    1: payload_octet=8'd1;
                    default: begin
                        if (n>=2 && n<18)
                            payload_octet = (s >> (8*(n-2))) & 8'hff;
                        // OFFER snapshot kind=0, valid=0, ID=0, info=0;
                        // READY result=0, snapshot=0. No retained CPI yet.
                    end
                endcase
            end else if (t==4) begin
                if(n<16) payload_octet=(s >> (8*n)) & 8'hff;
                else if(n<20) payload_octet=(stage_id >> (8*(n-16))) & 8'hff;
                else if(n==20) payload_octet=sk; // stage_id=0 raw IQ
                else if(n<25) payload_octet=(stage_base >> (8*(n-21))) & 8'hff;
                else payload_octet=data_octet;
            end else if(t==5 || t==8) begin
                if(n<16)payload_octet=(s >> (8*n)) & 8'hff;
                else if(t==5)begin
                    if(n<20)payload_octet=(stage_id >> (8*(n-16))) & 8'hff;
                    else payload_octet=(rec >> (8*(n-20))) & 8'hff;
                end else begin
                    if(n==16)payload_octet=op;
                    else if(n<21)payload_octet=(stage_id >> (8*(n-17))) & 8'hff;
                    else payload_octet=(cnt >> (8*(n-21))) & 8'hff;
                end
            end else begin
                if (n<16) payload_octet=(s >> (8*n)) & 8'hff;
                else if (n<20) payload_octet=(serial >> (8*(n-16))) & 8'hff;
            end
        end
    endfunction
    function [7:0] wire_octet;
        input [9:0] index;
        input [15:0] len;
        input [7:0] t;
        input [7:0] op;
        input [127:0] s;
        input [31:0] sequence;
        input [31:0] acknum;
        input [31:0] crc_reg;
        input [31:0] stage_id;
        input [31:0] stage_base;
        input [7:0] stage_data_byte;
        input [7:0] sk;
        input [98:0] rec;
        input [15:0] cnt;
        reg [31:0] final_crc;
        begin
            final_crc=~crc_reg;
            wire_octet=0;
            case (index)
                0: wire_octet=8'hA5;
                1: wire_octet=8'h5A;
                2: wire_octet=8'hC3;
                3: wire_octet=8'h3C;
                4: wire_octet=8'h01;
                5: wire_octet=t;
                6: wire_octet=(t==9) ? 8'h00 : 8'h01;
                7: wire_octet=sequence[7:0];
                8: wire_octet=sequence[15:8];
                9: wire_octet=sequence[23:16];
                10: wire_octet=sequence[31:24];
                11: wire_octet=len[7:0];
                12: wire_octet=len[15:8];
                default:
                    if (index >= 13 && index < (13+len))
                        wire_octet=payload_octet(index-13,t,op,s,acknum,
                                                 stage_id,stage_base,stage_data_byte,sk,rec,cnt);
                    else if (index >= 13+len && index < 17+len)
                        wire_octet=(final_crc >> (8*(index-13-len))) & 8'hff;
            endcase
        end
    endfunction

    assign current_byte=wire_octet(pos,payload_length,kind,opcode,
                                   sid,seq,number,crc_state,
                                   stage_id_latched,stage_offset_latched,stage_byte,stage_kind_q,record_q,count_q);
    assign tx_data=current_byte;

    always @(posedge clk) begin
        if (rst) begin
            stage_kind_q<=0;map_read_addr<=0;map_lane<=0;record_q<=0;count_q<=0;
            active<=0;
            pos<=0;
            payload_length<=0;
            kind<=0;
            opcode<=0;
            sid<=0;
            seq<=0;
            number<=0;
            stage_id_latched<=0;
            stage_offset_latched<=0;
            stage_count_latched<=0;
            crc_state<=32'hFFFFFFFF;
        end else begin
            if (!active && send_valid) begin
                stage_kind_q<=stage_kind;map_read_addr<=map_base;map_lane<=0;
                record_q<=result_record;count_q<=terminal_count;
                active<=1;
                pos<=0;
                payload_length<=(response_type==9) ?
                                 ((response_opcode==2) ? 16'd26 : 16'd27) :
                                 (response_type==4) ? (16'd25+stage_count) :
                                 (response_type==5) ? 16'd33 :
                                 (response_type==8) ? 16'd23 :
                                 16'd20;
                kind<=response_type;
                opcode<=response_opcode;
                sid<=response_sid;
                seq<=response_seq;
                number<=response_number;
                stage_id_latched<=stage_cpi_id;
                stage_offset_latched<=stage_offset;
                stage_count_latched<=stage_count;
                crc_state<=32'hFFFFFFFF;
            end else if (active && tx_ready) begin
                if(kind==4 && stage_kind_q!=0 && pos>=38 && pos<13+payload_length)begin
                    if(map_lane==5)begin map_lane<=0;map_read_addr<=map_read_addr+1'b1;end
                    else map_lane<=map_lane+1'b1;
                end
                if (pos>=4 && pos<(13+payload_length))
                    crc_state<=crc32_byte(crc_state,current_byte);
                if (pos == frame_len-1'b1) begin
                    active<=0;
                    pos<=0;
                end else pos<=pos+1'b1;
            end
        end
    end
endmodule

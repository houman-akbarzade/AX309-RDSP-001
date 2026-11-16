-- AUTO-TRANSLATED from uart/s05_dsp_reply_tx.v; independent validation REQUIRED.
-- Source SHA256: e5468822610d807f0c89ba22457c5729ad8c211bd839fd9369a70208c215075f
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity s05_dsp_reply_tx is
    port (
        clk : in std_logic;
        rst : in std_logic;
        send_valid : in std_logic;
        send_ready : out std_logic;
        response_type : in std_logic_vector(7 downto 0);
        response_opcode : in std_logic_vector(7 downto 0);
        response_sid : in std_logic_vector(127 downto 0);
        response_seq : in std_logic_vector(31 downto 0);
        response_number : in std_logic_vector(31 downto 0);
        stage_cpi_id : in std_logic_vector(31 downto 0);
        stage_offset : in std_logic_vector(31 downto 0);
        stage_count : in std_logic_vector(15 downto 0);
        stage_kind : in std_logic_vector(7 downto 0);
        map_base : in std_logic_vector(11 downto 0);
        map_read_addr : out std_logic_vector(11 downto 0);
        map_read_power : in std_logic_vector(45 downto 0);
        result_record : in std_logic_vector(98 downto 0);
        terminal_count : in std_logic_vector(15 downto 0);
        iq_read_addr : out std_logic_vector(12 downto 0);
        iq_read_word : in std_logic_vector(31 downto 0);
        tx_data : out std_logic_vector(7 downto 0);
        tx_valid : out std_logic;
        tx_ready : in std_logic;
        busy : out std_logic
    );
end entity s05_dsp_reply_tx;

architecture rtl of s05_dsp_reply_tx is
    signal stage_kind_q : std_logic_vector(7 downto 0);
    signal map_lane : std_logic_vector(2 downto 0);
    signal record_q : std_logic_vector(98 downto 0);
    signal count_q : std_logic_vector(15 downto 0);
    signal map_word : std_logic_vector(47 downto 0);
    signal stage_byte : std_logic_vector(7 downto 0);
    signal active : std_logic;
    signal pos : std_logic_vector(9 downto 0);
    signal payload_length : std_logic_vector(15 downto 0);
    signal kind : std_logic_vector(7 downto 0);
    signal opcode : std_logic_vector(7 downto 0);
    signal sid : std_logic_vector(127 downto 0);
    signal seq : std_logic_vector(31 downto 0);
    signal number : std_logic_vector(31 downto 0);
    signal stage_id_latched : std_logic_vector(31 downto 0);
    signal stage_offset_latched : std_logic_vector(31 downto 0);
    signal stage_count_latched : std_logic_vector(15 downto 0);
    signal crc_state : std_logic_vector(31 downto 0);
    signal iq_byte_offset : std_logic_vector(31 downto 0);
    signal iq_byte : std_logic_vector(7 downto 0);
    signal iq_word_shifted : std_logic_vector(31 downto 0);
    signal frame_len : std_logic_vector(9 downto 0);
    signal current_byte : std_logic_vector(7 downto 0);
    signal map_read_addr_reg : std_logic_vector(11 downto 0);

    impure function crc32_byte(crc_in : std_logic_vector(31 downto 0); value : std_logic_vector(7 downto 0)) return std_logic_vector is
        variable crc32_byte_result : std_logic_vector(31 downto 0);
        variable x : std_logic_vector(31 downto 0);
    begin
        x := (crc_in) xor (std_logic_vector'(std_logic_vector(to_unsigned(0, 24)) & value));
        for j in 0 to 7 loop
            if x(0) = '1' then
                x := (std_logic_vector(shift_right(unsigned(x), 1))) xor ("11101101101110001000001100100000");
            else
                x := std_logic_vector(shift_right(unsigned(x), 1));
            end if;
        end loop;
        crc32_byte_result := x;
        return crc32_byte_result;
    end function crc32_byte;

    -- Right-shift by a whole number of bytes and truncate to the low byte.
    -- The shift and truncation match Verilog's 8-bit assignment semantics.
    function octet_at(data : std_logic_vector; n : natural) return std_logic_vector is
        variable shifted : unsigned(data'length-1 downto 0);
    begin
        shifted := shift_right(unsigned(data), 8*n);
        return std_logic_vector(resize(shifted,8));
    end function;

    function payload_octet(n : std_logic_vector(9 downto 0);
           t : std_logic_vector(7 downto 0); op : std_logic_vector(7 downto 0);
           s : std_logic_vector(127 downto 0);
           serial : std_logic_vector(31 downto 0);
           stage_id : std_logic_vector(31 downto 0);
           stage_base : std_logic_vector(31 downto 0);
           data_octet : std_logic_vector(7 downto 0);
           sk : std_logic_vector(7 downto 0);
           rec : std_logic_vector(98 downto 0);
           cnt : std_logic_vector(15 downto 0)) return std_logic_vector is
        variable result_byte : std_logic_vector(7 downto 0) := (others=>'0');
        variable ix : integer range 0 to 1023;
    begin
        ix := to_integer(unsigned(n));
        if unsigned(t)=to_unsigned(9,8) then
            if ix=0 then result_byte := op;
            elsif ix=1 then result_byte := x"01";
            elsif ix>=2 and ix<18 then result_byte := octet_at(s,ix-2);
            end if;
        elsif unsigned(t)=to_unsigned(4,8) then
            if ix<16 then result_byte := octet_at(s,ix);
            elsif ix<20 then result_byte := octet_at(stage_id,ix-16);
            elsif ix=20 then result_byte := sk;
            elsif ix<25 then result_byte := octet_at(stage_base,ix-21);
            else result_byte := data_octet;
            end if;
        elsif unsigned(t)=to_unsigned(5,8) or unsigned(t)=to_unsigned(8,8) then
            if ix<16 then result_byte := octet_at(s,ix);
            elsif unsigned(t)=to_unsigned(5,8) then
                if ix<20 then result_byte := octet_at(stage_id,ix-16);
                else result_byte := octet_at(rec,ix-20);end if;
            else
                if ix=16 then result_byte := op;
                elsif ix<21 then result_byte := octet_at(stage_id,ix-17);
                else result_byte := octet_at(cnt,ix-21);end if;
            end if;
        else
            if ix<16 then result_byte := octet_at(s,ix);
            elsif ix<20 then result_byte := octet_at(serial,ix-16);end if;
        end if;
        return result_byte;
    end function payload_octet;

    impure function wire_octet(index : std_logic_vector(9 downto 0); len : std_logic_vector(15 downto 0); t : std_logic_vector(7 downto 0); op : std_logic_vector(7 downto 0); s : std_logic_vector(127 downto 0); sequence : std_logic_vector(31 downto 0); acknum : std_logic_vector(31 downto 0); crc_reg : std_logic_vector(31 downto 0); stage_id : std_logic_vector(31 downto 0); stage_base : std_logic_vector(31 downto 0); stage_data_byte : std_logic_vector(7 downto 0); sk : std_logic_vector(7 downto 0); rec : std_logic_vector(98 downto 0); cnt : std_logic_vector(15 downto 0)) return std_logic_vector is
        variable wire_octet_result : std_logic_vector(7 downto 0);
        variable final_crc : std_logic_vector(31 downto 0);
    begin
        final_crc := not crc_reg;
        wire_octet_result := std_logic_vector(to_unsigned(0, 8));
        case index is
            when "0000000000" =>
                wire_octet_result := std_logic_vector(to_unsigned(165, 8));
            when "0000000001" =>
                wire_octet_result := std_logic_vector(to_unsigned(90, 8));
            when "0000000010" =>
                wire_octet_result := std_logic_vector(to_unsigned(195, 8));
            when "0000000011" =>
                wire_octet_result := std_logic_vector(to_unsigned(60, 8));
            when "0000000100" =>
                wire_octet_result := std_logic_vector(to_unsigned(1, 8));
            when "0000000101" =>
                wire_octet_result := t;
            when "0000000110" =>
                if unsigned(t) = to_unsigned(9, 8) then
    wire_octet_result := std_logic_vector(to_unsigned(0, 8));
else
    wire_octet_result := std_logic_vector(to_unsigned(1, 8));
end if;
            when "0000000111" =>
                wire_octet_result := sequence(7 downto 0);
            when "0000001000" =>
                wire_octet_result := sequence(15 downto 8);
            when "0000001001" =>
                wire_octet_result := sequence(23 downto 16);
            when "0000001010" =>
                wire_octet_result := sequence(31 downto 24);
            when "0000001011" =>
                wire_octet_result := len(7 downto 0);
            when "0000001100" =>
                wire_octet_result := len(15 downto 8);
            when others =>
                if (unsigned(index) >= to_unsigned(13, 10)) and (resize(unsigned(index), 16) < unsigned(std_logic_vector(to_unsigned(13, 16) + unsigned(len)))) then
                    wire_octet_result := payload_octet(std_logic_vector(resize(unsigned(index), 10) - to_unsigned(13, 10)), t, op, s, acknum, stage_id, stage_base, stage_data_byte, sk, rec, cnt);
                elsif (resize(unsigned(index), 16) >= unsigned(std_logic_vector(to_unsigned(13, 16) + unsigned(len)))) and (resize(unsigned(index), 16) < unsigned(std_logic_vector(to_unsigned(17, 16) + unsigned(len)))) then
                    wire_octet_result := octet_at(final_crc,
                       to_integer(unsigned(index))-13-to_integer(unsigned(len)));
                end if;
        end case;
        return wire_octet_result;
    end function wire_octet;

begin

    map_word <= std_logic_vector'("00" & map_read_power);
    stage_byte <= iq_byte when unsigned(stage_kind_q) = to_unsigned(0, 8) else std_logic_vector(resize(unsigned(std_logic_vector(shift_right(unsigned(map_word), to_integer(unsigned(std_logic_vector(unsigned(map_lane) * 8)))))), 8));
    iq_byte_offset <= std_logic_vector(unsigned(stage_offset_latched) +
            resize(unsigned(pos)-to_unsigned(38,10),32))
            when unsigned(pos)>=to_unsigned(38,10) else stage_offset_latched;
    iq_word_shifted <= std_logic_vector(shift_right(unsigned(iq_read_word), 8*to_integer(unsigned(iq_byte_offset(1 downto 0)))));
    iq_byte <= iq_word_shifted(7 downto 0);
    frame_len <= std_logic_vector(resize(unsigned(std_logic_vector(to_unsigned(17, 10))), 10) + resize(unsigned(payload_length(9 downto 0)), 10));
    iq_read_addr <= iq_byte_offset(14 downto 2);
    send_ready <= '1' when not (active = '1') else '0';
    busy <= active;
    tx_valid <= active;
    current_byte <= wire_octet(pos, payload_length, kind, opcode, sid, seq, number, crc_state, stage_id_latched, stage_offset_latched, stage_byte, stage_kind_q, record_q, count_q);
    tx_data <= current_byte;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                stage_kind_q <= std_logic_vector(to_unsigned(0, 8));
                map_read_addr_reg <= std_logic_vector(to_unsigned(0, 12));
                map_lane <= std_logic_vector(to_unsigned(0, 3));
                record_q <= std_logic_vector(to_unsigned(0, 99));
                count_q <= std_logic_vector(to_unsigned(0, 16));
                active <= '0';
                pos <= std_logic_vector(to_unsigned(0, 10));
                payload_length <= std_logic_vector(to_unsigned(0, 16));
                kind <= std_logic_vector(to_unsigned(0, 8));
                opcode <= std_logic_vector(to_unsigned(0, 8));
                sid <= std_logic_vector(to_unsigned(0, 128));
                seq <= std_logic_vector(to_unsigned(0, 32));
                number <= std_logic_vector(to_unsigned(0, 32));
                stage_id_latched <= std_logic_vector(to_unsigned(0, 32));
                stage_offset_latched <= std_logic_vector(to_unsigned(0, 32));
                stage_count_latched <= std_logic_vector(to_unsigned(0, 16));
                crc_state <= "11111111111111111111111111111111";
            else
                if (not (active = '1')) and (send_valid = '1') then
                    stage_kind_q <= stage_kind;
                    map_read_addr_reg <= map_base;
                    map_lane <= std_logic_vector(to_unsigned(0, 3));
                    record_q <= result_record;
                    count_q <= terminal_count;
                    active <= '1';
                    pos <= std_logic_vector(to_unsigned(0, 10));
                    if unsigned(response_type) = to_unsigned(9, 8) then
    if unsigned(response_opcode) = to_unsigned(2,8) then
        payload_length <= std_logic_vector(to_unsigned(26,16));
    else
        payload_length <= std_logic_vector(to_unsigned(27,16));
    end if;
else
    if unsigned(response_type)=to_unsigned(4,8) then
        payload_length <= std_logic_vector(to_unsigned(25,16)+unsigned(stage_count));
    elsif unsigned(response_type)=to_unsigned(5,8) then
        payload_length <= std_logic_vector(to_unsigned(33,16));
    elsif unsigned(response_type)=to_unsigned(8,8) then
        payload_length <= std_logic_vector(to_unsigned(23,16));
    else
        payload_length <= std_logic_vector(to_unsigned(20,16));
    end if;
end if;
                    kind <= response_type;
                    opcode <= response_opcode;
                    sid <= response_sid;
                    seq <= response_seq;
                    number <= response_number;
                    stage_id_latched <= stage_cpi_id;
                    stage_offset_latched <= stage_offset;
                    stage_count_latched <= stage_count;
                    crc_state <= "11111111111111111111111111111111";
                elsif (active = '1') and (tx_ready = '1') then
                    if (((unsigned(kind) = to_unsigned(4, 8)) and (unsigned(stage_kind_q) /= to_unsigned(0, 8))) and (unsigned(pos) >= to_unsigned(38, 10))) and (resize(unsigned(pos), 16) < unsigned(std_logic_vector(to_unsigned(13, 16) + unsigned(payload_length)))) then
                        if unsigned(map_lane) = to_unsigned(5, 3) then
                            map_lane <= std_logic_vector(to_unsigned(0, 3));
                            map_read_addr_reg <= std_logic_vector(resize(unsigned(map_read_addr_reg), 12) + to_unsigned(1, 12));
                        else
                            map_lane <= std_logic_vector(resize(unsigned(map_lane), 3) + to_unsigned(1, 3));
                        end if;
                    end if;
                    if (unsigned(pos) >= to_unsigned(4, 10)) and (resize(unsigned(pos), 16) < unsigned(std_logic_vector(to_unsigned(13, 16) + unsigned(payload_length)))) then
                        crc_state <= crc32_byte(crc_state, current_byte);
                    end if;
                    if unsigned(pos) = unsigned(std_logic_vector(unsigned(frame_len) - to_unsigned(1, 10))) then
                        active <= '0';
                        pos <= std_logic_vector(to_unsigned(0, 10));
                    else
                        pos <= std_logic_vector(resize(unsigned(pos), 10) + to_unsigned(1, 10));
                    end if;
                end if;
            end if;
        end if;
    end process;

    map_read_addr <= map_read_addr_reg;

end architecture rtl;

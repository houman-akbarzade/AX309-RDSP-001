#!/usr/bin/env python3
"""Explicit VHDL-93 byte extraction for S05 UART reply formatter.
Manual translation of source Verilog functions; preserves exact byte offsets.
"""
from pathlib import Path
p=Path(__file__).parent/'src/uart/s05_dsp_reply_tx.vhd'
s=p.read_text()
start=s.index('    impure function payload_octet(')
end=s.index('    impure function wire_octet(',start)
replacement='''    -- Right-shift by a whole number of bytes and truncate to the low byte.
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

'''
s=s[:start]+replacement+s[end:]
# Final CRC byte extraction was emitted as 32-bit expression assigned to 8-bit return.
start=s.index('                    wire_octet_result := (std_logic_vector(shift_right(unsigned(final_crc),')
end=s.index(';',start)
s=s[:start]+'''                    wire_octet_result := octet_at(final_crc,
                       to_integer(unsigned(index))-13-to_integer(unsigned(len)))'''+s[end:]
p.write_text(s)
print('Updated UART byte extraction')

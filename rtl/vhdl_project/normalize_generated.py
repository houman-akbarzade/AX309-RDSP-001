#!/usr/bin/env python3
"""Fix predictable Verilog-to-VHDL syntax/type differences without editing RTL.
Only operates inside rtl/vhdl_project/src. Generated outputs are *not* yet
considered functionally equivalent; exhaustive validation is separate.
"""
from pathlib import Path
import re
R=Path(__file__).resolve().parent/'src'
def update(rel,fn):
 p=R/rel;s=p.read_text();t=fn(s)
 if s!=t:p.write_text(t)
 print(rel,'changed',s!=t)

def rom(s):
 return re.sub(r'-std_logic_vector\(to_unsigned\((\d+),\s*16\)\)',
               lambda m:'std_logic_vector(to_signed(-'+m.group(1)+', 16))',s)
update('mf16/mf16_coeff_rom.vhd',rom)

def grouping(s):
 start=s.index('    merged_stat <= ')
 end=s.index('    choose_current <= ',start)
 s=s[:start]+'''
    -- Preserve each field's own conditional selection; no ambiguous ternary+concat.
    merged_stat(81 downto 36) <= stat_a(81 downto 36) when choose_a='1' else stat_q(81 downto 36);
    merged_stat(35 downto 29) <= stat_a(35 downto 29) when choose_a='1' else stat_q(35 downto 29);
    merged_stat(28 downto 24) <= stat_a(28 downto 24) when choose_a='1' else stat_q(28 downto 24);
    merged_stat(23 downto 12) <= merged_cells(11 downto 0);
    merged_stat(11 downto 0) <= merged_equal(11 downto 0) when equal_union_power='1' else
                                stat_a(11 downto 0) when choose_a='1' else stat_q(11 downto 0);
''' + s[end:]
 start=s.index('    added_stat <= ')
 end=s.index('    in_ready <= ',start)
 s=s[:start]+'''
    added_stat(81 downto 36) <= current_power when choose_current='1' else stat_q(81 downto 36);
    added_stat(35 downto 29) <= expected_range when choose_current='1' else stat_q(35 downto 29);
    added_stat(28 downto 24) <= expected_bin when choose_current='1' else stat_q(28 downto 24);
    added_stat(23 downto 12) <= std_logic_vector(unsigned(stat_q(23 downto 12))+to_unsigned(1,12));
    added_stat(11 downto 0) <= std_logic_vector(unsigned(stat_q(11 downto 0))+to_unsigned(1,12))
                                when current_power=stat_q(81 downto 36) else
                                std_logic_vector(to_unsigned(1,12)) when choose_current='1' else
                                stat_q(11 downto 0);
''' + s[end:]
 return s
update('grouping/grouping_8conn.vhd',grouping)

def bank(s):
 for sig in ('write_addr','read_addr'):
  for hi,lo in ((11,0),(6,0)):
   s=s.replace(f'{sig}({hi} downto {lo}))',f'to_integer(unsigned({sig}({hi} downto {lo}))))')
 return s
update('uart/s05_iq_cpi_banked.vhd',bank)

def session(s):
 s=re.sub(r'fields\((\d+) \+ downto (\d+)\)',
          lambda m: f'fields({int(m.group(1))+int(m.group(2))-1} downto {int(m.group(1))})',s)
 return s
update('uart/s05_dsp_session_arq.vhd',session)

def echo(s):
 s=s.replace('header_sequence(8*(write_pos-7) + downto 8) <= std_logic_vector(resize(unsigned(rx_data), 32));',
 '''header_sequence((8*(to_integer(unsigned(write_pos))-7))+7 downto
                         8*(to_integer(unsigned(write_pos))-7)) <= rx_data;''')
 s=s.replace('rx_crc(8*crc_pos + downto 8) <= std_logic_vector(resize(unsigned(rx_data), 32));',
 '''rx_crc(8*to_integer(unsigned(crc_pos))+7 downto 8*to_integer(unsigned(crc_pos))) <= rx_data;''')
 return s
update('uart/s02_frame_echo.vhd',echo)

def reply(s):
 line=next(x for x in s.splitlines() if 'iq_byte_offset <=' in x)
 start=s.index(line);end=start+len(line)
 s=s[:start]+'''    iq_byte_offset <= std_logic_vector(unsigned(stage_offset_latched) +
            resize(unsigned(pos)-to_unsigned(38,10),32))
            when unsigned(pos)>=to_unsigned(38,10) else stage_offset_latched;'''+s[end:]
 s=s.replace('payload_length <= std_logic_vector(to_unsigned(26, 16)) when unsigned(response_opcode) = to_unsigned(2, 8) else std_logic_vector(to_unsigned(27, 16));',
 '''if unsigned(response_opcode) = to_unsigned(2,8) then
        payload_length <= std_logic_vector(to_unsigned(26,16));
    else
        payload_length <= std_logic_vector(to_unsigned(27,16));
    end if;''')
 s=s.replace('payload_length <= std_logic_vector(unsigned(std_logic_vector(to_unsigned(25, 16))) + unsigned(stage_count)) when unsigned(response_type) = to_unsigned(4, 8) else std_logic_vector(to_unsigned(33, 16)) when unsigned(response_type) = to_unsigned(5, 8) else std_logic_vector(to_unsigned(23, 16)) when unsigned(response_type) = to_unsigned(8, 8) else std_logic_vector(to_unsigned(20, 16));',
 '''if unsigned(response_type)=to_unsigned(4,8) then
        payload_length <= std_logic_vector(to_unsigned(25,16)+unsigned(stage_count));
    elsif unsigned(response_type)=to_unsigned(5,8) then
        payload_length <= std_logic_vector(to_unsigned(33,16));
    elsif unsigned(response_type)=to_unsigned(8,8) then
        payload_length <= std_logic_vector(to_unsigned(23,16));
    else
        payload_length <= std_logic_vector(to_unsigned(20,16));
    end if;''')
 return s
update('uart/s05_dsp_reply_tx.vhd',reply)

def dsptop(s):
 s=s.replace('    u_iq_store : entity work.s05_iq_cpi_banked','''    selected_iq_read_addr <= dsp_addr when dsp_busy='1' else iq_read_addr;

    u_iq_store : entity work.s05_iq_cpi_banked''')
 s=s.replace("read_addr => dsp_addr when dsp_busy = '1' else iq_read_addr,",'read_addr => selected_iq_read_addr,')
 key='    signal dsp_addr : std_logic_vector(12 downto 0);'
 assert key in s
 s=s.replace(key,key+'\n    signal selected_iq_read_addr : std_logic_vector(12 downto 0);')
 return s
update('uart/uart_s05_dsp_top.vhd',dsptop)

def core(s):
 s=s.replace('in_valid => unsigned(state) = to_unsigned(MTI_SEND, 4),',
             'in_valid => mti_send_flag,')
 s=s.replace('start => unsigned(state) = to_unsigned(BEGIN_RANGE, 4),',
             'start => begin_range_flag,')
 s=s.replace('    u_mti : entity work.mti2_diff',
 '''    mti_send_flag <= '1' when unsigned(state)=to_unsigned(MTI_SEND,4) else '0';
    begin_range_flag <= '1' when unsigned(state)=to_unsigned(BEGIN_RANGE,4) else '0';

    u_mti : entity work.mti2_diff''')
 key='    signal mf_error : std_logic;'
 if key not in s:
  raise RuntimeError('missing mf_error in core')
 s=s.replace(key,key+'\n    signal mti_send_flag : std_logic;\n    signal begin_range_flag : std_logic;')
 s=s.replace('if ((mf_sat) or (fft_sat)) or (pow_sat) then',
             "if (mf_sat='1') or (fft_sat='1') or (pow_sat='1') then")
 return s
update('integration/radar_cpi_core.vhd',core)

def fft(s):
 s=s.replace('start => unsigned(state) = to_unsigned(START_IP, 2),',
             'start => start_ip_flag,')
 s=s.replace('    u_ip : entity work.fft32_ip',
 '''    start_ip_flag <= '1' when unsigned(state)=to_unsigned(START_IP,2) else '0';

    u_ip : entity work.fft32_ip''')
 key='    signal ip_ce : std_logic;'
 assert key in s
 s=s.replace(key,key+'\n    signal start_ip_flag : std_logic;')
 return s
update('fft32_ip/fft32_ip_adapter.vhd',fft)

# Verilog integer state enum values cannot be used as VHDL std_logic_vector case literals.
for rel in ['integration/radar_cpi_core.vhd','grouping/grouping_8conn.vhd',
 'uart/s02_frame_echo.vhd','uart/s05_dsp_reply_tx.vhd',
 'uart/s05_dsp_session_arq.vhd','fft32_ip/fft32_ip_adapter.vhd',
 'power_cfar/cfar_2d_scan.vhd','mf16/mf16_serial_mac.vhd']:
 p=R/rel;s=p.read_text()
 if 'case state is' in s:
  p.write_text(s.replace('case state is','case to_integer(unsigned(state)) is'))
  print(rel,'case-state normalized')

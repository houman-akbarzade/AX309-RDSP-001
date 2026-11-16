library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity tb_mti_vhdl is end;
architecture sim of tb_mti_vhdl is
 signal clk: std_logic:='0';
 signal rst: std_logic:='1';
 signal vin: std_logic:='0';
 signal next_r,next_i,prev_r,prev_i:std_logic_vector(21 downto 0):=(others=>'0');
 signal rng: std_logic_vector(6 downto 0):=(others=>'0');
 signal pulse:std_logic_vector(4 downto 0):=(others=>'0');
 signal vout:std_logic;
 signal diff_r,diff_i:std_logic_vector(22 downto 0);
 signal r_out:std_logic_vector(6 downto 0);
 signal p_out:std_logic_vector(4 downto 0);
begin
 clk<=not clk after 5 ns;
 dut: entity work.mti2_diff port map
 (clk=>clk,rst=>rst,in_valid=>vin,
 pulse_next_re=>next_r,pulse_next_im=>next_i,
 pulse_prev_re=>prev_r,pulse_prev_im=>prev_i,
 range_in=>rng,pulse_in=>pulse,
 out_valid=>vout,diff_re=>diff_r,diff_im=>diff_i,
 range_out=>r_out,pulse_out=>p_out);
 process
 begin
 wait until rising_edge(clk);wait for 1 ns;
 rst<='0';vin<='1';
 next_r<=std_logic_vector(to_signed(30,22));
 prev_r<=std_logic_vector(to_signed(-5,22));
 next_i<=std_logic_vector(to_signed(-20,22));
 prev_i<=std_logic_vector(to_signed(80,22));
 rng<=std_logic_vector(to_unsigned(40,7));
 pulse<=std_logic_vector(to_unsigned(4,5));
 wait until rising_edge(clk);wait for 1 ns;
 assert vout='1' severity failure;
 assert to_integer(signed(diff_r))=35 severity failure;
 assert to_integer(signed(diff_i))=-100 severity failure;
 assert to_integer(unsigned(r_out))=40 severity failure;
 assert to_integer(unsigned(p_out))=4 severity failure;
 vin<='0';
 wait until rising_edge(clk);wait for 1 ns;
 assert vout='0' severity failure;
 report "PASS MTI VHDL" severity note;
 wait;
 end process;
end architecture;

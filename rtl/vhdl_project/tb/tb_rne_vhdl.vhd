library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity tb_rne_vhdl is end;
architecture sim of tb_rne_vhdl is
  signal x : std_logic_vector(15 downto 0) := (others=>'0');
  signal n : std_logic_vector(5 downto 0) := (others=>'0');
  signal y : std_logic_vector(7 downto 0);
  signal ov : std_logic;
  signal p : std_logic_vector(63 downto 0);
begin
  dut: entity work.rne_sat_signed
    generic map (IN_W=>16,OUT_W=>8)
    port map (in_value=>x,shift_amt=>n,out_value=>y,overflow=>ov,prelimit=>p);

  process
    procedure check(v:integer; sh:integer; expectation:integer; flag:std_logic) is
    begin
      x<=std_logic_vector(to_signed(v,16));n<=std_logic_vector(to_unsigned(sh,6));
      wait for 5 ns;
      assert to_integer(signed(y))=expectation report "RNE value mismatch" severity failure;
      assert ov=flag report "RNE overflow mismatch" severity failure;
    end procedure;
  begin
    check(19,2,5,'0');
    check(-19,2,-5,'0');
    check(18,2,4,'0');   -- midpoint 4.5 rounds to even 4
    check(22,2,6,'0');   -- midpoint 5.5 rounds to even 6
    check(-22,2,-6,'0');
    check(512,0,127,'1');
    check(-512,0,-128,'1');
    check(126,0,126,'0');
    report "PASS RNE VHDL" severity note;
    wait;
  end process;
end architecture;

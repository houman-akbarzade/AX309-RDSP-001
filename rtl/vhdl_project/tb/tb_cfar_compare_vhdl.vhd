library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity tb_cfar_compare_vhdl is end;
architecture sim of tb_cfar_compare_vhdl is
  signal cut : std_logic_vector(45 downto 0);
  signal sum40 : std_logic_vector(51 downto 0);
  signal alarm,eq : std_logic;
  signal lhs,rhs : std_logic_vector(71 downto 0);
begin
  dut: entity work.cfar_compare port map
    (p_cut=>cut,sum40=>sum40,alarm=>alarm,equality=>eq,lhs=>lhs,rhs=>rhs);
  process
    procedure check(a:integer;b:integer;expect_alarm:std_logic;expect_eq:std_logic) is
    begin
      cut<=std_logic_vector(to_unsigned(a,46));
      sum40<=std_logic_vector(to_unsigned(b,52));
      wait for 5 ns;
      assert alarm=expect_alarm report "CFAR alarm mismatch" severity failure;
      assert eq=expect_eq report "CFAR equality mismatch" severity failure;
    end procedure;
  begin
    check(0,0,'0','1');
    check(1,100,'0','0');
    check(100,100,'1','0');
    check(490007,2621440,'0','1');  -- exact threshold equality
    report "PASS CFAR comparator VHDL" severity note;
    wait;
  end process;
end architecture;

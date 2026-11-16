library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity tb_grouping_vhdl is end;
architecture sim of tb_grouping_vhdl is
  signal clk : std_logic := '0';
  signal rst : std_logic := '1';
  signal start,vin,alarm : std_logic := '0';
  signal ready : std_logic;
  signal range_in : std_logic_vector(6 downto 0) := (others=>'0');
  signal bin_in : std_logic_vector(4 downto 0) := (others=>'0');
  signal power_in : std_logic_vector(45 downto 0) := (others=>'0');
  signal vout : std_logic;signal out_ready : std_logic := '1';
  signal rid : std_logic_vector(9 downto 0);
  signal rr : std_logic_vector(6 downto 0);
  signal bb : std_logic_vector(4 downto 0);
  signal sb : std_logic_vector(5 downto 0);
  signal pp : std_logic_vector(45 downto 0);
  signal cells, equalp : std_logic_vector(11 downto 0);
  signal tie,busy,done,ov,pe,fi : std_logic;
begin
  clk <= not clk after 5 ns;
  dut: entity work.grouping_8conn
    generic map (MAX_LABELS=>702)
    port map(
      clk=>clk,rst=>rst,start=>start,
      in_valid=>vin,in_ready=>ready,in_range=>range_in,
      in_bin=>bin_in,in_power=>power_in,in_alarm=>alarm,
      out_valid=>vout,out_ready=>out_ready,out_record_id=>rid,
      out_range=>rr,out_bin=>bb,out_signed_bin=>sb,
      out_peak_power=>pp,out_cluster_cells=>cells,
      out_tie_flag=>tie,out_equal_power_cells=>equalp,
      busy=>busy,done=>done,overflow_sticky=>ov,
      protocol_error=>pe,frame_invalid=>fi);
  process
    variable found : boolean := false;
    variable seen_records : integer := 0;
    variable r,b : integer;
  begin
    wait until falling_edge(clk);
    rst<='0';start<='1';
    wait until falling_edge(clk);
    start<='0';
    -- Exactly 2782 valid CFAR CUTs, zero-based bins [3..109]×[3..28].
    for i in 0 to 2781 loop
      loop
        wait until falling_edge(clk);
        exit when ready='1';
      end loop;
      r:=3+i/26; b:=3+(i mod 26);
      range_in<=std_logic_vector(to_unsigned(r,7));
      bin_in<=std_logic_vector(to_unsigned(b,5));
      if (r=40 and b=4) then
        power_in<=std_logic_vector(to_unsigned(123,46));alarm<='1';
      elsif (r=40 and b=5) then
        power_in<=std_logic_vector(to_unsigned(99,46));alarm<='1';
      else
        power_in<=(others=>'0');alarm<='0';
      end if;
      vin<='1';
      wait until rising_edge(clk);
      wait for 1 ns;
      vin<='0';
    end loop;
    -- Wait a bounded time for the single two-cell connected cluster.
    for cycle in 0 to 300000 loop
      wait until rising_edge(clk);wait for 1 ns;
      assert ov='0' and pe='0' and fi='0'
        report "Grouping overflow/protocol/frame error" severity failure;
      if vout='1' then
        assert to_integer(unsigned(rid))=0 report "ID mismatch" severity failure;
        assert to_integer(unsigned(rr))=40 report "Peak range mismatch" severity failure;
        assert to_integer(unsigned(bb))=4 report "Peak Doppler mismatch" severity failure;
        assert to_integer(unsigned(pp))=123 report "Peak power mismatch" severity failure;
        assert to_integer(unsigned(cells))=2 report "Cluster size mismatch" severity failure;
        assert tie='0' report "Unexpected equal-peak tie" severity failure;
        seen_records:=seen_records+1;
      end if;
      if done='1' then found:=true;exit;end if;
    end loop;
    assert found report "Grouping completion timeout" severity failure;
    assert seen_records=1 report "Grouping record count mismatch" severity failure;
    report "PASS GROUPING VHDL" severity note;
    wait;
  end process;
end architecture;

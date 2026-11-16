-- VHDL counterpart of the accepted Verilog board wrapper.
-- This is a NEW engineering variant; original Verilog and bitstream are frozen.
library ieee;
use ieee.std_logic_1164.all;
library unisim;
use unisim.vcomponents.all;

entity radar_ip_ax309_top is
  port (
    clk50    : in  std_logic;
    reset_n  : in  std_logic;
    uart_rxd : in  std_logic;
    uart_txd : out std_logic
  );
end entity;

architecture rtl of radar_ip_ax309_top is
  signal reset_pipe : std_logic_vector(2 downto 0) := "111";
  signal clk_g : std_logic;
  signal rst : std_logic;
begin
  u_global_clock: BUFG
    port map (I=>clk50, O=>clk_g);

  process(clk_g,reset_n)
  begin
    if reset_n='0' then
      reset_pipe <= "111";
    elsif rising_edge(clk_g) then
      reset_pipe <= reset_pipe(1 downto 0) & '0';
    end if;
  end process;
  rst <= reset_pipe(2);

  u_link: entity work.uart_s05_dsp_top
    generic map (
      CLOCK_HZ=>50000000,
      BAUD=>115200,
      TIMEOUT_CLKS=>86800,
      TX_ACK_TIMEOUT_CLKS=>100000000
    )
    port map (
      clk=>clk_g, rst=>rst,
      uart_rxd=>uart_rxd, uart_txd=>uart_txd,
      active_session=>open, expected_seq=>open,
      activation_count=>open, accepted_count=>open,
      duplicate_count=>open, stale_count=>open,
      nack_count=>open, good_frames=>open,
      crc_errors=>open, header_errors=>open,
      length_errors=>open, partial_timeouts=>open,
      uart_errors=>open, cpi_open=>open, cpi_id=>open,
      iq_uploaded_bytes=>open, iq_readback_acked_bytes=>open,
      tx_next_seq=>open, tx_retry_exhausted=>open
    );
end architecture;

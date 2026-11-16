-- ISE 14.7 FFT v7.1 CoreGen synthesis black box.
-- The behavior and implementation are provided ONLY by licensed Xilinx IP.
-- IMPORTANT: This declaration is NOT a reimplementation of its butterfly logic.
library ieee;
use ieee.std_logic_1164.all;

entity fft32_ip is
  port (
    clk : in std_logic; ce : in std_logic; sclr : in std_logic;
    start : in std_logic; unload : in std_logic;
    fwd_inv : in std_logic; fwd_inv_we : in std_logic;
    scale_sch_we : in std_logic;
    xn_re : in std_logic_vector(24 downto 0);
    xn_im : in std_logic_vector(24 downto 0);
    scale_sch : in std_logic_vector(9 downto 0);
    rfd : out std_logic; busy : out std_logic; edone : out std_logic;
    done : out std_logic; dv : out std_logic; ovflo : out std_logic;
    xn_index : out std_logic_vector(4 downto 0);
    xk_index : out std_logic_vector(4 downto 0);
    xk_re : out std_logic_vector(24 downto 0);
    xk_im : out std_logic_vector(24 downto 0)
  );
end entity;
architecture rtl of fft32_ip is
  attribute syn_black_box : boolean;
  attribute syn_black_box of rtl : architecture is true;
  attribute box_type : string;
  attribute box_type of rtl : architecture is "black_box";
begin
  -- Intentionally no HDL drivers. Physical implementation comes from CoreGen NGC.
end architecture;

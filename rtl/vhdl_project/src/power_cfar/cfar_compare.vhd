-- AUTO-TRANSLATED from power_cfar/cfar_compare.v; independent validation REQUIRED.
-- Source SHA256: 33f7445a18f3f6cddd4d8dcb577c3684b7e6b7075bd6922bba213753d90db530
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity cfar_compare is
    port (
        p_cut : in std_logic_vector(45 downto 0);
        sum40 : in std_logic_vector(51 downto 0);
        alarm : out std_logic;
        equality : out std_logic;
        lhs : out std_logic_vector(71 downto 0);
        rhs : out std_logic_vector(71 downto 0)
    );
end entity cfar_compare;

architecture rtl of cfar_compare is
    signal p_cut_ext : std_logic_vector(51 downto 0);
    signal forty_p : std_logic_vector(51 downto 0);
    signal sum_ext : std_logic_vector(70 downto 0);
    signal rhs_product : std_logic_vector(70 downto 0);
    signal lhs_int : std_logic_vector(71 downto 0);
    signal rhs_int : std_logic_vector(71 downto 0);
begin

    p_cut_ext <= std_logic_vector'(std_logic_vector(to_unsigned(0, 6)) & p_cut);
    forty_p <= std_logic_vector(resize(unsigned(std_logic_vector(shift_left(unsigned(p_cut_ext), 5))), 52) + resize(unsigned(std_logic_vector(shift_left(unsigned(p_cut_ext), 3))), 52));
    sum_ext <= std_logic_vector'(std_logic_vector(to_unsigned(0, 19)) & sum40);
    rhs_product <= std_logic_vector(resize(unsigned(sum_ext) * 490007, 71));
    lhs_int <= std_logic_vector'(std_logic_vector(to_unsigned(0, 4)) & forty_p & std_logic_vector(to_unsigned(0, 16)));
    rhs_int <= std_logic_vector'('0' & rhs_product);
    alarm <= '1' when unsigned(lhs_int) > unsigned(rhs_int) else '0';
    equality <= '1' when unsigned(lhs_int) = unsigned(rhs_int) else '0';

    lhs <= lhs_int;
    rhs <= rhs_int;

end architecture rtl;

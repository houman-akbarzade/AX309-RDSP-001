-- AUTO-TRANSLATED from mf16/mf16_coeff_rom.v; independent validation REQUIRED.
-- Source SHA256: 16504b3754280156b249aa0d99732941adf9ea0d15635c93429eba4bc23131e1
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity mf16_coeff_rom is
    port (
        index : in std_logic_vector(3 downto 0);
        coeff_re : out std_logic_vector(15 downto 0);
        coeff_im : out std_logic_vector(15 downto 0)
    );
end entity mf16_coeff_rom;

architecture rtl of mf16_coeff_rom is
    signal coeff_re_reg : std_logic_vector(15 downto 0);
    signal coeff_im_reg : std_logic_vector(15 downto 0);
begin

    process(index)
    begin
        coeff_re_reg <= std_logic_vector(to_unsigned(0, 16));
        coeff_im_reg <= std_logic_vector(to_unsigned(0, 16));
        case index is
            when "0000" =>
                coeff_re_reg <= std_logic_vector(to_unsigned(30425, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(12167, 16));
            when "0001" =>
                coeff_re_reg <= std_logic_vector(to_unsigned(15800, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(28707, 16));
            when "0010" =>
                coeff_re_reg <= std_logic_vector(to_signed(-2811, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(32647, 16));
            when "0011" =>
                coeff_re_reg <= std_logic_vector(to_signed(-17869, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(27467, 16));
            when "0100" =>
                coeff_re_reg <= std_logic_vector(to_signed(-27020, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(18538, 16));
            when "0101" =>
                coeff_re_reg <= std_logic_vector(to_signed(-31238, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(9896, 16));
            when "0110" =>
                coeff_re_reg <= std_logic_vector(to_signed(-32568, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(3612, 16));
            when "0111" =>
                coeff_re_reg <= std_logic_vector(to_signed(-32766, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(402, 16));
            when "1000" =>
                coeff_re_reg <= std_logic_vector(to_signed(-32766, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(402, 16));
            when "1001" =>
                coeff_re_reg <= std_logic_vector(to_signed(-32568, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(3612, 16));
            when "1010" =>
                coeff_re_reg <= std_logic_vector(to_signed(-31238, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(9896, 16));
            when "1011" =>
                coeff_re_reg <= std_logic_vector(to_signed(-27020, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(18538, 16));
            when "1100" =>
                coeff_re_reg <= std_logic_vector(to_signed(-17869, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(27467, 16));
            when "1101" =>
                coeff_re_reg <= std_logic_vector(to_signed(-2811, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(32647, 16));
            when "1110" =>
                coeff_re_reg <= std_logic_vector(to_unsigned(15800, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(28707, 16));
            when "1111" =>
                coeff_re_reg <= std_logic_vector(to_unsigned(30425, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(12167, 16));
            when others =>
                coeff_re_reg <= std_logic_vector(to_unsigned(0, 16));
                coeff_im_reg <= std_logic_vector(to_unsigned(0, 16));
        end case;
    end process;

    coeff_re <= coeff_re_reg;
    coeff_im <= coeff_im_reg;

end architecture rtl;

-- AUTO-TRANSLATED from mti/mti2_diff.v; independent validation REQUIRED.
-- Source SHA256: 6263f92316e9f2a8d4816cf34d5bd53e01975988f22b06cfd1ca7c0e858def19
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity mti2_diff is
    port (
        clk : in std_logic;
        rst : in std_logic;
        in_valid : in std_logic;
        pulse_next_re : in std_logic_vector(21 downto 0);
        pulse_next_im : in std_logic_vector(21 downto 0);
        pulse_prev_re : in std_logic_vector(21 downto 0);
        pulse_prev_im : in std_logic_vector(21 downto 0);
        range_in : in std_logic_vector(6 downto 0);
        pulse_in : in std_logic_vector(4 downto 0);
        out_valid : out std_logic;
        diff_re : out std_logic_vector(22 downto 0);
        diff_im : out std_logic_vector(22 downto 0);
        range_out : out std_logic_vector(6 downto 0);
        pulse_out : out std_logic_vector(4 downto 0)
    );
end entity mti2_diff;

architecture rtl of mti2_diff is
    signal next_re_ext : std_logic_vector(22 downto 0);
    signal next_im_ext : std_logic_vector(22 downto 0);
    signal prev_re_ext : std_logic_vector(22 downto 0);
    signal prev_im_ext : std_logic_vector(22 downto 0);
    signal out_valid_reg : std_logic;
    signal diff_re_reg : std_logic_vector(22 downto 0);
    signal diff_im_reg : std_logic_vector(22 downto 0);
    signal range_out_reg : std_logic_vector(6 downto 0);
    signal pulse_out_reg : std_logic_vector(4 downto 0);
begin

    next_re_ext <= std_logic_vector'(pulse_next_re(21) & pulse_next_re);
    next_im_ext <= std_logic_vector'(pulse_next_im(21) & pulse_next_im);
    prev_re_ext <= std_logic_vector'(pulse_prev_re(21) & pulse_prev_re);
    prev_im_ext <= std_logic_vector'(pulse_prev_im(21) & pulse_prev_im);

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                out_valid_reg <= '0';
                diff_re_reg <= std_logic_vector(to_unsigned(0, 23));
                diff_im_reg <= std_logic_vector(to_unsigned(0, 23));
                range_out_reg <= std_logic_vector(to_unsigned(0, 7));
                pulse_out_reg <= std_logic_vector(to_unsigned(0, 5));
            else
                out_valid_reg <= in_valid;
                if in_valid = '1' then
                    diff_re_reg <= std_logic_vector(signed(next_re_ext) - signed(prev_re_ext));
                    diff_im_reg <= std_logic_vector(signed(next_im_ext) - signed(prev_im_ext));
                    range_out_reg <= range_in;
                    pulse_out_reg <= pulse_in;
                end if;
            end if;
        end if;
    end process;

    out_valid <= out_valid_reg;
    diff_re <= diff_re_reg;
    diff_im <= diff_im_reg;
    range_out <= range_out_reg;
    pulse_out <= pulse_out_reg;

end architecture rtl;

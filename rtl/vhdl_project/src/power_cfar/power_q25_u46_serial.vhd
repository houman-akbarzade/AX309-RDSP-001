-- AUTO-TRANSLATED from power_cfar/power_q25_u46_serial.v; independent validation REQUIRED.
-- Source SHA256: bdba2c51088145d4b6dd8d0e4228bca3f4d7cc6eda3aa614d4c12c84213276df
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity power_q25_u46_serial is
    port (
        clk : in std_logic;
        rst : in std_logic;
        in_valid : in std_logic;
        in_ready : out std_logic;
        in_re : in std_logic_vector(24 downto 0);
        in_im : in std_logic_vector(24 downto 0);
        range_in : in std_logic_vector(6 downto 0);
        bin_in : in std_logic_vector(4 downto 0);
        out_valid : out std_logic;
        out_ready : in std_logic;
        power_out : out std_logic_vector(45 downto 0);
        range_out : out std_logic_vector(6 downto 0);
        bin_out : out std_logic_vector(4 downto 0);
        overflow_sticky : out std_logic
    );
end entity power_q25_u46_serial;

architecture rtl of power_q25_u46_serial is
    function reduce_or(v : std_logic_vector) return std_logic is
        variable r : std_logic := '0';
    begin
        for i in v'range loop
            r := r or v(i);
        end loop;
        return r;
    end function;

    function repeat_slv(value : std_logic_vector; count : natural) return std_logic_vector is
        variable result_v : std_logic_vector(value'length * count - 1 downto 0);
    begin
        for i in 0 to count - 1 loop
            result_v((i + 1) * value'length - 1 downto i * value'length) := value;
        end loop;
        return result_v;
    end function;

    function repeat_slv(value : std_logic; count : natural) return std_logic_vector is
        variable result_v : std_logic_vector(count - 1 downto 0);
    begin
        result_v := (others => value);
        return result_v;
    end function;

    signal state : std_logic_vector(3 downto 0);
    signal ar : std_logic_vector(24 downto 0);
    signal ai : std_logic_vector(24 downto 0);
    signal acc : std_logic_vector(50 downto 0);
    signal a : std_logic_vector(16 downto 0);
    signal b : std_logic_vector(16 downto 0);
    signal product : std_logic_vector(33 downto 0);
    signal operand : std_logic_vector(24 downto 0);
    signal range_out_reg : std_logic_vector(6 downto 0);
    signal bin_out_reg : std_logic_vector(4 downto 0);
    signal overflow_sticky_reg : std_logic;
begin

    product <= std_logic_vector(resize(unsigned(a) * unsigned(b), 34));
    operand <= ar when unsigned(state) < to_unsigned(4, 4) else ai;
    in_ready <= '1' when unsigned(state) = to_unsigned(0, 4) else '0';
    out_valid <= '1' when unsigned(state) = to_unsigned(7, 4) else '0';
    power_out <= (others => '1') when reduce_or(acc(50 downto 46)) = '1' else acc(45 downto 0);

    process(state, operand)
    begin
        a <= std_logic_vector(to_unsigned(0, 17));
        b <= std_logic_vector(to_unsigned(0, 17));
        case state is
            when "0001" | "0100" =>
                a <= std_logic_vector'('0' & operand(15 downto 0));
                b <= std_logic_vector'('0' & operand(15 downto 0));
            when "0010" | "0101" =>
                a <= std_logic_vector'('0' & operand(15 downto 0));
                b <= std_logic_vector'(std_logic_vector(to_unsigned(0, 8)) & operand(24 downto 16));
            when "0011" | "0110" =>
                a <= std_logic_vector'(std_logic_vector(to_unsigned(0, 8)) & operand(24 downto 16));
                b <= std_logic_vector'(std_logic_vector(to_unsigned(0, 8)) & operand(24 downto 16));
            when others =>
                null;
        end case;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= std_logic_vector(to_unsigned(0, 4));
                ar <= std_logic_vector(to_unsigned(0, 25));
                ai <= std_logic_vector(to_unsigned(0, 25));
                acc <= std_logic_vector(to_unsigned(0, 51));
                range_out_reg <= std_logic_vector(to_unsigned(0, 7));
                bin_out_reg <= std_logic_vector(to_unsigned(0, 5));
                overflow_sticky_reg <= '0';
            else
                case state is
                    when "0000" =>
                        if in_valid = '1' then
                            if in_re(24) = '1' then
    ar <= std_logic_vector(resize(unsigned(not in_re), 25) + resize(unsigned(std_logic_vector(to_unsigned(1, 25))), 25));
else
    ar <= in_re;
end if;
                            if in_im(24) = '1' then
    ai <= std_logic_vector(resize(unsigned(not in_im), 25) + resize(unsigned(std_logic_vector(to_unsigned(1, 25))), 25));
else
    ai <= in_im;
end if;
                            acc <= std_logic_vector(to_unsigned(0, 51));
                            range_out_reg <= range_in;
                            bin_out_reg <= bin_in;
                            state <= std_logic_vector(to_unsigned(1, 4));
                        end if;
                    when "0001" | "0100" =>
                        acc <= std_logic_vector(resize(unsigned(acc), 51) + resize(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 17)) & product)), 51));
                        state <= std_logic_vector(resize(unsigned(state), 4) + to_unsigned(1, 4));
                    when "0010" | "0101" =>
                        acc <= std_logic_vector(resize(unsigned(acc), 51) + resize(unsigned(std_logic_vector(shift_left(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 17)) & product)), 17))), 51));
                        state <= std_logic_vector(resize(unsigned(state), 4) + to_unsigned(1, 4));
                    when "0011" | "0110" =>
                        acc <= std_logic_vector(resize(unsigned(acc), 51) + resize(unsigned(std_logic_vector(shift_left(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 17)) & product)), 32))), 51));
                        state <= std_logic_vector(resize(unsigned(state), 4) + to_unsigned(1, 4));
                    when "0111" =>
                        if reduce_or(acc(50 downto 46)) = '1' then
                            overflow_sticky_reg <= '1';
                        end if;
                        if out_ready = '1' then
                            state <= std_logic_vector(to_unsigned(0, 4));
                        end if;
                    when others =>
                        null;
                end case;
            end if;
        end if;
    end process;

    range_out <= range_out_reg;
    bin_out <= bin_out_reg;
    overflow_sticky <= overflow_sticky_reg;

end architecture rtl;

-- AUTO-TRANSLATED from uart/uart_rx_8n1.v; independent validation REQUIRED.
-- Source SHA256: dbc893a83aa8d318797cd4bddf4ab9ee11527f45a29b99b809e7b12809de0e37
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_rx_8n1 is
    generic (
        CLOCK_HZ : integer := 50000000;
        BAUD : integer := 115200
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        rx_pin : in std_logic;
        data_out : out std_logic_vector(7 downto 0);
        data_valid : out std_logic;
        framing_error : out std_logic;
        busy : out std_logic
    );
end entity uart_rx_8n1;

architecture rtl of uart_rx_8n1 is
    constant TICKS : integer := (CLOCK_HZ / BAUD);
    constant HALF : integer := (TICKS / 2);
    constant IDLE : std_logic_vector(1 downto 0) := "00";
    constant START : std_logic_vector(1 downto 0) := "01";
    constant DATA : std_logic_vector(1 downto 0) := "10";
    constant STOP : std_logic_vector(1 downto 0) := "11";
    signal state : std_logic_vector(1 downto 0);
    signal sync_a : std_logic;
    signal sync_b : std_logic;
    signal timer : std_logic_vector(15 downto 0);
    signal bit_index : std_logic_vector(2 downto 0);
    signal shifting : std_logic_vector(7 downto 0);
    signal data_out_reg : std_logic_vector(7 downto 0);
    signal data_valid_reg : std_logic;
    signal framing_error_reg : std_logic;
begin

    busy <= '1' when unsigned(state) /= unsigned(IDLE) else '0';

    process(clk)
    begin
        if rising_edge(clk) then
            sync_a <= rx_pin;
            sync_b <= sync_a;
            if rst = '1' then
                state <= IDLE;
                sync_a <= '1';
                sync_b <= '1';
                timer <= std_logic_vector(to_unsigned(0, 16));
                bit_index <= std_logic_vector(to_unsigned(0, 3));
                shifting <= std_logic_vector(to_unsigned(0, 8));
                data_valid_reg <= '0';
                framing_error_reg <= '0';
                data_out_reg <= std_logic_vector(to_unsigned(0, 8));
            else
                data_valid_reg <= '0';
                framing_error_reg <= '0';
                case state is
                    when IDLE =>
                        if not (sync_b = '1') then
                            timer <= std_logic_vector(to_unsigned((HALF - 1), 16));
                            state <= START;
                        end if;
                    when START =>
                        if unsigned(timer) = to_unsigned(0, 16) then
                            if not (sync_b = '1') then
                                timer <= std_logic_vector(to_unsigned((TICKS - 1), 16));
                                bit_index <= std_logic_vector(to_unsigned(0, 3));
                                state <= DATA;
                            else
                                state <= IDLE;
                            end if;
                        else
                            timer <= std_logic_vector(resize(unsigned(timer), 16) - to_unsigned(1, 16));
                        end if;
                    when DATA =>
                        if unsigned(timer) = to_unsigned(0, 16) then
                            shifting(to_integer(unsigned(bit_index))) <= sync_b;
                            timer <= std_logic_vector(to_unsigned((TICKS - 1), 16));
                            if unsigned(bit_index) = to_unsigned(7, 3) then
                                state <= STOP;
                            else
                                bit_index <= std_logic_vector(resize(unsigned(bit_index), 3) + to_unsigned(1, 3));
                            end if;
                        else
                            timer <= std_logic_vector(resize(unsigned(timer), 16) - to_unsigned(1, 16));
                        end if;
                    when STOP =>
                        if unsigned(timer) = to_unsigned(0, 16) then
                            if sync_b = '1' then
                                data_out_reg <= shifting;
                                data_valid_reg <= '1';
                            else
                                framing_error_reg <= '1';
                            end if;
                            state <= IDLE;
                        else
                            timer <= std_logic_vector(resize(unsigned(timer), 16) - to_unsigned(1, 16));
                        end if;
                    when others =>
                        state <= IDLE;
                end case;
            end if;
        end if;
    end process;

    data_out <= data_out_reg;
    data_valid <= data_valid_reg;
    framing_error <= framing_error_reg;

end architecture rtl;

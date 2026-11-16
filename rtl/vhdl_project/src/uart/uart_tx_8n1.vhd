-- AUTO-TRANSLATED from uart/uart_tx_8n1.v; independent validation REQUIRED.
-- Source SHA256: 2e655a7e0fd7c76acf302d765d926e3dc11de190dc3ee3b9275151f7642cf6a4
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_tx_8n1 is
    generic (
        CLOCK_HZ : integer := 50000000;
        BAUD : integer := 115200
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        data_in : in std_logic_vector(7 downto 0);
        data_valid : in std_logic;
        data_ready : out std_logic;
        tx_pin : out std_logic;
        byte_done : out std_logic
    );
end entity uart_tx_8n1;

architecture rtl of uart_tx_8n1 is
    constant TICKS : integer := (CLOCK_HZ / BAUD);
    constant IDLE : std_logic_vector(1 downto 0) := "00";
    constant START : std_logic_vector(1 downto 0) := "01";
    constant DATA : std_logic_vector(1 downto 0) := "10";
    constant STOP : std_logic_vector(1 downto 0) := "11";
    signal state : std_logic_vector(1 downto 0);
    signal timer : std_logic_vector(15 downto 0);
    signal bit_index : std_logic_vector(2 downto 0);
    signal byte_latched : std_logic_vector(7 downto 0);
    signal tx_pin_reg : std_logic;
    signal byte_done_reg : std_logic;
begin

    data_ready <= '1' when unsigned(state) = unsigned(IDLE) else '0';

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= IDLE;
                timer <= std_logic_vector(to_unsigned(0, 16));
                bit_index <= std_logic_vector(to_unsigned(0, 3));
                byte_latched <= std_logic_vector(to_unsigned(0, 8));
                tx_pin_reg <= '1';
                byte_done_reg <= '0';
            else
                byte_done_reg <= '0';
                case state is
                    when IDLE =>
                        tx_pin_reg <= '1';
                        if data_valid = '1' then
                            byte_latched <= data_in;
                            timer <= std_logic_vector(to_unsigned((TICKS - 1), 16));
                            tx_pin_reg <= '0';
                            state <= START;
                        end if;
                    when START =>
                        if unsigned(timer) = to_unsigned(0, 16) then
                            tx_pin_reg <= byte_latched(0);
                            bit_index <= std_logic_vector(to_unsigned(0, 3));
                            timer <= std_logic_vector(to_unsigned((TICKS - 1), 16));
                            state <= DATA;
                        else
                            timer <= std_logic_vector(resize(unsigned(timer), 16) - to_unsigned(1, 16));
                        end if;
                    when DATA =>
                        if unsigned(timer) = to_unsigned(0, 16) then
                            timer <= std_logic_vector(to_unsigned((TICKS - 1), 16));
                            if unsigned(bit_index) = to_unsigned(7, 3) then
                                tx_pin_reg <= '1';
                                state <= STOP;
                            else
                                bit_index <= std_logic_vector(resize(unsigned(bit_index), 3) + to_unsigned(1, 3));
                                tx_pin_reg <= byte_latched(to_integer(unsigned(bit_index)) + 1);
                            end if;
                        else
                            timer <= std_logic_vector(resize(unsigned(timer), 16) - to_unsigned(1, 16));
                        end if;
                    when STOP =>
                        if unsigned(timer) = to_unsigned(0, 16) then
                            byte_done_reg <= '1';
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

    tx_pin <= tx_pin_reg;
    byte_done <= byte_done_reg;

end architecture rtl;

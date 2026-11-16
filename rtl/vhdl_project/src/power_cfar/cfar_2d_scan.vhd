-- AUTO-TRANSLATED from power_cfar/cfar_2d_scan.v; independent validation REQUIRED.
-- Source SHA256: ab5974d08fd41e566bea503cb62b2866c14d9c84c7968244eafaa544941654b4
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity cfar_2d_scan is
    port (
        clk : in std_logic;
        rst : in std_logic;
        start : in std_logic;
        debug_read : in std_logic;
        debug_addr : in std_logic_vector(11 downto 0);
        debug_power : out std_logic_vector(45 downto 0);
        map_valid : in std_logic;
        map_ready : out std_logic;
        map_power : in std_logic_vector(45 downto 0);
        out_valid : out std_logic;
        out_ready : in std_logic;
        out_range : out std_logic_vector(6 downto 0);
        out_bin : out std_logic_vector(4 downto 0);
        out_power : out std_logic_vector(45 downto 0);
        out_sum40 : out std_logic_vector(51 downto 0);
        out_alarm : out std_logic;
        out_equality : out std_logic;
        busy : out std_logic;
        done : out std_logic;
        overflow_event : out std_logic;
        overflow_sticky : out std_logic;
        protocol_error : out std_logic
    );
end entity cfar_2d_scan;

architecture rtl of cfar_2d_scan is
    constant ST_IDLE : std_logic_vector(2 downto 0) := "000";
    constant ST_LOAD : std_logic_vector(2 downto 0) := "001";
    constant ST_SCAN_INIT : std_logic_vector(2 downto 0) := "010";
    constant ST_READ : std_logic_vector(2 downto 0) := "011";
    constant ST_ACCUM : std_logic_vector(2 downto 0) := "100";
    constant ST_EMIT : std_logic_vector(2 downto 0) := "101";
    type power_mem_array_t is array (0 to 4095) of std_logic_vector(45 downto 0);
    signal power_mem : power_mem_array_t;
    signal state : std_logic_vector(2 downto 0);
    signal load_addr : std_logic_vector(11 downto 0);
    signal cut_range : std_logic_vector(6 downto 0);
    signal cut_bin : std_logic_vector(4 downto 0);
    signal win_row : std_logic_vector(2 downto 0);
    signal win_col : std_logic_vector(2 downto 0);
    signal training_count : std_logic_vector(5 downto 0);
    signal mem_q : std_logic_vector(45 downto 0);
    signal cut_power : std_logic_vector(45 downto 0);
    signal sum40 : std_logic_vector(51 downto 0);
    signal cut_addr : std_logic_vector(11 downto 0);
    signal train_range_ext : std_logic_vector(8 downto 0);
    signal train_bin_ext : std_logic_vector(7 downto 0);
    signal train_range_12 : std_logic_vector(11 downto 0);
    signal train_addr : std_logic_vector(11 downto 0);
    signal guard_cell : std_logic;
    signal sum_next : std_logic_vector(52 downto 0);
    signal cmp_alarm : std_logic;
    signal cmp_equality : std_logic;
    signal ram_read_enable : std_logic;
    signal ram_read_addr : std_logic_vector(11 downto 0);
    signal busy_reg : std_logic;
    signal done_reg : std_logic;
    signal overflow_event_reg : std_logic;
    signal overflow_sticky_reg : std_logic;
    signal protocol_error_reg : std_logic;
    signal map_ready_int : std_logic;
    signal out_valid_int : std_logic;
begin

    cut_addr <= std_logic_vector(resize(unsigned(std_logic_vector'(cut_range & "00000")), 12) + resize(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 7)) & cut_bin)), 12));
    train_range_ext <= std_logic_vector(unsigned(std_logic_vector(resize(unsigned(std_logic_vector'("00" & cut_range)), 9) + resize(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 6)) & win_row)), 9))) - resize(unsigned(std_logic_vector(to_unsigned(3, 9))), 9));
    train_bin_ext <= std_logic_vector(unsigned(std_logic_vector(resize(unsigned(std_logic_vector'("000" & cut_bin)), 8) + resize(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 5)) & win_col)), 8))) - resize(unsigned(std_logic_vector(to_unsigned(3, 8))), 8));
    train_range_12 <= std_logic_vector'("000" & train_range_ext);
    train_addr <= std_logic_vector(resize(unsigned(std_logic_vector(shift_left(unsigned(train_range_12), 5))), 12) + resize(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 4)) & train_bin_ext)), 12));
    guard_cell <= '1' when (((unsigned(win_row) >= unsigned(std_logic_vector(to_unsigned(2, 3)))) and (unsigned(win_row) <= unsigned(std_logic_vector(to_unsigned(4, 3))))) and (unsigned(win_col) >= unsigned(std_logic_vector(to_unsigned(2, 3))))) and (unsigned(win_col) <= unsigned(std_logic_vector(to_unsigned(4, 3)))) else '0';
    sum_next <= std_logic_vector(resize(unsigned(std_logic_vector'('0' & sum40)), 53) + resize(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 7)) & mem_q)), 53));
    ram_read_enable <= '1' when ((unsigned(state) = unsigned(ST_SCAN_INIT)) or ((unsigned(state) = unsigned(ST_READ)) and (not (guard_cell = '1')))) or ((unsigned(state) = unsigned(ST_IDLE)) and (debug_read = '1')) else '0';
    ram_read_addr <= debug_addr when unsigned(state) = unsigned(ST_IDLE) else cut_addr when unsigned(state) = unsigned(ST_SCAN_INIT) else train_addr;
    debug_power <= mem_q;
    map_ready_int <= '1' when unsigned(state) = unsigned(ST_LOAD) else '0';
    out_valid_int <= '1' when unsigned(state) = unsigned(ST_EMIT) else '0';
    out_range <= cut_range;
    out_bin <= cut_bin;
    out_power <= cut_power;
    out_sum40 <= sum40;
    out_alarm <= cmp_alarm;
    out_equality <= cmp_equality;

    u_cfar_compare : entity work.cfar_compare
        port map (
            p_cut => cut_power,
            sum40 => sum40,
            alarm => cmp_alarm,
            equality => cmp_equality,
            lhs => open,
            rhs => open
        );

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= ST_IDLE;
                busy_reg <= '0';
                done_reg <= '0';
                overflow_event_reg <= '0';
                overflow_sticky_reg <= '0';
                protocol_error_reg <= '0';
                load_addr <= std_logic_vector(to_unsigned(0, 12));
                cut_range <= std_logic_vector(to_unsigned(3, 7));
                cut_bin <= std_logic_vector(to_unsigned(3, 5));
                win_row <= std_logic_vector(to_unsigned(0, 3));
                win_col <= std_logic_vector(to_unsigned(0, 3));
                training_count <= std_logic_vector(to_unsigned(0, 6));
                cut_power <= std_logic_vector(to_unsigned(0, 46));
                sum40 <= std_logic_vector(to_unsigned(0, 52));
            else
                done_reg <= '0';
                overflow_event_reg <= '0';
                if start = '1' then
                    if unsigned(state) /= unsigned(ST_IDLE) then
                        protocol_error_reg <= '1';
                    else
                        state <= ST_LOAD;
                        busy_reg <= '1';
                        load_addr <= std_logic_vector(to_unsigned(0, 12));
                        overflow_sticky_reg <= '0';
                        protocol_error_reg <= '0';
                    end if;
                end if;
                case state is
                    when ST_IDLE =>
                        null;
                    when ST_LOAD =>
                        if (map_valid = '1') and (map_ready_int = '1') then
                            power_mem(to_integer(unsigned(load_addr))) <= map_power;
                            if unsigned(load_addr) = unsigned(std_logic_vector(to_unsigned(4095, 12))) then
                                cut_range <= std_logic_vector(to_unsigned(3, 7));
                                cut_bin <= std_logic_vector(to_unsigned(3, 5));
                                state <= ST_SCAN_INIT;
                            else
                                load_addr <= std_logic_vector(resize(unsigned(load_addr), 12) + resize(unsigned(std_logic_vector(to_unsigned(1, 12))), 12));
                            end if;
                        end if;
                    when ST_SCAN_INIT =>
                        win_row <= std_logic_vector(to_unsigned(0, 3));
                        win_col <= std_logic_vector(to_unsigned(0, 3));
                        training_count <= std_logic_vector(to_unsigned(0, 6));
                        sum40 <= std_logic_vector(to_unsigned(0, 52));
                        state <= ST_READ;
                    when ST_READ =>
                        if guard_cell = '1' then
                            if unsigned(win_col) = unsigned(std_logic_vector(to_unsigned(6, 3))) then
                                win_col <= std_logic_vector(to_unsigned(0, 3));
                                win_row <= std_logic_vector(resize(unsigned(win_row), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                            else
                                win_col <= std_logic_vector(resize(unsigned(win_col), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                            end if;
                        else
                            if (unsigned(win_row) = unsigned(std_logic_vector(to_unsigned(0, 3)))) and (unsigned(win_col) = unsigned(std_logic_vector(to_unsigned(0, 3)))) then
                                cut_power <= mem_q;
                            end if;
                            state <= ST_ACCUM;
                        end if;
                    when ST_ACCUM =>
                        sum40 <= sum_next(51 downto 0);
                        if sum_next(52) = '1' then
                            overflow_event_reg <= '1';
                            overflow_sticky_reg <= '1';
                        end if;
                        if unsigned(training_count) = unsigned(std_logic_vector(to_unsigned(39, 6))) then
                            state <= ST_EMIT;
                        else
                            training_count <= std_logic_vector(resize(unsigned(training_count), 6) + resize(unsigned(std_logic_vector(to_unsigned(1, 6))), 6));
                            if unsigned(win_col) = unsigned(std_logic_vector(to_unsigned(6, 3))) then
                                win_col <= std_logic_vector(to_unsigned(0, 3));
                                win_row <= std_logic_vector(resize(unsigned(win_row), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                            else
                                win_col <= std_logic_vector(resize(unsigned(win_col), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                            end if;
                            state <= ST_READ;
                        end if;
                    when ST_EMIT =>
                        if (out_valid_int = '1') and (out_ready = '1') then
                            if (unsigned(cut_range) = unsigned(std_logic_vector(to_unsigned(109, 7)))) and (unsigned(cut_bin) = unsigned(std_logic_vector(to_unsigned(28, 5)))) then
                                state <= ST_IDLE;
                                busy_reg <= '0';
                                done_reg <= '1';
                            else
                                if unsigned(cut_bin) = unsigned(std_logic_vector(to_unsigned(28, 5))) then
                                    cut_bin <= std_logic_vector(to_unsigned(3, 5));
                                    cut_range <= std_logic_vector(resize(unsigned(cut_range), 7) + resize(unsigned(std_logic_vector(to_unsigned(1, 7))), 7));
                                else
                                    cut_bin <= std_logic_vector(resize(unsigned(cut_bin), 5) + resize(unsigned(std_logic_vector(to_unsigned(1, 5))), 5));
                                end if;
                                state <= ST_SCAN_INIT;
                            end if;
                        end if;
                    when others =>
                        state <= ST_IDLE;
                        busy_reg <= '0';
                end case;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if ram_read_enable = '1' then
                mem_q <= power_mem(to_integer(unsigned(ram_read_addr)));
            end if;
        end if;
    end process;

    busy <= busy_reg;
    done <= done_reg;
    overflow_event <= overflow_event_reg;
    overflow_sticky <= overflow_sticky_reg;
    protocol_error <= protocol_error_reg;
    map_ready <= map_ready_int;
    out_valid <= out_valid_int;

end architecture rtl;

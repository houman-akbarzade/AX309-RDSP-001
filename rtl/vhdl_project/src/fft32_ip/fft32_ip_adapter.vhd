-- AUTO-TRANSLATED from fft32_ip/fft32_ip_adapter.v; independent validation REQUIRED.
-- Source SHA256: 170642d68eb37794c86716eb6ac562964a7248e71df440e28f27b037ea3f5de7
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity fft32_dit is
    port (
        clk : in std_logic;
        rst : in std_logic;
        start : in std_logic;
        range_in : in std_logic_vector(6 downto 0);
        in_valid : in std_logic;
        in_ready : out std_logic;
        in_re : in std_logic_vector(22 downto 0);
        in_im : in std_logic_vector(22 downto 0);
        out_valid : out std_logic;
        out_ready : in std_logic;
        out_last : out std_logic;
        out_re : out std_logic_vector(24 downto 0);
        out_im : out std_logic_vector(24 downto 0);
        range_out : out std_logic_vector(6 downto 0);
        busy : out std_logic;
        done : out std_logic;
        overflow_event : out std_logic;
        overflow_sticky : out std_logic;
        overflow_stage : out std_logic_vector(2 downto 0);
        overflow_butterfly : out std_logic_vector(3 downto 0);
        overflow_mask : out std_logic_vector(3 downto 0);
        overflow_pre_plus_re : out std_logic_vector(63 downto 0);
        overflow_pre_plus_im : out std_logic_vector(63 downto 0);
        overflow_pre_minus_re : out std_logic_vector(63 downto 0);
        overflow_pre_minus_im : out std_logic_vector(63 downto 0);
        protocol_error : out std_logic
    );
end entity fft32_dit;

architecture rtl of fft32_dit is
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

    constant IDLE : integer := 0;
    constant LOAD : integer := 1;
    constant START_IP : integer := 2;
    constant RUN_IP : integer := 3;
    type samples_array_t is array (0 to 31) of std_logic_vector(45 downto 0);
    signal samples : samples_array_t;
    signal state : std_logic_vector(1 downto 0);
    signal load_index : std_logic_vector(4 downto 0);
    signal write_index : std_logic_vector(4 downto 0);
    signal ip_xn : std_logic_vector(4 downto 0);
    signal ip_xk : std_logic_vector(4 downto 0);
    signal input_sample : std_logic_vector(45 downto 0);
    signal ip_dv : std_logic;
    signal ip_overflow : std_logic;
    signal ip_ce : std_logic;
    signal start_ip_flag : std_logic;
    signal range_out_reg : std_logic_vector(6 downto 0);
    signal done_reg : std_logic;
    signal overflow_sticky_reg : std_logic;
    signal protocol_error_reg : std_logic;
    signal in_ready_int : std_logic;
    signal out_valid_int : std_logic;
    signal out_last_int : std_logic;
begin

    write_index <= std_logic_vector'(load_index(0) & load_index(1) & load_index(2) & load_index(3) & load_index(4));
    input_sample <= samples(to_integer(unsigned(ip_xn)));
    ip_ce <= '1' when not (((unsigned(state) = to_unsigned(RUN_IP, 2)) and (ip_dv = '1')) and (not (out_ready = '1'))) else '0';
    in_ready_int <= '1' when unsigned(state) = to_unsigned(LOAD, 2) else '0';
    out_valid_int <= '1' when (unsigned(state) = to_unsigned(RUN_IP, 2)) and (ip_dv = '1') else '0';
    out_last_int <= '1' when (out_valid_int = '1') and (unsigned(ip_xk) = to_unsigned(31, 5)) else '0';
    busy <= '1' when unsigned(state) /= to_unsigned(IDLE, 2) else '0';
    overflow_event <= '1' when (unsigned(state) = to_unsigned(RUN_IP, 2)) and (ip_overflow = '1') else '0';
    overflow_stage <= std_logic_vector(to_unsigned(0, 3));
    overflow_butterfly <= std_logic_vector(to_unsigned(0, 4));
    overflow_mask <= std_logic_vector(to_unsigned(15, 4)) when ip_overflow = '1' else std_logic_vector(to_unsigned(0, 4));
    overflow_pre_plus_re <= std_logic_vector(to_signed(0, 64));
    overflow_pre_plus_im <= (others => '0');
    overflow_pre_minus_re <= std_logic_vector(to_signed(0, 64));
    overflow_pre_minus_im <= (others => '0');

    start_ip_flag <= '1' when unsigned(state)=to_unsigned(START_IP,2) else '0';

    u_ip : entity work.fft32_ip
        port map (
            clk => clk,
            ce => ip_ce,
            sclr => rst,
            start => start_ip_flag,
            unload => '1',
            fwd_inv => '1',
            fwd_inv_we => '1',
            scale_sch => std_logic_vector(to_unsigned(324, 10)),
            scale_sch_we => '1',
            xn_re => std_logic_vector'(repeat_slv(input_sample(22), 2) & input_sample(22 downto 0)),
            xn_im => std_logic_vector'(repeat_slv(input_sample(45), 2) & input_sample(45 downto 23)),
            rfd => open,
            xn_index => ip_xn,
            busy => open,
            edone => open,
            done => open,
            dv => ip_dv,
            ovflo => ip_overflow,
            xk_index => ip_xk,
            xk_re => out_re,
            xk_im => out_im
        );

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= std_logic_vector(to_unsigned(IDLE, 2));
                load_index <= std_logic_vector(to_unsigned(0, 5));
                range_out_reg <= std_logic_vector(to_unsigned(0, 7));
                done_reg <= '0';
                overflow_sticky_reg <= '0';
                protocol_error_reg <= '0';
            else
                done_reg <= '0';
                if (start = '1') and (unsigned(state) /= to_unsigned(IDLE, 2)) then
                    protocol_error_reg <= '1';
                end if;
                if (in_valid = '1') and (not (in_ready_int = '1')) then
                    protocol_error_reg <= '1';
                end if;
                if (unsigned(state) = to_unsigned(RUN_IP, 2)) and (ip_overflow = '1') then
                    overflow_sticky_reg <= '1';
                end if;
                case to_integer(unsigned(state)) is
                    when IDLE =>
                        if start = '1' then
                            state <= std_logic_vector(to_unsigned(LOAD, 2));
                            load_index <= std_logic_vector(to_unsigned(0, 5));
                            range_out_reg <= range_in;
                            overflow_sticky_reg <= '0';
                        end if;
                    when LOAD =>
                        if in_valid = '1' then
                            samples(to_integer(unsigned(write_index))) <= std_logic_vector'(in_im & in_re);
                            if unsigned(load_index) = to_unsigned(31, 5) then
                                state <= std_logic_vector(to_unsigned(START_IP, 2));
                            else
                                load_index <= std_logic_vector(resize(unsigned(load_index), 5) + to_unsigned(1, 5));
                            end if;
                        end if;
                    when START_IP =>
                        state <= std_logic_vector(to_unsigned(RUN_IP, 2));
                    when RUN_IP =>
                        if (out_last_int = '1') and (out_ready = '1') then
                            done_reg <= '1';
                            state <= std_logic_vector(to_unsigned(IDLE, 2));
                        end if;
                    when others =>
                        null;
                end case;
            end if;
        end if;
    end process;

    range_out <= range_out_reg;
    done <= done_reg;
    overflow_sticky <= overflow_sticky_reg;
    protocol_error <= protocol_error_reg;
    in_ready <= in_ready_int;
    out_valid <= out_valid_int;
    out_last <= out_last_int;

end architecture rtl;

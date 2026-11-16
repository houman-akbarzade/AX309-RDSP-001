-- AUTO-TRANSLATED from integration/radar_cpi_core.v; independent validation REQUIRED.
-- Source SHA256: fe5afea6408acca90b8232c5c240ec0ba984fb76abc727e53f16390f71a52cd4
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity radar_cpi_core is
    port (
        clk : in std_logic;
        rst : in std_logic;
        start : in std_logic;
        debug_read : in std_logic;
        debug_addr : in std_logic_vector(11 downto 0);
        debug_power : out std_logic_vector(45 downto 0);
        iq_read_addr : out std_logic_vector(12 downto 0);
        iq_read_word : in std_logic_vector(31 downto 0);
        out_valid : out std_logic;
        out_ready : in std_logic;
        out_record_id : out std_logic_vector(9 downto 0);
        out_range : out std_logic_vector(6 downto 0);
        out_bin : out std_logic_vector(4 downto 0);
        out_signed_bin : out std_logic_vector(5 downto 0);
        out_peak_power : out std_logic_vector(45 downto 0);
        out_cluster_cells : out std_logic_vector(11 downto 0);
        out_tie_flag : out std_logic;
        out_equal_power_cells : out std_logic_vector(11 downto 0);
        busy : out std_logic;
        done : out std_logic;
        error : out std_logic;
        saturation_sticky : out std_logic;
        power_valid : out std_logic;
        power_value : out std_logic_vector(45 downto 0);
        power_range : out std_logic_vector(6 downto 0);
        power_bin : out std_logic_vector(4 downto 0)
    );
end entity radar_cpi_core;

architecture rtl of radar_cpi_core is
    constant IDLE : integer := 0;
    constant BEGIN_RANGE : integer := 1;
    constant MF_BEGIN : integer := 2;
    constant TAP_ADDR : integer := 3;
    constant TAP_WAIT : integer := 4;
    constant TAP_SEND : integer := 5;
    constant MF_WAIT : integer := 6;
    constant MTI_SEND : integer := 7;
    constant FFT_SEND : integer := 8;
    constant FFT_WAIT : integer := 9;
    constant WAIT_GROUP : integer := 10;
    signal state : std_logic_vector(3 downto 0);
    signal range_index : std_logic_vector(6 downto 0);
    signal load_index : std_logic_vector(4 downto 0);
    signal bin_index : std_logic_vector(4 downto 0);
    signal second_pulse : std_logic;
    signal tap : std_logic_vector(3 downto 0);
    signal zero_sample : std_logic;
    signal previous_re : std_logic_vector(21 downto 0);
    signal previous_im : std_logic_vector(21 downto 0);
    signal reversed_pulse : std_logic_vector(4 downto 0);
    signal pulse : std_logic_vector(5 downto 0);
    signal sample_index : std_logic_vector(8 downto 0);
    signal mf_start : std_logic;
    signal mf_done : std_logic;
    signal mf_sat : std_logic;
    signal mf_error : std_logic;
    signal mti_send_flag : std_logic;
    signal tap_send_flag : std_logic;
    signal begin_range_flag : std_logic;
    signal detect_start_flag : std_logic;
    signal power_value_int : std_logic_vector(45 downto 0);
    signal mf_re : std_logic_vector(21 downto 0);
    signal mf_im : std_logic_vector(21 downto 0);
    signal sample_re_selected : std_logic_vector(15 downto 0);
    signal sample_im_selected : std_logic_vector(15 downto 0);
    signal mti_valid : std_logic;
    signal diff_re : std_logic_vector(22 downto 0);
    signal diff_im : std_logic_vector(22 downto 0);
    signal fft_ready : std_logic;
    signal fft_valid : std_logic;
    signal fft_done : std_logic;
    signal fft_last : std_logic;
    signal fft_sat : std_logic;
    signal fft_error : std_logic;
    signal fft_re : std_logic_vector(24 downto 0);
    signal fft_im : std_logic_vector(24 downto 0);
    signal pow_ready : std_logic;
    signal map_ready : std_logic;
    signal group_done : std_logic;
    signal group_error : std_logic;
    signal group_overflow : std_logic;
    signal group_invalid : std_logic;
    signal pow_sat : std_logic;
    signal iq_read_addr_reg : std_logic_vector(12 downto 0);
    signal busy_reg : std_logic;
    signal done_reg : std_logic;
    signal saturation_sticky_reg : std_logic;
    signal power_valid_int : std_logic;
    signal power_bin_int : std_logic_vector(4 downto 0);
begin

    reversed_pulse <= std_logic_vector'(load_index(0) & load_index(1) & load_index(2) & load_index(3) & load_index(4));
    pulse <= std_logic_vector(resize(unsigned(std_logic_vector'('0' & reversed_pulse)), 6) + unsigned(std_logic_vector'("00000" & second_pulse)));
    sample_index <= std_logic_vector(unsigned(std_logic_vector(resize(unsigned(std_logic_vector'("00" & range_index)), 9) + resize(unsigned(std_logic_vector(to_unsigned(15, 9))), 9))) - resize(unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 5)) & tap)), 9));
    mf_start <= '1' when unsigned(state) = to_unsigned(MF_BEGIN, 4) else '0';
    sample_re_selected <= std_logic_vector(to_unsigned(0, 16)) when zero_sample = '1' else iq_read_word(15 downto 0);
    sample_im_selected <= std_logic_vector(to_unsigned(0, 16)) when zero_sample = '1' else iq_read_word(31 downto 16);
    error <= ((((mf_error) or (fft_error)) or (group_error)) or (group_overflow)) or (group_invalid);

    u_mf : entity work.mf16_serial_mac
        port map (
            clk => clk,
            rst => rst,
            start => mf_start,
            range_in => range_index,
            tap_valid => tap_send_flag,
            tap_index => tap,
            sample_re => sample_re_selected,
            sample_im => sample_im_selected,
            busy => open,
            done => mf_done,
            range_out => open,
            result_re => mf_re,
            result_im => mf_im,
            saturation_event => mf_sat,
            saturation_mask => open,
            prelimit_re => open,
            prelimit_im => open,
            protocol_error => mf_error
        );

    detect_start_flag <= '1' when start='1' and busy_reg='0' else '0';
    power_value <= power_value_int;
    tap_send_flag <= '1' when unsigned(state)=to_unsigned(TAP_SEND,4) else '0';
    mti_send_flag <= '1' when unsigned(state)=to_unsigned(MTI_SEND,4) else '0';
    begin_range_flag <= '1' when unsigned(state)=to_unsigned(BEGIN_RANGE,4) else '0';

    u_mti : entity work.mti2_diff
        port map (
            clk => clk,
            rst => rst,
            in_valid => mti_send_flag,
            pulse_next_re => mf_re,
            pulse_next_im => mf_im,
            pulse_prev_re => previous_re,
            pulse_prev_im => previous_im,
            range_in => range_index,
            pulse_in => reversed_pulse,
            out_valid => mti_valid,
            diff_re => diff_re,
            diff_im => diff_im,
            range_out => open,
            pulse_out => open
        );

    u_fft : entity work.fft32_dit
        port map (
            clk => clk,
            rst => rst,
            start => begin_range_flag,
            range_in => range_index,
            in_valid => mti_valid,
            in_ready => fft_ready,
            in_re => diff_re,
            in_im => diff_im,
            out_valid => fft_valid,
            out_ready => pow_ready,
            out_last => fft_last,
            out_re => fft_re,
            out_im => fft_im,
            range_out => open,
            busy => open,
            done => fft_done,
            overflow_event => open,
            overflow_sticky => fft_sat,
            overflow_stage => open,
            overflow_butterfly => open,
            overflow_mask => open,
            overflow_pre_plus_re => open,
            overflow_pre_plus_im => open,
            overflow_pre_minus_re => open,
            overflow_pre_minus_im => open,
            protocol_error => fft_error
        );

    u_power : entity work.power_q25_u46_serial
        port map (
            clk => clk,
            rst => rst,
            in_valid => fft_valid,
            in_ready => pow_ready,
            in_re => fft_re,
            in_im => fft_im,
            range_in => range_index,
            bin_in => bin_index,
            out_valid => power_valid_int,
            out_ready => map_ready,
            power_out => power_value_int,
            range_out => power_range,
            bin_out => power_bin_int,
            overflow_sticky => pow_sat
        );

    u_detect : entity work.cfar_grouping_subsystem
        port map (
            clk => clk,
            rst => rst,
            start => detect_start_flag,
            debug_read => debug_read,
            debug_addr => debug_addr,
            debug_power => debug_power,
            map_valid => power_valid_int,
            map_ready => map_ready,
            map_power => power_value_int,
            cut_pause => '0',
            out_valid => out_valid,
            out_ready => out_ready,
            out_record_id => out_record_id,
            out_range => out_range,
            out_bin => out_bin,
            out_signed_bin => out_signed_bin,
            out_peak_power => out_peak_power,
            out_cluster_cells => out_cluster_cells,
            out_tie_flag => out_tie_flag,
            out_equal_power_cells => out_equal_power_cells,
            busy => open,
            done => group_done,
            scanner_done => open,
            overflow_sticky => group_overflow,
            protocol_error => group_error,
            frame_invalid => group_invalid
        );

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= std_logic_vector(to_unsigned(IDLE, 4));
                busy_reg <= '0';
                done_reg <= '0';
                range_index <= std_logic_vector(to_unsigned(0, 7));
                load_index <= std_logic_vector(to_unsigned(0, 5));
                bin_index <= std_logic_vector(to_unsigned(0, 5));
                second_pulse <= '0';
                tap <= std_logic_vector(to_unsigned(0, 4));
                zero_sample <= '0';
                previous_re <= std_logic_vector(to_signed(0, 22));
                previous_im <= std_logic_vector(to_signed(0, 22));
                iq_read_addr_reg <= std_logic_vector(to_unsigned(0, 13));
                saturation_sticky_reg <= '0';
            else
                done_reg <= '0';
                if (mf_sat='1') or (fft_sat='1') or (pow_sat='1') then
                    saturation_sticky_reg <= '1';
                end if;
                if (fft_valid = '1') and (pow_ready = '1') then
                    bin_index <= std_logic_vector(resize(unsigned(bin_index), 5) + to_unsigned(1, 5));
                end if;
                case to_integer(unsigned(state)) is
                    when IDLE =>
                        if start = '1' then
                            busy_reg <= '1';
                            range_index <= std_logic_vector(to_unsigned(0, 7));
                            state <= std_logic_vector(to_unsigned(BEGIN_RANGE, 4));
                        end if;
                    when BEGIN_RANGE =>
                        load_index <= std_logic_vector(to_unsigned(0, 5));
                        bin_index <= std_logic_vector(to_unsigned(0, 5));
                        second_pulse <= '0';
                        state <= std_logic_vector(to_unsigned(MF_BEGIN, 4));
                    when MF_BEGIN =>
                        tap <= std_logic_vector(to_unsigned(0, 4));
                        state <= std_logic_vector(to_unsigned(TAP_ADDR, 4));
                    when TAP_ADDR =>
                        iq_read_addr_reg <= std_logic_vector(resize(unsigned(std_logic_vector'(pulse & "0000000")), 13) + resize(unsigned(sample_index), 13));
                        if unsigned(sample_index) >= to_unsigned(128, 9) then
    zero_sample <= '1';
else
    zero_sample <= '0';
end if;
                        state <= std_logic_vector(to_unsigned(TAP_WAIT, 4));
                    when TAP_WAIT =>
                        state <= std_logic_vector(to_unsigned(TAP_SEND, 4));
                    when TAP_SEND =>
                        if unsigned(tap) = to_unsigned(15, 4) then
                            state <= std_logic_vector(to_unsigned(MF_WAIT, 4));
                        else
                            tap <= std_logic_vector(resize(unsigned(tap), 4) + to_unsigned(1, 4));
                            state <= std_logic_vector(to_unsigned(TAP_ADDR, 4));
                        end if;
                    when MF_WAIT =>
                        if mf_done = '1' then
                            if not (second_pulse = '1') then
                                previous_re <= mf_re;
                                previous_im <= mf_im;
                                second_pulse <= '1';
                                state <= std_logic_vector(to_unsigned(MF_BEGIN, 4));
                            else
                                state <= std_logic_vector(to_unsigned(MTI_SEND, 4));
                            end if;
                        end if;
                    when MTI_SEND =>
                        state <= std_logic_vector(to_unsigned(FFT_SEND, 4));
                    when FFT_SEND =>
                        second_pulse <= '0';
                        if unsigned(load_index) = to_unsigned(31, 5) then
                            state <= std_logic_vector(to_unsigned(FFT_WAIT, 4));
                        else
                            load_index <= std_logic_vector(resize(unsigned(load_index), 5) + to_unsigned(1, 5));
                            state <= std_logic_vector(to_unsigned(MF_BEGIN, 4));
                        end if;
                    when FFT_WAIT =>
                        if ((power_valid_int = '1') and (map_ready = '1')) and (unsigned(power_bin_int) = to_unsigned(31, 5)) then
                            if unsigned(range_index) = to_unsigned(127, 7) then
                                state <= std_logic_vector(to_unsigned(WAIT_GROUP, 4));
                            else
                                range_index <= std_logic_vector(resize(unsigned(range_index), 7) + to_unsigned(1, 7));
                                state <= std_logic_vector(to_unsigned(BEGIN_RANGE, 4));
                            end if;
                        end if;
                    when WAIT_GROUP =>
                        if group_done = '1' then
                            busy_reg <= '0';
                            done_reg <= '1';
                            state <= std_logic_vector(to_unsigned(IDLE, 4));
                        end if;
                    when others =>
                        null;
                end case;
            end if;
        end if;
    end process;

    iq_read_addr <= iq_read_addr_reg;
    busy <= busy_reg;
    done <= done_reg;
    saturation_sticky <= saturation_sticky_reg;
    power_valid <= power_valid_int;
    power_bin <= power_bin_int;

end architecture rtl;

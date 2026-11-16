-- AUTO-TRANSLATED from integration/cfar_grouping_subsystem.v; independent validation REQUIRED.
-- Source SHA256: fa33ca48dd3a5065c6ccf520f2f89cfe8617ccbdf954431b9fcff0330fb8fa41
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity cfar_grouping_subsystem is
    generic (
        GROUP_MAX_LABELS : integer := 702
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        start : in std_logic;
        debug_read : in std_logic;
        debug_addr : in std_logic_vector(11 downto 0);
        debug_power : out std_logic_vector(45 downto 0);
        map_valid : in std_logic;
        cut_pause : in std_logic;
        map_ready : out std_logic;
        map_power : in std_logic_vector(45 downto 0);
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
        scanner_done : out std_logic;
        overflow_sticky : out std_logic;
        protocol_error : out std_logic;
        frame_invalid : out std_logic
    );
end entity cfar_grouping_subsystem;

architecture rtl of cfar_grouping_subsystem is
    signal cut_valid : std_logic;
    signal cut_ready : std_logic;
    signal cut_alarm : std_logic;
    signal group_ready : std_logic;
    signal group_valid : std_logic;
    signal cut_range : std_logic_vector(6 downto 0);
    signal cut_bin : std_logic_vector(4 downto 0);
    signal cut_power : std_logic_vector(45 downto 0);
    signal scan_busy : std_logic;
    signal group_busy : std_logic;
    signal scan_overflow : std_logic;
    signal scan_proto : std_logic;
    signal group_overflow : std_logic;
    signal group_proto : std_logic;
    signal group_invalid : std_logic;
begin

    cut_ready <= (group_ready) and (not cut_pause);
    group_valid <= (cut_valid) and (not cut_pause);
    busy <= (scan_busy) or (group_busy);
    overflow_sticky <= (scan_overflow) or (group_overflow);
    protocol_error <= (scan_proto) or (group_proto);
    frame_invalid <= ((group_invalid) or (scan_overflow)) or (scan_proto);

    u_scanner : entity work.cfar_2d_scan
        port map (
            clk => clk,
            rst => rst,
            start => start,
            debug_read => debug_read,
            debug_addr => debug_addr,
            debug_power => debug_power,
            map_valid => map_valid,
            map_ready => map_ready,
            map_power => map_power,
            out_valid => cut_valid,
            out_ready => cut_ready,
            out_range => cut_range,
            out_bin => cut_bin,
            out_power => cut_power,
            out_sum40 => open,
            out_alarm => cut_alarm,
            out_equality => open,
            busy => scan_busy,
            done => scanner_done,
            overflow_event => open,
            overflow_sticky => scan_overflow,
            protocol_error => scan_proto
        );

    u_grouping : entity work.grouping_8conn
        generic map (
            MAX_LABELS => GROUP_MAX_LABELS
        )
        port map (
            clk => clk,
            rst => rst,
            start => start,
            in_valid => group_valid,
            in_ready => group_ready,
            in_range => cut_range,
            in_bin => cut_bin,
            in_power => cut_power,
            in_alarm => cut_alarm,
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
            busy => group_busy,
            done => done,
            overflow_sticky => group_overflow,
            protocol_error => group_proto,
            frame_invalid => group_invalid
        );


end architecture rtl;

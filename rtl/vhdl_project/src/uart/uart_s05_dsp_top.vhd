-- AUTO-TRANSLATED from uart/uart_s05_dsp_top.v; independent validation REQUIRED.
-- Source SHA256: 0ba70959709102204c48e43e817baa9e74c84bc2326ab41e395ec09bb930260a
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity uart_s05_dsp_top is
    generic (
        CLOCK_HZ : integer := 50000000;
        BAUD : integer := 115200;
        TIMEOUT_CLKS : integer := 86800;
        TX_ACK_TIMEOUT_CLKS : integer := 100000000
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        uart_rxd : in std_logic;
        uart_txd : out std_logic;
        active_session : out std_logic;
        expected_seq : out std_logic_vector(31 downto 0);
        activation_count : out std_logic_vector(31 downto 0);
        accepted_count : out std_logic_vector(31 downto 0);
        duplicate_count : out std_logic_vector(31 downto 0);
        stale_count : out std_logic_vector(31 downto 0);
        nack_count : out std_logic_vector(31 downto 0);
        good_frames : out std_logic_vector(15 downto 0);
        crc_errors : out std_logic_vector(15 downto 0);
        header_errors : out std_logic_vector(15 downto 0);
        length_errors : out std_logic_vector(15 downto 0);
        partial_timeouts : out std_logic_vector(15 downto 0);
        uart_errors : out std_logic_vector(15 downto 0);
        cpi_open : out std_logic;
        cpi_id : out std_logic_vector(31 downto 0);
        iq_uploaded_bytes : out std_logic_vector(14 downto 0);
        iq_readback_acked_bytes : out std_logic_vector(14 downto 0);
        tx_next_seq : out std_logic_vector(31 downto 0);
        tx_retry_exhausted : out std_logic
    );
end entity uart_s05_dsp_top;

architecture rtl of uart_s05_dsp_top is
    signal rx_byte : std_logic_vector(7 downto 0);
    signal tx_byte : std_logic_vector(7 downto 0);
    signal rd_byte : std_logic_vector(7 downto 0);
    signal rx_valid : std_logic;
    signal rx_framing_error : std_logic;
    signal tx_valid : std_logic;
    signal tx_ready : std_logic;
    signal frame_ready : std_logic;
    signal frame_done : std_logic;
    signal frame_type : std_logic_vector(7 downto 0);
    signal frame_flags : std_logic_vector(7 downto 0);
    signal frame_seq : std_logic_vector(31 downto 0);
    signal frame_crc : std_logic_vector(31 downto 0);
    signal frame_length : std_logic_vector(15 downto 0);
    signal rd_index : std_logic_vector(9 downto 0);
    signal reply_valid : std_logic;
    signal reply_ready : std_logic;
    signal reply_type : std_logic_vector(7 downto 0);
    signal reply_opcode : std_logic_vector(7 downto 0);
    signal reply_sid : std_logic_vector(127 downto 0);
    signal reply_seq : std_logic_vector(31 downto 0);
    signal reply_number : std_logic_vector(31 downto 0);
    signal iq_write_en : std_logic;
    signal iq_write_addr : std_logic_vector(12 downto 0);
    signal iq_read_addr : std_logic_vector(12 downto 0);
    signal iq_write_data : std_logic_vector(31 downto 0);
    signal iq_read_word : std_logic_vector(31 downto 0);
    signal stage_cpi_id : std_logic_vector(31 downto 0);
    signal stage_offset : std_logic_vector(31 downto 0);
    signal stage_count : std_logic_vector(15 downto 0);
    signal dsp_start : std_logic;
    signal dsp_clear : std_logic;
    signal dsp_busy : std_logic;
    signal dsp_done : std_logic;
    signal dsp_error : std_logic;
    signal dsp_sat : std_logic;
    signal result_valid : std_logic;
    signal result_ready : std_logic;
    signal map_enable : std_logic;
    signal result_data : std_logic_vector(98 downto 0);
    signal result_record : std_logic_vector(98 downto 0);
    signal stage_kind : std_logic_vector(7 downto 0);
    signal map_base : std_logic_vector(11 downto 0);
    signal map_addr : std_logic_vector(11 downto 0);
    signal map_power : std_logic_vector(45 downto 0);
    signal terminal_count : std_logic_vector(15 downto 0);
    signal dsp_addr : std_logic_vector(12 downto 0);
    signal selected_iq_read_addr : std_logic_vector(12 downto 0);
    signal rid : std_logic_vector(9 downto 0);
    signal rr : std_logic_vector(6 downto 0);
    signal rb : std_logic_vector(4 downto 0);
    signal rs : std_logic_vector(5 downto 0);
    signal rp : std_logic_vector(45 downto 0);
    signal cells : std_logic_vector(11 downto 0);
    signal eq : std_logic_vector(11 downto 0);
    signal tie : std_logic;
begin

    result_data <= std_logic_vector'(rid & rr & rb & rs & rp & cells & tie & eq);

    u_rx : entity work.uart_rx_8n1
        generic map (
            CLOCK_HZ => CLOCK_HZ,
            BAUD => BAUD
        )
        port map (
            clk => clk,
            rst => rst,
            rx_pin => uart_rxd,
            data_out => rx_byte,
            data_valid => rx_valid,
            framing_error => rx_framing_error,
            busy => open
        );

    u_parser : entity work.s02_frame_echo
        generic map (
            TIMEOUT_CLKS => TIMEOUT_CLKS,
            ECHO_MODE => 0
        )
        port map (
            clk => clk,
            rst => rst,
            rx_data => rx_byte,
            rx_valid => rx_valid,
            rx_framing_error => rx_framing_error,
            tx_data => open,
            tx_valid => open,
            tx_ready => '0',
            good_count => good_frames,
            crc_error_count => crc_errors,
            header_error_count => header_errors,
            length_error_count => length_errors,
            partial_timeout_count => partial_timeouts,
            uart_error_count => uart_errors,
            busy_drop_count => open,
            response_busy => open,
            frame_ready => frame_ready,
            frame_done => frame_done,
            frame_type => frame_type,
            frame_flags => frame_flags,
            frame_seq => frame_seq,
            frame_length => frame_length,
            frame_crc => frame_crc,
            frame_rd_index => rd_index,
            frame_rd_byte => rd_byte
        );

    u_core : entity work.radar_cpi_core
        port map (
            clk => clk,
            rst => (rst) or (dsp_clear),
            start => dsp_start,
            iq_read_addr => dsp_addr,
            iq_read_word => iq_read_word,
            out_valid => result_valid,
            out_ready => result_ready,
            out_record_id => rid,
            out_range => rr,
            out_bin => rb,
            out_signed_bin => rs,
            out_peak_power => rp,
            out_cluster_cells => cells,
            out_tie_flag => tie,
            out_equal_power_cells => eq,
            busy => dsp_busy,
            done => dsp_done,
            error => dsp_error,
            saturation_sticky => dsp_sat,
            power_valid => open,
            power_value => open,
            power_range => open,
            power_bin => open,
            debug_read => map_enable,
            debug_addr => map_addr,
            debug_power => map_power
        );

    u_session : entity work.s05_dsp_session_arq
        generic map (
            TX_ACK_TIMEOUT_CLKS => TX_ACK_TIMEOUT_CLKS
        )
        port map (
            dsp_start => dsp_start,
            dsp_clear => dsp_clear,
            dsp_busy => dsp_busy,
            dsp_done => dsp_done,
            dsp_error => dsp_error,
            dsp_saturation => dsp_sat,
            result_valid => result_valid,
            result_ready => result_ready,
            result_data => result_data,
            result_record => result_record,
            stage_kind => stage_kind,
            map_base => map_base,
            terminal_count => terminal_count,
            map_read_enable => map_enable,
            clk => clk,
            rst => rst,
            frame_ready => frame_ready,
            frame_done => frame_done,
            frame_type => frame_type,
            frame_flags => frame_flags,
            frame_seq => frame_seq,
            frame_length => frame_length,
            frame_crc => frame_crc,
            rd_index => rd_index,
            rd_byte => rd_byte,
            reply_ready => reply_ready,
            reply_valid => reply_valid,
            reply_type => reply_type,
            reply_opcode => reply_opcode,
            reply_sid => reply_sid,
            reply_seq => reply_seq,
            reply_number => reply_number,
            active_session => active_session,
            rx_expected_seq => expected_seq,
            activation_count => activation_count,
            accepted_count => accepted_count,
            duplicate_count => duplicate_count,
            stale_count => stale_count,
            nack_count => nack_count,
            cpi_id => cpi_id,
            cpi_open => cpi_open,
            iq_uploaded_bytes => iq_uploaded_bytes,
            iq_write_en => iq_write_en,
            iq_write_addr => iq_write_addr,
            iq_write_data => iq_write_data,
            iq_readback_acked_bytes => iq_readback_acked_bytes,
            stage_cpi_id => stage_cpi_id,
            stage_offset => stage_offset,
            stage_count => stage_count,
            tx_next_seq => tx_next_seq,
            tx_retry_exhausted => tx_retry_exhausted
        );

    u_reply : entity work.s05_dsp_reply_tx
        port map (
            stage_kind => stage_kind,
            map_base => map_base,
            map_read_addr => map_addr,
            map_read_power => map_power,
            result_record => result_record,
            terminal_count => terminal_count,
            clk => clk,
            rst => rst,
            send_valid => reply_valid,
            send_ready => reply_ready,
            response_type => reply_type,
            response_opcode => reply_opcode,
            response_sid => reply_sid,
            response_seq => reply_seq,
            response_number => reply_number,
            stage_cpi_id => stage_cpi_id,
            stage_offset => stage_offset,
            stage_count => stage_count,
            iq_read_addr => iq_read_addr,
            iq_read_word => iq_read_word,
            tx_data => tx_byte,
            tx_valid => tx_valid,
            tx_ready => tx_ready,
            busy => open
        );

    selected_iq_read_addr <= dsp_addr when dsp_busy='1' else iq_read_addr;

    u_iq_store : entity work.s05_iq_cpi_banked
        port map (
            clk => clk,
            write_en => iq_write_en,
            write_addr => iq_write_addr,
            write_word => iq_write_data,
            read_addr => selected_iq_read_addr,
            read_word => iq_read_word
        );

    u_tx : entity work.uart_tx_8n1
        generic map (
            CLOCK_HZ => CLOCK_HZ,
            BAUD => BAUD
        )
        port map (
            clk => clk,
            rst => rst,
            data_in => tx_byte,
            data_valid => tx_valid,
            data_ready => tx_ready,
            tx_pin => uart_txd,
            byte_done => open
        );


end architecture rtl;

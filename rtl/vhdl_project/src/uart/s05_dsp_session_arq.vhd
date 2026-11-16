-- AUTO-TRANSLATED from uart/s05_dsp_session_arq.v; independent validation REQUIRED.
-- Source SHA256: 4b46d7fe137674bea1ce3b2bbdeb0391153c197029b44aa222e7f1298fabb6e4
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity s05_dsp_session_arq is
    generic (
        TX_ACK_TIMEOUT_CLKS : integer := 100000000;
        TX_MAX_RETRIES : integer := 3
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        dsp_start : out std_logic;
        dsp_clear : out std_logic;
        dsp_busy : in std_logic;
        dsp_done : in std_logic;
        dsp_error : in std_logic;
        dsp_saturation : in std_logic;
        result_valid : in std_logic;
        result_ready : out std_logic;
        result_data : in std_logic_vector(98 downto 0);
        result_record : out std_logic_vector(98 downto 0);
        stage_kind : out std_logic_vector(7 downto 0);
        map_base : out std_logic_vector(11 downto 0);
        terminal_count : out std_logic_vector(15 downto 0);
        map_read_enable : out std_logic;
        frame_ready : in std_logic;
        frame_done : out std_logic;
        frame_type : in std_logic_vector(7 downto 0);
        frame_flags : in std_logic_vector(7 downto 0);
        frame_seq : in std_logic_vector(31 downto 0);
        frame_length : in std_logic_vector(15 downto 0);
        frame_crc : in std_logic_vector(31 downto 0);
        rd_index : out std_logic_vector(9 downto 0);
        rd_byte : in std_logic_vector(7 downto 0);
        reply_ready : in std_logic;
        reply_valid : out std_logic;
        reply_type : out std_logic_vector(7 downto 0);
        reply_opcode : out std_logic_vector(7 downto 0);
        reply_sid : out std_logic_vector(127 downto 0);
        reply_seq : out std_logic_vector(31 downto 0);
        reply_number : out std_logic_vector(31 downto 0);
        active_session : out std_logic;
        rx_expected_seq : out std_logic_vector(31 downto 0);
        activation_count : out std_logic_vector(31 downto 0);
        accepted_count : out std_logic_vector(31 downto 0);
        duplicate_count : out std_logic_vector(31 downto 0);
        stale_count : out std_logic_vector(31 downto 0);
        nack_count : out std_logic_vector(31 downto 0);
        cpi_id : out std_logic_vector(31 downto 0);
        cpi_open : out std_logic;
        iq_uploaded_bytes : out std_logic_vector(14 downto 0);
        iq_write_en : out std_logic;
        iq_write_addr : out std_logic_vector(12 downto 0);
        iq_write_data : out std_logic_vector(31 downto 0);
        iq_readback_acked_bytes : out std_logic_vector(14 downto 0);
        stage_cpi_id : out std_logic_vector(31 downto 0);
        stage_offset : out std_logic_vector(31 downto 0);
        stage_count : out std_logic_vector(15 downto 0);
        tx_next_seq : out std_logic_vector(31 downto 0);
        tx_retry_exhausted : out std_logic
    );
end entity s05_dsp_session_arq;

architecture rtl of s05_dsp_session_arq is
    constant IDLE : std_logic_vector(3 downto 0) := "0000";
    constant READ_SETUP : std_logic_vector(3 downto 0) := "0001";
    constant READ_WAIT : std_logic_vector(3 downto 0) := "0010";
    constant READ_STORE : std_logic_vector(3 downto 0) := "0011";
    constant DECIDE : std_logic_vector(3 downto 0) := "0100";
    constant REPLY_START : std_logic_vector(3 downto 0) := "0101";
    constant REPLY_BUSY : std_logic_vector(3 downto 0) := "0110";
    constant REPLY_DONE : std_logic_vector(3 downto 0) := "0111";
    constant RELEASE : std_logic_vector(3 downto 0) := "1000";
    constant COPY_SETUP : std_logic_vector(3 downto 0) := "1001";
    constant COPY_WAIT : std_logic_vector(3 downto 0) := "1010";
    constant COPY_STORE : std_logic_vector(3 downto 0) := "1011";
    constant COPY_END : std_logic_vector(3 downto 0) := "1100";
    constant STAGE_START : std_logic_vector(3 downto 0) := "1101";
    constant STAGE_BUSY : std_logic_vector(3 downto 0) := "1110";
    signal input_verified : std_logic;
    signal running : std_logic;
    signal finished : std_logic;
    signal terminal_sent : std_logic;
    signal terminal_acked : std_logic;
    signal failed : std_logic;
    signal outbound_kind : std_logic_vector(7 downto 0);
    signal map_acked_bytes : std_logic_vector(15 downto 0);
    signal map_acked_words : std_logic_vector(11 downto 0);
    signal watchdog : std_logic_vector(25 downto 0);
    signal map_expected_count : std_logic_vector(15 downto 0);
    signal state : std_logic_vector(3 downto 0);
    signal read_idx : std_logic_vector(5 downto 0);
    signal read_target : std_logic_vector(5 downto 0);
    signal fields : std_logic_vector(215 downto 0);
    signal sid : std_logic_vector(127 downto 0);
    signal retired_sid : std_logic_vector(127 downto 0);
    signal retired_valid : std_logic;
    signal pending : std_logic;
    signal last_seq : std_logic_vector(31 downto 0);
    signal last_crc : std_logic_vector(31 downto 0);
    signal last_length : std_logic_vector(15 downto 0);
    signal last_type : std_logic_vector(7 downto 0);
    signal last_valid : std_logic;
    signal reply_started : std_logic;
    signal copy_idx : std_logic_vector(9 downto 0);
    signal sample_word : std_logic_vector(31 downto 0);
    signal current_iq_size : std_logic_vector(15 downto 0);
    signal stage_pending : std_logic;
    signal stage_outstanding : std_logic;
    signal tx_ack_ticks : std_logic_vector(31 downto 0);
    signal tx_retries : std_logic_vector(2 downto 0);
    signal expected_read_count : std_logic_vector(15 downto 0);
    signal incoming_read_offset : std_logic_vector(31 downto 0);
    signal incoming_read_count : std_logic_vector(15 downto 0);
    signal incoming_cpi : std_logic_vector(31 downto 0);
    signal incoming_offset : std_logic_vector(31 downto 0);
    signal expected_chunk : std_logic_vector(15 downto 0);
    signal boot_sid : std_logic_vector(127 downto 0);
    signal active_sid : std_logic_vector(127 downto 0);
    signal app_opcode : std_logic_vector(7 downto 0);
    signal app_cpi_id : std_logic_vector(31 downto 0);
    signal dsp_start_reg : std_logic;
    signal dsp_clear_reg : std_logic;
    signal result_record_reg : std_logic_vector(98 downto 0);
    signal stage_kind_reg : std_logic_vector(7 downto 0);
    signal map_base_reg : std_logic_vector(11 downto 0);
    signal terminal_count_reg : std_logic_vector(15 downto 0);
    signal frame_done_reg : std_logic;
    signal rd_index_reg : std_logic_vector(9 downto 0);
    signal reply_type_reg : std_logic_vector(7 downto 0);
    signal reply_opcode_reg : std_logic_vector(7 downto 0);
    signal reply_sid_reg : std_logic_vector(127 downto 0);
    signal reply_seq_reg : std_logic_vector(31 downto 0);
    signal reply_number_reg : std_logic_vector(31 downto 0);
    signal active_session_reg : std_logic;
    signal rx_expected_seq_reg : std_logic_vector(31 downto 0);
    signal activation_count_reg : std_logic_vector(31 downto 0);
    signal accepted_count_reg : std_logic_vector(31 downto 0);
    signal duplicate_count_reg : std_logic_vector(31 downto 0);
    signal stale_count_reg : std_logic_vector(31 downto 0);
    signal nack_count_reg : std_logic_vector(31 downto 0);
    signal cpi_id_reg : std_logic_vector(31 downto 0);
    signal cpi_open_reg : std_logic;
    signal iq_uploaded_bytes_reg : std_logic_vector(14 downto 0);
    signal iq_write_en_reg : std_logic;
    signal iq_write_addr_reg : std_logic_vector(12 downto 0);
    signal iq_write_data_reg : std_logic_vector(31 downto 0);
    signal iq_readback_acked_bytes_reg : std_logic_vector(14 downto 0);
    signal stage_cpi_id_reg : std_logic_vector(31 downto 0);
    signal stage_offset_reg : std_logic_vector(31 downto 0);
    signal stage_count_reg : std_logic_vector(15 downto 0);
    signal tx_next_seq_reg : std_logic_vector(31 downto 0);
    signal tx_retry_exhausted_reg : std_logic;
    signal result_ready_int : std_logic;
begin

    map_expected_count <= std_logic_vector(to_unsigned(480, 16)) when unsigned(map_acked_bytes) < unsigned(std_logic_vector(to_unsigned(24480, 16))) else std_logic_vector(to_unsigned(96, 16));
    expected_read_count <= std_logic_vector(to_unsigned(484, 16)) when unsigned(iq_readback_acked_bytes_reg) < unsigned(std_logic_vector(to_unsigned(16456, 15))) else std_logic_vector(to_unsigned(440, 16));
    incoming_read_offset <= std_logic_vector(resize(unsigned(fields(199 downto 168)), 32));
    incoming_read_count <= std_logic_vector(resize(unsigned(fields(215 downto 200)), 16));
    incoming_cpi <= std_logic_vector(resize(unsigned(fields(159 downto 128)), 32));
    incoming_offset <= std_logic_vector(resize(unsigned(fields(191 downto 160)), 32));
    expected_chunk <= std_logic_vector(to_unsigned(488, 16)) when unsigned(iq_uploaded_bytes_reg) < unsigned(std_logic_vector(to_unsigned(16592, 15))) else std_logic_vector(to_unsigned(304, 16));
    boot_sid <= std_logic_vector(resize(unsigned(fields(143 downto 16)), 128));
    active_sid <= std_logic_vector(resize(unsigned(fields(127 downto 0)), 128));
    app_opcode <= std_logic_vector(resize(unsigned(fields(135 downto 128)), 8));
    app_cpi_id <= std_logic_vector(resize(unsigned(fields(167 downto 136)), 32));
    result_ready_int <= '1' when (((running = '1') and (not (stage_pending = '1'))) and (not (stage_outstanding = '1'))) and (not (tx_retry_exhausted_reg = '1')) else '0';
    map_read_enable <= '1' when (finished = '1') and (not (running = '1')) else '0';
    reply_valid <= '1' when (unsigned(state) = unsigned(REPLY_START)) or (unsigned(state) = unsigned(STAGE_START)) else '0';

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                dsp_start_reg <= '0';
                dsp_clear_reg <= '0';
                input_verified <= '0';
                running <= '0';
                finished <= '0';
                terminal_sent <= '0';
                terminal_acked <= '0';
                failed <= '0';
                outbound_kind <= std_logic_vector(to_unsigned(4, 8));
                terminal_count_reg <= std_logic_vector(to_unsigned(0, 16));
                result_record_reg <= std_logic_vector(to_unsigned(0, 99));
                stage_kind_reg <= std_logic_vector(to_unsigned(0, 8));
                map_base_reg <= std_logic_vector(to_unsigned(0, 12));
                map_acked_bytes <= std_logic_vector(to_unsigned(0, 16));
                map_acked_words <= std_logic_vector(to_unsigned(0, 12));
                watchdog <= std_logic_vector(to_unsigned(0, 26));
                state <= IDLE;
                read_idx <= std_logic_vector(to_unsigned(0, 6));
                read_target <= std_logic_vector(to_unsigned(0, 6));
                rd_index_reg <= std_logic_vector(to_unsigned(0, 10));
                fields <= std_logic_vector(to_unsigned(0, 216));
                frame_done_reg <= '0';
                reply_started <= '0';
                reply_type_reg <= std_logic_vector(to_unsigned(0, 8));
                reply_opcode_reg <= std_logic_vector(to_unsigned(0, 8));
                reply_sid_reg <= std_logic_vector(to_unsigned(0, 128));
                reply_seq_reg <= std_logic_vector(to_unsigned(0, 32));
                reply_number_reg <= std_logic_vector(to_unsigned(0, 32));
                active_session_reg <= '0';
                rx_expected_seq_reg <= std_logic_vector(to_unsigned(0, 32));
                activation_count_reg <= std_logic_vector(to_unsigned(0, 32));
                accepted_count_reg <= std_logic_vector(to_unsigned(0, 32));
                duplicate_count_reg <= std_logic_vector(to_unsigned(0, 32));
                stale_count_reg <= std_logic_vector(to_unsigned(0, 32));
                nack_count_reg <= std_logic_vector(to_unsigned(0, 32));
                cpi_id_reg <= std_logic_vector(to_unsigned(0, 32));
                cpi_open_reg <= '0';
                iq_uploaded_bytes_reg <= std_logic_vector(to_unsigned(0, 15));
                iq_write_en_reg <= '0';
                iq_write_addr_reg <= std_logic_vector(to_unsigned(0, 13));
                iq_write_data_reg <= std_logic_vector(to_unsigned(0, 32));
                copy_idx <= std_logic_vector(to_unsigned(0, 10));
                sample_word <= std_logic_vector(to_unsigned(0, 32));
                current_iq_size <= std_logic_vector(to_unsigned(0, 16));
                iq_readback_acked_bytes_reg <= std_logic_vector(to_unsigned(0, 15));
                stage_cpi_id_reg <= std_logic_vector(to_unsigned(0, 32));
                stage_offset_reg <= std_logic_vector(to_unsigned(0, 32));
                stage_count_reg <= std_logic_vector(to_unsigned(0, 16));
                tx_next_seq_reg <= std_logic_vector(to_unsigned(0, 32));
                tx_retry_exhausted_reg <= '0';
                stage_pending <= '0';
                stage_outstanding <= '0';
                tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                tx_retries <= std_logic_vector(to_unsigned(0, 3));
                pending <= '0';
                sid <= std_logic_vector(to_unsigned(0, 128));
                retired_sid <= std_logic_vector(to_unsigned(0, 128));
                retired_valid <= '0';
                last_seq <= std_logic_vector(to_unsigned(0, 32));
                last_crc <= std_logic_vector(to_unsigned(0, 32));
                last_length <= std_logic_vector(to_unsigned(0, 16));
                last_type <= std_logic_vector(to_unsigned(0, 8));
                last_valid <= '0';
            else
                frame_done_reg <= '0';
                dsp_start_reg <= '0';
                dsp_clear_reg <= '0';
                iq_write_en_reg <= '0';
                if running = '1' then
                    if (not (stage_pending = '1')) and (not (stage_outstanding = '1')) then
                        watchdog <= std_logic_vector(resize(unsigned(watchdog), 26) + to_unsigned(1, 26));
                    end if;
                    if ((dsp_error = '1') or (dsp_saturation = '1')) or (unsigned(watchdog) = unsigned(std_logic_vector(to_unsigned(49999999, 26)))) then
                        failed <= '1';
                        running <= '0';
                        finished <= '1';
                        dsp_clear_reg <= '1';
                    elsif dsp_done = '1' then
                        running <= '0';
                        finished <= '1';
                    end if;
                end if;
                if (result_valid = '1') and (result_ready_int = '1') then
                    result_record_reg <= result_data;
                    terminal_count_reg <= std_logic_vector(resize(unsigned(terminal_count_reg), 16) + to_unsigned(1, 16));
                    outbound_kind <= std_logic_vector(to_unsigned(5, 8));
                    stage_pending <= '1';
                    tx_retries <= std_logic_vector(to_unsigned(0, 3));
                    tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                end if;
                if (((finished = '1') and (not (terminal_sent = '1'))) and (not (stage_pending = '1'))) and (not (stage_outstanding = '1')) then
                    outbound_kind <= std_logic_vector(to_unsigned(8, 8));
                    stage_pending <= '1';
                    terminal_sent <= '1';
                    tx_retries <= std_logic_vector(to_unsigned(0, 3));
                    tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                end if;
                case state is
                    when IDLE =>
                        if frame_ready = '1' then
                            fields <= std_logic_vector(to_unsigned(0, 216));
                            read_idx <= std_logic_vector(to_unsigned(0, 6));
                            if unsigned(frame_length) > to_unsigned(27, 16) then
                                read_target <= std_logic_vector(to_unsigned(27, 6));
                            else
                                read_target <= frame_length(5 downto 0);
                            end if;
                            if unsigned(frame_length) = to_unsigned(0, 16) then
                                state <= DECIDE;
                            else
                                state <= READ_SETUP;
                            end if;
                        elsif (((stage_pending = '1') and (not (stage_outstanding = '1'))) and (reply_ready = '1')) and (not (tx_retry_exhausted_reg = '1')) then
                            reply_type_reg <= outbound_kind;
                            reply_sid_reg <= sid;
                            reply_seq_reg <= tx_next_seq_reg;
                            if failed = '1' then
    reply_opcode_reg <= std_logic_vector(to_unsigned(7, 8));
else
    reply_opcode_reg <= std_logic_vector(to_unsigned(6, 8));
end if;
                            reply_number_reg <= std_logic_vector(to_unsigned(0, 32));
                            state <= STAGE_START;
                        elsif (stage_outstanding = '1') and (not (tx_retry_exhausted_reg = '1')) then
                            if unsigned(tx_ack_ticks) >= to_unsigned((TX_ACK_TIMEOUT_CLKS - 1), 32) then
                                tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                                if unsigned(tx_retries) < to_unsigned(TX_MAX_RETRIES, 3) then
                                    tx_retries <= std_logic_vector(resize(unsigned(tx_retries), 3) + to_unsigned(1, 3));
                                    stage_outstanding <= '0';
                                    reply_type_reg <= outbound_kind;
                                    if failed = '1' then
    reply_opcode_reg <= std_logic_vector(to_unsigned(7, 8));
else
    reply_opcode_reg <= std_logic_vector(to_unsigned(6, 8));
end if;
                                    reply_sid_reg <= sid;
                                    reply_seq_reg <= tx_next_seq_reg;
                                    state <= STAGE_START;
                                else
                                    tx_retry_exhausted_reg <= '1';
                                end if;
                            else
                                tx_ack_ticks <= std_logic_vector(resize(unsigned(tx_ack_ticks), 32) + to_unsigned(1, 32));
                            end if;
                        end if;
                    when READ_SETUP =>
                        rd_index_reg <= std_logic_vector(resize(unsigned(std_logic_vector(to_unsigned(9, 10))), 10) + resize(unsigned(read_idx), 10));
                        state <= READ_WAIT;
                    when READ_WAIT =>
                        state <= READ_STORE;
                    when READ_STORE =>
                        fields(8*to_integer(unsigned(read_idx))+7 downto 8*to_integer(unsigned(read_idx))) <= rd_byte;
                        if unsigned(std_logic_vector(unsigned(read_idx) + to_unsigned(1, 6))) = unsigned(read_target) then
                            state <= DECIDE;
                        else
                            read_idx <= std_logic_vector(resize(unsigned(read_idx), 6) + to_unsigned(1, 6));
                            state <= READ_SETUP;
                        end if;
                    when DECIDE =>
                        if (((((((((unsigned(frame_type) = to_unsigned(9, 8)) and (unsigned(frame_flags) = to_unsigned(0, 8))) and (unsigned(frame_seq) = to_unsigned(0, 32))) and (unsigned(frame_length) = to_unsigned(24, 16))) and (unsigned(fields(7 downto 0)) = unsigned(std_logic_vector(to_unsigned(1, 8))))) and (unsigned(fields(15 downto 8)) = unsigned(std_logic_vector(to_unsigned(1, 8))))) and (unsigned(boot_sid) /= to_unsigned(0, 128))) and (unsigned(fields(151 downto 144)) = to_unsigned(0, 8))) and (unsigned(fields(159 downto 152)) = to_unsigned(0, 8))) and (unsigned(fields(191 downto 160)) = to_unsigned(0, 32)) then
                            if ((unsigned(sid) = unsigned(boot_sid)) and ((pending = '1') or (active_session_reg = '1'))) or ((not (cpi_open_reg = '1')) and ((not (retired_valid = '1')) or (unsigned(boot_sid) /= unsigned(retired_sid)))) then
                                if unsigned(sid) /= unsigned(boot_sid) then
                                    if unsigned(sid) /= to_unsigned(0, 128) then
                                        retired_sid <= sid;
                                        retired_valid <= '1';
                                    end if;
                                    sid <= boot_sid;
                                    pending <= '1';
                                    active_session_reg <= '0';
                                end if;
                                reply_type_reg <= std_logic_vector(to_unsigned(9, 8));
                                reply_opcode_reg <= std_logic_vector(to_unsigned(2, 8));
                                reply_sid_reg <= boot_sid;
                                reply_seq_reg <= std_logic_vector(to_unsigned(0, 32));
                                reply_number_reg <= std_logic_vector(to_unsigned(0, 32));
                                state <= REPLY_START;
                            else
                                stale_count_reg <= std_logic_vector(resize(unsigned(stale_count_reg), 32) + to_unsigned(1, 32));
                                state <= RELEASE;
                            end if;
                        elsif ((((((((((unsigned(frame_type) = to_unsigned(9, 8)) and (unsigned(frame_flags) = to_unsigned(0, 8))) and (unsigned(frame_seq) = to_unsigned(0, 32))) and (unsigned(frame_length) = to_unsigned(27, 16))) and (unsigned(fields(7 downto 0)) = unsigned(std_logic_vector(to_unsigned(3, 8))))) and (unsigned(fields(15 downto 8)) = unsigned(std_logic_vector(to_unsigned(1, 8))))) and (unsigned(boot_sid) = unsigned(sid))) and (unsigned(sid) /= to_unsigned(0, 128))) and (unsigned(fields(151 downto 144)) = to_unsigned(0, 8))) and (unsigned(fields(215 downto 152)) = to_unsigned(0, 64))) and ((pending = '1') or (active_session_reg = '1')) then
                            if (pending = '1') and (not (active_session_reg = '1')) then
                                active_session_reg <= '1';
                                pending <= '0';
                                rx_expected_seq_reg <= std_logic_vector(to_unsigned(0, 32));
                                tx_next_seq_reg <= std_logic_vector(to_unsigned(0, 32));
                                activation_count_reg <= std_logic_vector(resize(unsigned(activation_count_reg), 32) + to_unsigned(1, 32));
                                accepted_count_reg <= std_logic_vector(to_unsigned(0, 32));
                                last_valid <= '0';
                            end if;
                            reply_type_reg <= std_logic_vector(to_unsigned(9, 8));
                            reply_opcode_reg <= std_logic_vector(to_unsigned(4, 8));
                            reply_sid_reg <= sid;
                            reply_seq_reg <= std_logic_vector(to_unsigned(0, 32));
                            reply_number_reg <= std_logic_vector(to_unsigned(0, 32));
                            state <= REPLY_START;
                        elsif unsigned(frame_type) = to_unsigned(9, 8) then
                            stale_count_reg <= std_logic_vector(resize(unsigned(stale_count_reg), 32) + to_unsigned(1, 32));
                            state <= RELEASE;
                        elsif (((not (active_session_reg = '1')) or (unsigned(frame_flags) /= to_unsigned(1, 8))) or (unsigned(frame_length) < to_unsigned(16, 16))) or (unsigned(active_sid) /= unsigned(sid)) then
                            stale_count_reg <= std_logic_vector(resize(unsigned(stale_count_reg), 32) + to_unsigned(1, 32));
                            state <= RELEASE;
                        elsif (unsigned(frame_type) = to_unsigned(6, 8)) or (unsigned(frame_type) = to_unsigned(7, 8)) then
                            if (((unsigned(frame_length) = to_unsigned(20, 16)) and (stage_outstanding = '1')) and (unsigned(frame_seq) = unsigned(tx_next_seq_reg))) and (unsigned(std_logic_vector'("0000000000000000000000000000000" & fields(159 downto 128))) = unsigned(tx_next_seq_reg)) then
                                if unsigned(frame_type) = to_unsigned(6, 8) then
                                    stage_outstanding <= '0';
                                    stage_pending <= '0';
                                    tx_next_seq_reg <= std_logic_vector(resize(unsigned(tx_next_seq_reg), 32) + to_unsigned(1, 32));
                                    if unsigned(outbound_kind) = to_unsigned(4, 8) then
                                        if unsigned(stage_kind_reg) = to_unsigned(0, 8) then
                                            iq_readback_acked_bytes_reg <= std_logic_vector(resize(unsigned(iq_readback_acked_bytes_reg), 15) + resize(unsigned(stage_count_reg), 15));
                                        else
                                            map_acked_bytes <= std_logic_vector(resize(unsigned(map_acked_bytes), 16) + resize(unsigned(stage_count_reg), 16));
                                            if unsigned(stage_count_reg) = to_unsigned(480, 16) then
                    map_acked_words <= std_logic_vector(unsigned(map_acked_words)+to_unsigned(80,12));
                else
                    map_acked_words <= std_logic_vector(unsigned(map_acked_words)+to_unsigned(16,12));
                end if;
                                        end if;
                                    end if;
                                    if unsigned(outbound_kind) = to_unsigned(8, 8) then
                                        terminal_acked <= '1';
                                    end if;
                                    tx_retries <= std_logic_vector(to_unsigned(0, 3));
                                    tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                                    tx_retry_exhausted_reg <= '0';
                                elsif unsigned(tx_retries) < to_unsigned(TX_MAX_RETRIES, 3) then
                                    stage_outstanding <= '0';
                                    tx_retries <= std_logic_vector(resize(unsigned(tx_retries), 3) + to_unsigned(1, 3));
                                    tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                                else
                                    tx_retry_exhausted_reg <= '1';
                                end if;
                            end if;
                            state <= RELEASE;
                        else
                            reply_type_reg <= std_logic_vector(to_unsigned(7, 8));
                            reply_opcode_reg <= std_logic_vector(to_unsigned(0, 8));
                            reply_sid_reg <= sid;
                            reply_seq_reg <= frame_seq;
                            reply_number_reg <= rx_expected_seq_reg;
                            state <= REPLY_START;
                            if ((((((((((unsigned(frame_seq) = unsigned(rx_expected_seq_reg)) and (unsigned(frame_seq) /= unsigned'(x"FFFFFFFF"))) and (unsigned(frame_type) = to_unsigned(3, 8))) and (unsigned(frame_length) = to_unsigned(27, 16))) and (cpi_open_reg = '1')) and (not (running = '1'))) and (unsigned(iq_uploaded_bytes_reg) = unsigned(std_logic_vector(to_unsigned(16896, 15))))) and (not (stage_pending = '1'))) and (not (stage_outstanding = '1'))) and (unsigned(incoming_cpi) = unsigned(cpi_id_reg))) and ((((((unsigned(fields(167 downto 160)) = unsigned(std_logic_vector(to_unsigned(0, 8)))) and (not (input_verified = '1'))) and (unsigned(iq_readback_acked_bytes_reg) < to_unsigned(16896, 15))) and (unsigned(incoming_read_offset) = unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 17)) & iq_readback_acked_bytes_reg)))) and (unsigned(incoming_read_count) = unsigned(expected_read_count))) or ((((((unsigned(fields(167 downto 160)) = unsigned(std_logic_vector(to_unsigned(4, 8)))) and (terminal_acked = '1')) and (not (failed = '1'))) and (unsigned(map_acked_bytes) < to_unsigned(24576, 16))) and (unsigned(incoming_read_offset) = unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 16)) & map_acked_bytes)))) and (unsigned(incoming_read_count) = unsigned(map_expected_count)))) then
                                stage_cpi_id_reg <= cpi_id_reg;
                                stage_offset_reg <= incoming_read_offset;
                                stage_count_reg <= incoming_read_count;
                                stage_kind_reg <= fields(167 downto 160);
                                map_base_reg <= map_acked_words;
                                outbound_kind <= std_logic_vector(to_unsigned(4, 8));
                                stage_pending <= '1';
                                tx_retries <= std_logic_vector(to_unsigned(0, 3));
                                tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                                rx_expected_seq_reg <= std_logic_vector(resize(unsigned(rx_expected_seq_reg), 32) + to_unsigned(1, 32));
                                accepted_count_reg <= std_logic_vector(resize(unsigned(accepted_count_reg), 32) + to_unsigned(1, 32));
                                last_valid <= '1';
                                last_seq <= frame_seq;
                                last_crc <= frame_crc;
                                last_type <= frame_type;
                                last_length <= frame_length;
                                reply_type_reg <= std_logic_vector(to_unsigned(6, 8));
                                reply_number_reg <= frame_seq;
                            elsif (((((((((unsigned(frame_seq) = unsigned(rx_expected_seq_reg)) and (unsigned(frame_seq) /= unsigned'(x"FFFFFFFF"))) and (unsigned(frame_type) = to_unsigned(2, 8))) and (cpi_open_reg = '1')) and (not (input_verified = '1'))) and (not (running = '1'))) and (unsigned(iq_uploaded_bytes_reg) < unsigned(std_logic_vector(to_unsigned(16896, 15))))) and (unsigned(incoming_cpi) = unsigned(cpi_id_reg))) and (unsigned(incoming_offset) = unsigned(std_logic_vector'(std_logic_vector(to_unsigned(0, 17)) & iq_uploaded_bytes_reg)))) and (unsigned(frame_length) = unsigned(std_logic_vector(unsigned(std_logic_vector(to_unsigned(24, 16))) + unsigned(expected_chunk)))) then
                                copy_idx <= std_logic_vector(to_unsigned(24, 10));
                                sample_word <= std_logic_vector(to_unsigned(0, 32));
                                current_iq_size <= expected_chunk;
                                state <= COPY_SETUP;
                            elsif (((((unsigned(frame_seq) = unsigned(rx_expected_seq_reg)) and (unsigned(frame_seq) /= unsigned'(x"FFFFFFFF"))) and (unsigned(frame_type) = to_unsigned(1, 8))) and (unsigned(frame_length) = to_unsigned(21, 16))) and (unsigned(app_opcode) = unsigned(std_logic_vector(to_unsigned(1, 8))))) and (not (cpi_open_reg = '1')) then
                                cpi_open_reg <= '1';
                                cpi_id_reg <= app_cpi_id;
                                rx_expected_seq_reg <= std_logic_vector(resize(unsigned(rx_expected_seq_reg), 32) + to_unsigned(1, 32));
                                accepted_count_reg <= std_logic_vector(resize(unsigned(accepted_count_reg), 32) + to_unsigned(1, 32));
                                last_valid <= '1';
                                last_seq <= frame_seq;
                                last_crc <= frame_crc;
                                last_type <= frame_type;
                                last_length <= frame_length;
                                reply_type_reg <= std_logic_vector(to_unsigned(6, 8));
                                reply_number_reg <= frame_seq;
                            elsif ((((((unsigned(frame_seq) = unsigned(rx_expected_seq_reg)) and (unsigned(frame_seq) /= unsigned'(x"FFFFFFFF"))) and (unsigned(frame_type) = to_unsigned(1, 8))) and (unsigned(frame_length) = to_unsigned(21, 16))) and (cpi_open_reg = '1')) and (unsigned(app_cpi_id) = unsigned(cpi_id_reg))) and ((((((unsigned(app_opcode) = to_unsigned(3, 8)) and (not (input_verified = '1'))) and (unsigned(iq_readback_acked_bytes_reg) = to_unsigned(16896, 15))) or ((((unsigned(app_opcode) = to_unsigned(4, 8)) and (input_verified = '1')) and (not (running = '1'))) and (not (finished = '1')))) or ((((unsigned(app_opcode) = to_unsigned(5, 8)) and (terminal_acked = '1')) and (not (stage_pending = '1'))) and (not (stage_outstanding = '1')))) or ((((unsigned(app_opcode) = to_unsigned(6, 8)) and (terminal_acked = '1')) and (not (stage_pending = '1'))) and (not (stage_outstanding = '1')))) then
                                if unsigned(app_opcode) = to_unsigned(3, 8) then
                                    input_verified <= '1';
                                end if;
                                if unsigned(app_opcode) = to_unsigned(4, 8) then
                                    running <= '1';
                                    dsp_start_reg <= '1';
                                    watchdog <= std_logic_vector(to_unsigned(0, 26));
                                end if;
                                if unsigned(app_opcode) = to_unsigned(5, 8) then
                                    outbound_kind <= std_logic_vector(to_unsigned(8, 8));
                                    stage_pending <= '1';
                                    tx_retries <= std_logic_vector(to_unsigned(0, 3));
                                    tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                                end if;
                                if unsigned(app_opcode) = to_unsigned(6, 8) then
                                    cpi_open_reg <= '0';
                                    input_verified <= '0';
                                    finished <= '0';
                                    terminal_sent <= '0';
                                    terminal_acked <= '0';
                                    failed <= '0';
                                    terminal_count_reg <= std_logic_vector(to_unsigned(0, 16));
                                    dsp_clear_reg <= '1';
                                    iq_uploaded_bytes_reg <= std_logic_vector(to_unsigned(0, 15));
                                    iq_readback_acked_bytes_reg <= std_logic_vector(to_unsigned(0, 15));
                                    map_acked_bytes <= std_logic_vector(to_unsigned(0, 16));
                                    map_acked_words <= std_logic_vector(to_unsigned(0, 12));
                                end if;
                                rx_expected_seq_reg <= std_logic_vector(resize(unsigned(rx_expected_seq_reg), 32) + to_unsigned(1, 32));
                                accepted_count_reg <= std_logic_vector(resize(unsigned(accepted_count_reg), 32) + to_unsigned(1, 32));
                                last_valid <= '1';
                                last_seq <= frame_seq;
                                last_crc <= frame_crc;
                                last_type <= frame_type;
                                last_length <= frame_length;
                                reply_type_reg <= std_logic_vector(to_unsigned(6, 8));
                                reply_number_reg <= frame_seq;
                            elsif ((((last_valid = '1') and (unsigned(frame_seq) = unsigned(last_seq))) and (unsigned(frame_crc) = unsigned(last_crc))) and (unsigned(frame_length) = unsigned(last_length))) and (unsigned(frame_type) = unsigned(last_type)) then
                                duplicate_count_reg <= std_logic_vector(resize(unsigned(duplicate_count_reg), 32) + to_unsigned(1, 32));
                                reply_type_reg <= std_logic_vector(to_unsigned(6, 8));
                                reply_number_reg <= frame_seq;
                            else
                                nack_count_reg <= std_logic_vector(resize(unsigned(nack_count_reg), 32) + to_unsigned(1, 32));
                            end if;
                        end if;
                    when COPY_SETUP =>
                        rd_index_reg <= std_logic_vector(resize(unsigned(std_logic_vector(to_unsigned(9, 10))), 10) + resize(unsigned(copy_idx), 10));
                        state <= COPY_WAIT;
                    when COPY_WAIT =>
                        state <= COPY_STORE;
                    when COPY_STORE =>
                        case to_integer((unsigned(copy_idx)-to_unsigned(24,10)) and to_unsigned(3,10)) is
                            when 0 =>
                                sample_word(7 downto 0) <= rd_byte;
                            when 1 =>
                                sample_word(15 downto 8) <= rd_byte;
                            when 2 =>
                                sample_word(23 downto 16) <= rd_byte;
                            when 3 =>
                                iq_write_en_reg <= '1';
                                iq_write_addr_reg <= std_logic_vector(resize(unsigned(std_logic_vector(shift_right(unsigned(std_logic_vector(unsigned(iq_uploaded_bytes_reg) + resize(unsigned(std_logic_vector(unsigned(copy_idx) - unsigned(std_logic_vector(to_unsigned(24, 10))))), 15))), 2))), 13));
                                iq_write_data_reg <= std_logic_vector'(rd_byte & sample_word(23 downto 0));
                            when others =>
                                null;
                        end case;
                        if resize(unsigned(std_logic_vector(unsigned(copy_idx) + to_unsigned(1, 10))), 16) = unsigned(frame_length) then
                            state <= COPY_END;
                        else
                            copy_idx <= std_logic_vector(resize(unsigned(copy_idx), 10) + to_unsigned(1, 10));
                            state <= COPY_SETUP;
                        end if;
                    when COPY_END =>
                        iq_uploaded_bytes_reg <= std_logic_vector(resize(unsigned(iq_uploaded_bytes_reg), 15) + resize(unsigned(current_iq_size), 15));
                        rx_expected_seq_reg <= std_logic_vector(resize(unsigned(rx_expected_seq_reg), 32) + to_unsigned(1, 32));
                        accepted_count_reg <= std_logic_vector(resize(unsigned(accepted_count_reg), 32) + to_unsigned(1, 32));
                        last_valid <= '1';
                        last_seq <= frame_seq;
                        last_crc <= frame_crc;
                        last_type <= frame_type;
                        last_length <= frame_length;
                        reply_type_reg <= std_logic_vector(to_unsigned(6, 8));
                        reply_seq_reg <= frame_seq;
                        reply_number_reg <= frame_seq;
                        state <= REPLY_START;
                    when REPLY_START =>
                        if reply_ready = '1' then
                            reply_started <= '0';
                            state <= REPLY_BUSY;
                        end if;
                    when REPLY_BUSY =>
                        if not (reply_ready = '1') then
                            reply_started <= '1';
                        elsif reply_started = '1' then
                            state <= RELEASE;
                        end if;
                    when RELEASE =>
                        frame_done_reg <= '1';
                        state <= REPLY_DONE;
                    when REPLY_DONE =>
                        if not (frame_ready = '1') then
                            state <= IDLE;
                        end if;
                    when STAGE_START =>
                        if reply_ready = '1' then
                            reply_started <= '0';
                            state <= STAGE_BUSY;
                        end if;
                    when STAGE_BUSY =>
                        if not (reply_ready = '1') then
                            reply_started <= '1';
                        elsif reply_started = '1' then
                            stage_outstanding <= '1';
                            tx_ack_ticks <= std_logic_vector(to_unsigned(0, 32));
                            state <= IDLE;
                        end if;
                    when others =>
                        state <= IDLE;
                end case;
            end if;
        end if;
    end process;

    dsp_start <= dsp_start_reg;
    dsp_clear <= dsp_clear_reg;
    result_record <= result_record_reg;
    stage_kind <= stage_kind_reg;
    map_base <= map_base_reg;
    terminal_count <= terminal_count_reg;
    frame_done <= frame_done_reg;
    rd_index <= rd_index_reg;
    reply_type <= reply_type_reg;
    reply_opcode <= reply_opcode_reg;
    reply_sid <= reply_sid_reg;
    reply_seq <= reply_seq_reg;
    reply_number <= reply_number_reg;
    active_session <= active_session_reg;
    rx_expected_seq <= rx_expected_seq_reg;
    activation_count <= activation_count_reg;
    accepted_count <= accepted_count_reg;
    duplicate_count <= duplicate_count_reg;
    stale_count <= stale_count_reg;
    nack_count <= nack_count_reg;
    cpi_id <= cpi_id_reg;
    cpi_open <= cpi_open_reg;
    iq_uploaded_bytes <= iq_uploaded_bytes_reg;
    iq_write_en <= iq_write_en_reg;
    iq_write_addr <= iq_write_addr_reg;
    iq_write_data <= iq_write_data_reg;
    iq_readback_acked_bytes <= iq_readback_acked_bytes_reg;
    stage_cpi_id <= stage_cpi_id_reg;
    stage_offset <= stage_offset_reg;
    stage_count <= stage_count_reg;
    tx_next_seq <= tx_next_seq_reg;
    tx_retry_exhausted <= tx_retry_exhausted_reg;
    result_ready <= result_ready_int;

end architecture rtl;

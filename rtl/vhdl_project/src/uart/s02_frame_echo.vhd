-- AUTO-TRANSLATED from uart/s02_frame_echo.v; independent validation REQUIRED.
-- Source SHA256: c6b7767a2f6b5f2bbf81c839d7e3acae048d8338970dfe14832e34183209b994
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity s02_frame_echo is
    generic (
        TIMEOUT_CLKS : integer := 86800;
        ECHO_MODE : integer := 1
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        rx_data : in std_logic_vector(7 downto 0);
        rx_valid : in std_logic;
        rx_framing_error : in std_logic;
        tx_data : out std_logic_vector(7 downto 0);
        tx_valid : out std_logic;
        tx_ready : in std_logic;
        good_count : out std_logic_vector(15 downto 0);
        crc_error_count : out std_logic_vector(15 downto 0);
        header_error_count : out std_logic_vector(15 downto 0);
        length_error_count : out std_logic_vector(15 downto 0);
        partial_timeout_count : out std_logic_vector(15 downto 0);
        uart_error_count : out std_logic_vector(15 downto 0);
        busy_drop_count : out std_logic_vector(15 downto 0);
        response_busy : out std_logic;
        frame_ready : out std_logic;
        frame_done : in std_logic;
        frame_type : out std_logic_vector(7 downto 0);
        frame_flags : out std_logic_vector(7 downto 0);
        frame_seq : out std_logic_vector(31 downto 0);
        frame_length : out std_logic_vector(15 downto 0);
        frame_crc : out std_logic_vector(31 downto 0);
        frame_rd_index : in std_logic_vector(9 downto 0);
        frame_rd_byte : out std_logic_vector(7 downto 0)
    );
end entity s02_frame_echo;

architecture rtl of s02_frame_echo is
    constant SEARCH : std_logic_vector(2 downto 0) := "000";
    constant HEADER : std_logic_vector(2 downto 0) := "001";
    constant PAYLOAD : std_logic_vector(2 downto 0) := "010";
    constant CRC_BYTES : std_logic_vector(2 downto 0) := "011";
    constant ECHO_FETCH : std_logic_vector(2 downto 0) := "100";
    constant ECHO_SEND : std_logic_vector(2 downto 0) := "101";
    constant HELD : std_logic_vector(2 downto 0) := "110";
    type frame_ram_array_t is array (0 to 524) of std_logic_vector(7 downto 0);
    signal frame_ram : frame_ram_array_t;
    signal state : std_logic_vector(2 downto 0);
    signal sof_seen : std_logic_vector(1 downto 0);
    signal write_pos : std_logic_vector(9 downto 0);
    signal read_pos : std_logic_vector(9 downto 0);
    signal frame_bytes : std_logic_vector(9 downto 0);
    signal declared_length : std_logic_vector(15 downto 0);
    signal remaining : std_logic_vector(15 downto 0);
    signal crc_pos : std_logic_vector(1 downto 0);
    signal crc_value : std_logic_vector(31 downto 0);
    signal rx_crc : std_logic_vector(31 downto 0);
    signal header_type : std_logic_vector(7 downto 0);
    signal header_flags : std_logic_vector(7 downto 0);
    signal header_sequence : std_logic_vector(31 downto 0);
    signal idle_cycles : std_logic_vector(31 downto 0);
    signal ram_read_q : std_logic_vector(7 downto 0);
    signal good_count_reg : std_logic_vector(15 downto 0);
    signal crc_error_count_reg : std_logic_vector(15 downto 0);
    signal header_error_count_reg : std_logic_vector(15 downto 0);
    signal length_error_count_reg : std_logic_vector(15 downto 0);
    signal partial_timeout_count_reg : std_logic_vector(15 downto 0);
    signal uart_error_count_reg : std_logic_vector(15 downto 0);
    signal busy_drop_count_reg : std_logic_vector(15 downto 0);

    impure function crc32_byte(old_crc : std_logic_vector(31 downto 0); data : std_logic_vector(7 downto 0)) return std_logic_vector is
        variable crc32_byte_result : std_logic_vector(31 downto 0);
        variable x : std_logic_vector(31 downto 0);
    begin
        x := (old_crc) xor (std_logic_vector'(std_logic_vector(to_unsigned(0, 24)) & data));
        for i in 0 to 7 loop
            if x(0) = '1' then
                x := (std_logic_vector(shift_right(unsigned(x), 1))) xor ("11101101101110001000001100100000");
            else
                x := std_logic_vector(shift_right(unsigned(x), 1));
            end if;
        end loop;
        crc32_byte_result := x;
        return crc32_byte_result;
    end function crc32_byte;

begin

    tx_data <= std_logic_vector(to_unsigned(165, 8)) when unsigned(read_pos) = to_unsigned(0, 10) else std_logic_vector(to_unsigned(90, 8)) when unsigned(read_pos) = to_unsigned(1, 10) else std_logic_vector(to_unsigned(195, 8)) when unsigned(read_pos) = to_unsigned(2, 10) else std_logic_vector(to_unsigned(60, 8)) when unsigned(read_pos) = to_unsigned(3, 10) else ram_read_q;
    tx_valid <= '1' when unsigned(state) = unsigned(ECHO_SEND) else '0';
    response_busy <= '1' when ((unsigned(state) = unsigned(ECHO_FETCH)) or (unsigned(state) = unsigned(ECHO_SEND))) or (unsigned(state) = unsigned(HELD)) else '0';
    frame_ready <= '1' when unsigned(state) = unsigned(HELD) else '0';
    frame_type <= header_type;
    frame_flags <= header_flags;
    frame_seq <= header_sequence;
    frame_length <= declared_length;
    frame_crc <= not crc_value;
    frame_rd_byte <= ram_read_q;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= SEARCH;
                sof_seen <= std_logic_vector(to_unsigned(0, 2));
                write_pos <= std_logic_vector(to_unsigned(0, 10));
                read_pos <= std_logic_vector(to_unsigned(0, 10));
                frame_bytes <= std_logic_vector(to_unsigned(0, 10));
                declared_length <= std_logic_vector(to_unsigned(0, 16));
                remaining <= std_logic_vector(to_unsigned(0, 16));
                crc_pos <= std_logic_vector(to_unsigned(0, 2));
                crc_value <= "11111111111111111111111111111111";
                rx_crc <= std_logic_vector(to_unsigned(0, 32));
                header_type <= std_logic_vector(to_unsigned(0, 8));
                header_flags <= std_logic_vector(to_unsigned(0, 8));
                header_sequence <= std_logic_vector(to_unsigned(0, 32));
                idle_cycles <= std_logic_vector(to_unsigned(0, 32));
                ram_read_q <= std_logic_vector(to_unsigned(0, 8));
                good_count_reg <= std_logic_vector(to_unsigned(0, 16));
                crc_error_count_reg <= std_logic_vector(to_unsigned(0, 16));
                header_error_count_reg <= std_logic_vector(to_unsigned(0, 16));
                length_error_count_reg <= std_logic_vector(to_unsigned(0, 16));
                partial_timeout_count_reg <= std_logic_vector(to_unsigned(0, 16));
                uart_error_count_reg <= std_logic_vector(to_unsigned(0, 16));
                busy_drop_count_reg <= std_logic_vector(to_unsigned(0, 16));
            else
                if unsigned(state) = unsigned(HELD) then
                    ram_read_q <= frame_ram(to_integer(unsigned(frame_rd_index)));
                end if;
                if (unsigned(state) = unsigned(HELD)) and (frame_done = '1') then
                    state <= SEARCH;
                    sof_seen <= std_logic_vector(to_unsigned(0, 2));
                end if;
                if unsigned(state) = unsigned(ECHO_FETCH) then
                    if unsigned(read_pos) >= to_unsigned(4, 10) then
                        ram_read_q <= frame_ram(to_integer(unsigned(read_pos)) - 4);
                    end if;
                    state <= ECHO_SEND;
                elsif (unsigned(state) = unsigned(ECHO_SEND)) and (tx_ready = '1') then
                    if unsigned(read_pos) = unsigned(std_logic_vector(unsigned(frame_bytes) - to_unsigned(1, 10))) then
                        state <= SEARCH;
                        sof_seen <= std_logic_vector(to_unsigned(0, 2));
                    else
                        read_pos <= std_logic_vector(resize(unsigned(read_pos), 10) + to_unsigned(1, 10));
                        state <= ECHO_FETCH;
                    end if;
                end if;
                if ((unsigned(state) = unsigned(HEADER)) or (unsigned(state) = unsigned(PAYLOAD))) or (unsigned(state) = unsigned(CRC_BYTES)) then
                    if (rx_valid = '1') or (rx_framing_error = '1') then
                        idle_cycles <= std_logic_vector(to_unsigned(0, 32));
                    elsif unsigned(idle_cycles) >= to_unsigned((TIMEOUT_CLKS - 1), 32) then
                        state <= SEARCH;
                        sof_seen <= std_logic_vector(to_unsigned(0, 2));
                        idle_cycles <= std_logic_vector(to_unsigned(0, 32));
                        partial_timeout_count_reg <= std_logic_vector(resize(unsigned(partial_timeout_count_reg), 16) + to_unsigned(1, 16));
                    else
                        idle_cycles <= std_logic_vector(resize(unsigned(idle_cycles), 32) + to_unsigned(1, 32));
                    end if;
                else
                    idle_cycles <= std_logic_vector(to_unsigned(0, 32));
                end if;
                if (rx_valid = '1') and (((unsigned(state) = unsigned(HEADER)) or (unsigned(state) = unsigned(PAYLOAD))) or (unsigned(state) = unsigned(CRC_BYTES))) then
                    frame_ram(to_integer(unsigned(write_pos)) - 4) <= rx_data;
                end if;
                if rx_framing_error = '1' then
                    uart_error_count_reg <= std_logic_vector(resize(unsigned(uart_error_count_reg), 16) + to_unsigned(1, 16));
                    if ((unsigned(state) = unsigned(HEADER)) or (unsigned(state) = unsigned(PAYLOAD))) or (unsigned(state) = unsigned(CRC_BYTES)) then
                        state <= SEARCH;
                        sof_seen <= std_logic_vector(to_unsigned(0, 2));
                    end if;
                elsif rx_valid = '1' then
                    case state is
                        when SEARCH =>
                            case sof_seen is
                                when "00" =>
                                    if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                when "01" =>
                                    if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(90, 8))) then
                                        sof_seen <= std_logic_vector(to_unsigned(2, 2));
                                    else
                                        if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                    end if;
                                when "10" =>
                                    if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(195, 8))) then
                                        sof_seen <= std_logic_vector(to_unsigned(3, 2));
                                    else
                                        if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                    end if;
                                when "11" =>
                                    if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(60, 8))) then
                                        state <= HEADER;
                                        write_pos <= std_logic_vector(to_unsigned(4, 10));
                                        crc_value <= "11111111111111111111111111111111";
                                        declared_length <= std_logic_vector(to_unsigned(0, 16));
                                        header_sequence <= std_logic_vector(to_unsigned(0, 32));
                                        sof_seen <= std_logic_vector(to_unsigned(0, 2));
                                        idle_cycles <= std_logic_vector(to_unsigned(0, 32));
                                    else
                                        if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                    end if;
                                when others =>
                                    null;
                            end case;
                        when HEADER =>
                            if (unsigned(write_pos) = to_unsigned(4, 10)) and (unsigned(rx_data) /= unsigned(std_logic_vector(to_unsigned(1, 8)))) then
                                state <= SEARCH;
                                if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                header_error_count_reg <= std_logic_vector(resize(unsigned(header_error_count_reg), 16) + to_unsigned(1, 16));
                            elsif (unsigned(write_pos) = to_unsigned(5, 10)) and ((unsigned(rx_data) < unsigned(std_logic_vector(to_unsigned(1, 8)))) or (unsigned(rx_data) > unsigned(std_logic_vector(to_unsigned(9, 8))))) then
                                state <= SEARCH;
                                if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                header_error_count_reg <= std_logic_vector(resize(unsigned(header_error_count_reg), 16) + to_unsigned(1, 16));
                            elsif (unsigned(write_pos) = to_unsigned(6, 10)) and (((unsigned(header_type) = unsigned(std_logic_vector(to_unsigned(9, 8)))) and (unsigned(rx_data) /= to_unsigned(0, 8))) or ((unsigned(header_type) /= unsigned(std_logic_vector(to_unsigned(9, 8)))) and (unsigned(rx_data) /= to_unsigned(1, 8)))) then
                                state <= SEARCH;
                                if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                header_error_count_reg <= std_logic_vector(resize(unsigned(header_error_count_reg), 16) + to_unsigned(1, 16));
                            elsif (unsigned(write_pos) = to_unsigned(12, 10)) and (unsigned(std_logic_vector'(rx_data & declared_length(7 downto 0))) > unsigned(std_logic_vector(to_unsigned(512, 16)))) then
                                state <= SEARCH;
                                if unsigned(rx_data) = unsigned(std_logic_vector(to_unsigned(165, 8))) then
    sof_seen <= std_logic_vector(to_unsigned(1, 2));
else
    sof_seen <= std_logic_vector(to_unsigned(0, 2));
end if;
                                length_error_count_reg <= std_logic_vector(resize(unsigned(length_error_count_reg), 16) + to_unsigned(1, 16));
                            elsif ((unsigned(write_pos) = to_unsigned(12, 10)) and (unsigned(header_type) = unsigned(std_logic_vector(to_unsigned(9, 8))))) and (unsigned(header_sequence) /= to_unsigned(0, 32)) then
                                state <= SEARCH;
                                sof_seen <= std_logic_vector(to_unsigned(0, 2));
                                header_error_count_reg <= std_logic_vector(resize(unsigned(header_error_count_reg), 16) + to_unsigned(1, 16));
                            else
                                crc_value <= crc32_byte(crc_value, rx_data);
                                write_pos <= std_logic_vector(resize(unsigned(write_pos), 10) + to_unsigned(1, 10));
                                if unsigned(write_pos) = to_unsigned(5, 10) then
                                    header_type <= rx_data;
                                end if;
                                if unsigned(write_pos) = to_unsigned(6, 10) then
                                    header_flags <= rx_data;
                                end if;
                                if (unsigned(write_pos) >= to_unsigned(7, 10)) and (unsigned(write_pos) <= to_unsigned(10, 10)) then
                                    header_sequence((8*(to_integer(unsigned(write_pos))-7))+7 downto
                         8*(to_integer(unsigned(write_pos))-7)) <= rx_data;
                                end if;
                                if unsigned(write_pos) = to_unsigned(11, 10) then
                                    declared_length(7 downto 0) <= rx_data;
                                end if;
                                if unsigned(write_pos) = to_unsigned(12, 10) then
                                    declared_length(15 downto 8) <= rx_data;
                                    remaining <= std_logic_vector'(rx_data & declared_length(7 downto 0));
                                    crc_pos <= std_logic_vector(to_unsigned(0, 2));
                                    if unsigned(std_logic_vector'(rx_data & declared_length(7 downto 0))) = to_unsigned(0, 16) then
                                        state <= CRC_BYTES;
                                    else
                                        state <= PAYLOAD;
                                    end if;
                                end if;
                            end if;
                        when PAYLOAD =>
                            crc_value <= crc32_byte(crc_value, rx_data);
                            write_pos <= std_logic_vector(resize(unsigned(write_pos), 10) + to_unsigned(1, 10));
                            if unsigned(remaining) = to_unsigned(1, 16) then
                                remaining <= std_logic_vector(to_unsigned(0, 16));
                                crc_pos <= std_logic_vector(to_unsigned(0, 2));
                                state <= CRC_BYTES;
                            else
                                remaining <= std_logic_vector(resize(unsigned(remaining), 16) - to_unsigned(1, 16));
                            end if;
                        when CRC_BYTES =>
                            write_pos <= std_logic_vector(resize(unsigned(write_pos), 10) + to_unsigned(1, 10));
                            rx_crc(8*to_integer(unsigned(crc_pos))+7 downto 8*to_integer(unsigned(crc_pos))) <= rx_data;
                            if unsigned(crc_pos) = to_unsigned(3, 2) then
                                if unsigned(std_logic_vector'(rx_data & rx_crc(23 downto 0))) = resize(unsigned(not crc_value), 32) then
                                    good_count_reg <= std_logic_vector(resize(unsigned(good_count_reg), 16) + to_unsigned(1, 16));
                                    frame_bytes <= std_logic_vector(resize(unsigned(write_pos), 10) + to_unsigned(1, 10));
                                    read_pos <= std_logic_vector(to_unsigned(0, 10));
                                    if ECHO_MODE /= 0 then
                                        state <= ECHO_FETCH;
                                    else
                                        state <= HELD;
                                    end if;
                                else
                                    crc_error_count_reg <= std_logic_vector(resize(unsigned(crc_error_count_reg), 16) + to_unsigned(1, 16));
                                    state <= SEARCH;
                                    sof_seen <= std_logic_vector(to_unsigned(0, 2));
                                end if;
                            else
                                crc_pos <= std_logic_vector(resize(unsigned(crc_pos), 2) + to_unsigned(1, 2));
                            end if;
                        when others =>
                            busy_drop_count_reg <= std_logic_vector(resize(unsigned(busy_drop_count_reg), 16) + to_unsigned(1, 16));
                    end case;
                end if;
            end if;
        end if;
    end process;

    good_count <= good_count_reg;
    crc_error_count <= crc_error_count_reg;
    header_error_count <= header_error_count_reg;
    length_error_count <= length_error_count_reg;
    partial_timeout_count <= partial_timeout_count_reg;
    uart_error_count <= uart_error_count_reg;
    busy_drop_count <= busy_drop_count_reg;

end architecture rtl;

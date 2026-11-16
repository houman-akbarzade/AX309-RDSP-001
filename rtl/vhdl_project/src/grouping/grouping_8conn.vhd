-- AUTO-TRANSLATED from grouping/grouping_8conn.v; independent validation REQUIRED.
-- Source SHA256: 602ae13a83ff6b006895290a7e7f2e512b965c08c7cb568fa224cba2849664da
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity grouping_8conn is
    generic (
        MAX_LABELS : integer := 702
    );
    port (
        clk : in std_logic;
        rst : in std_logic;
        start : in std_logic;
        in_valid : in std_logic;
        in_ready : out std_logic;
        in_range : in std_logic_vector(6 downto 0);
        in_bin : in std_logic_vector(4 downto 0);
        in_power : in std_logic_vector(45 downto 0);
        in_alarm : in std_logic;
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
        overflow_sticky : out std_logic;
        protocol_error : out std_logic;
        frame_invalid : out std_logic
    );
end entity grouping_8conn;

architecture rtl of grouping_8conn is
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

    constant PHYSICAL_LABELS : integer := 702;
    constant RAM_LAST_ADDRESS : integer := 1023;
    constant S_IDLE : std_logic_vector(5 downto 0) := "000000";
    constant S_INIT_ROW : std_logic_vector(5 downto 0) := "000001";
    constant S_ACCEPT : std_logic_vector(5 downto 0) := "000010";
    constant S_NEIGH : std_logic_vector(5 downto 0) := "000011";
    constant S_FIND : std_logic_vector(5 downto 0) := "000100";
    constant S_FIND_READ : std_logic_vector(5 downto 0) := "010001";
    constant S_UNION_A : std_logic_vector(5 downto 0) := "000101";
    constant S_UNION_B : std_logic_vector(5 downto 0) := "000110";
    constant S_UNION_WR : std_logic_vector(5 downto 0) := "000111";
    constant S_PROCESS : std_logic_vector(5 downto 0) := "001000";
    constant S_ADD_READ : std_logic_vector(5 downto 0) := "001001";
    constant S_ADD_WRITE : std_logic_vector(5 downto 0) := "001010";
    constant S_STEP : std_logic_vector(5 downto 0) := "001011";
    constant S_SHIFT_ROW : std_logic_vector(5 downto 0) := "001100";
    constant S_SORT_INIT : std_logic_vector(5 downto 0) := "001101";
    constant S_SORT_READ : std_logic_vector(5 downto 0) := "001110";
    constant S_SORT_CHECK : std_logic_vector(5 downto 0) := "001111";
    constant S_OUTPUT : std_logic_vector(5 downto 0) := "010000";
    constant STAT_W : integer := 82;
    type stat_mem_array_t is array (0 to 1023) of std_logic_vector(STAT_W-1 downto 0);
    signal stat_mem : stat_mem_array_t;
    type parent_array_t is array (0 to 1023) of std_logic_vector(9 downto 0);
    signal parent : parent_array_t;
    type emitted_array_t is array (0 to 1023) of std_logic;
    signal emitted : emitted_array_t;
    type prev_row_array_t is array (0 to 31) of std_logic_vector(9 downto 0);
    signal prev_row : prev_row_array_t;
    type curr_row_array_t is array (0 to 31) of std_logic_vector(9 downto 0);
    signal curr_row : curr_row_array_t;
    signal stat_q : std_logic_vector(STAT_W-1 downto 0);
    signal stat_a : std_logic_vector(STAT_W-1 downto 0);
    signal parent_q : std_logic_vector(9 downto 0);
    signal state : std_logic_vector(5 downto 0);
    signal expected_range : std_logic_vector(6 downto 0);
    signal expected_bin : std_logic_vector(4 downto 0);
    signal row_index : std_logic_vector(4 downto 0);
    signal neighbor_index : std_logic_vector(2 downto 0);
    signal neighbor0 : std_logic_vector(9 downto 0);
    signal neighbor1 : std_logic_vector(9 downto 0);
    signal neighbor2 : std_logic_vector(9 downto 0);
    signal neighbor3 : std_logic_vector(9 downto 0);
    signal find_ptr : std_logic_vector(9 downto 0);
    signal selected_root : std_logic_vector(9 downto 0);
    signal label_count : std_logic_vector(9 downto 0);
    signal root_count : std_logic_vector(9 downto 0);
    signal emitted_count : std_logic_vector(9 downto 0);
    signal scan_index : std_logic_vector(9 downto 0);
    signal best_index : std_logic_vector(9 downto 0);
    signal best_found : std_logic;
    signal best_stat : std_logic_vector(STAT_W-1 downto 0);
    signal current_power : std_logic_vector(45 downto 0);
    signal next_label : std_logic_vector(9 downto 0);
    signal union_lo : std_logic_vector(9 downto 0);
    signal union_hi : std_logic_vector(9 downto 0);
    signal choose_a : std_logic;
    signal equal_union_power : std_logic;
    signal merged_cells : std_logic_vector(12 downto 0);
    signal merged_equal : std_logic_vector(12 downto 0);
    signal merged_stat : std_logic_vector(STAT_W-1 downto 0);
    signal choose_current : std_logic;
    signal added_stat : std_logic_vector(STAT_W-1 downto 0);
    signal next_neighbor : std_logic_vector(9 downto 0);
    signal stats_read_addr : std_logic_vector(9 downto 0);
    signal stat_write_en : std_logic;
    signal stat_write_addr : std_logic_vector(9 downto 0);
    signal stat_write_data : std_logic_vector(STAT_W-1 downto 0);
    signal parent_write_en : std_logic;
    signal parent_write_addr : std_logic_vector(9 downto 0);
    signal parent_write_data : std_logic_vector(9 downto 0);
    signal parent_read_addr : std_logic_vector(9 downto 0);
    signal emitted_we : std_logic;
    signal emitted_data : std_logic;
    signal emitted_addr : std_logic_vector(9 downto 0);
    signal curr_we : std_logic;
    signal prev_we : std_logic;
    signal curr_addr : std_logic_vector(4 downto 0);
    signal curr_data : std_logic_vector(9 downto 0);
    signal prev_data : std_logic_vector(9 downto 0);
    signal busy_reg : std_logic;
    signal done_reg : std_logic;
    signal overflow_sticky_reg : std_logic;
    signal protocol_error_reg : std_logic;
    signal frame_invalid_reg : std_logic;

    impure function signed_bin(b : std_logic_vector(4 downto 0)) return std_logic_vector is
        variable signed_bin_result : std_logic_vector(5 downto 0);
    begin
        if unsigned(b) <= unsigned(std_logic_vector(to_unsigned(15, 5))) then
            signed_bin_result := std_logic_vector'('0' & b);
        else
            signed_bin_result := std_logic_vector(signed(std_logic_vector'('0' & b)) - signed(std_logic_vector(to_unsigned(32, 6))));
        end if;
        return signed_bin_result;
    end function signed_bin;

    impure function better_peak(power_a : std_logic_vector(45 downto 0); power_b : std_logic_vector(45 downto 0); range_a : std_logic_vector(6 downto 0); range_b : std_logic_vector(6 downto 0); bin_a : std_logic_vector(4 downto 0); bin_b : std_logic_vector(4 downto 0)) return std_logic is
        variable better_peak_result : std_logic;
    begin
        if unsigned(power_a) /= unsigned(power_b) then
            if unsigned(power_a) > unsigned(power_b) then
    better_peak_result := '1';
else
    better_peak_result := '0';
end if;
        elsif signed_bin(bin_a) /= signed_bin(bin_b) then
            if signed_bin(bin_a) < signed_bin(bin_b) then
    better_peak_result := '1';
else
    better_peak_result := '0';
end if;
        elsif unsigned(range_a) /= unsigned(range_b) then
            if unsigned(range_a) < unsigned(range_b) then
    better_peak_result := '1';
else
    better_peak_result := '0';
end if;
        else
            if unsigned(bin_a) < unsigned(bin_b) then
    better_peak_result := '1';
else
    better_peak_result := '0';
end if;
        end if;
        return better_peak_result;
    end function better_peak;

    impure function better_record(a : std_logic_vector(STAT_W-1 downto 0); b : std_logic_vector(STAT_W-1 downto 0)) return std_logic is
        variable better_record_result : std_logic;
    begin
        if unsigned(a(35 downto 29)) /= unsigned(b(35 downto 29)) then
            if unsigned(a(35 downto 29)) < unsigned(b(35 downto 29)) then
    better_record_result := '1';
else
    better_record_result := '0';
end if;
        elsif signed_bin(a(28 downto 24)) /= signed_bin(b(28 downto 24)) then
            if signed_bin(a(28 downto 24)) < signed_bin(b(28 downto 24)) then
    better_record_result := '1';
else
    better_record_result := '0';
end if;
        else
            if unsigned(a(28 downto 24)) < unsigned(b(28 downto 24)) then
    better_record_result := '1';
else
    better_record_result := '0';
end if;
        end if;
        return better_record_result;
    end function better_record;

begin

    next_label <= std_logic_vector(resize(unsigned(label_count), 10) + resize(unsigned(std_logic_vector(to_unsigned(1, 10))), 10));
    union_lo <= selected_root when unsigned(selected_root) < unsigned(find_ptr) else find_ptr;
    union_hi <= find_ptr when unsigned(selected_root) < unsigned(find_ptr) else selected_root;
    choose_a <= better_peak(stat_a(81 downto 36), stat_q(81 downto 36), stat_a(35 downto 29), stat_q(35 downto 29), stat_a(28 downto 24), stat_q(28 downto 24));
    equal_union_power <= '1' when unsigned(stat_a(81 downto 36)) = unsigned(stat_q(81 downto 36)) else '0';
    merged_cells <= std_logic_vector(resize(unsigned(std_logic_vector'('0' & stat_a(23 downto 12))), 13) + resize(unsigned(std_logic_vector'('0' & stat_q(23 downto 12))), 13));
    merged_equal <= std_logic_vector(resize(unsigned(std_logic_vector'('0' & stat_a(11 downto 0))), 13) + resize(unsigned(std_logic_vector'('0' & stat_q(11 downto 0))), 13));

    -- Preserve each field's own conditional selection; no ambiguous ternary+concat.
    merged_stat(81 downto 36) <= stat_a(81 downto 36) when choose_a='1' else stat_q(81 downto 36);
    merged_stat(35 downto 29) <= stat_a(35 downto 29) when choose_a='1' else stat_q(35 downto 29);
    merged_stat(28 downto 24) <= stat_a(28 downto 24) when choose_a='1' else stat_q(28 downto 24);
    merged_stat(23 downto 12) <= merged_cells(11 downto 0);
    merged_stat(11 downto 0) <= merged_equal(11 downto 0) when equal_union_power='1' else
                                stat_a(11 downto 0) when choose_a='1' else stat_q(11 downto 0);
    choose_current <= better_peak(current_power, stat_q(81 downto 36), expected_range, stat_q(35 downto 29), expected_bin, stat_q(28 downto 24));

    added_stat(81 downto 36) <= current_power when choose_current='1' else stat_q(81 downto 36);
    added_stat(35 downto 29) <= expected_range when choose_current='1' else stat_q(35 downto 29);
    added_stat(28 downto 24) <= expected_bin when choose_current='1' else stat_q(28 downto 24);
    added_stat(23 downto 12) <= std_logic_vector(unsigned(stat_q(23 downto 12))+to_unsigned(1,12));
    added_stat(11 downto 0) <= std_logic_vector(unsigned(stat_q(11 downto 0))+to_unsigned(1,12))
                                when current_power=stat_q(81 downto 36) else
                                std_logic_vector(to_unsigned(1,12)) when choose_current='1' else
                                stat_q(11 downto 0);
    in_ready <= '1' when unsigned(state) = unsigned(S_ACCEPT) else '0';
    out_valid <= '1' when unsigned(state) = unsigned(S_OUTPUT) else '0';
    out_record_id <= emitted_count;
    out_range <= best_stat(35 downto 29);
    out_bin <= best_stat(28 downto 24);
    out_signed_bin <= signed_bin(best_stat(28 downto 24));
    out_peak_power <= best_stat(81 downto 36);
    out_cluster_cells <= best_stat(23 downto 12);
    out_tie_flag <= '1' when unsigned(best_stat(11 downto 0)) > unsigned(std_logic_vector(to_unsigned(1, 12))) else '0';
    out_equal_power_cells <= best_stat(11 downto 0);

    process(neighbor_index, neighbor0, neighbor1, neighbor2, neighbor3)
    begin
        case neighbor_index is
            when "000" =>
                next_neighbor <= neighbor0;
            when "001" =>
                next_neighbor <= neighbor1;
            when "010" =>
                next_neighbor <= neighbor2;
            when others =>
                next_neighbor <= neighbor3;
        end case;
    end process;

    process(state, find_ptr, selected_root, label_count, scan_index)
    begin
        case state is
            when S_UNION_A =>
                stats_read_addr <= selected_root;
            when S_UNION_B =>
                stats_read_addr <= find_ptr;
            when S_ADD_READ =>
                stats_read_addr <= selected_root;
            when S_SORT_READ =>
                if unsigned(scan_index) <= unsigned(label_count) then
    stats_read_addr <= scan_index;
else
    stats_read_addr <= std_logic_vector(to_unsigned(0, 10));
end if;
            when others =>
                stats_read_addr <= std_logic_vector(to_unsigned(0, 10));
        end case;
    end process;

    process(state, expected_range, expected_bin, selected_root, label_count, current_power, next_label, union_lo, merged_stat, added_stat)
    begin
        stat_write_en <= '0';
        stat_write_addr <= std_logic_vector(to_unsigned(0, 10));
        stat_write_data <= (others => '0');
        case state is
            when S_UNION_WR =>
                stat_write_en <= '1';
                stat_write_addr <= union_lo;
                stat_write_data <= merged_stat;
            when S_PROCESS =>
                if ((unsigned(selected_root) = unsigned(std_logic_vector(to_unsigned(0, 10)))) and (unsigned(label_count) < to_unsigned(MAX_LABELS, 10))) and (unsigned(label_count) < to_unsigned(PHYSICAL_LABELS, 10)) then
                    stat_write_en <= '1';
                    stat_write_addr <= next_label;
                    stat_write_data <= std_logic_vector'(current_power & expected_range & expected_bin & std_logic_vector(to_unsigned(1, 12)) & std_logic_vector(to_unsigned(1, 12)));
                end if;
            when S_ADD_WRITE =>
                stat_write_en <= '1';
                stat_write_addr <= selected_root;
                stat_write_data <= added_stat;
            when others =>
                null;
        end case;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if stat_write_en = '1' then
                stat_mem(to_integer(unsigned(stat_write_addr))) <= stat_write_data;
            end if;
            stat_q <= stat_mem(to_integer(unsigned(stats_read_addr)));
        end if;
    end process;

    process(state, find_ptr, selected_root, label_count, scan_index, next_label, union_lo, union_hi)
    begin
        parent_write_en <= '0';
        parent_write_addr <= std_logic_vector(to_unsigned(0, 10));
        parent_write_data <= std_logic_vector(to_unsigned(0, 10));
        parent_read_addr <= std_logic_vector(to_unsigned(0, 10));
        case state is
            when S_UNION_WR =>
                parent_write_en <= '1';
                parent_write_addr <= union_hi;
                parent_write_data <= union_lo;
            when S_PROCESS =>
                if ((unsigned(selected_root) = unsigned(std_logic_vector(to_unsigned(0, 10)))) and (unsigned(label_count) < to_unsigned(MAX_LABELS, 10))) and (unsigned(label_count) < to_unsigned(PHYSICAL_LABELS, 10)) then
                    parent_write_en <= '1';
                    parent_write_addr <= next_label;
                    parent_write_data <= next_label;
                end if;
            when others =>
                null;
        end case;
        case state is
            when S_FIND_READ =>
                parent_read_addr <= find_ptr;
            when S_SORT_READ =>
                if unsigned(scan_index) <= unsigned(label_count) then
    parent_read_addr <= scan_index;
else
    parent_read_addr <= std_logic_vector(to_unsigned(0, 10));
end if;
            when others =>
                parent_read_addr <= std_logic_vector(to_unsigned(0, 10));
        end case;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if parent_write_en = '1' then
                parent(to_integer(unsigned(parent_write_addr))) <= parent_write_data;
            end if;
            parent_q <= parent(to_integer(unsigned(parent_read_addr)));
        end if;
    end process;

    process(in_valid, in_range, in_bin, in_alarm, out_ready, state, expected_range, expected_bin, row_index, selected_root, label_count, best_index, next_label)
    begin
        emitted_we <= '0';
        emitted_addr <= std_logic_vector(to_unsigned(0, 10));
        emitted_data <= '0';
        curr_we <= '0';
        curr_addr <= std_logic_vector(to_unsigned(0, 5));
        curr_data <= std_logic_vector(to_unsigned(0, 10));
        prev_we <= '0';
        prev_data <= std_logic_vector(to_unsigned(0, 10));
        if (((unsigned(state) = unsigned(S_PROCESS)) and (unsigned(selected_root) = to_unsigned(0, 10))) and (unsigned(label_count) < to_unsigned(MAX_LABELS, 10))) and (unsigned(label_count) < to_unsigned(PHYSICAL_LABELS, 10)) then
            emitted_we <= '1';
            emitted_addr <= next_label;
            emitted_data <= '0';
            curr_we <= '1';
            curr_addr <= std_logic_vector(resize(unsigned(expected_bin), 5) - resize(unsigned(std_logic_vector(to_unsigned(3, 5))), 5));
            curr_data <= next_label;
        end if;
        if (unsigned(state) = unsigned(S_OUTPUT)) and (out_ready = '1') then
            emitted_we <= '1';
            emitted_addr <= best_index;
            emitted_data <= '1';
        end if;
        if unsigned(state) = unsigned(S_INIT_ROW) then
            curr_we <= '1';
            curr_addr <= row_index;
            curr_data <= std_logic_vector(to_unsigned(0, 10));
            prev_we <= '1';
            prev_data <= std_logic_vector(to_unsigned(0, 10));
        end if;
        if unsigned(state) = unsigned(S_SHIFT_ROW) then
            curr_we <= '1';
            curr_addr <= row_index;
            curr_data <= std_logic_vector(to_unsigned(0, 10));
            prev_we <= '1';
            prev_data <= curr_row(to_integer(unsigned(row_index)));
        end if;
        if ((((unsigned(state) = unsigned(S_ACCEPT)) and (in_valid = '1')) and (unsigned(in_range) = unsigned(expected_range))) and (unsigned(in_bin) = unsigned(expected_bin))) and (not (in_alarm = '1')) then
            curr_we <= '1';
            curr_addr <= std_logic_vector(resize(unsigned(expected_bin), 5) - resize(unsigned(std_logic_vector(to_unsigned(3, 5))), 5));
            curr_data <= std_logic_vector(to_unsigned(0, 10));
        end if;
        if unsigned(state) = unsigned(S_ADD_WRITE) then
            curr_we <= '1';
            curr_addr <= std_logic_vector(resize(unsigned(expected_bin), 5) - resize(unsigned(std_logic_vector(to_unsigned(3, 5))), 5));
            curr_data <= selected_root;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if not (rst = '1') then
                if emitted_we = '1' then
                    emitted(to_integer(unsigned(emitted_addr))) <= emitted_data;
                end if;
                if curr_we = '1' then
                    curr_row(to_integer(unsigned(curr_addr))) <= curr_data;
                end if;
                if prev_we = '1' then
                    prev_row(to_integer(unsigned(row_index))) <= prev_data;
                end if;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= S_IDLE;
                busy_reg <= '0';
                done_reg <= '0';
                overflow_sticky_reg <= '0';
                protocol_error_reg <= '0';
                frame_invalid_reg <= '0';
                expected_range <= std_logic_vector(to_unsigned(3, 7));
                expected_bin <= std_logic_vector(to_unsigned(3, 5));
                row_index <= std_logic_vector(to_unsigned(0, 5));
                neighbor_index <= std_logic_vector(to_unsigned(0, 3));
                neighbor0 <= std_logic_vector(to_unsigned(0, 10));
                neighbor1 <= std_logic_vector(to_unsigned(0, 10));
                neighbor2 <= std_logic_vector(to_unsigned(0, 10));
                neighbor3 <= std_logic_vector(to_unsigned(0, 10));
                find_ptr <= std_logic_vector(to_unsigned(0, 10));
                selected_root <= std_logic_vector(to_unsigned(0, 10));
                label_count <= std_logic_vector(to_unsigned(0, 10));
                root_count <= std_logic_vector(to_unsigned(0, 10));
                emitted_count <= std_logic_vector(to_unsigned(0, 10));
                scan_index <= std_logic_vector(to_unsigned(0, 10));
                best_index <= std_logic_vector(to_unsigned(0, 10));
                best_found <= '0';
                best_stat <= (others => '0');
                current_power <= std_logic_vector(to_unsigned(0, 46));
                stat_a <= (others => '0');
            else
                done_reg <= '0';
                if (start = '1') and (unsigned(state) /= unsigned(S_IDLE)) then
                    protocol_error_reg <= '1';
                end if;
                case state is
                    when S_IDLE =>
                        if start = '1' then
                            busy_reg <= '1';
                            overflow_sticky_reg <= '0';
                            protocol_error_reg <= '0';
                            frame_invalid_reg <= '0';
                            expected_range <= std_logic_vector(to_unsigned(3, 7));
                            expected_bin <= std_logic_vector(to_unsigned(3, 5));
                            row_index <= std_logic_vector(to_unsigned(0, 5));
                            label_count <= std_logic_vector(to_unsigned(0, 10));
                            root_count <= std_logic_vector(to_unsigned(0, 10));
                            emitted_count <= std_logic_vector(to_unsigned(0, 10));
                            state <= S_INIT_ROW;
                        end if;
                    when S_INIT_ROW =>
                        if unsigned(row_index) = unsigned(std_logic_vector(to_unsigned(31, 5))) then
                            state <= S_ACCEPT;
                        else
                            row_index <= std_logic_vector(resize(unsigned(row_index), 5) + resize(unsigned(std_logic_vector(to_unsigned(1, 5))), 5));
                        end if;
                    when S_ACCEPT =>
                        if in_valid = '1' then
                            if (unsigned(in_range) /= unsigned(expected_range)) or (unsigned(in_bin) /= unsigned(expected_bin)) then
                                protocol_error_reg <= '1';
                                frame_invalid_reg <= '1';
                                busy_reg <= '0';
                                done_reg <= '1';
                                state <= S_IDLE;
                            elsif not (in_alarm = '1') then
                                state <= S_STEP;
                            else
                                current_power <= in_power;
                                if unsigned(expected_bin) = unsigned(std_logic_vector(to_unsigned(3, 5))) then
    neighbor0 <= std_logic_vector(to_unsigned(0, 10));
else
    neighbor0 <= curr_row(to_integer(unsigned(expected_bin))-4);
end if;
                                if unsigned(expected_bin) = unsigned(std_logic_vector(to_unsigned(3, 5))) then
    neighbor1 <= std_logic_vector(to_unsigned(0, 10));
else
    neighbor1 <= prev_row(to_integer(unsigned(expected_bin))-4);
end if;
                                neighbor2 <= prev_row(to_integer(unsigned(expected_bin))-3);
                                if unsigned(expected_bin) = unsigned(std_logic_vector(to_unsigned(28, 5))) then
    neighbor3 <= std_logic_vector(to_unsigned(0, 10));
else
    neighbor3 <= prev_row(to_integer(unsigned(expected_bin))-2);
end if;
                                neighbor_index <= std_logic_vector(to_unsigned(0, 3));
                                selected_root <= std_logic_vector(to_unsigned(0, 10));
                                state <= S_NEIGH;
                            end if;
                        end if;
                    when S_NEIGH =>
                        if unsigned(neighbor_index) = unsigned(std_logic_vector(to_unsigned(4, 3))) then
                            state <= S_PROCESS;
                        elsif unsigned(next_neighbor) = unsigned(std_logic_vector(to_unsigned(0, 10))) then
                            neighbor_index <= std_logic_vector(resize(unsigned(neighbor_index), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                        else
                            find_ptr <= next_neighbor;
                            state <= S_FIND_READ;
                        end if;
                    when S_FIND_READ =>
                        state <= S_FIND;
                    when S_FIND =>
                        if unsigned(parent_q) /= unsigned(find_ptr) then
                            find_ptr <= parent_q;
                            state <= S_FIND_READ;
                        elsif unsigned(selected_root) = unsigned(std_logic_vector(to_unsigned(0, 10))) then
                            selected_root <= find_ptr;
                            neighbor_index <= std_logic_vector(resize(unsigned(neighbor_index), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                            state <= S_NEIGH;
                        elsif unsigned(selected_root) = unsigned(find_ptr) then
                            neighbor_index <= std_logic_vector(resize(unsigned(neighbor_index), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                            state <= S_NEIGH;
                        else
                            state <= S_UNION_A;
                        end if;
                    when S_UNION_A =>
                        state <= S_UNION_B;
                    when S_UNION_B =>
                        stat_a <= stat_q;
                        state <= S_UNION_WR;
                    when S_UNION_WR =>
                        selected_root <= union_lo;
                        root_count <= std_logic_vector(resize(unsigned(root_count), 10) - resize(unsigned(std_logic_vector(to_unsigned(1, 10))), 10));
                        neighbor_index <= std_logic_vector(resize(unsigned(neighbor_index), 3) + resize(unsigned(std_logic_vector(to_unsigned(1, 3))), 3));
                        state <= S_NEIGH;
                    when S_PROCESS =>
                        if unsigned(selected_root) = unsigned(std_logic_vector(to_unsigned(0, 10))) then
                            if (unsigned(label_count) >= to_unsigned(MAX_LABELS, 10)) or (unsigned(label_count) >= to_unsigned(PHYSICAL_LABELS, 10)) then
                                overflow_sticky_reg <= '1';
                                frame_invalid_reg <= '1';
                                busy_reg <= '0';
                                done_reg <= '1';
                                state <= S_IDLE;
                            else
                                label_count <= next_label;
                                root_count <= std_logic_vector(resize(unsigned(root_count), 10) + resize(unsigned(std_logic_vector(to_unsigned(1, 10))), 10));
                                state <= S_STEP;
                            end if;
                        else
                            state <= S_ADD_READ;
                        end if;
                    when S_ADD_READ =>
                        state <= S_ADD_WRITE;
                    when S_ADD_WRITE =>
                        state <= S_STEP;
                    when S_STEP =>
                        if unsigned(expected_bin) = unsigned(std_logic_vector(to_unsigned(28, 5))) then
                            if unsigned(expected_range) = unsigned(std_logic_vector(to_unsigned(109, 7))) then
                                state <= S_SORT_INIT;
                            else
                                row_index <= std_logic_vector(to_unsigned(0, 5));
                                state <= S_SHIFT_ROW;
                            end if;
                        else
                            expected_bin <= std_logic_vector(resize(unsigned(expected_bin), 5) + resize(unsigned(std_logic_vector(to_unsigned(1, 5))), 5));
                            state <= S_ACCEPT;
                        end if;
                    when S_SHIFT_ROW =>
                        if unsigned(row_index) = unsigned(std_logic_vector(to_unsigned(31, 5))) then
                            expected_range <= std_logic_vector(resize(unsigned(expected_range), 7) + resize(unsigned(std_logic_vector(to_unsigned(1, 7))), 7));
                            expected_bin <= std_logic_vector(to_unsigned(3, 5));
                            state <= S_ACCEPT;
                        else
                            row_index <= std_logic_vector(resize(unsigned(row_index), 5) + resize(unsigned(std_logic_vector(to_unsigned(1, 5))), 5));
                        end if;
                    when S_SORT_INIT =>
                        if unsigned(emitted_count) = unsigned(root_count) then
                            busy_reg <= '0';
                            done_reg <= '1';
                            state <= S_IDLE;
                        else
                            scan_index <= std_logic_vector(to_unsigned(1, 10));
                            best_found <= '0';
                            state <= S_SORT_READ;
                        end if;
                    when S_SORT_READ =>
                        if unsigned(scan_index) > unsigned(label_count) then
                            state <= S_OUTPUT;
                        else
                            state <= S_SORT_CHECK;
                        end if;
                    when S_SORT_CHECK =>
                        if (unsigned(parent_q) = unsigned(scan_index)) and (not (emitted(to_integer(unsigned(scan_index))) = '1')) then
                            if (not (best_found = '1')) or (better_record(stat_q, best_stat) = '1') then
                                best_stat <= stat_q;
                                best_index <= scan_index;
                                best_found <= '1';
                            end if;
                        end if;
                        scan_index <= std_logic_vector(resize(unsigned(scan_index), 10) + resize(unsigned(std_logic_vector(to_unsigned(1, 10))), 10));
                        state <= S_SORT_READ;
                    when S_OUTPUT =>
                        if out_ready = '1' then
                            emitted_count <= std_logic_vector(resize(unsigned(emitted_count), 10) + resize(unsigned(std_logic_vector(to_unsigned(1, 10))), 10));
                            state <= S_SORT_INIT;
                        end if;
                    when others =>
                        protocol_error_reg <= '1';
                        frame_invalid_reg <= '1';
                        busy_reg <= '0';
                        done_reg <= '1';
                        state <= S_IDLE;
                end case;
            end if;
        end if;
    end process;

    busy <= busy_reg;
    done <= done_reg;
    overflow_sticky <= overflow_sticky_reg;
    protocol_error <= protocol_error_reg;
    frame_invalid <= frame_invalid_reg;

end architecture rtl;

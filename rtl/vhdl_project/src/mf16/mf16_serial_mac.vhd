-- AUTO-TRANSLATED from mf16/mf16_serial_mac.v; independent validation REQUIRED.
-- Source SHA256: cb06afe430edd32e2cd736d2740ec2d8994b79f07a4b7d022449b200f74fb08b
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity mf16_serial_mac is
    port (
        clk : in std_logic;
        rst : in std_logic;
        start : in std_logic;
        range_in : in std_logic_vector(6 downto 0);
        tap_valid : in std_logic;
        tap_index : in std_logic_vector(3 downto 0);
        sample_re : in std_logic_vector(15 downto 0);
        sample_im : in std_logic_vector(15 downto 0);
        busy : out std_logic;
        done : out std_logic;
        range_out : out std_logic_vector(6 downto 0);
        result_re : out std_logic_vector(21 downto 0);
        result_im : out std_logic_vector(21 downto 0);
        saturation_event : out std_logic;
        saturation_mask : out std_logic_vector(1 downto 0);
        prelimit_re : out std_logic_vector(63 downto 0);
        prelimit_im : out std_logic_vector(63 downto 0);
        protocol_error : out std_logic
    );
end entity mf16_serial_mac;

architecture rtl of mf16_serial_mac is
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

    signal coeff_re : std_logic_vector(15 downto 0);
    signal coeff_im : std_logic_vector(15 downto 0);
    signal expected_tap : std_logic_vector(3 downto 0);
    signal finalize_pending : std_logic;
    signal final_re : std_logic_vector(36 downto 0);
    signal final_im : std_logic_vector(36 downto 0);
    signal accum_re : std_logic_vector(36 downto 0);
    signal accum_im : std_logic_vector(36 downto 0);
    signal p_rr : std_logic_vector(31 downto 0);
    signal p_ii : std_logic_vector(31 downto 0);
    signal p_ri : std_logic_vector(31 downto 0);
    signal p_ir : std_logic_vector(31 downto 0);
    signal pair_re : std_logic_vector(32 downto 0);
    signal pair_im : std_logic_vector(32 downto 0);
    signal accum_re_next : std_logic_vector(36 downto 0);
    signal accum_im_next : std_logic_vector(36 downto 0);
    signal rounded_re : std_logic_vector(21 downto 0);
    signal rounded_im : std_logic_vector(21 downto 0);
    signal ov_re : std_logic;
    signal ov_im : std_logic;
    signal pre_re : std_logic_vector(63 downto 0);
    signal pre_im : std_logic_vector(63 downto 0);
    signal busy_reg : std_logic;
    signal done_reg : std_logic;
    signal range_out_reg : std_logic_vector(6 downto 0);
    signal result_re_reg : std_logic_vector(21 downto 0);
    signal result_im_reg : std_logic_vector(21 downto 0);
    signal saturation_event_reg : std_logic;
    signal saturation_mask_reg : std_logic_vector(1 downto 0);
    signal prelimit_re_reg : std_logic_vector(63 downto 0);
    signal prelimit_im_reg : std_logic_vector(63 downto 0);
    signal protocol_error_reg : std_logic;
begin

    p_rr <= std_logic_vector(resize(signed(std_logic_vector(signed(sample_re) * signed(coeff_re))), 32));
    p_ii <= std_logic_vector(resize(signed(std_logic_vector(signed(sample_im) * signed(coeff_im))), 32));
    p_ri <= std_logic_vector(resize(signed(std_logic_vector(signed(sample_re) * signed(coeff_im))), 32));
    p_ir <= std_logic_vector(resize(signed(std_logic_vector(signed(sample_im) * signed(coeff_re))), 32));
    pair_re <= std_logic_vector(signed(std_logic_vector'(p_rr(31) & p_rr)) - signed(std_logic_vector'(p_ii(31) & p_ii)));
    pair_im <= std_logic_vector(signed(std_logic_vector'(p_ri(31) & p_ri)) + signed(std_logic_vector'(p_ir(31) & p_ir)));
    accum_re_next <= std_logic_vector(signed(accum_re) + resize(signed(std_logic_vector'(repeat_slv(pair_re(32), 4) & pair_re)), 37));
    accum_im_next <= std_logic_vector(signed(accum_im) + resize(signed(std_logic_vector'(repeat_slv(pair_im(32), 4) & pair_im)), 37));

    u_coeff : entity work.mf16_coeff_rom
        port map (
            index => tap_index,
            coeff_re => coeff_re,
            coeff_im => coeff_im
        );

    u_rne_re : entity work.rne_sat_signed
        generic map (
            IN_W => 37,
            OUT_W => 22
        )
        port map (
            in_value => final_re,
            shift_amt => std_logic_vector(to_unsigned(15, 6)),
            out_value => rounded_re,
            overflow => ov_re,
            prelimit => pre_re
        );

    u_rne_im : entity work.rne_sat_signed
        generic map (
            IN_W => 37,
            OUT_W => 22
        )
        port map (
            in_value => final_im,
            shift_amt => std_logic_vector(to_unsigned(15, 6)),
            out_value => rounded_im,
            overflow => ov_im,
            prelimit => pre_im
        );

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                busy_reg <= '0';
                finalize_pending <= '0';
                final_re <= std_logic_vector(to_signed(0, 37));
                final_im <= std_logic_vector(to_signed(0, 37));
                done_reg <= '0';
                range_out_reg <= std_logic_vector(to_unsigned(0, 7));
                result_re_reg <= std_logic_vector(to_unsigned(0, 22));
                result_im_reg <= std_logic_vector(to_unsigned(0, 22));
                accum_re <= std_logic_vector(to_unsigned(0, 37));
                accum_im <= std_logic_vector(to_unsigned(0, 37));
                expected_tap <= std_logic_vector(to_unsigned(0, 4));
                saturation_event_reg <= '0';
                saturation_mask_reg <= std_logic_vector(to_unsigned(0, 2));
                prelimit_re_reg <= std_logic_vector(to_unsigned(0, 64));
                prelimit_im_reg <= std_logic_vector(to_unsigned(0, 64));
                protocol_error_reg <= '0';
            else
                done_reg <= '0';
                saturation_event_reg <= '0';
                saturation_mask_reg <= std_logic_vector(to_unsigned(0, 2));
                if finalize_pending = '1' then
                    result_re_reg <= rounded_re;
                    result_im_reg <= rounded_im;
                    prelimit_re_reg <= pre_re;
                    prelimit_im_reg <= pre_im;
                    saturation_mask_reg <= std_logic_vector'(ov_im & ov_re);
                    saturation_event_reg <= (ov_re) or (ov_im);
                    done_reg <= '1';
                    busy_reg <= '0';
                    finalize_pending <= '0';
                end if;
                if start = '1' then
                    if busy_reg = '1' then
                        protocol_error_reg <= '1';
                    else
                        busy_reg <= '1';
                        accum_re <= std_logic_vector(to_unsigned(0, 37));
                        accum_im <= std_logic_vector(to_unsigned(0, 37));
                        expected_tap <= std_logic_vector(to_unsigned(0, 4));
                        range_out_reg <= range_in;
                    end if;
                end if;
                if (tap_valid = '1') and (finalize_pending = '1') then
                    protocol_error_reg <= '1';
                end if;
                if ((tap_valid = '1') and (busy_reg = '1')) and (not (finalize_pending = '1')) then
                    if unsigned(tap_index) /= unsigned(expected_tap) then
                        protocol_error_reg <= '1';
                        busy_reg <= '0';
                    else
                        accum_re <= accum_re_next;
                        accum_im <= accum_im_next;
                        expected_tap <= std_logic_vector(resize(unsigned(expected_tap), 4) + resize(unsigned(std_logic_vector(to_unsigned(1, 4))), 4));
                        if unsigned(tap_index) = unsigned(std_logic_vector(to_unsigned(15, 4))) then
                            final_re <= accum_re_next;
                            final_im <= accum_im_next;
                            finalize_pending <= '1';
                        end if;
                    end if;
                end if;
            end if;
        end if;
    end process;

    busy <= busy_reg;
    done <= done_reg;
    range_out <= range_out_reg;
    result_re <= result_re_reg;
    result_im <= result_im_reg;
    saturation_event <= saturation_event_reg;
    saturation_mask <= saturation_mask_reg;
    prelimit_re <= prelimit_re_reg;
    prelimit_im <= prelimit_im_reg;
    protocol_error <= protocol_error_reg;

end architecture rtl;

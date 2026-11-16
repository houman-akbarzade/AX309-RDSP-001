-- Manual VHDL-93-equivalent of rne_sat_signed.v (S04/C02).
-- Signed magnitude Round-to-Nearest-Even, then saturation. No pipeline.
-- This file is independent of vendor FFT-IP.
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity rne_sat_signed is
  generic (IN_W: integer := 43; OUT_W: integer := 25);
  port (in_value: in std_logic_vector(IN_W-1 downto 0);
        shift_amt: in std_logic_vector(5 downto 0);
        out_value: out std_logic_vector(OUT_W-1 downto 0);
        overflow: out std_logic;
        prelimit: out std_logic_vector(63 downto 0));
end entity;
architecture rtl of rne_sat_signed is
begin
  process(in_value,shift_amt)
    variable xv, yv: signed(63 downto 0);
    variable magnitude,quotient,remainder,half,mask: unsigned(63 downto 0);
    variable maximum,minimum: signed(63 downto 0);
    variable shift: integer range 0 to 63;
  begin
    xv := resize(signed(in_value),64);
    shift := to_integer(unsigned(shift_amt));
    maximum := shift_left(to_signed(1,64),OUT_W-1)-to_signed(1,64);
    minimum := -shift_left(to_signed(1,64),OUT_W-1);
    if shift=0 then
      yv := xv;
    else
      if xv < 0 then
        magnitude := unsigned(-xv);
      else
        magnitude := unsigned(xv);
      end if;
      quotient := shift_right(magnitude,shift);
      mask := shift_left(to_unsigned(1,64),shift)-to_unsigned(1,64);
      remainder := magnitude and mask;
      half := shift_left(to_unsigned(1,64),shift-1);
      if (remainder>half) or ((remainder=half) and (quotient(0)='1')) then
        quotient := quotient+to_unsigned(1,64);
      end if;
      if xv<0 then yv:=-signed(quotient);
      else yv:=signed(quotient); end if;
    end if;
    prelimit <= std_logic_vector(yv);
    if yv>maximum or yv<minimum then overflow<='1';
    else overflow<='0'; end if;
    if yv>maximum then out_value<=std_logic_vector(maximum(OUT_W-1 downto 0));
    elsif yv<minimum then out_value<=std_logic_vector(minimum(OUT_W-1 downto 0));
    else out_value<=std_logic_vector(yv(OUT_W-1 downto 0)); end if;
  end process;
end architecture;

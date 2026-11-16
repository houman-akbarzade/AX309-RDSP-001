-- AUTO-TRANSLATED from uart/s05_iq_cpi_banked.v; independent validation REQUIRED.
-- Source SHA256: c65f71b9bdf1875ab88b0f19df31aa23ac972400eb4b054f9d1ae9cf56806c00
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity s05_iq_cpi_banked is
    port (
        clk : in std_logic;
        write_en : in std_logic;
        write_addr : in std_logic_vector(12 downto 0);
        write_word : in std_logic_vector(31 downto 0);
        read_addr : in std_logic_vector(12 downto 0);
        read_word : out std_logic_vector(31 downto 0)
    );
end entity s05_iq_cpi_banked;

architecture rtl of s05_iq_cpi_banked is
    type bank0_array_t is array (0 to 4095) of std_logic_vector(31 downto 0);
    signal bank0 : bank0_array_t;
    type bank1_array_t is array (0 to 127) of std_logic_vector(31 downto 0);
    signal bank1 : bank1_array_t;
    signal read0 : std_logic_vector(31 downto 0);
    signal read1 : std_logic_vector(31 downto 0);
    signal read_bank : std_logic;
begin

    read_word <= read1 when read_bank = '1' else read0;

    process(clk)
    begin
        if rising_edge(clk) then
            read_bank <= read_addr(12);
            if (write_en = '1') and (not (write_addr(12) = '1')) then
                bank0(to_integer(unsigned(write_addr(11 downto 0)))) <= write_word;
            end if;
            if ((write_en = '1') and (write_addr(12) = '1')) and (unsigned(write_addr(11 downto 7)) = to_unsigned(0, 5)) then
                bank1(to_integer(unsigned(write_addr(6 downto 0)))) <= write_word;
            end if;
            read0 <= bank0(to_integer(unsigned(read_addr(11 downto 0))));
            read1 <= bank1(to_integer(unsigned(read_addr(6 downto 0))));
        end if;
    end process;


end architecture rtl;

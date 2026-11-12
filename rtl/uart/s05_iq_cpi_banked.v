// S05 laboratory CPI IQ banked storage: 33 pulses x 128 complex IQ samples,
// 4224 32-bit words = 16896 bytes. Bank0: 4096, bank1: 128 words.
// One synchronous read port and one write port; intended Spartan-6 BRAM.
// No reset clears RAM itself; upload-byte coverage reset invalidates old data.
// No extra raw/MF frame buffer is allocated by this module.
module s05_iq_cpi_banked (
    input wire clk,
    input wire write_en,
    input wire [12:0] write_addr,
    input wire [31:0] write_word,
    input wire [12:0] read_addr,
    output wire [31:0] read_word
);
    reg [31:0] bank0[0:4095];
    reg [31:0] bank1[0:127];
    reg [31:0] read0;
    reg [31:0] read1;
    reg read_bank;
    always @(posedge clk) begin
        read_bank<=read_addr[12];
        if (write_en && !write_addr[12])
            bank0[write_addr[11:0]] <= write_word;
        if (write_en && write_addr[12] && write_addr[11:7]==0)
            bank1[write_addr[6:0]] <= write_word;
        // Unconditional synchronous reads support ISE BRAM inference.
        read0 <= bank0[read_addr[11:0]];
        read1 <= bank1[read_addr[6:0]];
    end
    assign read_word = read_bank ? read1 : read0;
endmodule

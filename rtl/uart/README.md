# S05 UART RX/TX + S02 frame parser: laboratory echo RTL

This is synthesizable Verilog-2001 for Xilinx ISE 14.7, XC6SLX9-2FTG256.
`uart_s02_echo_top` contains one 8N1 UART RX, one 8N1 UART TX and
`s02_frame_echo`. On receipt of a complete S02 frame with valid
SOF/version/TYPE/flags, 0..512 payload length and CRC32/ISO-HDLC, the
top **echoes the exact original wire frame** including its CRC.

**This is NOT a protocol ACK, Session/Epoch FSM, IQ CPI controller or ARQ.**
A host must wait for the full echo before sending another frame; a second
frame during echo is deliberately **dropped and counted** (`busy_drop_count`).
The Echo is a laboratory PHY/framing integrity probe only.

## Reproduce on Linux with Xilinx ISE 14.7

From repository root:

```sh
bash rtl/tb/run_uart_s02_echo_isim.sh
bash rtl/tools/run_xst_uart_s02.sh
python3 -m unittest discover -s tests -p 'test_s05_pc*.py' -v
```

The runner first calls `rtl/tools/generate_uart_pc_vectors.py`, which imports
**`pc_link.codec`** for the 41-byte SESSION_HELLO, 529-byte IQ_UPLOAD
(including SOF embedded inside the payload) and 37-byte ACK framing.
The ISim testbench serializes these bytes at actual **nominal 50MHz clock,
115200 8N1, 434 clock cycles per bit**, checks TX start/data/stop bits
using an independent bit sampler and compares every observed byte to the
PC-generated golden byte file. Invalid CRC, version/flags, 513-byte
declared payload, truncated frame timeout, bad stop and noise are injected.

`uart_rx_8n1.v`, `uart_tx_8n1.v`, `s02_frame_echo.v` and
`uart_s02_echo_top.v` are the only synthesizable RTL in this step.
No Xilinx HDL test-bench tasks or RAM initialization files are used in
synthesizable RTL. The echo RAM uses one synchronous read and one indexed
write port; XST inferred one RAMB8BWER after a first implementation
had incorrectly mapped the entire buffer into LUT/FF. Retained evidence
covers the corrected source only.

## Scope / constraints

Nominal AX309 oscillator **50MHz** is documented in project S01 and S02;
the physical board oscillator and pin wiring are **not yet verified**.
The RXD=C11, TXD=D12 and clock=T8 assignments are reported by the board
manual; **no UCF or board test** was produced in this work package.
Integer baud-divider quantization uses `50000000/115200=434` cycles.
Parser byte inactivity timeout is 20 nominal byte times by default;
the TB uses a shorter deterministic test override (16000 cycles).

No physical UART pin timing, connected full-radar XST, MAP/PAR,
post-route STA, real FPGA transaction/ARQ, Session FSM, signal-processing
changes or 702-record result transmission occurred here.
Independent XST minimum-period estimates are not timing closure.
Older S04 dispositions and the seven open DSP-stage output schemas remain
unchanged.

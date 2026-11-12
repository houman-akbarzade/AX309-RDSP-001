# AX309 S05 PC UART reference — executable software only

This package implements **PC-side** S02 framing and R1 session-tagged byte formats.
It also contains a **Python FPGA software simulator**, not an FPGA RTL implementation,
and an optional pyserial adapter to use after an FPGA UART endpoint exists.

## Run (from repository root)

```sh
python3 -m unittest discover -s tests -p 'test_s05_pc*.py' -v
python3 -m pc_link demo --json-out engineering/evidence/s05/pc_link/demo-v0.1.json
python3 -m pc_link iq-fixture --out /tmp/ax309_synthetic_cpi_iq.bin
python3 -m pc_link --help
```

Optional, **only when UART RTL is available on the board** (not tested on AX309):

```sh
python3 -m pc_link handshake --port /dev/ttyUSB0 --baud 115200
```

`python3` and the standard library suffice for codec/simulator/tests.
The optional physical `handshake` command requires `pyserial` (`import serial`).
The command opens a serial port and sends HELLO/ACTIVATE but **does not** run
a CPI on real hardware. No physical serial, CP2102GM pin, baud or FPGA test
has been performed yet.

## Modules

- `codec.py`: SOF/header/CRC32-ISO-HDLC, incremental SOF resync, R1 tagged
  ACK/NACK and four exact SESSION_CONTROL payload schemas.
- `session.py`: PC/FPGASoftwareSimulator four-message handshake and
  `activated_once` latch; a lost READY causes an identical response, never
  an application-sequence reset.
- `arq.py`: one outstanding reliable frame per direction, exact ACK and SID,
  NACK, duplicates, delayed/stale ACK rejection, 2-second *caller-controlled*
  timeout and 3 retransmissions; no arbitrary ACK-of-ACK loop.
- `iq.py`: deterministic 33x128 signed Q1.15 IQ bytes, 35×<=488B
  upload, 35×<=484B bytewise readback, and 99-bit/13-byte LE grouping
  record serialization with zero five-bit padding.
- `simulator.py`: **software-only** FPGA behavior for IQ acceptance and
  readback, RUN gate and 702 *synthetic transport records*, plus host
  provisional records and COMMIT count/ID validation. The generated
  records are **not** actual radar clustering or an S04 oracle result.
- `serial_io.py`: optional pyserial-backed stream reader and Stop-and-Wait
  sender (and dependency-injected fake-byte-serial tests).
- `__main__.py`: runnable CLI entry points.

`tests/test_s05_pc_link.py` and `tests/test_s05_pc_serial.py` exercise the
above. All results must be based on the actual recorded test log.

## Conservative implementation boundaries

The engineer authorized **laboratory development**, not full UART or REQ-LIST-01
acceptance. In this reference, numeric TYPE/opcode fields use the proposed
R2/R1 values, and normal active payloads carry the 16-byte R1 session ID.
Original S02 17-byte outer envelope, CRC coverage and <=512 payload are
unchanged. The four bootstrap frames are 41/43/44/44 bytes.

The simulator can replay COMMIT with the original seq or recover its immutable
decision by QUERY with a **new SID and new reliable sequence**. Its state is
volatile Python RAM, not a persistent FPGA or host journal. `RELEASE_CPI`,
`RECOVER_UNKNOWN`, durable host journal and seven DSP stage-output schemas
remain **blocked/unimplemented** until their error-state and durable-recovery
conditions are explicitly validated. The simulator refuses unsupported
commands instead of approving partial results. The physical serial CLI
currently supports **handshake only**; it does not claim tested board
CPI upload, RESULT/COMMIT or full FPGA resource/timing fit.

The demonstration's short synthetic IQ and cluster semantics are **transport
fixtures only**. Do not infer radar detection, Range-Resolution, statistical
qualification, RTL readiness or board PASS from the software tests.

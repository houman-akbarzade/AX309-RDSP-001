"""Run the S05 PC reference without a board, or handshake with a real serial port."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets

from .iq import synthetic_iq
from .simulator import run_demo
from .session import PCSession
from .serial_io import connect_serial_port, handshake


def main(argv=None):
    ap = argparse.ArgumentParser(description="AX309 S05 PC UART protocol reference (NO FPGA RTL)")
    sub = ap.add_subparsers(dest="task", required=True)
    demo = sub.add_parser("demo", help="Software-only end-to-end protocol exchange, no board")
    demo.add_argument("--json-out", type=Path, help="Save actual software exchange summary JSON")
    fixture = sub.add_parser("iq-fixture", help="Write 16896 deterministic synthetic IQ bytes")
    fixture.add_argument("--out", type=Path, required=True)
    physical = sub.add_parser("handshake", help="Try CP2102 serial handshake; FPGA UART RTL REQUIRED")
    physical.add_argument("--port", required=True, help="e.g. /dev/ttyUSB0")
    physical.add_argument("--baud", type=int, default=115200)
    physical.add_argument("--timeout", type=float, default=2.0)
    board = sub.add_parser("board-iq-smoke", help="Physical AX309: handshake, 35 IQ uploads and byte-exact 35 readbacks (NO DSP)")
    board.add_argument("--port", required=True, help="e.g. /dev/ttyUSB0 for CP2102GM")
    board.add_argument("--baud", type=int, default=115200)
    board.add_argument("--timeout", type=float, default=2.0)
    board.add_argument("--cpi-id", type=int, default=23)
    args = ap.parse_args(argv)
    if args.task == "demo":
        result = run_demo()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.json_out:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(json.dumps(result, indent=2) + "\n")
    elif args.task == "iq-fixture":
        data = synthetic_iq()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
        print(f"IQ_BYTES={len(data)} SHA256={hashlib.sha256(data).hexdigest()} PATH={args.out}")
    elif args.task == "board-iq-smoke":
        from dataclasses import asdict
        from .board_iq import run_board_iq_smoke
        sid = secrets.token_bytes(16)
        if not any(sid):
            raise RuntimeError("OS CSPRNG generated invalid zero session ID")
        uart = connect_serial_port(args.port, args.baud)
        try:
            result = run_board_iq_smoke(uart, sid, args.cpi_id, args.timeout)
            print(json.dumps(asdict(result), indent=2))
            print("WARNING: UART IQ-only test; no DSP, CPI_COMMIT or whole-radar acceptance")
        finally:
            uart.io.close()
    elif args.task == "handshake":
        sid = secrets.token_bytes(16)
        if not any(sid):
            raise RuntimeError("OS CSPRNG generated invalid zero session ID")
        uart = connect_serial_port(args.port, args.baud)
        try:
            client = PCSession(sid)
            handshake(uart, client, args.timeout)
            print(f"HANDSHAKE_ACTIVE SIMULATION=NO SID={sid.hex()} (UART+FPGA must be tested separately)")
        finally:
            uart.io.close()


if __name__ == "__main__":
    main()

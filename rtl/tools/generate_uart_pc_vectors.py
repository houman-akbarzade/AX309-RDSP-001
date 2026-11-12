#!/usr/bin/env python3
"""Create independent PC codec golden wire bytes for ISim UART bit-serial TB.

The oracle imports pc_link.codec; it does not reimplement frame CRC or S02
serialization in the Verilog testbench.
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pc_link.codec import Frame, Type, SessionOp, SOF, bootstrap, active_payload
from pc_link.iq import synthetic_iq

OUT = ROOT / "rtl" / "tb" / "vectors" / "uart_pc"
SID = bytes.fromhex("00112233445566778899aabbccddeeff")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hello = bootstrap(SessionOp.HELLO, SID, mode=0, prior_valid=0, cpi_id=0)
    raw = bytearray(synthetic_iq()[:488])
    # Embed a real SOF inside an independently PC-packed CRC-valid IQ payload.
    # It must remain data, NOT start a new UART frame.
    raw[100:104] = SOF
    iq = Frame(Type.IQ_UPLOAD, 1, active_payload(
        SID, struct.pack("<II", 23, 0) + raw)).encode()
    after = Frame(Type.ACK, 1, active_payload(
        SID, struct.pack("<I", 1))).encode()
    invalid_crc = bytearray(hello)
    invalid_crc[20] ^= 0x20  # mutate payload, intentionally do NOT update CRC
    invalid_version = bytearray(hello)
    invalid_version[4] = 2
    invalid_flags = bytearray(hello)
    invalid_flags[6] = 1
    invalid_length = SOF + struct.pack("<BBBIH", 1, Type.IQ_UPLOAD, 1, 5, 513)
    partial = hello[:20]
    noise = bytes.fromhex("1112a501a55a01a55ac3100000")
    vectors = {
        "hello": hello,
        "iq_529": iq,
        "after": after,
        "bad_crc": bytes(invalid_crc),
        "bad_version": bytes(invalid_version),
        "bad_flags": bytes(invalid_flags),
        "bad_length": invalid_length,
        "truncated": partial,
        "noise": noise,
        "expected_echo": hello + iq + after,
    }
    lengths = {name: len(v) for name, v in vectors.items()}
    assert lengths == {
        "hello": 41, "iq_529": 529, "after": 37,
        "bad_crc": 41, "bad_version": 41, "bad_flags": 41,
        "bad_length": 13, "truncated": 20, "noise": 13,
        "expected_echo": 607,
    }, lengths
    for name, data in vectors.items():
        (OUT / f"{name}.mem").write_text("".join(f"{x:02x}\n" for x in data))
    import zlib
    record = {
        "project": "AX309-RDSP-001", "stage": "S05",
        "oracle": "pc_link.codec.Frame.encode and bootstrap, direct import",
        "simulator": "ISim, serial 8N1, 50MHz/115200 => 434 clocks per bit",
        "status": "GENERATED_REFERENCE_BYTES_NOT_RTL_TEST_RESULT",
        "session_id": SID.hex(),
        "frame_sizes": lengths,
        "byte_sha256": {name: hashlib.sha256(data).hexdigest()
                        for name, data in vectors.items()},
        "valid_crc": {name: (zlib.crc32(data[4:-4])
                             == struct.unpack("<I", data[-4:])[0])
                      for name, data in vectors.items()
                      if name in ("hello", "iq_529", "after")},
        "independent_pc_IQ_payload_SOF_offset": 100,
        "RX_frame_count_expected": 3,
        "TX_byte_count_expected": 607,
        "not_covered": "Not Session FSM/ARQ/CPI/board; echo only",
    }
    (OUT / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    print("PC_CODEC_VECTORS lengths=", lengths, "validated_crc=", record["valid_crc"])
    print("PC_CODEC_VECTOR_SHA256", hashlib.sha256(
        (OUT / "manifest.json").read_bytes()).hexdigest())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate independent R1 PC wire vectors and expected FPGA responses."""
from __future__ import annotations
from pathlib import Path
import hashlib, json, struct, sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from pc_link.codec import (Frame, Type, SessionOp, Command, bootstrap,
                           active_payload, SOF)
SID_A=bytes.fromhex("00112233445566778899aabbccddeeff")
SID_B=bytes.fromhex("887766554433221100ffeeddccbbaa99")
OUT=ROOT/"rtl/tb/vectors/uart_r1"
OUT.mkdir(parents=True,exist_ok=True)


def response(kind:Type,sid,seq:int,number:int):
    return Frame(kind,seq,active_payload(sid,struct.pack("<I",number))).encode()


def command(sid,seq,op=Command.OPEN_CPI,cpi=23):
    return Frame(Type.COMMAND,seq,active_payload(sid,struct.pack("<BI",op,cpi))).encode()


def store(name,value):
    (OUT/(name+".mem")).write_text("".join(f"{v:02x}\n" for v in value))
    return value

hello_a=store("hello_a",bootstrap(SessionOp.HELLO,SID_A))
activate_a=store("activate_a",bootstrap(SessionOp.ACTIVATE,SID_A,mode=0,
                                        kind=0,cpi_valid=0,cpi_id=0,info=0))
hello_b=store("hello_b",bootstrap(SessionOp.HELLO,SID_B))
activate_b=store("activate_b",bootstrap(SessionOp.ACTIVATE,SID_B,mode=0,
                                        kind=0,cpi_valid=0,cpi_id=0,info=0))
open_b=store("open_b",command(SID_B,0))
old_a=store("old_a",command(SID_A,0))
future_b=store("future_b",command(SID_B,2))
new_bad_b=store("new_bad_b",command(SID_B,1)) # OPEN when CPI already open
old_seq_b=store("old_seq_b",command(SID_A,1))
corrupt=bytearray(command(SID_B,1))
corrupt[-5]^=0x40
store("bad_crc",bytes(corrupt))
trunc=store("truncated",command(SID_B,1)[:18])
control_ack=store("inbound_ack_b",response(Type.ACK,SID_B,0,0))
offer_a=bootstrap(SessionOp.OFFER,SID_A,kind=0,cpi_valid=0,cpi_id=0,info=0)
ready_a=bootstrap(SessionOp.READY,SID_A,result=0,kind=0,cpi_valid=0,cpi_id=0,info=0)
offer_b=bootstrap(SessionOp.OFFER,SID_B,kind=0,cpi_valid=0,cpi_id=0,info=0)
ready_b=bootstrap(SessionOp.READY,SID_B,result=0,kind=0,cpi_valid=0,cpi_id=0,info=0)
ack_b0=response(Type.ACK,SID_B,0,0)
nack_b2=response(Type.NACK,SID_B,2,1)
nack_b1=response(Type.NACK,SID_B,1,1)
# Expected response stream, in chronological order:
# HELLO_A/OFFER_A; ACTIVATE_A/READY_A; repeated ACTIVATE_A/READY_A;
# HELLO_B/OFFER_B; ACTIVATE_B/READY_B;
# OPEN_B/ACK0; repeated OPEN_B/ACK0;
# repeated ACTIVATE_B/READY_B;
# future_B/NACK2; unsupported current seq1/NACK1;
# reset; HELLO_A/OFFER_A; ACTIVATE_A/READY_A;
# reset while negotiation pending: HELLO_A/OFFER_A, reset, ACTIVATE_A ignored,
# HELLO_A/OFFER_A and ACTIVATE_A/READY_A.
answers=[offer_a,ready_a,ready_a,offer_b,ready_b,
         ack_b0,ack_b0,ready_b,nack_b2,nack_b1,offer_a,ready_a,
         offer_a,offer_a,ready_a]
expected=store("expected_responses",b"".join(answers))
manifest={
 "project":"AX309-RDSP-001","stage":"S05","status":"PC_CODEC_GOLDEN_ONLY_NOT_RTL_PASS",
 "source":"pc_link.codec.Frame.encode/bootstrap direct, not RTL producer",
 "inputs":{p.stem:len(bytes.fromhex(''.join(p.read_text().splitlines())))
           for p in sorted(OUT.glob("*.mem")) if p.stem!="expected_responses"},
 "expected_frame_lengths":[len(x) for x in answers],
 "expected_TX_frames":len(answers),"expected_TX_bytes":len(expected),
 "SID_A":SID_A.hex(),"SID_B":SID_B.hex(),
 "source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(OUT.glob("*.mem"))},
 "test_meaning":"R1 session/ARQ handshake and simple COMMAND OPEN_CPI only, IQ not accepted yet"
}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("PC_R1_VECTOR_GEN",manifest["expected_frame_lengths"],"TX",len(expected),
      "inputs",manifest["inputs"])
if __name__=="__main__":
    pass

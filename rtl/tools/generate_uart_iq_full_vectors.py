#!/usr/bin/env python3
"""PC codec golden 35xIQ_UPLOAD and 35xSTAGE_DATA full CPI serial vectors.

Synthesis/RTL testbench NEVER generates a CRC or expected reply; these
golden byte streams are produced through pc_link.codec only.
"""
from pathlib import Path
import json
import hashlib
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from pc_link.codec import Frame,Type,SessionOp,Command,bootstrap,active_payload
from pc_link.iq import synthetic_iq,upload_chunks,readback_requests,CPI_SIZE

OUT=ROOT/"rtl/tb/vectors/uart_iq_full"
OUT.mkdir(parents=True,exist_ok=True)
SID=bytes.fromhex("102132435465768798a9bacbdcedfe0f")
SID_OLD=bytes.fromhex("ffeeddccbbaa99887766554433221100")
CPI=23

def packet(kind,seq,sid,body):
    return Frame(kind,seq,active_payload(sid,body)).encode()

def a(n):
    return packet(Type.ACK,n,SID,struct.pack("<I",n))

def n(offender,expected):
    return packet(Type.NACK,offender,SID,struct.pack("<I",expected))

def cmd(seq,op=Command.OPEN_CPI):
    return packet(Type.COMMAND,seq,SID,struct.pack("<BI",op,CPI))

def write(name,data):
    path=OUT/(name+".mem")
    path.write_text("".join(f"{x:02x}\n" for x in data))
    return data

raw=synthetic_iq()
hello=write("hello",bootstrap(SessionOp.HELLO,SID))
activate=write("activate",bootstrap(SessionOp.ACTIVATE,SID,mode=0,
                 kind=0,cpi_valid=0,cpi_id=0,info=0))
open_cpi=write("open_cpi",cmd(0))
good_upload=[packet(Type.IQ_UPLOAD,index+1,SID,chunk)
             for index,chunk in enumerate(upload_chunks(CPI,raw))]
assert len(good_upload)==35 and len(good_upload[-1])==345
upload_flat=write("uploads_flat",b"".join(good_upload))
upload_offsets=[0]
for frame in good_upload:
    upload_offsets.append(upload_offsets[-1]+len(frame))
write("upload_offsets_16bit_le",b"".join(struct.pack("<H",o) for o in upload_offsets))
assert upload_offsets[-1]==len(upload_flat)
requests=[packet(Type.STAGE_REQUEST,36+index,SID,body)
          for index,body in enumerate(readback_requests(CPI))]
assert len(requests)==35 and all(len(req)==44 for req in requests)
requests_flat=write("requests_flat",b"".join(requests))
stage_data=[packet(Type.STAGE_DATA,index,SID,struct.pack("<IBI",CPI,0,offset)+
                   raw[offset:offset+min(484,CPI_SIZE-offset)])
            for index,offset in enumerate(range(0,CPI_SIZE,484))]
assert len(stage_data)==35 and all(len(x)==526 for x in stage_data[:-1]) and len(stage_data[-1])==482
stage_ack=[packet(Type.ACK,index,SID,struct.pack("<I",index)) for index in range(35)]
stage_ack_flat=write("stage_acks_flat",b"".join(stage_ack))
offer=bootstrap(SessionOp.OFFER,SID,kind=0,cpi_valid=0,cpi_id=0,info=0)
ready=bootstrap(SessionOp.READY,SID,result=0,kind=0,cpi_valid=0,cpi_id=0,info=0)
bad_offset=packet(Type.IQ_UPLOAD,1,SID,struct.pack("<II",CPI,488)+raw[:488])
future=cmd(3)
bad_crc=bytearray(good_upload[1])
bad_crc[-5]^=0x80
bad_crc=bytes(bad_crc)
old_sid=packet(Type.IQ_UPLOAD,2,SID_OLD,
               struct.pack("<II",CPI,488)+raw[488:976])
truncated=good_upload[1][:34]
bad_stage=packet(Type.STAGE_REQUEST,36,SID,
                 struct.pack("<IBIH",CPI,1,0,484))
for name,val in (("bad_offset",bad_offset),("future",future),
                 ("bad_crc",bad_crc),("old_sid",old_sid),
                 ("truncated",truncated),("bad_stage",bad_stage)):
    write(name,val)

# Host script expected FPGA replies; inject one bad-offset request and
# future seq (NACK), an exact duplicate first upload, and a lost first
# stage reply ACK (outbound retransmission after timeout).
replies=[offer,ready,a(0),n(1,1),n(3,1),a(1),a(1)]
replies += [a(i) for i in range(2,36)]
# Invalid stage0 request at seq36 must NACK36 without consuming seq.
replies.append(n(36,36))
# Stage requests: one inbound ACK then stage data per chunk.
# First stage data is resent once with IDENTICAL bytes and seq0.
for index in range(35):
    replies.append(a(36+index))
    replies.append(stage_data[index])
    if index==0:
        replies.append(stage_data[index])
expected=write("expected_responses",b"".join(replies))
write("response_lengths",b"".join(struct.pack("<H",len(x)) for x in replies))
print("FULL_IQ_GENERATED",{
  "IQ_bytes":len(raw),
  "upload_frames":len(good_upload),"upload_flat_bytes":len(upload_flat),
  "stage_req_frames":len(requests),"stage_reply_frames":len(stage_data),
  "expected_responses":len(replies),"expected_TX_bytes":len(expected),
  "last_upload_frame_len":len(good_upload[-1]),
  "last_stage_frame_len":len(stage_data[-1])
})
m={
 "project":"AX309-RDSP-001","stage":"S05",
 "status":"PC_CODEC_VECTOR_ONLY_NOT_RTL_PASS",
 "source":["pc_link.codec.Frame.encode","pc_link.iq.synthetic_iq",
           "pc_link.iq.upload_chunks","pc_link.iq.readback_requests"],
 "SID":SID.hex(),"CPI_ID":CPI,"IQ_SHA256":hashlib.sha256(raw).hexdigest(),
 "upload_lengths":[len(x) for x in good_upload],
 "upload_offsets":upload_offsets,
 "stage_request_lengths":[len(x) for x in requests],
 "stage_data_lengths":[len(x) for x in stage_data],
 "expected_response_lengths":[len(x) for x in replies],
 "expected_TX_bytes":len(expected),
 "expected_TX_response_frames":len(replies),
 "reply_injection":"one 526B first STAGE_DATA replay after dropped ACK",
 "sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(OUT.glob("*.mem"))},
}
(OUT/"manifest.json").write_text(json.dumps(m,indent=2)+"\n")

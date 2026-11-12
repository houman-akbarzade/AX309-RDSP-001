#!/usr/bin/env python3
"""Analytical S02 UART 8N1 CPI timing budget; no RTL execution or board measurement.

Only approved S02 primitives are constants. Packet-batch payload layout and
empty ACKs are explicit non-approved modelling assumptions.
"""
from __future__ import annotations
from math import ceil
from pathlib import Path
from hashlib import sha256
import json

DOC=Path("engineering/S02-engineering-contracts-APPROVED-AMENDMENT-v1.1.md")
contract=DOC.read_text()
for phrase in ("IQ wire bytes: pulse-major", "33*128*4=16896B",
               "payload length 0..512", "initial UART 8N1 at 115200 baud",
               "up to 3 retransmissions", "timeout nominal 2s per frame"):
    assert phrase in contract,phrase

BAUD=115200
BIT_PER_BYTE=10
FRAME_OVERHEAD=4+1+1+1+4+2+4
MAX_PAYLOAD=512
IQ_BYTES=33*128*4
IQ_UPLOAD_METADATA=4+4
IQ_CHUNK=MAX_PAYLOAD-IQ_UPLOAD_METADATA
IQ_PACKETS=ceil(IQ_BYTES/IQ_CHUNK)
ACK_FRAME_BYTES=FRAME_OVERHEAD # modelling empty ACK, payload schema not frozen

def serial_s(n: int)->float:
    return n*BIT_PER_BYTE/BAUD

def phase(n_packets: int, data_bytes: int, metadata_bytes_per_packet: int) -> dict:
    frame_bytes=data_bytes+n_packets*(metadata_bytes_per_packet+FRAME_OVERHEAD)
    ack_bytes=n_packets*ACK_FRAME_BYTES
    return {
        "packet_count":n_packets,
        "payload_data_bytes":data_bytes,
        "metadata_bytes":n_packets*metadata_bytes_per_packet,
        "frame_overhead_bytes":n_packets*FRAME_OVERHEAD,
        "forward_transmitted_bytes":frame_bytes,
        "ack_assumed_zero_payload_bytes":ack_bytes,
        "both_directions_bytes_no_retries":frame_bytes+ack_bytes,
        "forward_airtime_s":serial_s(frame_bytes),
        "ack_airtime_s":serial_s(ack_bytes),
        "airtime_with_empty_acks_s":serial_s(frame_bytes+ack_bytes),
    }

input_case=phase(IQ_PACKETS,IQ_BYTES,IQ_UPLOAD_METADATA)
assert IQ_PACKETS==34 and input_case["forward_transmitted_bytes"]==17746
assert input_case["both_directions_bytes_no_retries"]==18324

result_count=702
record_width=99
record_bytes=ceil(record_width/8)
assert record_bytes==13
results={}
for n in (39,8,1):
    packs=ceil(result_count/n)
    assert 4+n*record_bytes<=MAX_PAYLOAD
    results[f"result_batch_{n}"]=phase(packs,record_bytes*result_count,4)
assert results['result_batch_39']["forward_transmitted_bytes"]==9504
assert results['result_batch_39']["both_directions_bytes_no_retries"]==9810
assert results['result_batch_8']["both_directions_bytes_no_retries"]==12470

out={
 "project":"AX309-RDSP-001",
 "method":"Analytical 8N1 UART line serialization, NOT UART RTL/board measurement",
 "normative_source":str(DOC),
 "normative_source_sha256":sha256(DOC.read_bytes()).hexdigest(),
 "approved_constants":{
   "pulses":33,"fast_time_samples_per_pulse":128,
   "I_bits":16,"Q_bits":16,"IQ_order":"pulse major, each complex sample I then Q, little-endian two's-complement signed Q1.15",
   "CPI_input_bytes":IQ_BYTES,"initial_nominal_baud":BAUD,
   "uart_bits_per_octet_8N1":BIT_PER_BYTE,
   "UART_SOF_hex":"A55AC33C","UART_version":1,
   "maximum_payload_bytes":MAX_PAYLOAD,"frame_overhead_bytes":FRAME_OVERHEAD,
   "IQ_UPLOAD_CPI_ID_bytes":4,"IQ_UPLOAD_offset_bytes":4,
   "per_frame_nominal_ARQ_timeout_s":2,"max_retransmissions_after_initial":3
 },
 "non_approved_calculation_assumptions":[
   "ACK packet assumed empty, exactly 17 bytes each; actual ACK payload may be longer",
   "RESULT example includes 4-byte CPI_ID followed by complete 13-byte records",
   "13-byte record byte packing, padding/endianness and UART TYPE values NOT APPROVED",
   "UART is at 115200 baud on board (unverified)",
   "No retransmissions, NACK, initial command, FINAL COMMIT, ABORT, CPI digest/readback, processing time, host latency or stalls",
   "No physical result packet/replay buffering implemented"
 ],
 "raw_line_octets_per_second":BAUD/BIT_PER_BYTE,
 "IQ_UPLOAD":{
   **input_case,
   "iq_bytes_per_full_packet":IQ_CHUNK,
   "full_packets":IQ_BYTES//IQ_CHUNK,
   "last_chunk_bytes":IQ_BYTES%IQ_CHUNK
 },
 "RESULT_max_702_components":{
   "record_bits":record_width,"per_record_packed_octets":record_bytes,
   "record_count":result_count,
   "candidate_batch_scenarios":results,
 },
 "two_phase_fault_free_lower_bound_with_empty_acks_s":{
   batch:input_case["airtime_with_empty_acks_s"]+p["airtime_with_empty_acks_s"]
   for batch,p in results.items()
 },
 "roundtrip_bytewise_readback_illustration":{
   "assumes_stage_data_8_byte_metadata_NOT_APPROVED":True,
   "additional_airtime_s_at_least_if_similar_34_packet_readback":input_case["airtime_with_empty_acks_s"],
   "full_readback_packet_schema_must_be_approved":True
 },
 "per_512_payload_max_529_byte_frame_airtime_s":serial_s(529),
 "failed_packet_nominal_four_2_s_ack_waits_s":2*(1+3),
 "failed_packet_note":"Approximately 8 s ACK waiting after four attempts if each times out, PLUS physical serial/transmission and error handling; not a whole CPI bound.",
 "CPI_processing_cycles_measured":False,
 "FPGA_UART_TX_RX_resource_measured":False,
 "full_cycle_upper_bound":"NOT_ESTABLISHED",
 "continuous_IQ_real_time_required":False,
 "REQ_LIST_01_technical_PASS":False
}
p=Path("engineering/S05-UART-CPI-TIMING-EVIDENCE-v0.1.json")
p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
for name,ans in [('IQ upload',input_case),('702 records batch39',results['result_batch_39']),('702 records batch8',results['result_batch_8'])]:
    print(name,"packets",ans['packet_count'],"forward_bytes",ans['forward_transmitted_bytes'],
          "min_airtime_s",format(ans['airtime_with_empty_acks_s'],'.9f'))
print("UPLOAD+RESULT39 (empty ACKs)",format(out['two_phase_fault_free_lower_bound_with_empty_acks_s']['result_batch_39'],'.9f'),"seconds")
print("UPLOAD+RESULT8 (empty ACKs)",format(out['two_phase_fault_free_lower_bound_with_empty_acks_s']['result_batch_8'],'.9f'),"seconds")
print("S02 SHA",out['normative_source_sha256'])
print("REPORT",p)

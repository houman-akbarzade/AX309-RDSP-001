"""AX309 CP2102GM PC smoke runner for the FPGA S05 UART/R1 IQ-only bitstream.

No DSP or COMMIT is claimed. Only OPEN_CPI, 35 IQ_UPLOAD and 35 raw
STAGE_REQUEST readbacks are used; every byte is compared before success.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import struct
from .codec import Frame,Type,Command,PacketError,active_payload,split_active
from .session import PCSession
from .serial_io import UARTStream,handshake,send_stop_and_wait
from .arq import ReliableEndpoint
from .iq import synthetic_iq,upload_chunks,readback_requests,unpack_stage_data,CPI_SIZE


@dataclass
class BoardIQResult:
    cpi_id: int
    iq_bytes: int
    iq_sha256: str
    upload_packets: int
    readback_packets: int
    bytewise_match: bool
    board_uart_observed: bool = True


def run_board_iq_smoke(uart: UARTStream, sid: bytes, cpi_id: int = 23,
                       timeout_s: float = 2.0, max_retries: int = 3) -> BoardIQResult:
    """Mutates only the explicitly selected CPI. Call on a fresh FPGA/reset.

    If interrupted, do not silently continue with another CPI_ID or COMMIT;
    reset/recover according to the separately controlled host/FPGA contract.
    """
    from .codec import check_sid
    check_sid(sid)
    raw = synthetic_iq()
    pc = PCSession(sid, mode=0, max_retries=max_retries)
    handshake(uart, pc, wait_s=timeout_s)
    if pc.state != "ACTIVE" or pc.application_locked:
        raise PacketError("fresh FPGA epoch not active")
    ep = ReliableEndpoint(sid, max_retries=max_retries, timeout_s=timeout_s)

    send_stop_and_wait(uart, ep, Type.COMMAND,
                       struct.pack("<BI", Command.OPEN_CPI, cpi_id),
                       wait_s=timeout_s)
    uploads=0
    for chunk in upload_chunks(cpi_id,raw):
        send_stop_and_wait(uart, ep, Type.IQ_UPLOAD, chunk, wait_s=timeout_s)
        uploads+=1
    if uploads != 35:
        raise PacketError("incomplete upload")

    # FPGA ACK of upload is not equivalent to successful host readback.
    readback=bytearray()
    replies=0
    fpga_tx_seq=0
    for req in readback_requests(cpi_id):
        cpi,stage,offset,count=struct.unpack("<IBIH",req)
        if cpi!=cpi_id or stage!=0 or offset!=len(readback):
            raise PacketError("local readback request does not match coverage")
        send_stop_and_wait(uart,ep,Type.STAGE_REQUEST,req,wait_s=timeout_s)
        accepted=False
        for _attempt in range(max_retries+1):
            frame=uart.read_frame(timeout_s*1.5)
            if frame is None:
                continue
            if frame.type != Type.STAGE_DATA:
                continue
            try:
                body=split_active(frame,sid)
                cpi_out, off_out, data=unpack_stage_data(body)
                if frame.seq!=fpga_tx_seq or cpi_out!=cpi_id or off_out!=offset:
                    raise PacketError("STAGE_DATA wrong CPI/offset/sequence")
                if len(data)!=count or data!=raw[offset:offset+count]:
                    raise PacketError("STAGE_DATA bytewise IQ mismatch")
            except PacketError:
                nack=Frame(Type.NACK,fpga_tx_seq,
                           active_payload(sid,struct.pack("<I",fpga_tx_seq))).encode()
                uart.write(nack)
                continue
            ack=Frame(Type.ACK,fpga_tx_seq,
                      active_payload(sid,struct.pack("<I",fpga_tx_seq))).encode()
            uart.write(ack)
            readback.extend(data)
            fpga_tx_seq+=1
            replies+=1
            accepted=True
            break
        if not accepted:
            raise PacketError("failed verified IQ STAGE_DATA; no success/COMMIT")
    if len(readback)!=CPI_SIZE or bytes(readback)!=raw or replies!=35:
        raise PacketError("incomplete or incorrect readback; CPI rejected")
    return BoardIQResult(cpi_id,len(raw),hashlib.sha256(raw).hexdigest(),
                         uploads,replies,True)

"""PC 'board-iq-smoke' integration through a SOFTWARE serial-like stub.

This does NOT exercise the AX309 board, UART bitstream or pin interface.
"""
from __future__ import annotations
import struct
import unittest
from pc_link.codec import Frame, Type, PacketError, active_payload
from pc_link.serial_io import UARTStream
from pc_link.simulator import FPGASoftwareSimulator
from pc_link.board_iq import run_board_iq_smoke

SID=bytes.fromhex("00112233445566778899aabbccddeeff")


class SoftFPGAByteSerial:
    def __init__(self, corrupt_stage=False):
        self.fpga=FPGASoftwareSimulator()
        self.queue=bytearray()
        self.corrupt_stage=corrupt_stage
        self.upload_packets_seen=0
        self.readbacks_sent=0

    def write(self, encoded):
        frame=Frame.decode(encoded)
        if frame.type==Type.IQ_UPLOAD:
            self.upload_packets_seen+=1
        replies=self.fpga.receive(encoded)
        for packet in replies:
            obj=Frame.decode(packet)
            if obj.type==Type.STAGE_DATA:
                self.readbacks_sent+=1
                if self.corrupt_stage and self.readbacks_sent==1:
                    p=bytearray(obj.payload)
                    p[-1]^=1
                    packet=Frame(obj.type,obj.seq,bytes(p)).encode()
            self.queue.extend(packet)
        return len(encoded)

    def read(self,n):
        data=bytes(self.queue[:n])
        del self.queue[:n]
        return data

    def close(self):
        pass


class BoardIQPCSoftwareOnlyTests(unittest.TestCase):
    def test_full_35_upload_and_35_readback_with_software_stub(self):
        fake=SoftFPGAByteSerial()
        result=run_board_iq_smoke(UARTStream(fake),SID,cpi_id=23,timeout_s=0.02)
        self.assertEqual((result.iq_bytes,result.upload_packets,result.readback_packets),
                         (16896,35,35))
        self.assertTrue(result.bytewise_match)
        self.assertEqual(fake.upload_packets_seen,35)
        self.assertEqual(fake.readbacks_sent,35)
        self.assertEqual(fake.fpga.assembler.next_offset,16896)

    def test_full_readback_mismatch_cannot_succeed(self):
        fake=SoftFPGAByteSerial(corrupt_stage=True)
        # FPGA software stub replies with an unmodified stage on NACK,
        # so successful correction is allowed; the corrupt one is never ACKed.
        result=run_board_iq_smoke(UARTStream(fake),SID,cpi_id=23,timeout_s=0.02)
        self.assertTrue(result.bytewise_match)
        self.assertGreater(fake.readbacks_sent,35)


if __name__=="__main__":
    unittest.main()

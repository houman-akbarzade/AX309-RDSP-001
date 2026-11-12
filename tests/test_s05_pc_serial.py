"""Fake-byte-serial tests of the real PC serial adapter; NOT AX309 hardware."""
from __future__ import annotations
from collections import deque
import struct
import time
import unittest

from pc_link.codec import Frame, Type, SessionOp, PacketError, parse_session, active_payload
from pc_link.session import PCSession, FPGASessionSimulator
from pc_link.serial_io import UARTStream, handshake, send_stop_and_wait
from pc_link.arq import ReliableEndpoint, RetryExhausted

SID = bytes.fromhex("00112233445566778899aabbccddeeff")


class FakeByteSerial:
    """Serial-like byte pump with actual framing but no UART PHY/FPGA RTL."""
    def __init__(self, *, drop_ready=False, drop_offer=False, drop_ack=False):
        self.rx = bytearray()
        self.fpga_session = FPGASessionSimulator()
        self.fpga_arq = None
        self.drop_ready = drop_ready
        self.drop_offer = drop_offer
        self.drop_ack = drop_ack
        self.accepted_data = []
        self.closed = False
        self.wires = []

    def write(self, data: bytes):
        self.wires.append(data)
        f = Frame.decode(data)
        if f.type == Type.SESSION_CONTROL:
            out = self.fpga_session.receive(data)
            if self.fpga_session.state == "ACTIVE" and self.fpga_arq is None:
                self.fpga_arq = ReliableEndpoint(self.fpga_session.sid)
            if out:
                op, _ = parse_session(Frame.decode(out))
                if op == SessionOp.READY and self.drop_ready:
                    self.drop_ready = False
                elif op == SessionOp.OFFER and self.drop_offer:
                    self.drop_offer = False
                else:
                    self.rx.extend(out)
        else:
            result = self.fpga_arq.receive(f, lambda kind, payload:
                                           self.accepted_data.append((kind,payload)))
            for reply in result.replies:
                if Frame.decode(reply).type == Type.ACK and self.drop_ack:
                    self.drop_ack = False
                else:
                    self.rx.extend(reply)
        return len(data)

    def read(self, size: int) -> bytes:
        if not self.rx:
            time.sleep(0.0004)
            return b""
        chunk = bytes(self.rx[:size])
        del self.rx[:size]
        return chunk

    def close(self):
        self.closed = True


class SerialAdapterTests(unittest.TestCase):
    def test_fake_byte_serial_handshake(self):
        fake = FakeByteSerial()
        stream = UARTStream(fake)
        pc = PCSession(SID)
        handshake(stream,pc,wait_s=0.02)
        self.assertEqual(pc.state,"ACTIVE")
        self.assertEqual(fake.fpga_session.activation_count,1)
        self.assertEqual([len(w) for w in fake.wires],[41,44])

    def test_fake_serial_lost_offer_and_ready(self):
        fake=FakeByteSerial(drop_offer=True,drop_ready=True)
        stream=UARTStream(fake)
        pc=PCSession(SID,max_retries=3)
        handshake(stream,pc,wait_s=0.006)
        self.assertEqual(pc.state,"ACTIVE")
        self.assertEqual(fake.fpga_session.activation_count,1)
        self.assertEqual([len(w) for w in fake.wires],[41,41,44,44])
        self.assertEqual(fake.wires[-1],fake.wires[-2])
        fake.fpga_session.app_rx_expected=5
        fake.fpga_session.app_tx_next=3
        fake.write(fake.wires[-1])
        self.assertEqual((fake.fpga_session.app_rx_expected,fake.fpga_session.app_tx_next),(5,3))

    def test_fake_serial_stop_wait_ack_replay_after_ack_drop(self):
        fake=FakeByteSerial(drop_ack=True)
        stream=UARTStream(fake)
        pc=PCSession(SID)
        handshake(stream,pc,wait_s=0.02)
        ep=ReliableEndpoint(SID)
        send_stop_and_wait(stream,ep,Type.COMMAND,b"abcd",wait_s=0.008)
        self.assertEqual(ep.tx_next,1)
        self.assertEqual(len(fake.accepted_data),1)
        self.assertEqual(fake.fpga_arq.duplicate,1)
        self.assertEqual(fake.wires[-1],fake.wires[-2])

    def test_fake_serial_rejects_old_ack(self):
        fake=FakeByteSerial()
        stream=UARTStream(fake)
        pc=PCSession(SID)
        handshake(stream,pc,wait_s=0.02)
        ep=ReliableEndpoint(SID)
        old_sid=bytes.fromhex("ffeeddccbbaa99887766554433221100")
        old_ack=Frame(Type.ACK,0,active_payload(old_sid,struct.pack("<I",0))).encode()
        fake.rx.extend(old_ack)
        send_stop_and_wait(stream,ep,Type.COMMAND,b"x",wait_s=0.02)
        self.assertEqual(ep.tx_next,1)
        self.assertGreater(ep.stale,0)

    def test_fake_serial_retry_exhaustion(self):
        fake=FakeByteSerial()
        stream=UARTStream(fake)
        pc=PCSession(SID)
        handshake(stream,pc,wait_s=0.02)
        fake.drop_ack=True
        original_write=fake.write
        def drop_all_acks(write_bytes):
            # Monkeypatch receiver to suppress all ACK responses, but still
            # apply only one identical valid application packet.
            fake.drop_ack=True
            return original_write(write_bytes)
        fake.write=drop_all_acks
        ep=ReliableEndpoint(SID,max_retries=3)
        with self.assertRaises(RetryExhausted):
            send_stop_and_wait(stream,ep,Type.IQ_UPLOAD,b"x",wait_s=0.004)
        self.assertEqual(len(fake.accepted_data),1)
        self.assertEqual(fake.fpga_arq.duplicate,3)
        self.assertEqual(ep.retries,3)

    def test_stream_parser_wire_corruption_then_valid_ack(self):
        fake=FakeByteSerial()
        port=UARTStream(fake)
        bad=bytearray(Frame(Type.ACK,0,active_payload(SID,struct.pack("<I",0))).encode())
        bad[-1]^=0x02
        good=Frame(Type.ACK,0,active_payload(SID,struct.pack("<I",0))).encode()
        fake.rx.extend(b"stray"+bad+good)
        parsed=port.read_frame(0.02)
        self.assertEqual(parsed,Frame.decode(good))
        self.assertGreater(port.parser.rejected,0)


if __name__ == "__main__":
    unittest.main()

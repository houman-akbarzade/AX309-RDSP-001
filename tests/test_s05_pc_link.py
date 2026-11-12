"""S05 PC-only S02/R1 protocol tests. Run explicitly, not the S04 suite."""
from __future__ import annotations
import hashlib
import json
import struct
import unittest
import zlib
from pathlib import Path

from pc_link.codec import (Frame, Type, SessionOp, Status, Command, PacketError,
                           StreamParser, SOF, bootstrap, parse_session, active_payload)
from pc_link.session import PCSession, FPGASessionSimulator, Snapshot
from pc_link.arq import ReliableEndpoint, RetryExhausted
from pc_link.iq import (CPI_SIZE, IQAssembler, Record, synthetic_iq, synthetic_records,
                        upload_chunks, readback_requests, unpack_stage_data,
                        parse_result, result_payloads, IQ_CHUNK, READBACK_CHUNK)
from pc_link.simulator import PCHost, FPGASoftwareSimulator, SoftwareLink, run_demo

SID_A = bytes.fromhex("00112233445566778899aabbccddeeff")
SID_B = bytes.fromhex("deadbeefcafecafe0011223344556677")
ROOT = Path(__file__).resolve().parents[1]


def frame(t=Type.COMMAND, seq=0, data=b"x", sid=SID_A):
    return Frame(t, seq, active_payload(sid, data)).encode()


def control(t, seq, sid=SID_A, val=None):
    return Frame(t, seq, active_payload(sid, struct.pack("<I", seq if val is None else val))).encode()


class CodecTests(unittest.TestCase):
    def test_crc_iso_hdlc_check(self):
        self.assertEqual(zlib.crc32(b"123456789"), 0xCBF43926)

    def test_wire_header_crc_exact(self):
        w = frame(data=b"abc", seq=0x01234567)
        self.assertEqual(w[:4], SOF)
        self.assertEqual(w[4:7], b"\x01\x01\x01")
        self.assertEqual(w[7:11], bytes.fromhex("67452301"))
        self.assertEqual(w[11:13], struct.pack("<H", 19))
        self.assertEqual(w[-4:], struct.pack("<I", zlib.crc32(w[4:-4])))
        self.assertEqual(Frame.decode(w).encode(), w)

    def test_512_max_and_513_refused(self):
        w = Frame(Type.COMMAND, 0, bytes(512)).encode()
        self.assertEqual(len(w), 529)
        with self.assertRaises(PacketError):
            Frame(Type.COMMAND, 0, bytes(513)).encode()

    def test_bad_payload_crc_rejected(self):
        w = bytearray(frame(data=b"abcd"))
        w[-5] ^= 1
        with self.assertRaisesRegex(PacketError, "CRC"):
            Frame.decode(bytes(w))

    def test_bad_header_version_length_and_flags(self):
        for index, replacement in ((4, 2), (6, 0), (11, 0xff), (12, 0xff)):
            w = bytearray(frame())
            w[index] = replacement
            with self.assertRaises(PacketError):
                Frame.decode(bytes(w))

    def test_stream_parser_fragmented_and_resync(self):
        a = frame(data=b"one")
        b = frame(seq=1, data=b"two")
        parser = StreamParser()
        self.assertEqual(parser.feed(b"garbage" + a[:10]), [])
        self.assertEqual(parser.feed(a[10:]+b"\x00\xff"+b), [Frame.decode(a), Frame.decode(b)])

    def test_stream_parser_crc_bad_then_good(self):
        bad = bytearray(frame(data=b"changed"))
        bad[-1] ^= 0x20
        good = frame(seq=1, data=b"ok")
        parser = StreamParser()
        out = parser.feed(bytes(bad) + good)
        self.assertEqual(out, [Frame.decode(good)])
        self.assertGreater(parser.rejected, 0)

    def test_stream_timeout_discards_partial(self):
        p = StreamParser()
        good = frame()
        self.assertEqual(p.feed(good[:13]), [])
        p.reset_partial()
        self.assertEqual(p.feed(good), [Frame.decode(good)])

    def test_sof_inside_payload_not_new_frame(self):
        wire = frame(data=b"aaa" + SOF + b"zzz")
        p = StreamParser()
        self.assertEqual(p.feed(wire), [Frame.decode(wire)])

    def test_old_session_and_wrong_flags(self):
        w = frame()
        f = Frame.decode(w)
        from pc_link.codec import split_active
        with self.assertRaises(PacketError):
            split_active(f, SID_B)
        with self.assertRaises(PacketError):
            Frame(Type.SESSION_CONTROL, 0, b"bad", 1).encode()


class SessionTests(unittest.TestCase):
    def negotiate(self):
        pc = PCSession(SID_A)
        fpga = FPGASessionSimulator()
        hello = pc.start()
        offer = fpga.receive(hello)
        activate = pc.receive(offer)
        ready = fpga.receive(activate)
        pc.receive(ready)
        return pc, fpga, hello, offer, activate, ready

    def test_handshake_wire_lengths_and_manifest_crc(self):
        pc, fpga, hello, offer, activate, ready = self.negotiate()
        self.assertEqual([len(x) for x in (hello,offer,activate,ready)], [41,43,44,44])
        audit=json.loads((ROOT/'engineering/S05-LINK-SESSION-EPOCH-R1-WIRE-AUDIT-v0.1.json').read_text())
        for name, actual in zip(("HELLO","OFFER","ACTIVATE","READY"),(hello,offer,activate,ready)):
            self.assertEqual(actual.hex(), audit['synthetic_handshake_frames'][name]['example_wire_hex'])
        self.assertEqual(fpga.activation_count,1)
        self.assertEqual(pc.activation_count,1)

    def test_lost_hello(self):
        pc = PCSession(SID_A)
        f = FPGASessionSimulator()
        lost = pc.start()
        self.assertEqual(pc.timeout(),lost)
        offer = f.receive(lost)
        self.assertEqual(parse_session(Frame.decode(offer))[0],SessionOp.OFFER)

    def test_lost_offer_identical_replay(self):
        pc = PCSession(SID_A)
        f = FPGASessionSimulator()
        hello=pc.start()
        offer=f.receive(hello)
        self.assertEqual(f.receive(pc.timeout()),offer)
        self.assertEqual(f.activation_count,0)

    def test_lost_activate_then_retry(self):
        pc=PCSession(SID_A); f=FPGASessionSimulator()
        activate=pc.receive(f.receive(pc.start()))
        self.assertEqual(pc.timeout(),activate)
        ready=f.receive(activate)
        pc.receive(ready)
        self.assertEqual((f.activation_count,pc.state),(1,"ACTIVE"))

    def test_lost_ready_no_double_reset_after_data_progress(self):
        pc=PCSession(SID_A); f=FPGASessionSimulator()
        activate=pc.receive(f.receive(pc.start()))
        ready=f.receive(activate)
        # Drop first READY, FPGA can already have advanced its reliable state.
        f.app_rx_expected=17; f.app_tx_next=9
        self.assertEqual(f.receive(pc.timeout()),ready)
        self.assertEqual((f.app_rx_expected,f.app_tx_next),(17,9))
        pc.receive(ready)
        self.assertEqual(pc.state,"ACTIVE")
        self.assertEqual(f.receive(activate),ready)
        self.assertEqual((f.app_rx_expected,f.app_tx_next,f.activation_count),(17,9,1))

    def test_stale_ready_and_snapshot_tamper(self):
        pc = PCSession(SID_A)
        fpga=FPGASessionSimulator()
        activate=pc.receive(fpga.receive(pc.start()))
        wrong = bootstrap(SessionOp.READY,SID_B,result=0)
        self.assertIsNone(pc.receive(wrong))
        f=bytearray(fpga.receive(activate))
        f[13+2+16+1] = 1  # changed snapshot kind, CRC deliberately refreshed
        f[-4:]=struct.pack("<I",zlib.crc32(f[4:-4]))
        with self.assertRaises(PacketError):
            pc.receive(bytes(f))
        self.assertNotEqual(pc.state,"ACTIVE")

    def test_reconnect_new_sid_and_old_ready_rejected(self):
        pc, fpga, hello, offer, activate, ready = self.negotiate()
        pc2 = PCSession(SID_B)
        hello2=pc2.start()
        offer2=fpga.receive(hello2)
        self.assertIsNone(pc2.receive(ready))
        activate2=pc2.receive(offer2)
        ready2=fpga.receive(activate2)
        pc2.receive(ready2)
        self.assertEqual(pc2.state,"ACTIVE")
        self.assertIn(SID_A,fpga.retired)
        self.assertIsNone(fpga.receive(activate))
        self.assertEqual(fpga.activation_count,2)

    def test_fresh_cannot_overwrite_retained_cpi(self):
        pc=PCSession(SID_A,mode=0)
        fpga=FPGASessionSimulator()
        fpga.update_snapshot(Snapshot(2,1,73,5))
        offer=fpga.receive(pc.start())
        with self.assertRaisesRegex(PacketError,"FRESH"):
            pc.receive(offer)
        self.assertEqual(pc.state,"RECOVERY_REQUIRED")
        self.assertEqual(fpga.snapshot,Snapshot(2,1,73,5))

    def test_recover_mismatched_CPI_refused(self):
        pc=PCSession(SID_A,mode=1,prior_cpi=20)
        fpga=FPGASessionSimulator()
        fpga.update_snapshot(Snapshot(4,1,21,6))
        with self.assertRaises(PacketError):
            pc.receive(fpga.receive(pc.start()))
        self.assertEqual(pc.state,"RECOVERY_REQUIRED")

    def test_unknown_snapshot_recovery_is_application_locked(self):
        pc=PCSession(SID_A,mode=1,prior_cpi=22)
        fpga=FPGASessionSimulator()
        activate=pc.receive(fpga.receive(pc.start()))
        pc.receive(fpga.receive(activate))
        self.assertEqual(pc.state,"ACTIVE")
        self.assertTrue(pc.application_locked)

    def test_all_handshake_retry_exhaustion(self):
        pc=PCSession(SID_A,max_retries=3)
        wire=pc.start()
        for _ in range(3):
            self.assertEqual(pc.timeout(),wire)
        with self.assertRaises(TimeoutError):
            pc.timeout()
        self.assertEqual(pc.state,"RECOVERY_REQUIRED")


class ARQTests(unittest.TestCase):
    def test_ack_exact_advances_once(self):
        a=ReliableEndpoint(SID_A)
        w=a.send(Type.COMMAND,b"a")
        ack=Frame.decode(control(Type.ACK,0))
        a.receive(ack)
        self.assertIsNone(a.outstanding)
        self.assertEqual(a.tx_next,1)
        a.receive(ack)
        self.assertEqual(a.tx_next,1)

    def test_delayed_ack_after_retries_same_wire(self):
        a=ReliableEndpoint(SID_A)
        raw=a.send(Type.COMMAND,b"hello")
        self.assertEqual(a.timeout(),raw)
        self.assertEqual(a.timeout(),raw)
        a.receive(Frame.decode(control(Type.ACK,0)))
        self.assertEqual((a.tx_next,a.retries),(1,0))

    def test_stale_ack_wrong_epoch_same_sequence(self):
        a=ReliableEndpoint(SID_B)
        raw=a.send(Type.IQ_UPLOAD,b"test")
        self.assertTrue(a.receive(Frame.decode(control(Type.ACK,0,SID_A))).ignored)
        self.assertEqual(a.outstanding,raw)
        self.assertEqual(a.tx_next,0)
        a.receive(Frame.decode(control(Type.ACK,0,SID_B)))
        self.assertEqual(a.tx_next,1)

    def test_header_payload_ack_mismatch(self):
        a=ReliableEndpoint(SID_A)
        raw=a.send(Type.COMMAND,b"a")
        a.receive(Frame.decode(control(Type.ACK,0,val=1)))
        self.assertEqual(a.outstanding,raw)

    def test_nack_current_replay_not_release(self):
        a=ReliableEndpoint(SID_A)
        raw=a.send(Type.COMMAND,b"a")
        result=a.receive(Frame.decode(control(Type.NACK,0)))
        self.assertEqual(result.replies,[raw])
        self.assertEqual(a.tx_next,0)
        self.assertEqual(a.outstanding,raw)

    def test_nack_expected_plus_one_does_not_ack(self):
        a=ReliableEndpoint(SID_A)
        raw=a.send(Type.COMMAND,b"a")
        a.receive(Frame.decode(control(Type.NACK,0,val=1)))
        self.assertEqual(a.outstanding,raw)

    def test_duplicate_identical_data_reack_once(self):
        b=ReliableEndpoint(SID_A)
        w=frame(seq=0)
        effects=[]
        first=b.receive(Frame.decode(w),lambda t,p:effects.append(p))
        second=b.receive(Frame.decode(w),lambda t,p:effects.append(p))
        self.assertEqual(effects,[b"x"])
        self.assertEqual(first.replies,second.replies)
        self.assertEqual((b.rx_expected,b.duplicate),(1,1))

    def test_conflicting_duplicate_does_not_apply(self):
        b=ReliableEndpoint(SID_A)
        b.receive(Frame.decode(frame(seq=0,data=b"A")))
        bad=b.receive(Frame.decode(frame(seq=0,data=b"B")))
        self.assertTrue(bad.ignored)
        self.assertEqual(Frame.decode(bad.replies[0]).type,Type.NACK)
        self.assertEqual(b.rx_expected,1)

    def test_future_out_of_order_nack_expected(self):
        b=ReliableEndpoint(SID_A)
        out=b.receive(Frame.decode(frame(seq=3)))
        n=Frame.decode(out.replies[0])
        self.assertEqual(n.type,Type.NACK)
        self.assertEqual(n.seq,3)
        self.assertEqual(n.payload[-4:],struct.pack("<I",0))

    def test_apply_rejection_not_ack(self):
        b=ReliableEndpoint(SID_A)
        def refuse(t,p):
            raise PacketError("bad IQ offset")
        out=b.receive(Frame.decode(frame(seq=0)),refuse)
        self.assertEqual(Frame.decode(out.replies[0]).type,Type.NACK)
        self.assertEqual(b.rx_expected,0)

    def test_retry_limit_and_uncertain_commit(self):
        a=ReliableEndpoint(SID_A)
        w=a.send(Type.STATUS,struct.pack("<BIH",Status.CPI_COMMIT,7,2))
        for _ in range(3):
            self.assertEqual(a.timeout(),w)
        with self.assertRaises(RetryExhausted):
            a.timeout()
        self.assertTrue(a.terminal_ack_uncertain)
        self.assertEqual(a.outstanding,w)

    def test_one_outstanding_and_rollover_guard(self):
        a=ReliableEndpoint(SID_A)
        a.send(Type.COMMAND,b"a")
        with self.assertRaises(PacketError):
            a.send(Type.COMMAND,b"b")
        a.outstanding=None
        a.tx_next=0xFFFFFFFF
        with self.assertRaises(PacketError):
            a.send(Type.COMMAND,b"c")


class IQTests(unittest.TestCase):
    def test_deterministic_bytes_and_shape(self):
        raw=synthetic_iq()
        self.assertEqual(len(raw),16896)
        self.assertEqual(raw,synthetic_iq())
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         "311812204baef218d4df282e5df372a816a25e340a5b68b21ca62b3801e55865")

    def test_35_upload_packets_exact_reconstruction(self):
        raw=synthetic_iq()
        chunks=list(upload_chunks(9,raw))
        self.assertEqual(len(chunks),35)
        self.assertEqual([len(c)-8 for c in chunks],[488]*34+[304])
        a=IQAssembler(9)
        for chunk in chunks:
            a.accept(chunk)
        self.assertTrue(a.complete)
        self.assertEqual(bytes(a.data),raw)
        self.assertEqual(a.sha256(),hashlib.sha256(raw).hexdigest())

    def test_partial_cpi_not_complete_and_readback_rejected(self):
        a=IQAssembler(9)
        chunks=list(upload_chunks(9,synthetic_iq()))
        for c in chunks[:-1]:
            a.accept(c)
        self.assertFalse(a.complete)
        with self.assertRaises(PacketError):
            a.readback(0,484)

    def test_wrong_offset_duplicate_and_cross_CPI_rejected(self):
        chunks=list(upload_chunks(9,synthetic_iq()))
        a=IQAssembler(9)
        with self.assertRaises(PacketError):
            a.accept(chunks[1])
        a.accept(chunks[0])
        with self.assertRaises(PacketError):
            a.accept(chunks[0])
        forged=struct.pack("<I",10)+chunks[1][4:]
        with self.assertRaises(PacketError):
            a.accept(forged)

    def test_readback_35_segments_byte_exact(self):
        raw=synthetic_iq()
        a=IQAssembler(1)
        for c in upload_chunks(1,raw):
            a.accept(c)
        result=bytearray()
        reqs=list(readback_requests(1))
        self.assertEqual(len(reqs),35)
        for req in reqs:
            cpi,stage,offset,n=struct.unpack("<IBIH",req)
            self.assertEqual(stage,0)
            chunk=a.readback(offset,n)
            body=struct.pack("<IBI",cpi,stage,offset)+chunk
            self.assertEqual(unpack_stage_data(body),(1,offset,chunk))
            result.extend(chunk)
        self.assertEqual(result,raw)

    def test_record_99bit_roundtrip_and_zero_padding(self):
        for rec in synthetic_records(702):
            packed=rec.pack()
            self.assertEqual(len(packed),13)
            self.assertEqual(packed[12]&0xF8,0)
            self.assertEqual(Record.unpack(packed),rec)

    def test_record_padding_or_bad_signed_value_rejected(self):
        rec=synthetic_records(1)[0]
        corrupt=bytearray(rec.pack())
        corrupt[-1]|=0x80
        with self.assertRaises(PacketError):
            Record.unpack(corrupt)
        with self.assertRaises(PacketError):
            Record(0,3,3,40,5,1,0,1).pack()

    def test_702_records_88_result_payloads(self):
        records=synthetic_records(702)
        chunks=list(result_payloads(6,records))
        self.assertEqual(len(chunks),88)
        self.assertEqual(len(chunks[0]),108)
        found=[]
        for chunk in chunks:
            cpi,r=parse_result(chunk)
            self.assertEqual(cpi,6)
            found.extend(r)
        self.assertEqual(found,records)

    def test_result_corrupt_padding_rejected(self):
        payload=bytearray(next(result_payloads(6,synthetic_records(1))))
        payload[-1] |= 0x80
        with self.assertRaises(PacketError):
            parse_result(bytes(payload))


class SimulatorTests(unittest.TestCase):
    def test_full_PC_to_simulator_CPI_and_702_records(self):
        r=run_demo()
        self.assertEqual(r['upload_packets'],35)
        self.assertEqual(r['IQ_bytes'],r['readback_bytes'])
        self.assertEqual(r['synthetic_records'],702)
        self.assertEqual(r['result_packet_count'],88)
        self.assertEqual(r['host_COMMIT_count'],1)
        self.assertEqual(r['simulator'].split()[0],"FPGASoftwareSimulator")

    def test_host_blocks_run_before_readback(self):
        raw=synthetic_iq()
        p=PCHost(SID_A,raw,7)
        f=FPGASoftwareSimulator()
        link=SoftwareLink(p,f)
        link.transfer("PC",p.session.start())
        link.pc_send(Type.COMMAND,struct.pack("<BI",Command.OPEN_CPI,7))
        with self.assertRaises(PacketError):
            p.send(Type.COMMAND,struct.pack("<BI",Command.HOST_VERIFIED_INPUT,7))
        with self.assertRaises(PacketError):
            p.send(Type.COMMAND,struct.pack("<BI",Command.RUN_CPI,7))
        self.assertFalse(f.running)

    def test_false_commit_without_all_records_nacked(self):
        p=PCHost(SID_A,synthetic_iq(),7)
        p.session.state="ACTIVE"
        p.arq=ReliableEndpoint(SID_A)
        p.run_acked=True
        commit=Frame(Type.STATUS,0,active_payload(SID_A,
                     struct.pack("<BIH",Status.CPI_COMMIT,7,2)))
        out=p.receive(commit.encode())
        self.assertEqual(Frame.decode(out[0]).type,Type.NACK)
        self.assertFalse(p.committed)
        self.assertEqual(p.arq.rx_expected,0)

    def test_malformed_second_record_does_not_partially_modify_host_ledger(self):
        p=PCHost(SID_A,synthetic_iq(),7)
        p.session.state="ACTIVE"
        p.arq=ReliableEndpoint(SID_A)
        p.run_acked=True
        wrong=synthetic_records(3)
        payload=struct.pack("<I",7)+wrong[0].pack()+wrong[2].pack()
        wire=Frame(Type.RESULT,0,active_payload(SID_A,payload)).encode()
        reply=p.receive(wire)
        self.assertEqual(Frame.decode(reply[0]).type,Type.NACK)
        self.assertEqual(len(p.records),0)
        self.assertEqual(p.arq.rx_expected,0)
        fixed=struct.pack("<I",7)+wrong[0].pack()+wrong[1].pack()
        ack=p.receive(Frame(Type.RESULT,0,active_payload(SID_A,fixed)).encode())
        self.assertEqual(Frame.decode(ack[0]).type,Type.ACK)
        self.assertEqual(list(p.records),[0,1])

    def test_unsolicited_commit_before_RUN_nacked(self):
        p=PCHost(SID_A,synthetic_iq(),7)
        p.session.state="ACTIVE"
        p.arq=ReliableEndpoint(SID_A)
        commit=Frame(Type.STATUS,0,active_payload(SID_A,
                     struct.pack("<BIH",Status.CPI_COMMIT,7,0)))
        reply=p.receive(commit.encode())
        self.assertEqual(Frame.decode(reply[0]).type,Type.NACK)
        self.assertFalse(p.committed)

    def test_COMMIT_ack_lost_same_epoch_exact_retransmit(self):
        raw=synthetic_iq();p=PCHost(SID_A,raw,7);f=FPGASoftwareSimulator()
        link=SoftwareLink(p,f)
        link.transfer("PC",p.session.start())
        p.run_acked=True; f.running=True; f.cpi_id=7
        original=f.commit_frame(0)
        responses=p.receive(original)
        self.assertTrue(p.committed)
        self.assertEqual(p.commit_count,1)
        # Lose ACK, resend complete frame. Host re-ACKs, no duplicate commit.
        self.assertEqual(f.timeout_output(),original)
        self.assertEqual(p.receive(original),responses)
        self.assertEqual(p.commit_count,1)
        f.receive(responses[0])
        self.assertIsNone(f.arq.outstanding)
        self.assertEqual(f.terminal,("COMMIT",7,0))

    def test_usb_unplug_COMMIT_ACK_lost_new_epoch_query(self):
        raw=synthetic_iq();p=PCHost(SID_A,raw,23);f=FPGASoftwareSimulator()
        link=SoftwareLink(p,f)
        link.transfer("PC",p.session.start())
        p.run_acked=True;f.running=True;f.cpi_id=23
        commit=f.commit_frame(0)
        old_ack=p.receive(commit)[0]  # PC accepted COMMIT but ACK dropped
        self.assertEqual(p.commit_count,1)
        p.session=PCSession(SID_B,mode=1,prior_cpi=23)
        link.transfer("PC",p.session.start())
        self.assertEqual(p.session.state,"ACTIVE")
        self.assertEqual(f.session.snapshot,Snapshot(2,1,23,0))
        self.assertTrue(f.arq.receive(Frame.decode(old_ack)).ignored)
        link.pc_send(Type.COMMAND,struct.pack("<BI",Command.QUERY_CPI_STATUS,23))
        self.assertTrue(p.committed)
        self.assertEqual(p.commit_count,1)
        self.assertEqual(f.terminal,("COMMIT",23,0))
        self.assertEqual(f.arq.tx_next,1)  # newly sequenced status, ACKed in new epoch


if __name__=="__main__":
    unittest.main()

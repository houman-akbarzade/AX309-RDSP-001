# S05 laboratory UART ICD as-built v1.0 — design baseline candidate

Status: SOURCE-RECONCILED; final Gate sign-off pending. Applies to the full-chain FFT-IP bitstream, not the separate Stage Lab images. Authority: selected FFT-IP decision, S01/S02 amendment and fail-closed recovery decision dated 2026-11-14. Source of exact bytes: pc_link/codec.py, iq.py, board_dsp.py; rtl/uart/s05_dsp_session_arq.v, s05_dsp_reply_tx.v, uart_s05_dsp_top.v. Historical R2/R1 candidates remain archived and do not override observed implementation.

## Physical and common frame

AX309 CP2102GM USB-UART, nominal 115200 8N1, laboratory stop-and-wait, full CPI before RUN; no continuous-IQ/real-time or Ethernet claim. Frame: SOF A5 5A C3 3C, version=1, TYPE:u8, flags:u8, seq:u32LE, length:u16LE <=512, payload, CRC32/ISO-HDLC:u32LE over version through payload. Total length 17+payload. CRC, length, epoch and sequence must validate before application action.

TYPE 1 COMMAND, 2 IQ_UPLOAD, 3 STAGE_REQUEST, 4 STAGE_DATA, 5 RESULT, 6 ACK, 7 NACK, 8 STATUS, 9 SESSION_CONTROL. Bootstrap type9 uses flags=0, seq=0, HELLO/OFFER/ACTIVATE/READY with 16-byte nonzero opaque SID; active application and ACK/NACK use flags=1 and the exact SID prefix in payload. Reliable application frames have directional u32 sequence; ACK/NACK are not themselves acknowledged. The host uses nominal 2 s timeout and at most three retransmissions. New SID on fresh connection; it is an epoch discriminator, not authentication.

## CPI and data

- IQ: 33×128 complex Q1.15, pulse-major I then Q signed16 LE; 16896 bytes. IQ_UPLOAD body after SID is CPI_ID:u32LE, byte_offset:u32LE and up to 488 raw bytes (35 chunks). The host verifies complete 484-byte-chunk stage0 readback (35 requests) byte-for-byte, then sends HOST_VERIFIED_INPUT and RUN.
- COMMAND body after SID is opcode:u8 and CPI_ID:u32LE: 1 OPEN_CPI, 3 HOST_VERIFIED_INPUT, 4 RUN_CPI, 5 QUERY_CPI_STATUS, 6 RELEASE_CPI in current RTL. Codec also defines opcode2 and opcode7, but they are not implemented as full-chain RTL command paths. Stage readback is requested directly by TYPE3.
- STAGE_REQUEST body after SID: CPI_ID:u32LE, stage_id:u8, offset:u32LE, count:u16LE. Full-chain stage0 is raw IQ; stage4 is the 4096-cell stored Power map, 46-bit integer padded to six LE bytes/cell (24576 bytes, chunks up to 480). Stage1/2/3/5/6 are not readbacks of the full-chain bitstream. Separate Stage Lab configurations capture the six processing outputs under their own laboratory protocol.
- RESULT: SID16, CPI_ID:u32LE, one 13-byte little-endian 99-bit Grouping record per frame in current FPGA implementation; five high padding bits zero. Fields: record_id10, range7, natural Doppler bin5, signed bin6, peak power46, cluster cells12, tie1, equal-power cells12. The host validates exact record order/count and region; zero records is valid with a matching COMMIT.
- STATUS terminal COMMIT/ABORT includes CPI_ID and count/reason. Before COMMIT records are provisional. Host journals complete validated records/count durably before terminal ACK; RELEASE only after complete result reconciliation. FPGA backpressure prevents silent list truncation; 702 is the logical upper bound.

## Fault and recovery boundary

The approved laboratory policy is fail-closed. The present host opens a fresh session and refuses a retained-state session; its normal path does not perform automatic in-place recovery after disconnect or power loss. A provisional CPI is never accepted. A previously host-validated durable COMMIT remains a host historical result after FPGA volatile state is lost, with device outcome marked unknown. Controlled reset/reprogramming and a fresh full upload are required before a new CPI if reconciliation cannot safely finish. The unused RECOVER_UNKNOWN enum is not evidence of implemented recovery. No normal-path feature claims immutable FPGA state across power loss.

## Verification ownership and open design evidence

S05 fixes this as-built contract and the separate Stage Lab schema mapping. S07/S10 can validate RTL/PC protocol and numerical equivalence; S11 owns physical UART integrity, disconnect/reset faults and board performance. Exact generated bitstream/configuration hashes and Stage Lab image identities must accompany corresponding measurements. This document does not silently amend historical R2/R1 fault guarantees; incompatible broader automatic recovery provisions are deferred from the present laboratory scope by the approved fail-closed decision.

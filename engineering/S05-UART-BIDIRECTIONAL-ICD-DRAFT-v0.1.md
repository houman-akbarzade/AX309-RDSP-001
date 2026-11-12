# AX309-RDSP-001 | S05 Bidirectional UART Transaction ICD — DRAFT v0.1

**Status:** ENGINEER_REVIEW_REQUIRED. This is an implementation contract proposal, **not** an approved byte-level ICD or verified FPGA link. Baseline: df14f10. Date: 2026-11-12.

## A. Frozen S02 wire contract (do not revise without a decision)

- Physical concept: AX309 CP2102GM USB-to-UART, initial nominal **115200 baud, 8N1**, subject to actual-board verification. The project S01 manual extract records FPGA RXD=C11, TXD=D12 and nominal clock T8/50MHz; actual board revision, voltage/IO standard, oscillator and UCF constraints remain unverified. VGA is not a data uplink.
- Envelope: `SOF(A5 5A C3 3C)[4] | version=1[1] | TYPE[1] | flags[1] | seq_LE32[4] | payload_len_LE16[2] | payload[0..512] | CRC32_LE[4]`. Total frame length **17 + payload_len** bytes, maximum **529** bytes. CRC-32/ISO-HDLC covers exactly `version..last_payload_byte`, excluding SOF and CRC; reflected poly 0xEDB88320, initial/final XOR FFFFFFFF, ASCII "123456789" check CBF43926.
- TYPE categories already defined in S02: COMMAND, IQ_UPLOAD, STAGE_REQUEST, STAGE_DATA, RESULT, ACK, NACK, STATUS. **Numeric TYPE/flag encodings not yet approved.** CPI_START, TARGET_RECORDS, CPI_COMMIT and CPI_ABORT are transaction *semantics*, not permission to invent new TYPE numbers.
- Stop-and-wait ARQ with monotonically increasing sequence per link direction, exact-sequence ACK, idempotent duplicate ACK/retransmission, NACK for out-of-order packet with expected sequence, up to 3 retransmissions after the original send; nominal timeout 2 seconds **per frame at nominal baud**, not a verified whole-CPI timeout. A frame cannot be considered accepted merely because UART serialized it.

## B. PC -> FPGA: IQ upload and processing gate

**Approved data:** 33 pulses x 128 fast-time complex samples; pulse major `m=0..32`, `n=0..127`. Each complex sample is `I_LE_int16, Q_LE_int16` signed two's complement (normalized Q1.15, approved ties-to-even quantization and explicit clipping reporting), **16,896 raw bytes per CPI**. Host input bytes and provenance/hashes remain distinct from intermediate DSP data.

**Approved IQ_UPLOAD payload prefix:** `CPI_ID: uint32 LE | offset: uint32 LE | raw_IQ_chunk`; payload max 512 -> raw chunk max 504 bytes. With contiguous maximal chunks: **34 IQ_UPLOAD packets** (33 x 504 + 264 bytes), each protected by S02 frame CRC and direction-specific seq. Proposed sender preserves the **identical serialized packet and payload** until exact ACK or terminal failure. It shall not start a second CPI while the current one is active.

**Receiver invariants to verify in RTL:** reserve current CPI_ID, accept in-order valid sequence + version/type/length/CRC only; reject inconsistent CPI_ID, out-of-bounds offsets or nonduplicate overlap; do not write a new accepted packet twice. A byte-for-byte duplicate of the same acknowledged packet/seq may be ACKed idempotently but MUST NOT be reapplied. A truncated/incomplete frame has no accepted bytes. Because RXD/TXD are the only specified link signals and there is no proven hardware RTS/CTS, the physical UART byte stream **cannot be paused mid-frame by an FPGA ready/valid signal**. Implement sufficient byte-rate processing and either a full-frame staging buffer or an equivalent tentative-write/rollback mechanism before ACK.

**Run gate:** 16,896 bytes present, coverage exact with no gaps/overlap, valid packet CRC/seq, host complete-transfer command and a **full-CPI byte-accurate verification** (readback or specified digest) must all succeed before FPGA can assert a processing START. S02 allows readback or full CPI digest and does not require SHA-256 in FPGA; the final digest algorithm, trust model and STAGE_DATA readback schema are **OPEN**, not silently chosen. Incomplete uploads, CRC failures, exhaustion of retries or conflicting duplicates cannot authorize processing. A failed/destructively overwritten CPI requires fresh full upload before a new run.

## C. FPGA -> PC: complete grouped target records

**Current approved RTL record fields:** `{record_id[9:0], peak_range[6:0], unsigned_doppler_bin[4:0], signed_doppler_bin[5:0], peak_power[45:0], cluster_cells[11:0], peak_tie[0], equal_power_cells[11:0]}` = 99 bits. The composite record bits are `[98:89] ID, [88:82] R, [81:77] unsigned bin, [76:71] signed bin, [70:25] power, [24:13] members, [12] tie, [11:0] equal-power cells`. This is **measured existing RTL**, not a frozen UART byte packing.

**PROPOSED serialization needing approval:** send each 99-bit packed word as exactly 13 octets in **least-significant-octet-first order**, requiring the top five padding bits of the 104-bit byte representation to be zero. A RESULT payload could be `CPI_ID_LE32 + 1..39 complete 13-byte records`, with no record splitting: 39 records -> 4+507=511 bytes <=512. A packet with eight records -> 4+104=108 bytes. Actual binary byte order, flags, record schema/version and RESULT type number are **OPEN**; the project must not treat this proposal as accepted.

**Flow-control invariant:** grouping_8conn outputs only after all 2782 CUTs are consumed, holds out_valid/data until out_ready; a full FIFO can therefore stall grouping without dropping target records. The 8-slot FIFO lab prototype accepted 702/702 records with a 60,000-cycle continuous stall. This is **not** proof of UART reliability or production depth. The FIFO must never release the *last retransmission-safe copy* of a record merely upon UART transmit. Alternatives: (i) hold record(s) through ACK, or (ii) move accepted complete records into a separate retained frame replay buffer and free FIFO slots; until exact ACK the replay buffer cannot be overwritten. The 39-record batch requires replay storage for the full ~511-byte payload, independent of any 8-record FIFO. The FIFO and replay memory are separate resource items.

**Transaction framing:** `CPI_START(CPI_ID)` -> `TARGET_RECORDS(CPI_ID, ids)` -> exactly one terminal `CPI_COMMIT(CPI_ID, count)` **or** `CPI_ABORT(CPI_ID, reason)`. Map those semantics to existing or newly reserved UART TYPE/STATUS/flags only after engineer ICD approval.

Host holds provisional records by CPI_ID. **COMMIT alone is insufficient**: valid CRC, matching CPI_ID, complete distinct IDs 0..count-1, count<=702 and correct packet seq must be verified. Identical retransmissions are idempotent; missing/conflicting/extra IDs or packet gaps prevent acceptance. Link loss after last record **but before COMMIT** invalidates the CPI. Abort after provisional records makes the entire CPI invalid. Legitimate zero detections require COMMIT count=0. No interleaved records from two CPI IDs.

**Critical unresolved distributed-commit case:** if the host receives COMMIT and acknowledges it but the ACK is lost, the FPGA cannot safely issue CPI_ABORT merely because it exhausts retries; the host may already have committed. This requires idempotent retransmission and a query/reconciliation status by CPI_ID, or another engineer-approved terminal handshake. The system must not simultaneously claim COMMIT and ABORT for one CPI. A missing COMMIT at the host is invalid; an uncertain COMMIT acknowledgement at the FPGA is **not equivalent** and requires explicit reconciliation behavior.

## D. Fatal error, reset and recovery

The future Frame Controller must latch first fault and CPI_ID outside the DSP reset domain, suppress success/COMMIT on fatal internal faults, assert synchronized scanner/grouping reset independent of a stalled valid/ready handshake, and report CPI_ABORT when transport remains operational. PC discards provisional records even if ABORT is lost and COMMIT never arrives. FPGA must not reuse potentially clobbered IQ memory for a new RUN without complete new verified CPI upload. The exact reset pulse cycles, abort status codes and system watchdog are not approved; do not equate UART's S02 2-s per-frame ARQ timeout to a DSP frame watchdog.

## E. Status and required decisions for engineer review

1. **Approve or revise proposed 13-byte packing and RESULT packet schema**, including endian/padding, schema version and numeric TYPE/flags.
2. **Select an ACK-safe replay strategy**: single-record/packet held through ACK, eight-record batch with short retained buffer, or up to 39 records with retained ~511-byte payload. Freeze physical FIFO depth *only after* integrated controller resource/flow tests; the proven 702 logical capacity is independent.
3. **Freeze CPI upload full-verification method** (bytewise STAGE_DATA readback or approved digest) and the COMMAND/START, completion and failure STATUS payloads.
4. **Approve the terminal COMMIT/ACK-loss reconciliation rule**, and error/status semantics; retain S02 2-s per-frame and max-three-retry base without inventing a whole-CPI hard deadline.
5. **Approve or postpone SDRAM/shared-memory implementation decision** only after XST resource/lifetime and timing evidence. No migration of FPGA Clustering to PC or tracking addition is authorized.

**No UART protocol RTL, host serial software, board build, full Frame Controller or PHY tests have been performed in this review.** REQ-LIST-01 OPEN; full XC6SLX9 fit OPEN; Gate-S04 CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03 FAIL 4/8; Fixed-Point statistical performance OPEN.

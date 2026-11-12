# AX309-RDSP-001 | S05 CPI-by-CPI UART Architecture & Readiness Review v0.1

**Date:** 2026-11-12. **Baseline:** df14f10. **Disposition:** PRE_IMPLEMENTATION_REVIEW_COMPLETE / ICD_AND_PHYSICAL_RESOURCE_FIT_PENDING_ENGINEER. **No UART or Frame Controller RTL was changed or executed.**

## 1. What is approved and what is actually available

**System-engineer direction:** use the existing AX309 CP2102GM USB-to-UART connection, laboratory CPI-by-CPI Stop-and-Wait, with one verified CPI processed and one committed result before the next CPI. No continuous IQ stream / RF acquisition throughput requirement. Keep on FPGA: MF16, MTI, FFT32, Power, CA-CFAR, 8-connected Grouping. No tracking on FPGA; no migration of clustering to the PC; no FT2232H/FT600 or external USB-FIFO purchase; VGA is not the PC data link. Software on the PC generates known IQ, uploads one CPI, verifies receipt, requests processing, receives provisional detections and validates/displays them on final COMMIT.

**Physical board evidence:** S01-problem-definition-DRAFT-v0.2.md and v0.3.md transcribe AX309 User Manual Rev 1.0, 2019-04-26: CP2102GM, FPGA RXD C11, TXD D12, nominal 50MHz oscillator T8 and external HY57V2562GTR SDRAM (256Mbit, 16-bit). This is manual-based/supplied documentation, **not a verified board-revision pin/UCF/clock measurement**.

**Existing RTL and scope:** rtl/mf16/mf16_serial_mac.v, rtl/mti/mti2_diff.v, rtl/fft32/fft32_dit.v, rtl/power_cfar, rtl/grouping/grouping_8conn.v, rtl/integration/cfar_grouping_subsystem.v and rtl/integration/grouping_fifo8_subsystem.v. No synthesizable UART RX/TX PHY, CRC/frame parser, ACK/ARQ controller, full-CPI IQ assembler/verifier, UART packet serializer, physical pin-constrained top-level or complete Frame Controller currently exists in the reviewed RTL source tree. Stagewise module and connected-subsystem test PASSs are not end-to-end radar PASS.

**Binding source:** engineering/S02-engineering-contracts-APPROVED-AMENDMENT-v1.1.md sections C-DAT-01, C-UART-01, C-TRACE-01; S02-requirements-matrix-APPROVED-AMENDMENT-v1.1.json; decisions/S05-REQ-LIST-01-LOGICAL-POLICY-APPROVAL-2026-11-12.json. The newly recorded direction is decisions/S05-UART-CPI-BY-CPI-DIRECTION-2026-11-12.json.

## 2. PC and FPGA responsibility boundary

| Phase | PC responsibilities | FPGA responsibilities | Acceptance guard |
|---|---|---|---|
| 1. Prepare/ID | Create deterministic 33x128 complex IQ, quantize to Q1.15 I/Q LE int16, manifest + 16,896-byte raw hash, choose CPI_ID | Clear previous transaction only after terminal outcome; reserve CPI_ID | Only one CPI active |
| 2. Upload | Form S02 IQ_UPLOAD packets (CPI_ID, byte offset), keep each packet until matching ACK | Parse framed UART, enforce CRC/version/seq/offset/CPI_ID, stage 16,896 bytes | No truncated/overlapping/unacknowledged packet accepted |
| 3. Verify | Issue final upload command, compare full bytewise STAGE_DATA readback or approved full-CPI digest | Verify exact coverage 0..16895 and complete content; ACK completion only after verification | **No processing START for a partial or unverifiable CPI** |
| 4. Process | Await explicit status; do not upload next CPI | Execute mandatory MF, MTI, FFT, Power, CA-CFAR and Grouping; capture cycle diagnostics | No false success from stage-level done flags |
| 5. Provisional output | Decode RESULT frames, check CRC/seq and CPI_ID; hold target records provisional | Package 99-bit output records, preserve FIFO back-pressure and per-packet retransmission-safe copy until ACK | No Top-K, no silent record loss, no cross-CPI mixing |
| 6. Terminal | Accept only valid COMMIT with exact 0..N-1 IDs/count and integrity; otherwise discard/abort | Send CPI_COMMIT(CPI_ID,N) only after result transmission/ACK eligibility; or CPI_ABORT with fault cause | Terminal state agreed; next CPI blocked until resolved |
| 7. Recovery | Invalidate any records without COMMIT, resynchronize UART, upload a new full CPI | Latch fault and CPI_ID outside DSP reset; reset stalled pipeline, maintain host-visible error and avoid unintended restart | No stale records or ghost commit in subsequent CPI |

A physically full RX UART frame arrives **without intra-frame ready/valid pause**, because only RXD/TXD are specified. RX must process the byte cadence and protect bytes against CRC failure with staging or rollback. Stop-and-Wait limits concurrent *packets*, not instantaneous byte arrival within a packet.

## 3. Data and packet format: frozen vs proposed

**Approved:** pulse-major 33x128; 4224 complex samples, each I then Q as LE signed int16 Q1.15, 16,896 input bytes. Each S02 UART frame has SOF A5 5A C3 3C (4B), version(1), type(1), flags(1), seq_LE32(4), payload_len_LE16(2), payload(0..512), CRC32_LE(4). 17 bytes overhead. CRC-32/ISO-HDLC poly reflected 0xEDB88320, init/final FFFFFFFF, check "123456789" = CBF43926. IQ_UPLOAD payload `CPI_ID_LE32 + offset_LE32 + <=504 IQ bytes`; requires 34 packets, 33 full chunks and final 264-byte chunk. ACK sequence exact and direction-specific; duplicate retransmissions idempotent. Nominal 2-second per-frame timeout, up to three retries; byte-accurate readback or full CPI digest required before RUN.

**Existing grouping bus:** 99 bits: record_ID(10), peak_range(7), Doppler_unsigned(5), Doppler_signed(6), peak_power(46), cluster_cells(12), tie(1), equal_power_cells(12). The mathematical maximum is 702 components for the approved nonwrapped 107x26 grid; logical Option A already approved with no Top-K and no silent discard.

**Proposed, not approved:** 13 octets per 99-bit record, with explicit 5-bit padding and byte order; RESULT frame payload starting with 4-byte CPI_ID followed by complete records. Max 39 records in a 511-byte payload, or 8 in a 108-byte payload. Numeric TYPE codes, bit/byte order, serializer packet staging, full result-count COMMIT schema, ACK-loss reconciliation, status/error codes and production FIFO depth need system-engineer ICD signoff. See engineering/S05-UART-BIDIRECTIONAL-ICD-DRAFT-v0.1.md.

## 4. Reproducible timing analysis, 115200 baud 8N1

The calculations below are **analytic wire-serialization lower bounds**, not observed board throughput. ACK frames are assumed to have empty payloads (17 bytes); any actual ACK metadata, commands, retries, full verification, host scheduling and FPGA processing make completion slower. Clock=50MHz and baud=115200 remain unverified on the board.

| Sequential phase | Packet count | Data/framing bytes in forward direction | Minimal ACK bytes in return direction | Minimum line time including these ACKs |
|---|---:|---:|---:|---:|
| Upload 16,896 IQ bytes as 504-byte chunks | **34** | **17,746** | **578** | **1.590625 s** |
| Send 702 records, proposed 39-record frames | **18** | **9,504** | **306** | **0.8515625 s** |
| Send 702 records, proposed 8-record frames | **88** | **10,974** | **1,496** | **1.0824653 s** |
| Alternative 1-record packet | **702** | **23,868** | **11,934** | **3.1078125 s** |

**Upload + 39-record RESULT lower bound = 2.4421875 seconds**, or **2.6730903 seconds** for 8-record packets, **excluding the mandatory full-CPI readback/digest**; neither alone is a valid complete CPI transaction. A bytewise readback of all IQ with *hypothetical* similar 34-packet overhead adds approximately >=1.590625 seconds (actual STAGE_DATA layout is not frozen), yielding a **conditional >=4.0328125-second** upload/readback/output line floor for 39-record packets, before START/COMMIT/ACK/control/processing or retries. A properly approved short full-CPI digest could reduce the verification serial cost; no digest selection has yet been made.

An entire CPI cycle has:
`T_cycle = T_upload + T_input_verify + T_command + T_FPGA_process + T_result+ACK + T_COMMIT/ACK + T_host_validate + T_optional_retries + T_recovery_if_fault`.
**Actual CPI/s = 1/T_cycle; no complete cycle time, guaranteed maximum latency, physical throughput or real-time sampling rate has been measured.** Even a perfect fault-free communication line is much slower than one radar pulse or illustrative DSP core rate, which is acceptable for this **offline CPI-by-CPI demonstrator**.

S02 per-packet nominal timeout 2s and up to three retransmissions can produce ~8s waiting on a failed packet alone, plus transmission, but **do not imply a bounded whole-CPI time** without additional host scheduling, packet/fault count and terminal-reconciliation assumptions. One serial frame can occupy up to 529*10/115200 = 0.04592s airtime.

Machine-readable calculations and S02 source hash: engineering/S05-UART-CPI-TIMING-EVIDENCE-v0.1.json. Reproducible program: engineering/s05_uart_cpi_budget.py.

## 5. FPGA resources and physical feasibility

| Existing actual scope | LUT | FF | BRAM | DSP | I/O | Timing significance |
|---|---:|---:|---:|---:|---:|---|
| Connected CFAR-Grouping XST | **4,374 / 5,720** (76%) | **1,849** | **18/32** | **5/16** | **159/186** parallel block-port IOB | 20.259ns XST estimate, not routed 50MHz PASS |
| Grouping + FIFO8 lab XST (different top; NOT additive) | **4,016** | **1,769** | **6** | 0 | **195/186**, warning Xst:1336 | 9.990ns XST estimate, **cannot place as bare parallel board top** |
| Isolated banked IQ upload store | measured storage-only | | **9** | | | Needs controller/ports/CRC acceptance |
| Isolated banked MF frame store | measured storage-only | | **14** | | | Needs controller/ports/overlap scheduling |

A separated nominal memory allocation needs 18+9+14 = **41 BRAM >32**, before UART/packet storage. The symbolic shared IQ/MF/Power memory plan plus Grouping has an **unmeasured projection** of approximately 14+6=20 BRAM, but the existing scanner owns a separate private power map; achieving that projection requires memory-interface/controller work and new end-to-end synthesis. No approved change is implicit. A full-CPI ingress store, a frame-replay buffer up to ~529 bytes, RX staging, UART byte FIFOs, CRC32, per-direction seq logic, host command parser, CPI transaction state and shared datapath reset add real resources; **none** has XST implementation evidence at this point.

Only two serial user pins would be needed for the board RX/TX data path; **do not infer real FPGA pin fit** by replacing the diagnostic 195 parallel IOBs arithmetically. A board UCF pin mapping, final top-level port list, I/O standard/voltage, timing constraints, MAP/PAR and STA are needed. The optional AX309 HY57V2562GTR external SDRAM could relieve on-chip bulk buffer demand, but its controller, SDRAM pin/time resource cost and integrity verification require a separate engineer-approved trade; SDRAM is not selected by this review.

## 6. Required independent validation stages (nothing reported PASS without execution)

| Stage | Fresh tests / evidence | Exit condition |
|---|---|---|
| P0 — **Now: ICD review** | Freeze TYPE/flags, record packing, result batching/replay, complete IQ verification and COMMIT ACK-loss protocol, host-state guards | Engineer decision; no unapproved production parameters |
| P1 — PC reference packet codec | Golden SOF, CRC check-vector, length 0/512, wrong version, bad CRC, truncation, packet duplicate/reorder, offset gap/overlap, forged CPI_ID | Independent host packetizer/parser unit PASS; preserved byte-for-byte vectors |
| P2 — UART RX/TX + framed ARQ RTL | Real 8N1 serial waveform at selected oscillator/baud, CRC, wrong sequence/NACK, duplicate idempotence, timeout and three retries, continuous 529-byte RX without dropped bytes | ISim serial-model PASS and standalone XST measured; no board claim |
| P3 — CPI assembler/verifier + RUN gate | Full 34 packets/16,896 IQ bytes, bytewise readback or frozen digest, missing/duplicate/conflicting/out-of-order packets, CRC corruption, no RUN until verified | Independent oracle + exact input bytes PASS, controlled abort on failure |
| P4 — Grouping FIFO/RESULT packet engine | 0 and 702 records, hard FIFO full, UART-paced receipt, ACK-safe replay, count/ID checking, disconnect after last record before COMMIT, lost COMMIT ACK/reconciliation | No loss/duplicate or false success with real serialized link |
| P5 — Frame Controller abort/reset, S05 integration | Fatal Grouping overflow under back-pressure, mid-upload abort, CPI_ID preserved across reset, two consecutive CPI, no cross-CPI state leakage, no ghost COMMIT | Integrated behavioral/oracle PASS; contract recovery accepted |
| P6 — FPGA feasibility and board evidence | Shared-memory lifetime+port arbiter, complete Architecture-C RTL XST, resource fit, UCF/MAP/PAR/STA at actual clock, CP2102GM loopback, hardware end-to-end CPI/hash/intermediate readback | Separate S05 RTL, S08/09 timing and S11 board pass records; cannot infer from block XST |

**No previous S04 REQ-RNG-03 (4/8 FAIL), statistical Fixed-Point campaigns or already accepted S05 block tests are rerun by this review.**

## 7. Engineer decisions required before broad RTL work

1. Approve the proposed minimum **bidirectional UART ICD**: TYPE codes/flags; RESULT 99-bit-to-13-byte byte order and record schema; CPI_ID, sequence and STATUS/COMMIT/ABORT encodings.
2. Choose the ACK-safe **output packet strategy** (1, 8 or up to 39 complete records per frame) and how its replay image is retained; FIFO8 is only a qualified laboratory example, not frozen production depth.
3. Specify full input verification (bytewise STAGE_DATA readback vs approved full-CPI digest), and the **lost COMMIT-ACK reconciliation/terminal-state** mechanism. An FPGA that has sent COMMIT but lost the ACK cannot safely send contradictory ABORT to a host that may already have committed.
4. Determine whether the shared on-chip memory feasibility study is the next implementation baseline, or request a measured external SDRAM trade; defer any hardware substitution/architecture change until evidence supports it.

**Recommendation:** keep the approved CPI-by-CPI USB-UART and all clustering on FPGA; proceed with packet codec/serial-RTL blocks only after the ICD decisions. Prioritize reliable, reversible upload and transactional output rather than unneeded real-time throughput. Full REQ-LIST-01, full-system FPGA fit and board verification remain OPEN. Gate-S04 CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS; REQ-RNG-03 FAIL 4/8; S04-C02-RISK-PERFORMANCE OPEN.

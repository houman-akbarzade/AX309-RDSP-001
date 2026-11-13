# S05 UART as-built reconciliation — engineer review candidate (2026-11-14)

Status: source-verified design mapping; **NOT final ICD or Gate approval**. Supersedes the earlier R2/ R1 candidates only after explicit disposition. Sources: pc_link/codec.py, session.py, board_dsp.py, iq.py; rtl/uart/s05_dsp_session_arq.v, s05_dsp_reply_tx.v and uart_s05_dsp_top.v.

| Subject | As-built laboratory implementation | Prior candidate / remaining decision |
|---|---|---|
| S02 frame | SOF A5 5A C3 3C, version 1, types 1..8 plus 9, flags, u32LE seq, u16LE payload <=512, CRC32; unchanged envelope | S02 envelope preserved; active flags and type 9 require formal R1 addendum adoption |
| Epoch | SESSION_CONTROL=9, flags=0/seq=0 bootstrap HELLO/OFFER/ACTIVATE/READY; active flags=1 and SID[16] payload prefix | R1 candidate details now implemented; accept exact session semantics and single trusted-PC scope |
| ARQ | ACK/NACK types 6/7, sid16+u32 seq, no ACK-of-ACK, directional reliable seq, identical retransmission; nominal 2s/3 retries in host | Adopt as-built exception to older generic S02 sequence/abort wording with traceable reason |
| IQ | 16896 bytes, upload, exact readback stage0 and HOST_VERIFIED_INPUT before RUN | Confirm identity, byte offsets, chunk size and resynchronization against golden vectors |
| RESULT | 99-bit Grouping record serialized 13 LE bytes with zero high padding, one reliable record per RESULT in current full-chain RTL | R2 allowed up to eight; current K=1 is a valid scoped subset, if explicitly adopted |
| Power | complete 4096×46-bit stored map read via stage4, six-byte padded per cell after terminal ACK | Full-chain stage1/2/3/5/6 readbacks are not present in this bitstream; separate Stage Lab images carry that obligation |
| COMMIT | FPGA terminal count and host validation of contiguous IDs; durable host journal before terminal ACK | Ordinary success path implemented and finite simulation/board cases recorded |
| Recovery | R1 proposal includes UNKNOWN/RECOVER_UNKNOWN and retained terminal reconciliation; current full-chain host uses fresh session and rejects retained state, current RTL command decoder accepts opcodes 1,3,4,5,6 only | **Not implemented end to end** for disconnect/global reset. Decide whether S05 lab ICD may specify fail-closed stop/manual restart with discarded provisional CPI and a fresh full upload, or require the R1 automated recovery extension before Gate. Do not represent unimplemented opcode 7 as working. |

Source-specific caution: `pc_link/codec.py` defines RECOVER_UNKNOWN=7, but that enum alone is not FPGA/host implementation. The prior candidate document lists more functions than the as-built full-chain readback provides. An ICD update must distinguish the full-chain bitstream from independent Stage Lab images, and S05 design acceptance from S11 physical fault tests.

Proposed minimum S05 disposition: adopt the actual lab frame, epoch, IQ, RESULT and Power schemas as the design baseline; explicitly scope disconnect/power-reset behavior to fail-closed, no automatic resume, until an authorized recovery extension. For a preterminal/disconnected CPI, preserve host journal and prohibit claiming success. For a fully durably committed host CPI, preserve its host result while marking FPGA terminal state unknown after power loss. Never transform a partial result into PASS or silently release a still-retained FPGA transaction. The precise method to regain an idle board after a retained terminal without reset remains a design decision and must be consistent with this scope.

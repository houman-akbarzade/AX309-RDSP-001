# S05 architecture decision and closure review — 2026-11-14

The system engineer explicitly selected the implemented FFT-IP configuration as the final S05 laboratory architecture. Decision: `decisions/S05-FINAL-FFT-IP-ARCHITECTURE-2026-11-14.json`. This supersedes the DIT choice in `S05-RTL-ARCHITECTURE-v0.1.md` and the earlier prohibition on changing architecture C for this laboratory configuration. The prior C02 model and historical evidence remain versioned and unchanged.

## As-built allocation

FPGA: MF → MTI → Xilinx FFT-IP → Power → CA-CFAR → 8-connected Grouping. PC: synthetic IQ source, UART transaction, display, scoring and references. The actual adapter sign-extends 23-bit MTI samples into the IP's 25-bit input, uses `scale_sch=10'h144`, and emits 25-bit components. The tested IP is Radix-2 Lite/BRAM, convergent rounding and the declared five-stage shift schedule. Pin exact generated XCO and build manifest at final baseline; the resource/timing evidence belongs to later S08/S09, board measurement to S11.

The S03 Float model remains a functional reference. The former C02 integer model is a historical numerical reference and is not bit-true for the IP. A separate FFT-IP-corresponding bit-accurate reference is the comparison authority for the selected configuration. The committed model Pd/Pfa campaigns passed within their limited populations; their statistical review does not imply board PASS. Stage arithmetic, Power, CFAR and Grouping equivalence claims must cite the specific model version and observed boundary.

## S05 closure checks still requiring disposition

1. **UART ICD reconciliation.** The document `S05-UART-ICD-v1.0-ENGINEER-REVIEW.md` is a conditional R2 candidate, while the actual `pc_link/codec.py` has SESSION_CONTROL type 9, ACTIVE_FLAGS=1, 16-byte SID and RECOVER_UNKNOWN opcode 7. The earlier candidate's flags=0 and type/opcode tables are not the as-built active wire format. Produce an as-built ICD from codec, host and RTL with a field/sequence/session/retry/COMMIT/recovery matrix. Identify any divergence from approved S02 frame/CRC and obtain scoped disposition.
2. **Stage observability.** Raw IQ, full Power and final records are available in the full-chain capture; CFAR display is reconstructed on the host. Seven stage readbacks have separate Lab images. Decide and document whether REQ-OBS-01 permits separate configurations or requires one final image, and pin each stage's dimensions, numeric format, ordering and validity flags. Do not infer simultaneous observability.
3. **Final requirement/interface trace.** Map as-built FPGA/PC allocation, input and output schemas, 702-record lossless policy, link behavior, error/overflow and recovery to current S01/S02 mission and acceptance rows. The lab stop-and-wait UART has no continuous real-time throughput claim; W5500 remains a future option.
4. **Gate record.** The S05 architecture selection is approved, but full interface and observability acceptance and explicit S05 Gate sign-off are still open. S04 has already been closed by engineer disposition with carryovers; software model qualification belongs to S04, physical board qualification to S11.

Verification scope: document and source review only; live hardware campaign untouched. Historical S05 and downstream evidence is not silently promoted by this record.

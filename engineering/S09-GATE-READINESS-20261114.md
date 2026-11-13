# S09 Gate readiness — routed timing and constraint coverage

Date: 2026-11-14. Status: **READY FOR ENGINEER REVIEW WITH DOCUMENTED ASYNCHRONOUS-BOUNDARY DISPOSITION**.

Basis: archived full-chain ISE 14.7 PAR/TRCE in `engineering/evidence/s10/full_ip_20261112/implementation/`, selected `rtl/uart/AX309_UART_S05.ucf`, and additional TRCE `engineering/audit/S09-unconstrained-audit-20261114.twr` generated from the existing placed-and-routed NCD/PCF with `trce -v 10 -u 20 -s 2`. No new PAR or bitstream was generated.

| Criterion | Observation | Disposition |
|---|---|---|
| XC6SLX9-2FTG256C, 50 MHz/20 ns | Device matches. TS_clk50 20 ns, min period 19.402 ns; worst setup slack +0.598 ns and hold +0.306 ns; zero reported timing errors. | PASS for constrained synchronous paths |
| Routing | PAR reports all signals routed, zero errors and zero timing score. | PASS |
| No unconstrained functional clocks/critical paths | `-u` reports 4 unconstrained OFFSET IN paths (reset_n and uart_rxd), 1 OFFSET OUT path (uart_txd), and 4376 unconstrained path-analysis paths. The first 20 sampled paths in the latter class are clk50-pad-to-clock-pins via BUFG, i.e. clock distribution rather than datapath; remaining paths need full classification or justified tool accounting. | OPEN: blanket zero-unconstrained claim unsupported |
| External UART/reset timing | UCF has pin, IOSTANDARD and clock period but no external OFFSET requirements. UART RX is asynchronous and uses synchronizer; TX bit time is internal clock division. Explicit documented exception and synchronizer/timing rationale or applied I/O constraints are needed before treating these as covered. | OPEN |
| Warning disposition | PAR has 39 warnings, including 37 loadless outputs already logged at S08. No timing error inferred from their count. | Tracked, not independently blocking if unchanged |

The original TRCE's “All constraints were met” refers to the applied 20 ns clock constraint, not exhaustive coverage. S09 acceptance requires nonnegative WNS and no unconstrained intended functional clocks or critical paths. Until the asynchronous-boundary and clock-distribution classifications are explicitly reviewed, ask the engineer for no final S09 Gate approval. Physical UART performance and board acceptance belong to S11.

## Follow-up 2026-11-14

A full -u 5000 review classified all 4376 reported unconstrained-path entries as clk50 PAD to clock-pin distribution (4131 FF, 236 RAM, 9 DSP), not functional data paths. The five OFFSET I/O entries are asynchronous reset/UART boundaries with RTL synchronization/serial sampling rationale. See `engineering/audit/S09-UNCONSTRAINED-PATH-DISPOSITION-20261114.md`. This later classification supersedes the OPEN classifications above; it does not alter the archived initial finding. S09 timing evidence is ready for engineer Gate review under this explicit interpretation.

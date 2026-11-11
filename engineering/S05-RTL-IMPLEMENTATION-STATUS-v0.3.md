# AX309-RDSP-001 | S05 RTL Implementation Status v0.3

**Status:** S05 implementation in progress; independent module-level evidence only, no integrated-chain or hardware PASS.
**Reference commit:** e9e99d2; Gate-S04 unchanged CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS.

## Implemented and tested modules

| Work package | Implemented module | Observed verification |
|---|---|---|
| WP01 | RNE, MF16, MTI2 | ISim local unit PASS |
| WP02 | FFT32 DIT | ISim zero/impulse 64-bin unit PASS |
| WP03 | Power U46.30, SUM40 U52.30, strict CFAR compare | ISim unit PASS |
| WP04 | 2-D CFAR scanner | ISim unit PASS and standalone XST PASS (as previously recorded) |
| WP05 | New 8-neighbour grouping_8conn | ISim 11 synthetic cases, 887/887 C05 oracle-matched records PASS; standalone XST PASS |

The reproducible five-module unit suite passes with bash rtl/tb/run_isim.sh. It does not prove end-to-end radar equivalence.

## Grouping standalone XST observations

Target XC6SLX9-2FTG256; 0 errors, 0 warnings. Measured in synthesis: 4,034 LUT (70%); 1,727 slice registers (15%); 6 BRAM (18%); 0 DSP48A1; 170 standalone IOBs. Unconstrained XST-estimated minimum period 11.797 ns (84.766 MHz). Not post-route timing closure.

## Remaining work and acceptance

- WP06: CPI capture, frame-controller scheduling, lifetime-safe memory reuse.
- WP07: Connect scanner to grouping and run independent full-chain input/output oracle verification. NOT RUN.
- WP08: Integrated top-level XST/MAP/PAR, confirmed board UCF and STA; board testing NOT RUN.
- REQ-LIST-01: external list capacity and selection on overflow are not frozen by S02. The internal 702-component allocation bound and diagnostic fail-stop do not close this requirement.
- REQ-RES-01: standalone fit does not establish system resource feasibility. Grouping already consumes 70% LUT, while the existing CFAR scanner separately consumes 464 LUT/12 BRAM. Memory reuse and total fit need independent integrated review.
- REQ-RNG-03 FAIL 4/8 and Fixed-Point statistical performance OPEN remain S04 carryovers to final evaluation; no retests or statistical CPI campaigns executed.

**Next:** self-checking connected cfar_2d_scan to grouping_8conn simulation with new synthetic power maps, then CPI/memory controller work. No architectural or numerical baseline change approved or made.

Evidence and exact source hashes: engineering/S05-GROUPING-EVIDENCE-MANIFEST-v0.1.json; traceability: engineering/S05-GROUPING-TRACEABILITY-v0.1.json; interface mapping: engineering/S05-GROUPING-CFAR-INTEGRATION-PLAN-v0.1.md.

# AX309-RDSP-001 | Independent Engineer Sign-off — S04-C02

**Decision:** S04-C02 = **PASS — SELECTED C BOUNDED NUMERIC CONTRACT**.

**Decision ID:** S04-C02-INDEPENDENT-SIGNOFF-001  
**Authority:** explicit independent engineer audit and approval in the current user directive, not a self-issued agent approval.  
**Historic selection commit:** `fac8ec8809861fd1b3afada61d8d53a344226660`.  
**Selection decision:** `decisions/S04-C02-ENGINEER-SELECTED-C-BASELINE-DECISION-v1.0.md`.  
**Executable numeric contract:** `engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json`.  
**Unchanged open obligations:** `engineering/S04-C02-SELECTED-C-OPEN-OBLIGATIONS-v1.0.json`.

## Exact scope of acceptance

Engineer-approved and change-controlled **C**, five FFT shifts `[0,1,0,1,1]`, no re-comparison without formally authorized change request.

| Interface | Accepted format |
|---|---|
| Input IQ | signed Q16.15, C01 frozen g5 noise-only or g1 laboratory reference-like single target |
| MF coefficient and FFT Twiddle | signed Q16.15, exact frozen integer coefficient tables |
| MF output | signed Q22.15 |
| MTI output | signed Q23.15 |
| FFT stage output | signed Q25.15 |
| RD power | unsigned U46.30 |
| SUM40 | unsigned U52.30 |
| CFAR alpha | 490007/65536 |
| CFAR decision | `40*Pcut*65536 > 490007*SUM40`, equality is no-alarm |

Approved arithmetic semantics are **exact full-width intermediate signed products/complex summation and Butterfly, followed by one RNE tie-to-even per designated output, pre-narrow overflow detection and explicit saturation rather than wrapping**. MF 16-tap real product/pair/accum W32/W33/W37 F30; MTI subtract W23 F15; FFT stage 1 product/pair/butterfly W39/W40/W41 F30, stages 2–5 W41/W42/W43 F30. FFT is forward unnormalized negative-exponent radix-2 DIT, bit-reversed input, natural Doppler-bin output. Cumulative FFT divide by 8 and original source reconstructions follow the locked JSON.

This sign-off accepts the **bounded arithmetic contract, not RTL correctness, native clustering implementation, generalized input populations, Float/Fixed end-to-end numeric error-budget or statistical Pfa/Pd**. No additional input gain g or dynamic selection policy is authorized.

## Independent verification evidence and scope

The engineer explicitly declares completion of an independent audit with **39/39 PASS**. Independently retained project execution records identify these 39 checks:

| Evidence group | Count |
|---|---:|
| Selected-C numeric contract test | 10/10 |
| Deterministic integer prototype v0.5 regression | 14/14 |
| Paired deterministic review v0.6 regression | 15/15 |
| **Total** | **39/39** |

Selected-C original execution log: `engineering/S04-C02-C-SELECTION-v1.0-UNITTESTS.log`; v0.5 regression: `engineering/S04-C02-C-SELECTION-v1.0-V05-RERUN.log`; v0.6 regression: `engineering/S04-C02-C-SELECTION-v1.0-V06-RERUN.log`. All are exact locally stored evidence, with independent readback and SHA-256 reported in the sign-off manifest. Tests were deterministic and did not use S03 accepted Pfa/Pd seeds for tuning.

**Engineer decision/risk acceptance is distinct from automatic proof of all later acceptance criteria**. The selected architecture was supported by v0.5 and v0.6 deterministic evidence, but cannot be generalized to unmeasured noise, clutter, multiple targets or FPGA implementations.

## Preserved residual obligations (no implied waiver)

The file `engineering/S04-C02-SELECTED-C-OPEN-OBLIGATIONS-v1.0.json` is preserved **byte for byte** and continues to assign owners, stage, acceptance conditions and Gate dependencies. In particular:

- **REQ-SCR-01** and **REQ-RNG-03** remain **BINDING OPEN**, with C02 design ownership / C06 independent verification and historical S03 provenance unchanged. Both must be expressly disposed/closed before Gate-S04.
- Two anomalous host-cluster peak signatures and missing native fixed-integer 8-connected clustering/target records: **C05/C06**, pending precise peak/tie rule and independent qualification.
- Full ordered overflow event retention beyond the v0.5 first-24 sample details: **C03/C07**; existing event counts/hashes do not substitute for full replayable traces.
- Fixed-Point error-budget acceptance and deterministic mismatch margins: **C06**, thresholds independently preapproved before verification; no retrospective parameter tuning.
- Statistical acceptance and seed-separated replay: **C06/C07/C08** and eventual Gate-S04 engineer decision.
- Actual FPGA resource, timing, power and hardware implementation: separate explicit authorization and later hardware acceptance; no hardware claims here.
- Physical UART/FPGA ICD: separate explicit engineering approval.

**Acceptance of known risks here does not close them** and does not authorize revising selected C's formats, shifts, coefficient bits, RNE locations or accepted C01 source profiles. Any such revision requires a separate engineering-change decision.

## Result, progress and C03 handoff

**C02=PASS; 2 of 8 S04 criteria complete, S04=25%.** With 12 equal stage weights, overall completion = `(3 + 2/8)/12 * 100 = 27.083333333333332%`, reported as **27.08%**. **Gate-S04=OPEN**.

**S04-C03** is now explicitly **ENTRY AUTHORIZED / OPEN**, not PASS. Its existing criterion is “Bit-true arithmetic primitive qualification”: an **independent exact integer/rational oracle for IQ packing, coefficient encoding, complex arithmetic, RNE ties and signed negative extremes, full-width intermediate operations, saturation/overflow behavior**. The separate handoff `engineering/S04-C03-ENTRY-PACKAGE-v0.1.md` describes the minimum test package and no statistical CPI, RTL, synthesis or FPGA actions.

The engineer's user directive and this final agent reply are stored as complete append-only Replay records, anchored to the current stage event. Archival insertion timestamps are not claimed as the original engineer message time or a handwritten physical signature.

**Final sign-off status:** **PASS** within the bounded C numeric interface only; **S04-C03 OPEN**, **Gate-S04 OPEN**, **S04 25%**, **overall 27.08%**.

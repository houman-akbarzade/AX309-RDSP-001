# AX309-RDSP-001 | S04-C03 Entry Package v0.1

**ENTRY AUTHORIZED; S04-C03 OPEN / NOT QUALIFIED.** Prerequisite S04-C02 has received an independent engineer PASS for the bounded selected C arithmetic contract. This entry package is not an acceptance test execution, not an expansion of C01 input populations and not an RTL or hardware development authorization.

## Frozen inputs and authoritative source hierarchy

1. S03 frozen Float reference `s03_reference/model.py` and approved S02 source/CFAR geometry.
2. C01 engineer-approved bounded input policy: noise-only g=5 and laboratory reference-like target g=1, 33x128 complex interleaved signed Q16.15 inputs, immutable profile metadata and CPI disposition rules.
3. **Signed C02 selected baseline:** `decisions/S04-C02-INDEPENDENT-ENGINEER-SIGNOFF-v1.0.md` and exact, change-controlled `engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json`. C, 5-stage shift schedule [0,1,0,1,1], no alternative architecture selection authorized.
4. Historical integer prototype `engineering/s04_numeric/s04_c02_integer_bittrue_v05.py` and v0.6 paired deterministic evidence are **regression references**, not automatically independent oracles and not proof of C03 qualification.

## Official criterion (from engineering/S04-progress.json)

**S04-C03 — Bit-true arithmetic primitive qualification.** Acceptance evidence: “Exact independent integer/rational oracle for IQ packing, coefficient encoding, complex arithmetic, rounding ties, negative extremes and overflow.”

## Smallest reviewable C03 work package

| ID | Primitive and independent oracle | Required evidence | Disposition today |
|---|---|---|---|
| C03-P01 | Input IQ Float-to-signed-Q16.15 packing for g1/g5; rational RNE and SAT, profile and source field integrity | Source-rational expected codes, full original source amplitude reconstruction and exact positive/negative clip edges | OPEN |
| C03-P02 | Frozen signed MF16 and FFT32 coefficient table encoding and exact order, conjugation, S03 twiddle sign; hash identity | Independent direct integer/rational coefficient oracle and immutable reference table comparison | OPEN |
| C03-P03 | Four signed real products -> complex multiply, signed sums and MF 16-tap accumulator | Independent full-product W32/W33/W37 and F30 oracle; no early rounding or silent wrap | OPEN |
| C03-P04 | MTI signed subtraction and five-stage FFT butterfly full-width arithmetic | Exact arithmetic oracle W23 and FFT W39/W41, pair W40/W42, butterfly W41/W43, F30; stage shift [0,1,0,1,1] | OPEN |
| C03-P05 | Signed RNE at positive/negative half-LSB, ties-even and odd; F30-to-F15 and FFT shift=0/1; signed min/max | Independent fraction oracle, explicit failure of naive arithmetic right-shift for negative ties | OPEN |
| C03-P06 | Power unsigned squares, full intermediate U51.30, U46.30 saturation; SUM40 U52.30; exact strict CFAR comparison | Independent integer max/min/exact-equality and adjacent-boundary oracles with no wrap | OPEN |
| C03-P07 | Complete overflow and saturation event trace and replay | Exact pre-limit integer, signedness, operation site, CPI/vector/pulse/range/bin/tap, sticky counts, event-order SHA and **all** events (not just first 24); byte-perfect readback | OPEN |
| C03-P08 | Independently self-checking verification/reproducibility | Independent expected outputs, deterministic IDs, source and outcome SHA256, interpreter and command, no stochastically selected CPI and explicit failure log | OPEN |

These IDs describe **entry-planning tasks**, not newly completed progress criteria or acceptance thresholds. Keep reference models independent: test oracle code must not use the candidate's same RNE or narrowing helper as its expected result. The previous 39/39 success is C02 supporting evidence and is **not** counted toward new C03 independent qualification without an explicit C03 audit.

## Boundaries and stop conditions

- The approved selected C format, coefficient integers, rounding, shifts, narrowing and overflow behavior are fixed. Any incompatibility discovered at C03 is recorded as a discrepancy for engineer change control; it does **not** authorize new A/B/C comparison or silent numeric fixes.
- Any fail at negative RNE ties, signed extrema, pre-narrow overflow, full event retention or byte-exact reproducibility must remain an OPEN issue until independent repair and re-evaluation.
- No statistics for Pfa/Pd; no accepted S03 seed used for tuning; no CPI acceptance; no RTL, synthesis, FPGA or unapproved hardware tests.
- Binding S02 obligations **REQ-SCR-01** and **REQ-RNG-03** remain OPEN, with C02 numerical coverage owner and C06 independent qualification responsibility; C03 entry neither closes nor waives them.
- Native integer clustering, host peak mismatches, end-to-end Float/Fixed tolerances and FPGA resources remain explicitly deferred under the **unchanged** `engineering/S04-C02-SELECTED-C-OPEN-OBLIGATIONS-v1.0.json`.

## Handoff checklist and next authorized step

Next work is **C03-P01 independent oracle definition and deterministic unit vectors** under its separate review; do not mark C03 PASS until its *entire* official criterion is independently evidenced. This package authorizes C03 planning/entry and qualification of exact integer/rational primitives, not RTL/hardware or new main statistical testing.

Current official state: **C01 PASS BOUNDED; C02 PASS bounded selected C; C03 OPEN ENTRY AUTHORIZED; Gate-S04 OPEN; S04 2/8=25%; overall 27.08%.**

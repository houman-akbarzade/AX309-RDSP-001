# AX309-RDSP-001 | S04-C06 Independent Sign-off Package v1.0

**Requested disposition:** ACCEPT BOUNDED A–E EXECUTION; final C06 PASS awaits an independent reviewer signature.
**No CPI re-execution is requested or permitted by this package.**

## Frozen basis

- Criteria decision: decisions/S04-C06-CRITERIA-INDEPENDENT-DECISION-v1.0.md (A–E approved with conditions; F remains OPEN).
- Execution lock: engineering/S04-C06-REPLACEMENT-EXECUTION-LOCK-v1.0.json.
- Campaign report: engineering/S04-C06-REPLACEMENT-16CPI-FINAL-REPORT-v1.0.md.
- Aggregate: engineering/s04_numeric/c06_replacement_16cpi_qualification_v1/S04-C06-REPLACEMENT-16CPI-QUALIFICATION-AGGREGATE-v1.0.json.
- Evidence manifest: engineering/s04_numeric/c06_replacement_16cpi_qualification_v1/S04-C06-REPLACEMENT-16CPI-FINAL-EVIDENCE-MANIFEST-v1.0.json.
- Attempt ledger: engineering/s04_numeric/c06_replacement_16cpi_qualification_v1/attempt_ledger.json.
- Prior campaign ledger remains preserved at engineering/s04_numeric/c06_16cpi_qualification_v1/attempt_ledger.json.

## Reported execution outcome

| Population | g | Fixed N | PASS | FAIL | INCONCLUSIVE |
|---|---:|---:|---:|---:|---:|
| NOISE_ONLY_UNIT | 5 | 8 | 8 | 0 | 0 |
| SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 8 | 8 | 0 | 0 |
| Total | — | 16 | 16 | 0 | 0 |

A–E: PASS in the bounded execution report. The report records 112 stagewise MAX/RMS checks, 65,536 power comparisons, 44,512 CUT comparisons, 1,780,480 training-cell comparisons, zero integer-oracle mismatches, zero Float/Fixed changed CUTs, zero new peak-coordinate differences, zero runtime saturation/overflow events, and 32 trace-scope manifests read back. The two historical exact-Float-tie phase-interference vectors are separately classified under the narrow approved D exception.

This is deterministic numeric evidence for the two C01-approved populations. It is not a statistical Pfa/Pd campaign and does not qualify clutter/SCR or two-target resolution.

## Required independent reviewer actions

1. Review the exact execution lock, prelock, input manifest, code/oracle versions and per-CPI result records.
2. Independently verify fixed denominators, unique CPI IDs/seeds, one attempt per CPI and preservation of the earlier INCONCLUSIVE campaign.
3. Review all 16 input and result hashes, all 32 trace-scope manifests/readbacks and the historical D replay evidence.
4. Confirm the frozen C02 architecture C, formats, alpha, RNE, coefficients and FFT shift schedule were not changed.
5. Sign this exact evidence set, record reviewer identity, date, disposition and the reviewed manifest SHA-256.

## Current status

- C06 execution result: PASS_PENDING_INDEPENDENT_SIGNOFF for bounded A–E.
- Official C06 criterion: OPEN until the independent reviewer signs.
- REQ-SCR-01 and REQ-RNG-03: BINDING OPEN; neither is covered by this campaign.
- Gate-S04: OPEN / NO-GO.
- No change to C01–C05 or the frozen numeric baseline.

## Independent reviewer sign-off (unfilled)

- Reviewer identity and affiliation: **PENDING**
- Independence/conflict declaration: **PENDING**
- Evidence manifest SHA-256 reviewed: **PENDING REVIEWER READBACK**
- Decision (PASS bounded A–E / REJECT / REQUEST CORRECTION): **PENDING**
- Scope exclusions and open F obligations acknowledged: **PENDING**
- Signature / authenticated approval record and date: **PENDING**

Until completed by an actual independent reviewer, this section is not a signature and does not change the official C06 status.

# S04-C06 Exact 16-CPI Execution Incident Report v1.0

**Project:** AX309-RDSP-001  
**Criterion:** S04-C06  
**Disposition:** INCONCLUSIVE — one-shot execution consumed; no retry authorized  
**Architecture:** C  
**FFT shifts:** [0, 1, 0, 1, 1]

## Executive result

The repository already contained a complete one-shot attempt ledger and per-CPI execution evidence when the current execution request was inspected. All 16 prelocked CPI IDs had exactly one attempt. The attempt ledger and aggregate both record 0 PASS, 0 FAIL, and 16 INCONCLUSIVE (8/8 in each approved profile). The one-shot runner explicitly refuses to run again when its output directory is non-empty. No CPI was re-run, replaced, regenerated, or retried during this review.

## Scope and integrity

- Locked package SHA-256: `da5d758601cdd3569401be29f473895e87a1cfbdff960e6eed54186f909d8b7d`
- Input manifest SHA-256: `59365ab6aadb1e2c9203415fe5f5b48b4d3298c9d9cb31c4c649f621ecadddb1`
- Authorized wrapper: `engineering/s04_numeric/s04_c06_16cpi_authorized_runner_v1.py`
- Wrapper SHA-256: `d6f77eeeab1dd4630198058e3cb75294ed2f05726bf39da8758586967b65dc8d`
- Frozen base runner SHA-256: `351209f907bff42d4435c2c1a9243634d2c1d20d38c2fba2d5efff9a608c4a27`
- Attempt ledger SHA-256: `91655e63a84e185b8c6b947064a713f29474994661601b52318c2e99c91402ee`
- Aggregate SHA-256: `f44c7c4235d85a6c83a7e336f9251e8a3e2dcf3b30f68520177693e8c128da80`
- First execution-error record SHA-256: `48236388748152f131c092046aad1d5ae518d4f7536210f3da4d319e0307f206`

## Per-CPI disposition

| Profile | Fixed denominator | PASS | FAIL | INCONCLUSIVE |
|---|---:|---:|---:|---:|
| NOISE_ONLY_UNIT (g=5) | 8 | 0 | 0 | 8 |
| SINGLE_TARGET_REFERENCE_LIKE_LAB (g=1) | 8 | 0 | 0 | 8 |
| **Total** | **16** | **0** | **0** | **16** |

Audit of the ledger found 16 unique planned IDs, 16 ledger rows, and attempts=1 for every row. There are 16 per-CPI execution-error records and 16 trace manifests. Every trace manifest reports `COMPLETE_READBACK_VERIFIED` with zero recorded overflow events. This is evidence of a complete empty event stream, not proof that the downstream C06 acceptance checks passed.

## Root cause

All 16 CPI executions stopped at the same software exception in:

`engineering/s04_numeric/s04_c06_16cpi_authorized_runner_v1.py`, function `pow_and_cfar`, line 210.

The uncertainty expression adds arrays with incompatible dimensions:

- `epow`: full range-Doppler map, shape (128, 32)
- training/CUT-domain uncertainty terms: valid-CUT region, shape (107, 26)

Python raised:

`ValueError: operands could not be broadcast together with shapes (128,32) (107,26)`

The failing expression begins with the full-map `epow` instead of a consistently sliced valid-CUT view. The exception occurs after the per-CPI fixed-point engine, trace capture, stage evaluation, and preliminary integer power/CFAR calculations have begun. However, the function fails before returning the complete CFAR/Float-Fixed classification; consequently no complete per-CPI result JSON or full CUT detail file was committed by the runner. No acceptance conclusion can be inferred from the partial in-memory calculations.

## Controls and non-actions

- No CPI was repeated, replaced, or regenerated.
- No frozen C arithmetic, architecture, FFT schedule, alpha, criteria, or seed was changed.
- No accepted S03 seed was used.
- No statistical Pfa/Pd campaign was run.
- No RTL, synthesis, or FPGA operation was run.
- REQ-SCR-01 and REQ-RNG-03 remain OPEN.
- C06 remains OPEN; Gate-S04 remains OPEN.
- Official progress remains S04=62.5%, overall=30.2083%.

## Required next decision

The existing 16 CPI IDs are consumed under the one-attempt rule and must remain INCONCLUSIVE. A software correction may be prepared and tested only with non-acceptance diagnostic fixtures. To obtain new C06 acceptance evidence, the engineer must issue a new controlled decision defining whether a new independent 8+8 CPI set with new IDs/seeds is authorized, or whether an explicit exception to the one-attempt rule is approved. The current authorization does not permit rerunning these same 16 CPI.

No PASS or FAIL is declared for C06.

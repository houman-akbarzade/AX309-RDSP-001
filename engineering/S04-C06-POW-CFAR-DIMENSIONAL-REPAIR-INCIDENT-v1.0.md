# AX309-RDSP-001 | S04-C06 Runner Repair Incident v1.0

**Disposition:** SOFTWARE DEFECT REPAIRED; ACCEPTANCE NOT RUN  
**Criterion:** S04-C06 remains OPEN  
**Scope:** pow_and_cfar() dimensional correction and deterministic unit verification only

## 1. Incident

The C06 runner formed the CFAR uncertainty envelope by adding the full epow power-error map (128×32) to CUT-local arrays (107×26). NumPy cannot broadcast these shapes. This caused the offline Float/Fixed CFAR evaluation to stop before producing its CUT comparison records.

The C05 geometry is unchanged:
- Power and training-average maps: 128×32.
- Valid CUT range indices: 3…109 (107 rows).
- Valid CUT Doppler indices: 3…28 (26 columns).
- Fixed denominator: 107×26 = 2,782 CUTs.
- Training ring: 7×7 outer window excluding the central 3×3; exactly 40 unique cells per CUT.

## 2. Repair

Added cfar_uncertainty_terms() to the authorized C06 runner. It:
1. Requires both source maps to be finite, nonnegative 128×32 arrays.
2. Verifies the exact 40 unique offsets of the frozen C05 training ring.
3. Slices the CUT-local power-error term to epow[3:110, 3:29].
4. Accumulates each of the 40 shifted training-error maps over the matching 107×26 CUT domain.
5. Retains the approved formula and constants:
   U = Ecut + alpha_fixed * sum(Etraining,40)/40 + |alpha_fixed-alpha_float| * training_average.
6. Returns the three uncertainty contributions and their total, each with shape 107×26.

pow_and_cfar() now uses this helper. No power calculation, CFAR threshold, training geometry, cluster rule, or acceptance criterion was changed.

## 3. Independent synthetic verification

A new deterministic test uses synthetic, nonuniform 128×32 arrays and an independently written scalar loop over all 2,782 CUTs. It compares the CUT term, 40-cell training-error sum, alpha-quantization term, and total uncertainty at every CUT.

A second integration test calls the repaired pow_and_cfar() using a synthetic all-zero 128×32 IQ map. It verifies:
- 4,096 power cells;
- 2,782 CUT records and denominator;
- 40-cell training behavior through the frozen C05 implementation;
- zero power, training, alarm, and exact-margin oracle mismatches;
- correct completion of the uncertainty path and detail-file generation.

Negative tests reject wrong map dimensions, missing/duplicate training offsets, and non-C05 geometry.

## 4. Test execution

Environment: /usr/bin/python3 3.14.4; NumPy 2.3.5.

Commands (executed from repository root):

    /usr/bin/python3 -B -m unittest discover -s tests -p 'test_s04_c06_pow_cfar_uncertainty_repair_v1.py' -v
    /usr/bin/python3 -B -m unittest discover -s tests -p 'test_s04_c06_final_runner_smoke_v1.py' -v
    /usr/bin/python3 -B -m unittest discover -s tests -p 'test_s04_c06_fulltrace_capture_unit.py' -v
    /usr/bin/python3 -B -m unittest discover -s tests -p 'test_s04_c05_integer_power_cfar_grouping_v1.py' -v

Results:
- New dimensional/uncertainty repair tests: 4/4 PASS.
- Existing C06 runner smoke tests: 3/3 PASS.
- Existing Full Trace persistence tests: 7/7 PASS.
- Existing C05 power/CFAR/grouping tests: 19/19 PASS.
- Total: 33/33 PASS.

The first C05 regression run exposed stale progress assertions (the test expected the pre-C05 state of 4 completed criteria / 50%). The test was aligned with the already-recorded project state of 5 completed criteria / 62.5% S04 / 30.2083% project progress. The official progress file was not modified.

## 5. Frozen decisions and execution boundaries

Verified by regression assertions and restricted diff:
- Architecture C unchanged.
- FFT shift schedule [0,1,0,1,1] unchanged.
- ALPHA_FIXED = 490007/65536 and ALPHA_FLOAT unchanged.
- Selected C executable arithmetic contract, coefficient files, RNE, narrowing, and C04 arithmetic implementation were not modified.
- No C06 16-CPI Runner invocation, CPI generation, input regeneration, or CPI replay occurred.
- No accepted S03 seed was accessed for tuning.
- No RTL, synthesis, FPGA, or statistical Pfa/Pd test was run.

## 6. Prior 16-CPI incident preservation

The existing attempt ledger was read without modification:
- Planned IDs: 16; ledger rows: 16.
- State: INCONCLUSIVE_EXECUTION_ERROR for all 16.
- Status: INCONCLUSIVE for all 16.
- Attempts per CPI: exactly 1.
- No CPI result file exists; no retry or replacement was performed.

This repair does not change or upgrade any prior CPI disposition.

## 7. Changed files

- engineering/s04_numeric/s04_c06_16cpi_authorized_runner_v1.py — dimensional repair.
- tests/test_s04_c06_pow_cfar_uncertainty_repair_v1.py — new independent synthetic and integration tests.
- tests/test_s04_c05_integer_power_cfar_grouping_v1.py — stale project-progress regression expectations aligned to the already approved C05 state.
- engineering/S04-C06-POW-CFAR-DIMENSIONAL-REPAIR-INCIDENT-v1.0.md — this incident report.

## 8. Disposition

**The Runner dimensional defect is closed in software scope.** This is not C06 acceptance evidence and does not satisfy the remaining numeric/performance, trace-on-real-CPI, or S02 open-requirement obligations.

C06 remains **OPEN**. The prior 16 CPI remain **INCONCLUSIVE**. Any new CPI generation or acceptance execution requires separate explicit authorization.

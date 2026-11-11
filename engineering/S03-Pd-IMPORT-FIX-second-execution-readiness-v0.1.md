# AX309-RDSP-001 | Pd IMPORT-FIX — second-execution readiness v0.1

**Decision:** IMPORT-FIX GO / Pd MAIN EXECUTION NO-GO.
**Readiness finding:** GO FOR ENGINEER REVIEW OF A NEW, SEPARATE EXECUTION AUTHORIZATION, NOT AUTHORIZATION TO RUN.
**No generated or processed Pd CPI:** 0/1000. Reserved master seed 411091704 NOT used. Main-run output directory and STARTED.json absent.
**Gate-S03:** OPEN; official S03 progress 75%; overall 22.916666666666668%.

## Exact change boundary
- Entry script engineering/run_s03_pd_main_once_v1.py only: derive BASE from resolved __file__, prepend its absolute path to sys.path BEFORE importing s03_reference.
- Add explicit --preflight mode. Preflight verifies import module physical source paths, frozen model/scorer/approved S02/contract SHA-256, fixed test parameters and deterministic exact Clopper-Pearson k_min=916, then exits without executing main(), constructing SeedSequence, generating a CPI or creating the run directory.
- The original main 1000-CPI processing, frozen scenario, alpha, clusters, matching, scoring and result semantics were not changed.
- No modifications to s03_reference/model.py, s03_reference/pd_acceptance_candidate.py, S02 baseline, v0.3 execution contract or historical attempt-one evidence.

## Evidence/check table

| Check | Result | Evidence |
|---|---|---|
| Syntax compile and module import | PASS | py_compile runner and programmatic safe module import in unit test. |
| Preflight from repository root | PASS | env -u PYTHONPATH python3 -B engineering/run_s03_pd_main_once_v1.py --preflight prints PREFLIGHT PASS; exit 0. |
| Preflight from unrelated /tmp directory | PASS | env -u PYTHONPATH python3 -B /home/houman/AX309-RDSP-001/engineering/run_s03_pd_main_once_v1.py --preflight prints PREFLIGHT PASS; exit 0. |
| Repository import origin | PASS | Assertions check module __file__ equals frozen model/scorer file paths inside this repository. Root directory is put first on import path. |
| SHA-256 source and contract lock | PASS | Frozen model, scorer, S02 approved matrix, execution contract match v0.3 checksums. New runner SHA recorded below. |
| Prohibit main, RNG and CPI in preflight | PASS | Mocked main(), np.random.SeedSequence, m.generate_cpi and Path.mkdir all asserted not called in deterministic test. No SeedSequence from reserved master constructed. |
| No output, STARTED.json, or CPI | PASS | Directory and marker absent before and after both preflights and full test suite. |
| Existing and new regression tests | PASS | 78/78 unittest tests, log retained. Three new guarded startup tests; no stochastic target CPI. |
| Historical first attempt preserved | PASS | INCONCLUSIVE files retained byte-for-byte, hashes below; no rewriting, no retry. |
| Main Pd execution | NO-GO | No authorization for retry/execution; this change only permits import repair and preflight. |

## Note on intermediate test feedback
The very first added safety test attempted to mock a bound PosixPath.mkdir object, which is immutable; that one test initially ERRORed. The test itself was corrected to patch the Path class (without changing runner logic), then all 78 tests PASS. No main invocation or seeded sample occurred during the failing test.

## Statistical/engineering boundary
The contractual D criterion stays >=916/1000 independent complete valid CPI, exact one-sided 95% Clopper-Pearson lower >=0.90. J is fully reported without adding a 90% guard. R/V/E are separate. All source locks and historical Pfa PASS remain unchanged. No Pd PASS/FAIL is inferred.

## Hashes (SHA-256)
- engineering/run_s03_pd_main_once_v1.py: 244cfe64ac06f41b067841d185d74d45e5f341f7a03fcc1d3aaa87eb1e550c3d
- tests/test_s03_pd_runner_import_preflight.py: ccbd1b73f3a98e0fcd88289cad2448ecdca934ca80185dfade3d26a60101c554
- engineering/S03-Pd-IMPORT-FIX-full-regression-v0.1.log: f08f7b51b4d562859597c5ce700b24881f824c8be0411159ac231e39cc8d3e8e
- s03_reference/model.py: 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b
- s03_reference/pd_acceptance_candidate.py: aa0661b52aa56a1da3b3b41332f0927eba58f4fcddace12a391c2488404784ea
- engineering/S03-Pd-independent-fixed-execution-contract-v0.3.json: 602e4fe6132c4d8521b33c61a1c2cd413c3e75cc4325fe8b9bca6dea966bed5f
- engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json: 23f07e63950c8bd4f3b04a805c37a46792b0068ae918b25d0713dd65a15c51a0
- engineering/S03-Pd-MAIN-FIRST-ATTEMPT-INCONCLUSIVE-v1/RESULT.json: 217f6f4bb936f3c01635681075ed972c1ee273bd810b8d2034907db15b6b13ae
- engineering/S03-Pd-MAIN-FIRST-ATTEMPT-INCONCLUSIVE-v1/REPORT.md: fca15081213c24bae5fc6c566021becccee49a9cb14805eaefde26e2d548427a
- engineering/S03-Pd-MAIN-FIRST-ATTEMPT-INCONCLUSIVE-v1/ERROR-TRANSCRIPT.txt: db20c857b8041a1c8c7f8710807fb5ca20582a1519ed009b700a385848c44234

Pre-import-fix HEAD: dfa2b68543ab1f25b829fc27351ed4edff4f9f42. Recorded UTC: 2026-11-11T08:16:38.553638+00:00.

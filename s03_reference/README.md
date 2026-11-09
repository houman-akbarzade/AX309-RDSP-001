# S03 floating-point functional reference
S02 baseline: decisions/GATE-S02-approved-baseline.json (immutable hash-pinned).
Requires Python 3.x, NumPy and SciPy. Version used for actual run is recorded in engineering/S03-execution-manifest-v0.1.json and in statistical JSON evidence.
Run all units from repo root:
    PYTHONPATH=. python3 -m unittest discover -s tests -v
Run deterministic six-case initial reference:
    PYTHONPATH=. python3 -m s03_reference.run_scenarios engineering
Run independent pre-registered count-model C04 qualification:
    PYTHONPATH=. python3 -m s03_reference.cfar_qualification engineering
Run separate exploratory 128-CPI spatial diagnostics:
    PYTHONPATH=. python3 -m s03_reference.spatial_diagnostic engineering
Do not run CA-CFAR final Pfa acceptance while C04 qualification is FAILED. Do not relabel alpha0 as calibrated. Test inputs/PRNG seeds are documented by each artifact. The PCG64 implementation/version is frozen by execution manifest.
The clustering is a deterministic 8-neighbor candidate baseline in software; module partitioning in RTL remains S05. Truth scoring exhaustive small-truth matcher is not intended for arbitrary thousands of targets.
No bittrue internal arithmetic, UART data transfer or real FPGA execution is included in S03.

## Cycle 3 independent research (NOT official C04 qualification)
The following scripts perform formula audit / separate development-only model experiments:
    PYTHONPATH=. python3 -m s03_reference.skew_formula_audit engineering
    PYTHONPATH=. python3 -m s03_reference.independent_ci_development engineering
    PYTHONPATH=. python3 -m s03_reference.second_order_edgeworth_development engineering
    PYTHONPATH=. python3 -m s03_reference.bootstrap_t_independent_development engineering
    PYTHONPATH=. python3 -m s03_reference.empirical_likelihood_development engineering
    PYTHONPATH=. python3 -m s03_reference.larger_cpi_development engineering
    PYTHONPATH=. python3 -m s03_reference.ablation_extra_clusters engineering
The s03_reference.calibrated_critical_candidate module is an UNAPPROVED algebraic interface only. It has not generated any CI calibration dataset or formal qualification. All results from official 7/15 failure, previous pilots, and these development studies must remain disjoint from any prospective v1.1 CI calibration, qualification, source-realistic spatial verification, CFAR alpha calibration, or main Pfa validation. See engineering/S03-C04-final-engineering-decision-cycle3-v0.3.md and draft S02-v1.1-C04-calibrated-Studentized-PROPOSED-ONLY.md.

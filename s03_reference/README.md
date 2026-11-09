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

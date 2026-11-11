# AX309-RDSP-001 | S03 Independent Pd MAIN — second authorized execution

## Outcome: PASS — Python floating-point reference only

Authorized SECOND main invocation after successful zero-sample preflight; first attempt remains INCONCLUSIVE unchanged. Pre-run frozen Git commit: 711fc04fa55070c6b51ccf74927607d00fdb1962.

- Main executed exactly once; 1000/1000 complete valid CPI, invalid=0.
- Source master seed 411091704 and per-CPI SeedSequence([411091704,i,191]), i=0..999. No retuning, repeat, optional stopping or sample supplementation.
- Environment: Python version in STARTED.json, NumPy and SciPy pinned by the start manifest; model/scorer/runner/contract source hashes in RESULT.json.
- Primary detection D=1000 successes, 0 failures; acceptance k_D >=916 and one-sided 95% exact CP lower >=0.90.
- Calculated exact L_CP(D) = Beta.ppf(0.05,1000,1) = 0.9970087504549047. **PASS.**

## Independent secondary metrics

| Metric | Observed |
|---|---:|
| D | 1000 |
| R | 1000 |
| V | 1000 |
| E | 1000 |
| J | 1000 |
| Invalid CPI | 0 |
| Unmatched extra clusters, summed | 4135 |
| Total CA-CFAR alarm cells, summed | 15617 |

- Matched range error: zero samples for all 1000 CPI.
- Matched Doppler error: zero m/s for all 1000 CPI.
- Extra unmatched clusters per CPI histogram:
2: 103, 3: 280, 4: 265, 5: 189, 6: 90, 7: 47, 8: 21, 9: 3, 10: 2.

- J is reported separately with NO new binding J>=0.90 population acceptance rule.

## Independent verification and provenance

- Post-execution validation read all 1000 JSONL rows: consecutive unique trial indices 0..999, matching per-CPI seed index, valid status, D/R/V/E/J and score flags, correct CFAR threshold, matched full 32-Doppler-bin row, additional cluster counts and aggregate statistics.
- Raw per-CPI JSONL contains cluster records, CFAR powers, threshold and counts, matching scores, matched 32-bin Doppler power and input-IQ/full-power-array SHA256 fingerprints.
- **Limitation:** full per-CPI 33x128 IQ arrays and 128x32 power maps were not stored as raw arrays. They can be reproduced using source/seed/environment and checked against hashes, but this has not been executed as a second simulation.
- No proof is claimed of physical statistical independence or general radar Pd across different geometry, clutter, SNR, off-bin Doppler, fixed-point RTL or hardware.
- First attempt import error remains INCONCLUSIVE and historically preserved; second invocation is its own authorized experiment.

## Engineering control

Gate-S03 OPEN. Official S03 6/8=75%, overall 22.916666666666668% unchanged. This test does not approve Gate-S03 or S04; independent engineer decision remains required.

## SHA-256 provenance
- engineering/run_s03_pd_main_once_v1.py: 244cfe64ac06f41b067841d185d74d45e5f341f7a03fcc1d3aaa87eb1e550c3d
- s03_reference/model.py: 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b
- s03_reference/pd_acceptance_candidate.py: aa0661b52aa56a1da3b3b41332f0927eba58f4fcddace12a391c2488404784ea
- engineering/S03-Pd-independent-fixed-execution-contract-v0.3.json: 602e4fe6132c4d8521b33c61a1c2cd413c3e75cc4325fe8b9bca6dea966bed5f
- engineering/S03-Pd-MAIN-1000CPI-v1/STARTED.json: 1253672d24dc84cc14d9f8f8c1a79bc9a9c971b8c9aa4749ab7c0889cb89d23f
- engineering/S03-Pd-MAIN-1000CPI-v1/RAW-CPI-records.jsonl: a676ee7f23065e9a72ce14121172805d80cc9a9358b79e9c960809433b70ae55
- engineering/S03-Pd-MAIN-1000CPI-v1/RESULT.json: ee0caae031c1e3dd96264232f07d7a57db4745f2482ec72357df2ba85cbbb510

Recorded UTC: 2026-11-11T08:21:50.915700+00:00

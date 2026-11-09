# AX309-RDSP-001 — Gate-S02 FINAL PROPOSED Review v0.9

**Status: READY FOR ENGINEER REVIEW, NOT APPROVED. Gate-S02 OPEN; S03 NOT STARTED.**

## Proposed statistical fix
A true-95%-coverage CI should not have only 5% chance of qualification. The qualification now deliberately separates target conditional coverage 95% from acceptable minimum 93%. It also separately audits fraction of studies with no valid CI. Exactly 3000 outer studies per each of 15 fixed conditions; 4096 independent CPI counts per outer study; no original 10000-bootstrap inner loop. Pass per condition iff Wilson one-sided 95% lower conditional coverage >=93%, lower valid-and-covered unconditional >=90%, upper inconclusive <=5%. Study qualification failure blocks Pfa test. This is NOT proof of nominal 95% coverage in all real CFAR conditions.

## Exact-binomial prospective operating characteristics
All figures below are mathematical tail probabilities under the simplified assumption of independent outer studies with true conditional valid-interval coverage c and true inconclusive rate q, NOT executed trials.
| True inconclusive q | True conditional coverage c | P(pass all 3 tests in one condition) |
|---:|---:|---:|
| 0% | 90% | 0.000000 |
| 0% | 93% | 0.051825 |
| 0% | 95% | 0.998821 |
| 0% | 97% | 1.000000 |
| 2% | 90% | 0.000000 |
| 2% | 93% | 0.048055 |
| 2% | 95% | 0.998428 |
| 2% | 97% | 1.000000 |
| 3% | 90% | 0.000000 |
| 3% | 93% | 0.036529 |
| 3% | 95% | 0.992449 |
| 3% | 97% | 0.999978 |
| 5% | 90% | 0.000000 |
| 5% | 93% | 0.000003 |
| 5% | 95% | 0.029214 |
| 5% | 97% | 0.048846 |

Under independent condition-level trials at true c=95%,q=2%, all 15 conditions PASS with approximate probability (0.9984285)^15=0.97668. This independence assumption is a power-planning simplification, NOT a familywise coverage guarantee. At c=93%, q=2% each single condition passes with probability about 0.04805, limiting false qualification of a method at the minimum coverage floor. At q=5%, c=95%, per-condition pass probability is approximately 0.02921, demonstrating that inconclusive-rate criterion is effective. At q=2% and c=90%, pass probability is practically zero.
Both conditional and unconditional coverage reports are required; all INCONCLUSIVE studies contribute to the denominator of unconditional valid-and-cover but NOT its success numerator. No coverage interval is issued for these studies.

## Resource and Gate
Measured laptop: Intel i5-1235U, 15GiB RAM and ~9.2GiB available at inspection; proposed coverage qualification requires 184.32 million CPI-count draws versus 614.4 billion nested-bootstrap index draws. This is a sample-count comparison, not measured wall-clock speed. S03 owns method qualification and actual radar-chain spatial correlation assessment, not S02. Failure triggers pre-approved revision and may not be resolved posthoc on validation results.

Official S02 criteria: C01,C02,C03,C05,C06,C07 completed at SPECIFICATION level by existing engineer approvals and contracts; C04 statistical protocol remains to be approved; C08 explicit final Gate approval remains open. S02 6/8=75%; project (1+0.75)/12=14.583333%. No independent engineering question needed now except review disposition on this correction. No S03 simulation, RTL, hardware test or FPGA demonstration performed.

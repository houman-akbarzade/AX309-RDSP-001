# AX309-RDSP-001 — S02 Gate Readiness FINAL PROPOSED v0.8

Status: **Gate-S02 OPEN**. No S03 model execution, statistical coverage simulation, ISE synthesis, FPGA processing or board tests.
S01 baseline remains approved. v0.6/v0.7 preserved. Engineering requirements matrix v0.8 and contracts v0.8 are proposed for review.

## Cost feasibility
Original v0.7 nested percentile bootstrap: 15000 independent outer studies, 150 million resample means, 614.4 billion CPI index draws and potentially 170.926 billion generated CUT indicators. A single 4096x10000 uint32 bootstrap index array occupies 156.25 MiB; all such arrays total 2.4576TB of generated index traffic. Streaming is memory-feasible on observed 15GiB project laptop but computation-heavy. Actual wall-clock time has NOT been benchmarked.

## Proposed alternative and honest validity
Candidate CPI-cluster Student-t upper interval: X_i=F_i/2782; one-sided 95% upper p_hat+t_0.95,4095*s/sqrt(4096). All CUP dependencies within each CPI absorbed into CPI variance, assuming independence between 4096 CPIs. No theoretical exact finite-sample 95% coverage when counts are heavily zero-inflated/skewed. Report positive CPI count and total alarms; require at least 100 of both and nonzero variance, else INCONCLUSIVE. Apply upper limit <=0.0015 ONLY if preregistered coverage qualification passes.
Qualification: 5 independent/beta-binomial count models, p at 0.0005,0.001,0.0015, 1000 independent outer trials/condition. Count-level O(61.44m draws), O(4096) memory. For each condition coverage Wilson one-sided 95% LOWER>=0.95 and inconclusive-rate Wilson one-sided 95% UPPER<=0.05. All conditions pass; no early stopping or after-results method swap. Spatially realistic S03 correlation diagnostics are separately required. If the candidate fails qualification or actual assumptions, block Pfa verdict and request prior engineer approval of changed protocol. This is not an assertion of unconditional validity.

## C06: specification-level completion evidence
Binding constraint: do not exceed actual XC6SLX9 device capabilities including 16 DSP, 576Kbit nominal BRAM and device-specific LUT/FF limits, while meeting place-route STA constraints for all defined/generated clocks, 50MHz nominal oscillator (20ns). S05 owns memory lifetime, port banking, optional SDRAM tradeoff, resource margins for each category, timing plan, RTL organization and cycle-counter design. S08 owns ISE utilization and capacity reports. S09 owns constrained place-route, STA/WNS>=0 and zero unconstrained intended paths. S11 owns board timing, frequency, FPGA processing cycles vs UART transfer time. No uniform 90 percent utilization cap and no real-time latency deadline. C06 is deemed complete **in the specifications sense only**, not proof of resource fit.

## Eight stage criteria
| ID | Completed? | Justification |
|---|---|---|
| S02-C01 | YES | Engineer approved input/data specification in v0.6 |
| S02-C02 | YES | Engineer approved signal/MF specification in v0.6 |
| S02-C03 | YES | Engineer explicitly approved v0.7 deterministic Doppler tie and half-bin qualification separation |
| S02-C04 | OPEN | OPEN: practical alternative confidence interval validity and formal acceptance protocol pending engineer approval; no coverage experiment run |
| S02-C05 | YES | Engineer explicitly approved v0.7 structured separation of assignment gate and estimator acceptance |
| S02-C06 | YES | Approved binding capacity/STA/cycle measurement policy and documented S05, S08, S09, S11 verification responsibilities; no actual resource claim |
| S02-C07 | YES | Engineer approved UART/reproducibility specification in v0.6 |
| S02-C08 | OPEN | OPEN: engineer explicit final Gate approval not provided |

**S02: 6/8=75%**, **project: (1+0.75)/12=14.5833%**. Only C04 methodology review/acceptance and C08 final Gate approval remain open. The revised statistical method is a **proposal**, not accepted or tested. Engineer's decision is required to adopt v0.8 and authorize eventual Gate passage; no automatic approval follows.

References informing statistical limitations: MacKinnon, Nielsen & Webb, Journal of Econometrics 232 (2023), DOI 10.1016/j.jeconom.2022.04.001; statistical CI behavior in skewed rare-event distributions must be qualified, not presumed.

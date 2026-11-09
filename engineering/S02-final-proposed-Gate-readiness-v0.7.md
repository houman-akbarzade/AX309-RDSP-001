# AX309-RDSP-001 | S02 FINAL PROPOSED GATE REVIEW v0.7

**Gate-S02 OPEN; not a signed baseline; no S03 execution.**

Sources: reviewed v0.6 engineering contracts and engineer's explicit request for three corrections. Contracts v0.7 and full 22-row structured JSON matrix v0.7 are source of truth. Prior v0.6 retained.

## Three corrected controls

- Statistical method qualification has 15 predeclared dependency/probability conditions, 1000 repeated experiments per condition, full CPI bootstrap; independently computed lower Wilson confidence bound must be >=0.95 for **every** condition, not merely observed coverage 95%. Failing or invalid qualification blocks Pfa claim.
- Deterministic peak-index output/tie and no-peak status are binding for all input patterns. Eligibility for half-bin error is a separate conditional test rule; excluded attempts remain visible.
- Truth matching gate (2 range samples / 1 Doppler bin) is not a parameter-estimation accuracy tolerance (clean range zero bin, noisy 20dB +/-1 bin is goal, conditional velocity half bin).

## Preserved agreements and risks

CA-CFAR geometric valid CUT count remains 2782 per CPI (107 x 26), 40 training cells. The 4096-CPI final noise-only Pfa validation uses the same bootstrap CI and 1.5e-3 upper bound, only after qualifying its statistical coverage. Number of study repetitions is computationally expensive; a failure to qualify percentile bootstrap is a BLOCKER to any Pfa PASS, not grounds for choosing a different CI after viewing evidence. Gaussian-copula and beta-binomial are stress models rather than exact CA-CFAR physical truth; qualification success does not prove coverage for arbitrary real clutter.

## S02 acceptance bookkeeping

| Criterion | Current status | Basis |
|---|---|---|
| S02-C01 | completed | Input data generation and measurable I/O definition approved by engineer for v0.6; no executable result required for this specification criterion |
| S02-C02 | completed | Engineer approves signal contract; MF reference indexing/valid-domain policy specified for S03 verification |
| S02-C03 | open | Doppler tie/eligibility revision v0.7 not yet engineer accepted and MTI quantitative test oracle remains architectural |
| S02-C04 | open | Corrected coverage qualification protocol v0.7 not yet engineer reviewed/accepted; future study not run |
| S02-C05 | open | Separate association and estimator-error JSON clauses newly corrected, not yet engineer accepted |
| S02-C06 | open | Per-class resource margins are S05, complete resource/timing budget review not engineer approved |
| S02-C07 | completed | Engineer accepted UART/data repeatability contract from v0.6; no test claimed |
| S02-C08 | open | Explicit integrated baseline and Gate approval withheld |

**3/8 officially completed specification criteria based on explicit approval of prior v0.6 areas, 5 still open, including Gate.** S02 stage progress 37.5%; project 1/12 + (3/8)/12 = 11.458333%. This is specification/approval progress only, not engineering implementation. Stage S02 and Gate-S02 remain OPEN. The newly revised v0.7 content cannot close C03-C05 without engineer approval.

## Deferred with owner

S03: qualify coverage and apply fixed Pfa experiment, measure target Pd and performance, verify MF/Doppler functional equations. S04: fixed-point and bit-true formatting/rounding. S05: peak sentinel encoding, list capacity, resource classes/BRAM bank-port design/SDRAM choice, RTL partition. S08/S09: synthesis and STA; S11: board and UART measurements. No independent engineer decision required now; review v0.7 and decide separately on the S02 Gate.

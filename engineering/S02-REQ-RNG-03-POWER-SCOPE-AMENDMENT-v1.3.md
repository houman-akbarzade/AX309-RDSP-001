# S02 Limited Amendment v1.3 — REQ-RNG-03 Power-Output Scope

Status: ENGINEER_APPROVED_SCOPE_CHANGE / ACCEPTANCE_DEFINITION_PENDING  
Decision: REQ-RNG-03-POWER-SCOPE-AMENDMENT-001  
Engineer source: AX309-20261113-RNG03-POWER-SCOPE-engineer

## Approved limited change

REQ-RNG-03 range separability shall be assessed only at the output of the Power stage, before CFAR and Grouping. Two separate CFAR regions or two final target/cluster records are not acceptance conditions of REQ-RNG-03.

This is an explicit engineer-directed requirement-scope amendment. It supplements the approved S02 v1.0 requirements, existing limited v1.1/v1.2 amendments and subsequent S04 RNG03 protocol. It does not alter other requirement rows or replace historical signed artifacts.

## Current requirement wording

The project shall demonstrate the declared two-target range-separability behavior in the relevant range–Doppler Power output, under the approved paired-target input conditions. The operational Power-domain definition of “resolved”, numerical tolerances and any minimum valley/prominence criterion shall be identified explicitly in the acceptance contract.

The measurement point is approved. A new local-maxima or 3 dB acceptance threshold is not approved by this amendment.

## Retained conditions and boundaries

No waveform, bandwidth, sample rate, Q-format, FFT configuration, CFAR alpha/geometry, grouping algorithm, UART or hardware interface is changed.

For the existing historical eight-case corpus, the previously approved input conditions remain the basis for review unless separately amended: equal amplitudes 0.18, common Doppler +4, g=1, no noise/clutter, separations 4 and 5 samples, four relative phases 0/90/180/270 degrees, with the historical +/-1-sample range allowance. The four 3-sample cases remain characterization only. This clause retains existing input conditions; it does not approve a new separability predicate.

The archived four-of-eight result remains FAIL under the former final-record criterion. It is not rewritten or treated as an implementation failure of a revised Power requirement. Current revised-requirement acceptance is OPEN pending criterion approval and scoped evidence disposition.

Other CFAR, grouping, target-record, estimator, no-silent-drop, statistical Pd/Pfa and capacity requirements remain separate. This decision does not declare them PASS or delete their applicable target-count/performance obligations.

## Proposed acceptance clarification — not yet approved

Candidate A: for each of the existing eight noise-free paired-target cases, the Power range profile at the common Doppler bin contains two distinct strict local maxima, one within +/-1 sample of each known target range, with at least one intervening sample strictly below both maxima. No additional minimum valley depth in dB. This describes finite noise-free Power peak separability only.

Candidate B: the same definition plus an independently selected minimum valley depth, such as 3 dB if the engineer chooses that quality convention. Three dB is an illustrative alternative, not a default or a historical approved threshold.

The two candidates yield different results on retained data. Neither may be represented as a prospective pre-registered acceptance trial: this proposal is made after observing the archived corpus. Any broader noise/population qualification requires its own declared conditions and appropriately independent data.

## Proposal for affected decisions

Replace truth-to-cluster success references for REQ-RNG-03 with Power-domain peak separability in new versioned overlays. Preserve C05 arithmetic/grouping acceptance and C06 bounded A–E results. Supplement C06-F, C07 and the S04 carryover view to point to this amendment; do not rewrite their historical content or reopen/close a Gate automatically.

The earlier multi-peak Grouping change proposal is no longer required merely to satisfy revised REQ-RNG-03. It remains an optional unapproved enhancement if separately needed by another target-extraction requirement.

No new model run, engineering test, FPGA programming, algorithm modification, Gate approval, merge or publication is authorized by this scope amendment.

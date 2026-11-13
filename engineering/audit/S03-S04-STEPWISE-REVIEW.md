# S03–S04 Stepwise Review

Review scope: existing S03 approval and the two explicit S04 carryovers. No subsequent stage is accepted by this review. No new engineering test, CPI processing, model/RTL run, statistical campaign or hardware programming was performed.

## Review policy requested by engineer

For each stage, identify the applicable requirement/criterion and configuration, inspect previously executed evidence first, and record a supported scoped result with source identity. Distinguish tested-and-failed from not-qualified. If required evidence is absent, define the bounded check and any required authorization before engineering execution. Do not reopen an accepted study merely to manufacture another PASS.

## S03 confirmation

decisions/GATE-S03-approved-baseline.json records APPROVED_S03_COMPLETE_S04_ENTRY_AUTHORIZED. All seven pinned artifact hashes in that approval match the current archived bytes. The review therefore confirms the existing approval within its actual scope: S03 floating functional reference and separately approved software statistical populations.

This is not a new Gate decision and does not expand S03 to fixed arithmetic, hardware, arbitrary clutter/off-grid scenarios or every final system requirement. Its known raw-array retention limitations remain. S03 is not reopened in this stepwise review.

## S04 disposition

The engineer's decisions/S04-C08-S05-TRANSITION-2026-11-12.json closed S04 with two carryovers. REQ-SCR-01 was separately accepted in its eleven-case scope and is not a third unresolved S04 carryover.

| Carryover | Has it been tested? | Existing outcome | Current review result |
|---|---|---|---|
| REQ-RNG-03 | Yes: twelve cases, eight mandatory | Four of eight mandatory PASS; required eight of eight | CRITERION_NOT_MET; historical FAIL retained |
| S04-C02-RISK-PERFORMANCE | No accepted qualifying Fixed-Point statistical campaign found | Statistical qualification incomplete | EVIDENCE_INCOMPLETE; OPEN retained |

Old nested result wording describing a Gate blocker is historical. The later explicit carryover decision removed it as an S05-entry blocker without changing its technical result. This review neither reopens Gate-S04 nor closes either carryover.

## 1. REQ-RNG-03: separating two nearby targets

The approved experiment uses equal target amplitudes 0.18, common Doppler bin +4, gain g=1, no noise and no clutter. Separations 4 and 5 samples with phases 0/90/180/270 degrees are mandatory; 3-sample cases are characterization only. The requirement is two separately matched targets in all eight mandatory cases, with the approved range-error allowance and numeric/oracle controls.

| Relative phase | 4 samples = 599.584916 m | 5 samples = 749.481145 m |
|---|---|---|
| 0 degrees | FAIL | FAIL |
| 90 degrees | FAIL | PASS |
| 180 degrees | PASS | PASS |
| 270 degrees | FAIL | PASS |

The Float and historical selected-C Fixed results have the same pass/fail split. This does not mean all their numerical outputs are identical. The result cannot be explained solely as Fixed-Point quantization damaging an otherwise passing Float requirement.

### Read-only localization using archived masks

S04-RNG03-ARCHIVED-MASK-DIAGNOSTIC.json reads the existing Float/Fixed CFAR masks and inspects nonwrapped eight-connected components. No input, threshold or algorithm was changed. The diagnostic uses range +/-1 around each known delay and Doppler bins 3..5 around the common bin +4; this window is an observation aid, not a new acceptance rule.

In all four failed mandatory cases, detections near both targets belong to the same connected component in both Float and Fixed masks. In all four passed cases, the target neighborhoods belong to separate components. Under the specified one-record-per-connected-group behavior, a connected pair is not reported as two independent targets.

This localizes the observed failure to unresolved/connected detection regions under the existing chain and grouping rule. It does not prove a software/RTL defect or quantify the causal contribution of waveform phase, MF response, CFAR geometry or grouping design. Exact agreement with an integer oracle can coexist with failure of a radar separability requirement.

### Later evidence

Later Lab development tests use a different local-maxima/3 dB valley criterion. They report not resolved at 599.584916 m and resolved at 1199.169832 m. They are not an approved replacement of the original eight-case protocol and do not establish its PASS. The later full-IP report also retains the close-target limitation.

Current status remains the existing tested FAIL, carried to final evaluation. A decision about accepting a laboratory limitation, changing the requirement through change control, or authorizing separate design work belongs to the engineer. No criterion is softened here.

## 2. Fixed-Point statistical performance

Existing successful numerical tests do not supply the missing statistical qualification:

- S03 accepted Pfa/Pd applies to the floating reference and prescribed populations.
- C06R2 sixteen-CPI PASS is bounded deterministic numeric evidence.
- Later Lab statistics use three noise CPI and three target CPI, software-Float Power injected into hardware CFAR, and actual CFAR masks into Grouping. They exercise that measurement mechanism, not the complete raw-IQ fixed/IP-chain population.
- Ninety-four stored-case comparisons and low FFT RMSE are finite numerical evidence, not an accepted statistical Pd/Pfa campaign.

No later accepted Fixed-Point qualification or explicit waiver was found in the reviewed decision/report sources. The existing source contract requires an appropriately declared configuration/population, criteria, independent seeds, fixed denominator and stopping rule. Before any future qualification, identify whether its numerical baseline is historical C02 or the later FFT-IP as-built model. Then approve a bounded protocol and execution scope. No reserved statistical data is regenerated by this review.

## History and evidence

S03-S04-STEPWISE-REVIEW.json pins the decisions, result, later evidence and independently checked eight-case summary. S04-RNG03-ARCHIVED-MASK-DIAGNOSTIC.json pins the source NPZ archives and diagnostic observations. Original evidence and approval records are unchanged.

Review result: existing S03 scoped approval confirmed; S04 remains closed by owner disposition with both technical carryovers retained. The next conversation can address REQ-RNG-03 first without advancing to unrelated stages.

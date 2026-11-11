# AX309-RDSP-001 | S04-C08 Gate Disposition v1.0

**Disposition:** NO-GO / Gate-S04 remains OPEN. This is a documented gate review, not an approval to waive requirements.

## Gate-S04 exit review

The approved S02 requirement matrix and subsequent S04 decisions retain binding obligations that must be closed before Gate-S04. In particular:

- REQ-SCR-01 is a binding requirement for SCR +10 dB and −10 dB plus a no-clutter condition. Its measurement region and generator tolerance remain open; no clutter source envelope or C01-authorised clutter population is approved.
- REQ-RNG-03 is a binding requirement for two equal-power targets around 600 m range separation. The equal-power convention, relative-phase coverage, spacing sweep, truth-to-cluster association and quantitative resolved-pair success metric remain open.
- S04-C02-RISK-PERFORMANCE is marked blocking_Gate_S04=true in the approved residual-obligations record. C06R2 is a 16-CPI deterministic numerical qualification, not fixed-point statistical Pfa/Pd qualification. No statistical claim is inferred from it.
- C06 A–E has an AI technical acceptance decision (ChatGPT, dated 2026-11-12, supplied by the owner and recorded in the existing C06 package). An authorized independent engineering sign-off or explicit owner-approved delegation to AI is not documented; official C06 PASS remains unavailable.

The original S02 ownership of REQ-SCR-01 and REQ-RNG-03 remains S03. The approved forward responsibilities remain S04-C02 for numeric coverage design and S04-C06 for independent qualification. No owner or requirement is removed by this review.

## Minimum closure work

1. Determine whether the recorded AI technical acceptance is an authorized independent sign-off under the project contract; otherwise obtain an authorized human sign-off on C06R2. Do not rerun its 16 CPI.
2. For REQ-SCR-01, freeze the active-support measurement region, generator tolerance, clutter amplitude/phase/statistical envelope, no-clutter control, authorised source profile and numerical headroom conditions; then obtain a separate test authorization and independent evidence.
3. For REQ-RNG-03, freeze equal received-power definition, target amplitude envelope, relative-phase sweep, fixed range-separation sweep around 600 m, truth-to-cluster association and resolved-pair metric; then obtain a separate test authorization and independent evidence.
4. Obtain an explicit engineer disposition of the still-blocking fixed-point performance obligation. The C06R2 deterministic corpus cannot substitute for statistical qualification.
5. Re-run the Gate-S04 exit checklist only after the above evidence and requirement dispositions are independently accepted.

## REQ-SCR-01 — existing evidence and minimum closure proposal (2026-11-12)

**Existing approved decisions:** S01-D15 approves the initial simple stationary clutter class with pulse-to-pulse fixed phase; broader temporally correlated clutter is a separate later case. S01-D18 approves weak/strong clutter relative to target and a no-clutter baseline, with numeric SCR deferred to S02. S02-D20 binds the three source conditions: no clutter, SCR +10 dB and SCR −10 dB, defined by target-echo power divided by clutter power at receiver input over a specified region. S02-D02 requires stationary-clutter suppression and moving-target MTI response; its finite-precision suppression threshold remains OPEN. C01's approved single-target lab profile is k=40, Doppler +4, amplitude 0.18, phase 0, SNR 20 dB, no clutter, g=1. It does not authorize clutter as an input population.

**Float-model evidence:** `s03_reference/model.py::generate_cpi` accepts a 128-element complex stationary clutter profile repeated identically over all 33 pulses. `s03_reference/extended_scenarios.py` contains developmental ±10 dB clutter examples, but those are three-target cases, not approved REQ-SCR qualification. `tests/test_s03_qualification_and_clutter.py` contains a source-level SCR power-definition check and a stationary-clutter MTI cancellation unit test; neither closes the full requirement. The generator capability exists; no Float algorithm change is needed. No scenario was executed for this disposition.

**Minimum proposed source scenarios (pending engineer approval):** use the already approved single-target k=40, Doppler +4, amplitude 0.18, phase 0, SNR 20 dB and g=1 profile as the matched no-clutter control. Add stationary uniform complex clutter, constant over range and identical across pulses. Define SCR before noise addition and before Q1.15 quantization as the ratio of target-only to clutter-only mean power over the same active-echo support: all 33 pulses × 16 samples at range indices [40,56). Proposed clutter amplitudes are 0.0569209979 for +10 dB and 0.5692099788 for −10 dB. For phase sensitivity, use four fixed clutter-to-target phase offsets 0°, 90°, 180°, 270° for each nonzero SCR. Add one clutter-only control at each SCR level to verify stationary cancellation. Total: 1 no-clutter target control + 8 target/clutter cases + 2 clutter-only controls = 11 deterministic cases. Use a newly predeclared seed, paired identically across target/no-clutter comparisons, not a seed from an accepted S03 campaign.

**Expected Float outputs:** the clutter-only pulse-compressed response is identical pulse-to-pulse and its ideal MTI difference is zero; the target-plus-clutter cases retain the target at range index 40 and Doppler bin +4, with output compared to the paired no-clutter Float control. Record SCR measured from separately retained source components, all Float stage outputs, peak/detection/cluster association, and the deviation from the no-clutter control. No statistical Pfa/Pd or wider correlated-clutter claim follows.

**Proposed Fixed-Point PASS/FAIL:** use the exact same frozen IQ inputs and g=1. Require no input clipping or internal saturation/overflow; exact zero post-MTI clutter-only output for the stationary deterministic controls; at least one correctly associated target record at range index 40 and Doppler bin +4 in each mixed case; report every unmatched/extra cluster without assigning an SCR-specific failure threshold that S02 has not approved; report stagewise Float-vs-Fixed MAX/RMS and mask/record differences. The numeric suppression threshold for non-ideal clutter and any nonzero Float/Fixed error tolerance are not approved by existing S02 decisions and must not be inferred from this proposal.

**Only unresolved engineer decisions for SCR:** (1) approve the measurement region [33 pulses × 16 active samples at k=40] and pre-noise/pre-quantization component-power definition; (2) approve generator tolerance ±0.1 dB; (3) approve the stationary-uniform clutter source profile, four phase offsets and its limited scope (not correlated/heterogeneous clutter); (4) approve the finite-precision suppression rule as exact zero for the clutter-only stationary controls, and the exact functional target/cluster checks above as the SCR Fixed-Point acceptance rule. Until these are approved, no SCR scenario is run and REQ-SCR-01 remains OPEN.

## Decision

C08 remains NO-GO / OPEN. REQ-SCR-01 is still binding and unexecuted; this section records existing decisions, Float-model capability and a minimum proposal only. No acceptance parameter was changed, no test was run, and no progress credit is claimed.


## Updated disposition after explicit engineer-owner C06/C07 approval — 2026-11-12

C06 A–E and C07 are officially accepted by the project owner acting as system engineer, using the documented scoped ChatGPT AI technical review for C06 and pre-existing reviewed corpus for C07. No independent human signature or repeat qualification is claimed. Earlier C06/C07 pending-status text is historical. **Current blocking Gate-S04 requirements are only REQ-SCR-01, REQ-RNG-03 and S04-C02-RISK-PERFORMANCE**; all remain binding. Gate-S04 stays OPEN / NO-GO, C08 stays incomplete. No statistical, clutter or paired-target tests are authorized by this update.

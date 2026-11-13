# REQ-RNG-03 Power-Scope Amendment — Decision Impact and Proposed Corrections

Approved change: range-separability assessment point is Power output only. Engineer decision: REQ-RNG-03-POWER-SCOPE-AMENDMENT-001. This document separates applied normative scope change from proposed acceptance-detail corrections.

## Authority and preservation

The new limited S02 amendment is engineering/S02-REQ-RNG-03-POWER-SCOPE-AMENDMENT-v1.3.md. The exact current engineer message and preceding rationale messages are pinned in decisions/REQ-RNG-03-POWER-SCOPE-AMENDMENT-20261113.json.

Earlier approved S02/S03/S04 files remain byte-identical. The original final-record result remains historical FAIL4/8. Current revised RNG03 status is APPROVED_SCOPE / ACCEPTANCE_CRITERION_AND_DISPOSITION_PENDING. No retroactive PASS or new Gate signature is created.

## S02 through current S04 impact

| Item / existing record | Effect of decision | Correction / action | State |
|---|---|---|---|
| S02 REQ-RNG-03; approved v1.0 row and later S04 refinement | CFAR/group-record multiplicity no longer measures this requirement | Adopt limited v1.3 scope overlay; define Power separability explicitly | Scope applied; metric proposed |
| S02 REQ-POWER-01 | Power becomes the observation product for RNG03 | Add RNG03 cross-reference and declare map orientation/scaling/configuration in evidence | Cross-reference proposed; numeric contract unchanged |
| S02 REQ-DET-01 and REQ-MATCH-01 | Their independent output/scoring obligations remain | Separate Power truth-to-peak evaluation for RNG03 from target-record matching. Do not globally waive target-count or one-to-one rules | Clarification proposed; other requirements unchanged |
| S03 approved Gate/model evidence | Existing approval remains valid | Use retained Power outputs for the revised requirement after metric acceptance; append scoped evidence disposition | No reopening or automatic new PASS |
| S04 C01–C04 arithmetic/reference contracts | No source, scaling, waveform or numeric operation changes | Retain approved results; no rerun required by observation-point change alone | Unchanged |
| S04 C05 signed Power/CFAR/Grouping qualification | Eight-connected one-maximum Grouping no longer conflicts with revised RNG03 observation point | Retain signed deterministic C05 scope. Do not introduce multi-peak extraction merely for RNG03 | Unchanged; optional redesign not authorized |
| S04 C06 A–E and execution result | Bounded numeric/oracle checks remain valid in original scope | Preserve reports, exceptions and denominators | Unchanged |
| S04 C06-F and independent criteria decision | Historical truth-to-cluster separability clause is superseded for current RNG03 | New overlay should refer to Power peaks/valley criterion instead; other F obligations retained | Scope supersession applied; quantitative clause pending |
| S04 C07 owner evidence-review acceptance | Historical review stays accepted in its original context | Add this amendment and Power evidence disposition to the current review index | Supplement proposed, old review unchanged |
| S04 C08 transition and carryover register | S04 remains closed with carryovers; old RNG03 FAIL stays historical | Current carryover view distinguishes old final-record FAIL from revised Power assessment pending | Current view updated; old decision preserved |
| S04-C02-RISK-PERFORMANCE | Statistical Fixed-Point qualification is separate | Keep OPEN; no statistical waiver or campaign authorization inferred | Unchanged |
| Grouping compatibility proposal / EXP-AX309-019 | Old finding remains true for old criterion; new requirement no longer demands that fix | Retain history/candidate, mark multi-peak redesign optional and unapproved for revised RNG03 | Context updated; no lesson promotion |

The exact historical C06-F clause is found in engineering/S04-C06-EXECUTION-CONTRACT-v1.0.md and decisions/S04-C06-CRITERIA-INDEPENDENT-DECISION-v1.0.md. They are preserved; this amendment provides forward precedence for RNG03 only.

## Proposed operational acceptance contract

Retain the historical eight-case input matrix unless the engineer separately amends it: two equal amplitude0.18 targets, common Doppler+4, g1, no noise/clutter, separations4/5 samples, relative phases0/90/180/270. The prior +/-1 sample target-location allowance is proposed for matching the Power peaks; it is not silently converted into a new approved numerical criterion.

Candidate A — noise-free peak existence:
- Evaluate the Power range profile at the declared common Doppler bin.
- Require two distinct strict immediate-neighbor local maxima, each within +/-1 sample of its respective known target delay, with one-to-one attribution.
- Require at least one intervening sample lower than both maxima.
- Require all eight cases. No additional minimum valley-depth dB.
- Limit the claim to this noise-free finite reference/fixed configuration; no CFAR/Grouping result condition.

Candidate B — peak prominence:
- Retain the same conditions and add an explicitly selected minimum valley depth.
- A 3 dB example is analyzed for comparison only; it has not been approved.

On already retained Float and selected-C Fixed Power profiles, A is satisfied in8/8 cases, while the illustrative B(3dB) is satisfied in2/8. This is retrospective inspection of stored diagnostics, not a new run or a prospective acceptance study. The old4/8 final-record result and both illustrative counts must be labeled by their different criteria.

Acceptance of A, B or another quantitative definition requires an explicit engineer decision. Broader noisy/physical performance is not established by either count.

## Downstream consequences, not new stage approvals

S05–S11: keep the existing Grouping algorithm and interfaces unless another requirement motivates change. Power-output access and correct scaling/orientation must support whatever later RTL/board validation is claimed. The eight-case observations above concern historical C02 Fixed and Float, not automatically the later IP bitstream or physical board.

S12: present old and new requirement versions, source decision, accepted criterion when available, configuration-specific result and traceability together. No source/configuration/Gate/merge/publication approval is inferred.

## Recommended next decision

For the current laboratory/noise-free requirement, review Candidate A as the minimal Power-domain interpretation, with its explicit limits. A stricter noise-robust or minimum-valley requirement should be separately defined rather than silently inserted. Until the criterion and evidence disposition are approved, retain revised RNG03 acceptance as OPEN.

## Additional interpretation boundaries

Power evaluation domains are governed by source echo support and processing validity, not automatically by CFAR valid-CUT/training-window exclusions. The retained paired targets lie inside both domains; no expanded edge-domain acceptance is inferred. The proposed paired-target +/-1 allowance does not replace isolated-MF zero-error requirements, Float/Fixed numerical-error checks, or the separate REQ-MATCH-01 estimator criteria.

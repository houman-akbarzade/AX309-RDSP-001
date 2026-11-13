# AX309-RDSP-001 — Current Project and Compliance Status

Status: DOCUMENTATION_RECOVERED_SUBSTANTIALLY / ENGINEERING_ACCEPTANCE_INCOMPLETE  
This current audit view supersedes outdated status summaries for review purposes only. It does not replace an approved baseline, historical decision, project.yaml or replay/stages.json.

## Direct answers

- The recovered history is substantially documented, but original platform conversation completeness is not proven.
- Technical development reached actual full-chain laboratory hardware execution (S11 domain).
- Formal stage closure is recorded through S04 only: S01–S03 approved; S04 explicitly closed with technical carryovers.
- S05–S11 have implementation directions and substantial evidence, but no separate final Gate closure records were located.
- S12 final delivery/baseline and repository/publication review are not complete.
- Not all requirements are PASS. Recorded FAIL/OPEN and unqualified scope remain.
- Source code and tests were not changed or rerun by this documentation mission.

## Twelve stages: four independent dimensions

| Stage | Documentation | Technical implementation | Verification evidence | Formal Gate |
|---|---|---|---|---|
| S01 Problem Definition | Approved historical baseline; mission addenda preserve later scope | Problem defined | Approved source artifact identified | APPROVED, decisions/GATE-S01-approved-baseline.json |
| S02 Requirements and Acceptance | 22 approved rows and limited amendments; current scoped audit refreshed | Contracts established | Requirement acceptance differs from specification approval | APPROVED, decisions/GATE-S02-approved-baseline.json |
| S03 Functional Reference | Source, failures, statistical protocols/results and retention limits recorded | Python floating reference completed | Accepted model scope; scoped Pfa/Pd and deterministic tests | APPROVED, decisions/GATE-S03-approved-baseline.json |
| S04 Bit-True Fixed-Point | C01–C08 and carryover decisions retained | Historical selected-C numerical model completed in accepted bounded scope | Bounded deterministic evidence; historical record-domain RNG03 FAIL retained, revised archived Float/C02 Power PASS8/8 each; statistical risk OPEN | CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS |
| S05 Architecture and Interfaces | Historical architecture plus recovered IP as-built report and Lab scope | Full laboratory architecture implemented | Source/evidence manifests and configuration-specific results | Entry/development authorized; FINAL_GATE_NOT_LOCATED |
| S06 RTL and Testbench | Main sources and pinned Lab sources/testbench archives documented | RTL exists and full laboratory chain implemented | Finite source/oracle/self-checking TB evidence | FINAL_GATE_NOT_LOCATED |
| S07 RTL Simulation | ISim and historical alternative-simulator distinctions retained | Simulation executed historically | Finite self-checking cases PASS; no universal coverage assertion | FINAL_GATE_NOT_LOCATED |
| S08 Synthesis | XST/MAP archives retained; configuration identity recorded | Full-chain and seven Lab images built historically | Archived resource fit; complete warning disposition remains | FINAL_GATE_NOT_LOCATED |
| S09 Implementation and STA | PAR/TRCE/Bitgen archives retained | Full-chain implementation executed historically | Applied 20ns internal constraints met; external/unconstrained qualification incomplete | FINAL_GATE_NOT_LOCATED |
| S10 System Integration | GUI/UART and injection workflows documented | Physical GUI-to-FPGA chain and Lab workflows implemented | Finite COMMIT/RELEASE, input verification and comparison evidence | FINAL_GATE_NOT_LOCATED |
| S11 Physical FPGA Board Testing | Main journals and selected immutable Lab captures imported | Actual AX309 chain executed historically | Main nine-case archive plus finite stage captures; no general physical statistical qualification | FINAL_GATE_NOT_LOCATED |
| S12 Delivery and Baseline | Preparation README, evidence/history/mission/experience/audit records exist | Delivery preparation | Final configuration, requirement/gate disposition and packaging review incomplete | NOT_ACCEPTED |

A direction to implement, “continue”, a successful tool report and a stage approval are different records. Missing final Gate records do not erase genuine technical accomplishments; technical accomplishments do not manufacture signatures.

## What was completed in this recovery

1. Seventeen source-backed historical direction records (13 original plus four PDF supplements) distinguish proposals, trials, implementation requests and acceptance.
2. Mission and scope addenda document the owner-requested physical demonstrator, UART input/readback/result output, GUI/scenarios, independent stage injection, Float/Fixed references, automatic reports, paired maps and zoom.
3. Sixteen original Git-backed Lab messages were recovered. Five copied-text fragments and ten PDF missing/source-variant fragments remain explicitly excerpts. Source variants are not claimed to be distinct original platform turns.
4. Two original Lab events were appended. Original canonical prefixes remain unchanged.
5. The 37-page PDF, extracted text and embedded stationary-question image were preserved. Page references and hashes identify source content.
6. A current 22-row requirement evidence audit replaces the earlier “not reassessed” snapshot for current review: REQUIREMENTS-CURRENT-AUDIT-v4.json. All sufficiency statements are scope-specific.

The PC-offload ideas are recorded as alternatives/experiments. The observed final laboratory allocation retains Power, CFAR and Grouping on FPGA. W5500 is a future intention. The FFT-IP numerical/overflow differences from C02 are retained and formal as-built numerical disposition remains pending.

## Are all evidence and tests registered?

A large, useful evidence archive is registered, but an “all historical evidence is complete” claim is unsupported.

- 1,470 immutable report/evidence files were copied into the preparation branch and their hashes verified.
- 58 archived executable/build images remain at pinned Lab references rather than being copied.
- 28 untracked user files were inventoried and left untouched; they are not automatically incorporated.
- 94 retained automatic-case archives and 184 comparisons against stored Fixed references were checked independently. These are not 94 unique board executions.
- Main full-chain journals retain nine cases, 36,864 Power cells and 56 records.
- Source/log indexing covers 321 software test functions across 32 files and mentions in 178 archived logs. Mechanical indexing is not complete test-by-test acceptance.
- The accepted S03 Pd study retains per-CPI records/hashes/selected metrics, but not every original full IQ and Power array.
- The platform export is still incomplete: a stopped answer and an empty printed marker remain; PDF omitted one final answer that was separately recovered from Lab.
- Full independent adjudication of every historical trace, final constraint/warning coverage and every requirement/configuration mapping is not complete.

No acceptance rerun was performed. Missing original arrays cannot be recreated from hashes and were not regenerated.

## Requirement outcomes

| Item | Current defensible statement |
|---|---|
| REQ-RNG-03 | Historical final-record FAIL4/8 retained; engineer amended observation point to Power only. Revised quantitative criterion and acceptance disposition pending |
| Fixed-Point statistical performance | OPEN; C06 deterministic PASS and three-CPI mechanism checks do not qualify it |
| REQ-CFAR-02 / REQ-PD-01 | Accepted scoped S03 floating-model populations; not automatically IP/physical qualification |
| REQ-SCR-01 | Owner-accepted historical eleven-case scope retained; no broadened physical acceptance |
| REQ-LIST-01 | Logical 702/no-silent-drop policy approved; final complete transport acceptance OPEN |
| REQ-OBS-01 / REQ-EVID-01 | Physical full-chain and separate stage evidence exists; complete finalized observability/contract acceptance pending |
| REQ-UART-01 | Finite real/simulation results; final ICD and interrupted-session recovery boundary pending |
| REQ-RES-01 | Actual final build fits and applied internal timing passes; complete external/unconstrained-path acceptance pending |
| REQ-TIME-01 | Host transfer/wait/elapsed records exist; complete required FPGA cycle/rollover qualification not established |

Other rows now link accepted reference tests and finite Lab results where available. EVIDENCE_SUFFICIENT for a stated claim is never relabeled as all-population/all-configuration requirement PASS.

## What remains

### Documentary work and final preparation

- Complete exhaustive test/requirement/configuration adjudication and archive-specific reproducibility checks where retained bytes permit.
- Finish the final as-built numerical/interface/constraint acceptance package and independent warning dispositions.
- Finalize canonical status/manifest/projection replacement after owner approval; separate proposals exist.
- Complete remaining EEM historical interpretation/triage; no experience was promoted automatically.
- Decide inclusion of currently referenced-only/untracked items and finish final delivery packaging/disclosure/vendor-IP review.
- The preparation branch is linked to the same Git repository; master is still protected and unmerged. Nothing was published.

### Engineer decisions

The engineer now requests stepwise review, currently S04. S03 scoped approval has been verified against all seven pinned hashes. The carryovers were re-examined; the later engineer amendment changes RNG03 observation to Power while its operational acceptance remains pending. Fixed statistical risk remains OPEN. See the stepwise review and the subsequent Power-scope impact review. This review order does not reopen the already closed Gate-S04. The FFT-IP as-built proposal remains available for the later architecture/configuration discussion; it is not a request to rerun work.

Then review individual S05–S11 Gate packages with preserved carryovers. Any requirement waiver/change, new statistical/coverage test, reference replacement, merge or public publication needs its own applicable authorization. No such approval is invented here.

## Progress

Repository Documentation & Compliance Progress: substantial recovery and organization completed, final review/closure incomplete; no defensible percentage assigned.

Engineering Project Progress: actual laboratory implementation reaches S11 activity. Historical Gate closure reaches S04 with open items. The old 33.33% Gate-weighted and 37.0833% R2 implementation tracker are historical metrics for different earlier states; neither is a defensible current functional-completion percentage. No new numeric progress is inferred from documentation.

Current status is not READY_FOR_GITHUB_REVIEW and not final S12 acceptance.

## Historical S04 grouping-policy diagnosis under former final-record criterion

A further read-only inspection finds two pre-grouping local Power maxima in each of the four failed mandatory cases; both survive CFAR, but share a connected region. The accepted one-record-per-region policy explains loss of separate target records in these cases. This is a contract/performance compatibility finding, not a demonstrated implementation bug or a new PASS. A multi-peak candidate is documented in S04-GROUPING-POLICY-COMPATIBILITY-PROPOSAL.md; no stable source changed.

## Current normative REQ-RNG-03 scope amendment

The explicit engineer decision REQ-RNG-03-POWER-SCOPE-AMENDMENT-001 now limits range-separability acceptance to Power output, before CFAR/Grouping. Old final-record failure and the associated grouping-policy finding remain historical under the former criterion. Multi-peak Grouping redesign is no longer required solely for revised RNG03; it remains optional/unapproved. Quantitative Power acceptance is pending; no new PASS is declared. See the S02 limited v1.3 amendment and REQ-RNG-03-POWER-SCOPE-IMPACT-REVIEW.md. Fixed-Point statistical qualification remains OPEN and Gates unchanged.


## Current S04 review update: approved Power peaks and statistical carryover (2026-11-13)

The engineer approved two distinct Power peaks under the prior proposed noise-free criterion. Read-only archived-data reassessment gives **Float PASS8/8 and selected-C/C02 Fixed PASS8/8**, with no additional3dB valley condition. Current authority: decisions/REQ-RNG-03-POWER-PEAKS-ACCEPTANCE-20261113.json; normative limited amendment: engineering/S02-REQ-RNG-03-POWER-PEAKS-AMENDMENT-v1.4.md. Earlier pending statements above are historical snapshots superseded for this scoped item. Historical final-record FAIL4/8 remains unchanged. Final FFT-IP/board resolution is not inferred.

Fixed-Point statistical performance remains **OPEN_NOT_STATISTICALLY_QUALIFIED**: no completed accepted qualifying campaign was located, and no statistical FAIL of Fixed-Point is established by that absence. See engineering/audit/S04-FIXED-POINT-STATISTICAL-QUALIFICATION-REVIEW-v1.0.md for the proposed bounded protocol. Current requirement review v4 and decision queue v4 apply. No code, model, test, historical result or Gate was changed; no new engineering campaign was run. Documentation progress does not imply engineering statistical completion.

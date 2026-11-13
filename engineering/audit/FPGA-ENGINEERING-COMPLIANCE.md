# FPGA Engineering Repository Compliance Audit

Project: AX309-RDSP-001  
Audit date: 2026-11-13  
Protected main HEAD: d45d350803c418f86cfc4fbfa098a9140daeedf5  
Stage Lab HEAD: 6c86a2e16b283d2cef82fd7be351b0b34ff95d74  
Preparation branch: docs/fpga-engineering-repository-audit

## Disposition and scope

**IN_PROGRESS — NOT_READY_FOR_GITHUB_REVIEW.** This report records completed documentary checks and unresolved review work. It is not an engineering acceptance or gate decision. No engineering test was rerun. No FPGA programming, merge, publication, reference-file replacement or Stage Lab transfer was performed.

The protected main worktree was clean at entry. Stage Lab was a linked worktree with 28 untracked files. A third worktree was created at /home/houman/AX309-RDSP-001-docs-audit. ENTRY-SNAPSHOT.json records SHA-256, size and tracked status for 1,361 main and 2,961 Stage Lab files. This inventory covers Git-tracked and nonignored untracked files; ignored build products were not comprehensively inventoried. It does not establish a formally approved new baseline: the main HEAD is the protected entry snapshot, and individual approved baselines remain those in decisions/.

## Evidence and authority hierarchy

Read the approved S02 v1.0 baseline together with its approved v1.1 and limited C-CFAR-02 v1.2 amendments. Later explicit engineer decisions govern stage disposition within their stated scope. A later laboratory report does not silently supersede numerical acceptance contracts. Historical files retain their original statements.

GATE-S03-approved-baseline.json explicitly approves S03 after the earlier readiness report. S04-C08-S05-TRANSITION-2026-11-12.json closes S04 with open items. The old stage projection and early project.yaml summaries are stale; they do not cancel those decisions or prove later gates approved.

## Twelve-stage assessment

“Partial” means that further documentary reconciliation or evidence review remains. Implementation and verification describe observed scope, independently of gates.

| Stage | Documentation | Implementation | Verification | Official gate / authority |
|---|---|---|---|---|
| S01 Problem Definition | Approved historical baseline; dialogue provenance partial | Problem defined | Approval/hash record present; comprehensive decision-to-dialogue check pending | Approved; decisions/GATE-S01-approved-baseline.json |
| S02 Requirements and Acceptance | Approved v1.0 plus v1.1/v1.2; derived current matrix needed | Contracts established | 22 requirements inventoried; per-contract historical cross-check incomplete | Approved baseline and limited amendments |
| S03 Functional Reference | Detailed reports and source locks; raw-array retention limits | Python floating reference executed historically | Scoped Pfa report; 1,000 Pd record aggregates independently checked in this audit | Approved; decisions/GATE-S03-approved-baseline.json |
| S04 Bit-True Fixed-Point | C01–C08 reports and carryover record; historical wording requires temporal interpretation | Architecture C implemented historically | C06R2 reports 16/16 bounded A–E; SCR scoped PASS; RNG03 FAIL 4/8; statistical performance OPEN | Closed by explicit engineer disposition with open items |
| S05 Architecture and Interfaces | Architecture/ICD and later IP path need consolidated change/acceptance map | Full laboratory IP chain exists | Source/evidence manifest 140/140 hash matches; IP is not C02 bit-equivalent | Entry authorized; no separate final S05 closure located |
| S06 RTL and Testbench | Modular RTL and test archives present; complete requirement coverage review pending | RTL and UART laboratory implementation present | Archived TB inspected; every historical TB not yet individually audited | No explicit S06 gate approval located |
| S07 RTL Simulation | ISim evidence present | Simulations historically executed | Full-IP two-CPI byte-exact TB/log reviewed; finite protocol scenarios only | No explicit S07 gate approval located |
| S08 Synthesis | XST/MAP archives present | Full-IP synthesis completed historically | Archived logs indexed; resources reported; full warning disposition pending | No explicit S08 gate approval located |
| S09 Implementation and STA | PAR/TRCE/Bitgen archives present | Full-IP implementation completed historically | 19.402 ns internal minimum period reported at 20 ns; I/O/constraint coverage review pending | No explicit S09 gate approval located |
| S10 System Integration | Integration report, GUI evidence, source manifest present | Host/UART/full DSP integrated in laboratory | Finite GUI/transport/COMMIT/RELEASE evidence; interrupted-session recovery limitation | No explicit S10 gate approval located |
| S11 Physical Board Testing | Nine-case journals retained; Stage Lab evidence separately inventoried | Physical AX309 execution historically documented | 9 journals: 36,864 Power cells and 56 records; finite development scope, not operational acceptance | No explicit S11 gate approval located |
| S12 Delivery and Baseline | Audit branch and English overview created; final packaging incomplete | Delivery preparation in progress | Preservation check required before each commit; public-release/IP/privacy review pending | No final delivery gate located or created |

### Stage output, decisions and remaining work

S01 inputs/outputs are the problem drafts and approved v0.3 hash in the gate record. S02 outputs are the 22-row matrix and normative contracts; acceptance is row-specific, not a blanket PASS. S03 outputs are s03_reference/, execution manifests, failed qualification history and separate Pfa/Pd reports. S04 outputs are engineering/s04_numeric/, C01–C08 decisions and explicit final-evaluation carryover.

S05–S11 outputs span rtl/, pc_link/, desktop_app/ and engineering/evidence/s05, s10 and s11. Development stages were performed under S05 authorizations; technical activity does not imply separate S06–S11 gate approval. S12 still requires configuration-controlled delivery scope, rights review and the owner's disposition. A fully expanded stage-by-stage input/assumption/rollback/criterion register is not yet complete.

## Completed checks and findings

| ID | Finding | Evidence | Disposition |
|---|---|---|---|
| AUD-001 | Conversation manifest is stale: 110 declared vs 111 actual; SHA differs | REPLAY-INTEGRITY.json; conversation last changed d45d350, manifest last changed 67901a2 | Proposed separate manifest only; reference unchanged |
| AUD-002 | Conversation identifiers mix 93 message_ref and 18 message_id records | REPLAY-INTEGRITY.json | Preserve originals; adapter proposal/review needed |
| AUD-003 | replay/stages.json last updated at S02; project.yaml predates full-IP board integration | Git history; later gate decisions and full integration report | Publish derived audit status; do not overwrite historical/reference files |
| AUD-004 | EEM current-path hashes differ for project.yaml in EXP014/015, but both exact recorded commit blobs match | EEM-INTEGRITY.json | Valid historical references, not corrupt evidence |
| AUD-005 | Nine Stage Lab v0.2 source hashes differ from current branch | EVIDENCE-MANIFEST-CHECKS.json | All nine historical versions found in Git; use pinned versions |
| AUD-006 | REQ-RNG-03 remains FAIL 4/8 against unchanged 8/8 criterion | S04 transition decision and req_rng03 results | Carry to final evaluation; no retest authorized |
| AUD-007 | Fixed-Point statistical performance remains OPEN | S04-C08 disposition | C06 deterministic PASS is not statistical acceptance |
| AUD-008 | FFT IP is not bit-exact to frozen custom C02; overflow semantics differ | rtl/experiments/fft_ip_20261112/README.md; later integration report | Consolidated engineer-approved numerical-baseline disposition needed |
| AUD-009 | Full historical dialogue cannot be asserted; excerpts remain excerpts | conversations archive and legacy policy | No reconstruction; explicit provenance limitation |
| AUD-010 | Main and Stage Lab are different executable configurations | STAGE-LAB-FILE-REGISTER.json | No transfer/replacement performed |
| AUD-011 | Root and package status descriptions disagree chronologically | project.yaml, pc_link/README.md, later integration report | New root README points to dated evidence and limitations |

## Existing test evidence audit

These verdicts assess evidence for the named narrow claim. They do not replace historical test status.

| Campaign / claim | Audit verdict | Basis and limits |
|---|---|---|
| S03 Pd second main, archived count and scoped D criterion | EVIDENCE_SUFFICIENT | 1,000 unique contiguous records; D/E/J/R/V all 1,000; raw hash matches; independent all-success CP lower 0.9970087504549047 matches report; D threshold 916. Fixed single target/no clutter/software only |
| Recovery of all original Pd IQ/full Power arrays from archive | RESULT_NOT_REPRODUCIBLE_FROM_ARCHIVED_EVIDENCE | Only hashes, selected rows and metrics retained; hashes cannot reconstruct original arrays |
| S03 Pfa final, full independent documentary recalculation | EVIDENCE_INCOMPLETE | Approved 20,000-CPI EB result identified; full alarm-vector/source-lock review remains |
| S04 C06R2 bounded A–E | EVIDENCE_INCOMPLETE | Detailed 16/16 report and runner checks identified; all individual archived traces not independently recalculated in this pass |
| REQ-RNG-03 | CRITERION_NOT_MET | Both Float and selected-C fixed reports retain 4/8 mandatory pass; no criterion change |
| Statistical Fixed-Point performance | EVIDENCE_INCOMPLETE | No accepted qualifying campaign located; explicit open carryover |
| Full-IP ISim two CPI transport/output claim | EVIDENCE_SUFFICIENT | Archived TB compares UART bytes and final flags; log records PASS at 72,123 bytes; simulation uses accelerated serial clocks, not board electrical qualification |
| Full-IP physical finite nine-case archive | EVIDENCE_SUFFICIENT | Journals retained with physical_UART, byte verification, COMMIT/RELEASE, Power and record counts. Original oracle equality remains reported, not newly rerun |
| Full operational Pd/Pfa / end-to-end Stage Lab statistical acceptance | REQUIRES_ENGINEER_REVIEW | Finite lab captures and three-CPI mechanism checks cannot establish this acceptance |
| Every other indexed historical JSON/test | REQUIRES_ENGINEER_REVIEW | JSON-EVIDENCE-INDEX.json is an inventory, not a completed individual test audit |

The nine physical cases include closely spaced targets with only one of two targets associated. Additional clusters are not silently removed and must not be converted to Pfa. GUI CFAR cells reconstructed on PC are derived visualization, not direct FPGA CFAR readback. Stage Lab per-block injection uses a different configuration from continuous full-chain processing.

## Stage Lab assessment

STAGE-LAB-FILE-REGISTER.json identifies 1,604 differing/additional paths: 1,553 evidence paths, 39 functional-source paths, five documentation paths, three historical-record paths and four other paths. Each includes hashes, main equivalence and latest tracked provenance. NPZ ZIP members/CRC were inspected without model execution. CRC and hash integrity do not prove numerical validity.

The v0.3 manifest has 1,222 matching hashes. The v0.2 manifest has 318 references: 309 match current files; nine match historical Git versions. No archived failure was erased. Content-level compatibility/requirement mapping for every individual file remains incomplete. Recommended action is immutable source references first; any evidence transfer requires owner approval. No Stage Lab file was copied into the main baseline or preparation branch.

## Engineering Experience Management

All 17 cards were read structurally, with 64 evidence references checked against current paths and supplied Git blobs. Sixteen are VALIDATED, one CANDIDATE; none was promoted. Two current-path mismatches are exact historical matches. The present audit does not certify every causal interpretation or approve the historical migration.

Repository-wide filenames and accessible Git history were inventoried; detailed triage across every historical experiment is incomplete. Therefore no new COMPLETE backfill claim is made. A new candidate concerning status-projection drift is recorded separately without changing the prior ledger or approved experience state.

## Replay

JSONL parsing, ID uniqueness, available text hashes and reply_to_message_id targets were checked. No duplicate message/event IDs or available-text hash mismatches were found. Events: 143 actual/declared; event hash matches. Missing legacy schema fields are not synthesized. Full decision-to-dialogue and chronological semantic checks remain outstanding.

manifest.PROPOSED.json corrects only observed count/hash data, is not installed, and does not fix schema compatibility or assert complete dialogue. Additional fields such as legacy quality counts and last_message_ref require full consistency review before replacement. Current mission's complete verbatim request/response pair has not been added to canonical Replay; conversation_capture_status: BLOCKED under this audit's reference-preservation workflow. No complete capture claim is made.

## Progress

Repository Documentation & Compliance Progress: **in progress; no defensible completion percentage yet**. Inventory and selected integrity checks are complete; exhaustive individual-test review, stage contracts, disclosure review and final packaging remain incomplete.

Engineering Project Progress: **unchanged**. Historical official stage-exit basis is 4/12 = 33.33% with S04 carryovers. project.yaml also stores a later implementation-weighted 37.0% measure; these are different measures and neither is updated by this audit. Later full-IP work is documented without inventing a new completion percentage.

## Decisions and next work

1. Complete per-test criterion/source/raw-output review and full S02 traceability reconciliation.
2. Complete read-only Pfa/C06 archival analysis and full STA warning/constraint disposition.
3. Complete EEM historical candidate triage and exact dialogue/decision linkage audit.
4. Present pinned Stage Lab reference/transfer recommendations for owner approval.
5. Present reference metadata replacement and numerical IP-baseline proposals separately.
6. Prepare S05–S11 gate packages only where criteria/evidence are sufficient; seek explicit owner decisions then.
7. Review vendor IP redistribution, license/disclosure scope and all public-facing history. No public release is authorized.

Before any commit, compare entry hashes, main/lab status, tracked diff and staged allowlist. Preserve all original files and all approved decisions.

## Additional read-only verification

The final S03 Pfa archived count vector was independently recomputed: N=20,000, total alarms=55,919; mean 0.0010050143781452192; EB U95=0.0014491445035750084 <=0.0015. All 12 referenced normative/source/result hashes match. Audit result for this archived numerical aggregate is EVIDENCE_SUFFICIENT within approved software noise-only scope. Earlier pending-count-vector wording above is superseded by this additional check; no full signal chain was rerun. See PFA-ARCHIVED-ARITHMETIC-REVIEW.json.

The archived STA summary explicitly reports zero errors and 784,082,425 analyzed paths, but also requests unconstrained-path reporting for complete coverage. Therefore all-applied-constraints-met is supported; comprehensive timing acceptance remains EVIDENCE_INCOMPLETE. No timing exception or constraint was changed.

## Source and case registers

SOFTWARE-TEST-SOURCE-REGISTER.json maps 321 test functions across 32 source files to static assertions and mentions in 178 archived logs; 309 functions have log mentions. This is a mechanical source/log index, not a substitute for full individual criterion adjudication. STAGE-LAB-CASE-REGISTER.json records 94 retained automatic-lab case JSONs with their scopes, metrics and physical-capture indicators. Reused captures remain explicitly identified. No test source was imported or executed.

## Replay follow-up and commit checkpoint

All 81 present text/content SHA-256 fields match exact stored text. Legacy labels are 30 EXCERPT, 57 FULL, six SUMMARY, and 18 verbatim. No label is promoted. Twenty decision files have a separate presence-only dialogue-reference register; semantic approval provenance remains to be adjudicated. manifest-v2.PROPOSED.json supersedes the first proposal for review by refreshing label counts and final ID as well as byte hashes/counts; neither proposal is installed.

Checkpoint commit 76475cd contains only new audit measurements and inventories. Subsequent narrative/readme/candidate work is also documentation only. This checkpoint is not the final mission handover. No publication, merge, gate approval, engineering rerun or baseline change is authorized or performed.

## Engineer-authorized existing-work recovery update

The subsequent engineer instruction authorizes reuse/import of existing Lab evidence. The current continuation is documented in EXISTING-WORK-RECOVERY-AND-AS-BUILT-REVIEW.md; it supersedes earlier no-transfer descriptions for the preparation branch only. STAGE-LAB-EVIDENCE-IMPORT.json pins 1,470 imported files; 58 archived executable/build images remain reference-only. LAB-ARCHIVED-NUMERICAL-REVIEW.json supports 94 finite case archives and 184 exact comparisons against stored Fixed references. No project test/model was executed.

The next explicit engineering decision concerns recognition of the FFT-IP as-built laboratory configuration alongside historical C02. S05–S11 approval records have not been invented. Current recovery dialogue is appended verbatim; this does not repair missing dialogue from the initial audit turn. The old canonical manifest remains unchanged pending reference-replacement approval; a fresh proposal is generated separately. No new engineering progress percentage is inferred.

## Historical dialogue and mission recovery

Sixteen authentic Git-backed Lab messages were appended unchanged, with original content hashes verified; five additional user-export fragments were recorded as excerpts. Two authentic Lab events were appended unchanged. Thirteen source-backed engineering directions now connect the resource problem, PC-offload alternatives, FFT-IP study, GUI/UART delivery, Stage Lab, automated reports and display fixes. See the new mission addendum and engineering history. The user export is partial (287 lines, cut mid-sentence); no full-history claim is made. The reference manifest is not replaced; an updated proposal is prepared separately. Approved requirements and Gate states remain unchanged.

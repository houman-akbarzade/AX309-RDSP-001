# AX309-RDSP-001 — Existing Work Recovery and As-Built Laboratory Review

Status: PROPOSED_FOR_ENGINEER_REVIEW. No new engineering gate decision is created. This document supplements the earlier audit checkpoint following the engineer's explicit instruction to recover and organize existing Stage Lab work.

## Purpose and provenance

Continue the project documentation from the last approved main-repository state using genuine retained development evidence. The imported work was executed historically in Stage Lab; this recovery checked and registered its results without rerunning it. No author, time, approval or experiment is retrospectively invented.

Protected entry main commit: d45d350803c418f86cfc4fbfa098a9140daeedf5. Laboratory source: 6c86a2e16b283d2cef82fd7be351b0b34ff95d74. Preparation uses a linked worktree of the same Git repository on docs/fpga-engineering-repository-audit. Main/master remains unchanged.

## Imported evidence

STAGE-LAB-EVIDENCE-IMPORT.json records 1,470 newly copied files with exact source hashes and Git provenance: three engineering reports plus retained JSON/NPZ/log/image/HTML/SVG evidence. Fifty-eight archived build/source images are referenced at their original pinned source rather than copied. Active RTL, Python/MATLAB, GUI, build settings, historical replay files and 28 untracked user files were not transferred.

LAB-ARCHIVED-NUMERICAL-REVIEW.json independently reads the 94 retained automatic-lab case archives. For every case, input/output little-endian word hashes, recorded lengths and zero numeric flags match. There are 184 exact comparisons to retained Fixed arrays/record references across these cases. Grouping words were decoded and compared to retained hardware records and Fixed signatures. All 94 case archives are sufficient for these finite archived-byte equivalence claims.

This does not imply 94 unique board executions: reused captures and repeated/derived reports remain separately identified. The designated quick suite reports 41 jobs and 40 distinct captures; its 65 original Fixed comparison count is a different denominator from this wider archive review.

## Configuration identity

Two numerical configurations coexist and must remain separate:

1. Historical approved selected-C custom FFT numerical design. Its decisions and bounded C06/SCR/RNG results are preserved.
2. Later laboratory FFT-IP full-chain design and separate per-stage injection images. The IP path is not bit-exact to C02 and has different overflow semantics. It has actual simulation/build/board evidence; it needs explicit engineering disposition as an as-built laboratory configuration, not silent replacement of the historical contract.

The full-chain bitstream SHA-256 is fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb, from engineering/evidence/s10/full_ip_20261112/manifest.json. The per-stage images and source-preservation locks are in engineering/evidence/stage_lab_v0.2/manifest.json. Their configuration identity does not authorize programming or rebuilding.

## Recovered stage evidence and acceptance boundaries

The following are retrospective evidence packages, not newly approved exit criteria. Applicable historical requirements/decisions remain authoritative. A proposed scoped disposition can be approved by the engineer while explicitly retaining final-evaluation open items.

| Stage | Existing outputs and measured evidence | Supported acceptance scope | Remaining decision or limitation |
|---|---|---|---|
| S05 Architecture and Interfaces | Historical architecture, UART ICD candidate, full-IP integration report, Lab image manifest | Documented as-built full-chain and injection configurations with source identity | Approve how the IP laboratory configuration relates to frozen C02; final normative ICD disposition remains open |
| S06 RTL and Testbench | Main RTL at protected commit; Lab RTL referenced at pinned commit; archived self-checking TB and source manifests | Implementation exists; full-IP source manifest 140/140 source/evidence hashes match; no new RTL required for this recovery | Does not certify exhaustive corner-case coverage or bit-equivalence of IP to C02 |
| S07 RTL Simulation | Full-IP two-CPI ISim archive; per-stage simulation results and logs | Expected UART output, finite protocol faults, Power and records; original simulation PASS retained | Accelerated UART simulation is not electrical or statistical qualification |
| S08 Synthesis | Archived XST and MAP reports for full chain and seven laboratory images | Full-chain mapped resources: 5,019 LUT, 3,913 FF, 14 DSP48A1, 25 RAMB16 and 5 RAMB8; per-image resources separately retained | RAMB8/RAMB16 must not be counted as identical sites; complete warning disposition still required for final delivery |
| S09 Implementation and STA | Full-chain PAR/TRCE/Bitgen logs; per-image implementation logs | At the applied 20 ns constraint, final full-chain internal minimum period 19.402 ns; reported setup/hold errors zero | Complete unconstrained/external-path qualification is not established |
| S10 System Integration | Main GUI/transport manifest; Lab reports; COMMIT/RELEASE and stored references | Existing host/FPGA laboratory integration, full-chain and stage-injection workflows, source-specific display semantics | PC-derived CFAR display is not direct full-chain CFAR readback; interrupted-session recovery limitation retained |
| S11 Physical Board Testing | Main nine-case journals plus imported Lab captures and independent archive checks | Main: nine finite CPI, 36,864 Power cells, 56 records. Lab: finite stage tests and archived Fixed equality, including MTI stationary/slow/moving and grouping-capacity evidence | Stage injection differs from continuous full-chain operation; no general operational Pd/Pfa, real-time, RF/ADC or environmental acceptance |

Relevant sources are engineering/FULL-IP-UART-GUI-INTEGRATION-20261112.md, engineering/AUTO-LAB-v0.3-REPORT.md, engineering/STAGE-LAB-v0.2-IMPLEMENTATION-REPORT.md, engineering/STAGE-LAB-v0.2.1-GUI-REPORT.md and their pinned manifests. New evidence registers reside in engineering/audit/.

## Preserved outcomes and open items

- REQ-RNG-03: unchanged FAIL, 4/8 mandatory cases, required 8/8. Development resolution characterizations do not replace this criterion.
- Fixed-Point statistical qualification: OPEN. No proposed approval below converts it to PASS.
- S03 accepted software Pfa/Pd: retained in its approved population and numerical configuration. The audit recalculated archived aggregates only.
- Lab statistical mechanism check: three noise CPI and three target CPI, CFAR/Grouping injection scope. It is not end-to-end IQ statistical acceptance.
- Full intermediate observability, maximum-capacity/no-drop behavior across complete final transport, ICD finality, IP numerical-baseline relationship, external timing and delivery reproducibility remain separately tracked.
- Genuine past failures, excerpts, unsigned reviews and old decisions remain intact.

## Read-only validator limitation

stage_lab/verify_auto_quality.py is not a read-only validator: its source contains writes to case JSON, suite.json, reports and GUI captures. stage_lab/verify_files.py also performs live application/programming operations. Neither was executed. Archive verification used standalone reading/hash/decoding calculations and did not import project models or test runners. This is a workflow restriction, not a new claim that the historical test results failed.

## Engineer disposition requested

The next necessary decision is whether to recognize configuration (2) above as the project's **as-built laboratory implementation**, with its exact hashes, evidence and stated exclusions, alongside the preserved historical selected-C baseline. Recommended disposition: accept the documented laboratory accomplishment within its tested scope, retain every listed open item, and authorize preparation of individual stage-gate closure records for review.

This first disposition does not itself close S05–S11, waive any requirement, replace an approved baseline, approve the ICD, or authorize tests/programming/merge/publication. Separate gate proposals must reference this configuration and state their carryovers.

## Progress and repository readiness

Documentation recovery has materially advanced; it has not increased engineering progress. The technical work described was already performed. No new project completion percentage is inferred.

Status: READY_FOR_AS_BUILT_ENGINEER_DISPOSITION, not READY_FOR_GITHUB_REVIEW or final S12 acceptance. Remaining documentary tasks include final approval records, current-status projections, disclosure/redistribution decisions and final packaging. Do not reopen accepted technical work merely to reproduce an already sufficient retained result.

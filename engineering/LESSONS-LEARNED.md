# Lessons Learned | AX309-RDSP-001

## LL-AX309-001 — Requirement-driven validation continuity from reference model to hardware

**Status:** Accepted project lesson; input to the next Radar Design Plugin workflow revision.
**Source:** AX309-RDSP-001 S02–S05 engineering experience.
**Scope:** Process lesson only. It does not change any approved project requirement, numeric contract, acceptance limit or gate decision.

### Lesson

Every approved system requirement must be converted, before reference-model qualification, into one or more quantitative test scenarios with a frozen input definition, measurable acceptance rule, expected output and explicit PASS/FAIL/INCONCLUSIVE disposition.

The same immutable scenario corpus must then be replayed through each implementation layer:

1. Floating-point functional reference.
2. Integer/Fraction oracle and Fixed-Point model.
3. RTL simulation.
4. Synthesis and timing/resource analysis.
5. FPGA/board verification where applicable.

A new model must not receive a separately generated, unlinked test set merely because it is a new implementation. If an additional vector is technically necessary, it must have a documented requirement link, a reason for addition, a stable ID and a versioned manifest. It supplements the common corpus; it does not replace or silently alter it.

### Evidence and limitation from this project

S03 provides a validated Float reference for its approved scope. S04 C03–C05 provide independent integer oracles and deterministic bit-true evidence. C06R2 reports 16/16 bounded numerical CPI PASS for its two C01-approved populations. Those results do not establish full requirement coverage: REQ-SCR-01 and REQ-RNG-03 remain OPEN, and the 16-CPI C06R2 campaign is not a statistical Pfa/Pd qualification. RTL equivalence and hardware feasibility are separate S05/S08/S09 activities.

### Required plugin workflow

The Radar Design Plugin should generate and maintain a Requirement-to-Test Traceability Matrix with at least:

- Requirement ID and approved revision.
- Quantitative acceptance criterion and units.
- Test scenario ID, version, profile and parameter envelope.
- Frozen input manifest, seed/source version and SHA-256.
- Expected Float-reference output and its version/hash.
- Float execution result and measured metrics.
- Expected integer/Fraction oracle output and its version/hash.
- Fixed-Point output and exact/quantitative Float-to-Fixed differences.
- RTL output and bit-true comparison result.
- PASS/FAIL/INCONCLUSIVE/STRESS_ONLY disposition at each applicable layer.
- Evidence links, execution environment, owner and approval state.

### Workflow controls

- A requirement cannot become PASS because a generic model or a few unrelated tests exist.
- Test denominators and scenario membership are frozen before execution; no silent deletion, replacement or post-hoc threshold changes.
- The common corpus is immutable after approval. New scenarios are versioned additions with explicit requirement traceability.
- Float-to-Fixed and Fixed-to-RTL comparisons use the same source vectors and scenario IDs.
- Statistical performance, deterministic arithmetic correctness, RTL equivalence and hardware feasibility are separate claims with separate evidence.
- Missing source profiles, undefined acceptance metrics or unsupported physical assumptions remain OPEN; the plugin must not invent them.

### Application to AX309-RDSP-001

Carry this lesson into S05 testbench architecture. Reuse the approved C03–C05 oracle interfaces and C06R2 input corpus where scope permits. Add each RTL vector by stable ID and preserve its originating Float/Fixed source. Do not rerun C06R2 CPI. REQ-SCR-01 and REQ-RNG-03 require separately approved scenario definitions and are not implicitly covered by the current corpus.

## LL-AX309-002 — Stage exit with explicit open-item carryover is not requirement acceptance

**Status:** Accepted project lesson; input to the next Radar Design Plugin workflow revision.
**Source:** AX309-RDSP-001 S04-to-S05 engineer disposition, 2026-11-12.
**Scope:** Process and traceability lesson. It does not change any technical requirement or acceptance threshold.

### Lesson

A system engineer may authorize a stage transition while retaining failed or incomplete technical obligations for later project evaluation. The project records must represent the administrative gate decision separately from each requirement's technical disposition.

In this project:
- Gate-S04 was closed by explicit engineer disposition to permit S05.
- REQ-RNG-03 remained FAIL at 4/8 mandatory scenarios; its 8/8 criterion was not changed.
- Fixed-Point statistical performance remained OPEN; deterministic evidence was not relabelled as statistical qualification.
- Both items were transferred to a versioned final-evaluation carryover register.

### Required plugin workflow

The Radar Design Plugin should maintain two independent state fields:
1. **Technical disposition:** PASS, FAIL, OPEN or INCONCLUSIVE, tied to the exact approved criterion and evidence.
2. **Gate/stage disposition:** OPEN, CLOSED, or CLOSED_WITH_OPEN_ITEMS, tied to an explicit authorized decision.

When a gate is closed with open items, the plugin must:
- Preserve the original test denominator, result, acceptance rule and evidence hash.
- Create a carryover record with a named next review point and final-report obligation.
- Remove the carried item only from the current stage's entry blockers; do not remove it from requirement traceability.
- Prevent any automatic conversion of FAIL or OPEN to PASS.
- Show the carried items in final project evaluation and the final report.

### Application to AX309-RDSP-001

The authoritative carryover record is engineering/S04-OPEN-ITEMS-CARRYOVER-v1.0.json; the engineer decision is decisions/S04-C08-S05-TRANSITION-2026-11-12.json. S05 may proceed, but neither REQ-RNG-03 nor Fixed-Point statistical performance is technically accepted by this transition.

## LL-AX309-003 — RAM inference and output-list policy are independent design controls

**Status:** Accepted S05 implementation lesson; candidate for Radar Design Plugin workflow revision.
**Source:** S05 grouping_8conn ISim/XST artifact and the frozen S02 REQ-LIST-01.

The synthesis resource cost of a small logical table can be dominated by its inferred read/write ports. The initial grouping implementation with multiply addressed parent/statistic memories produced excessive distributed-logic resource use. Refactoring both memories into single synchronous read/write port structures enabled XST block RAM inference while preserving bit-identical output records against the unchanged C05 BFS reference and independent union-find.

The final standalone synthesis shows 6 BRAM, 4,034 LUT, 1,727 registers, 0 DSP48A1 and 0 warnings, not a whole-system fit. The downstream scanner separately uses 12 BRAM; the project must check the actual combined memory lifetime and target capacity before claiming a hardware architecture fit.

**Plugin workflow implication:** Require each proposed streaming RTL memory to state its depth/width, number of reads and writes per cycle, inferred memory technology and resource budgets; inspect XST warnings and actual macro usage before reporting synthesis feasibility. Separately, an internal geometric bound or safe overflow diagnostic must not be treated as approval of an externally visible record-list capacity or selection policy when that decision is still open.

**Evidence:** engineering/S05-GROUPING-EVIDENCE-MANIFEST-v0.1.json, engineering/S05-GROUPING-RTL-VERIFICATION-REPORT-v0.1.md, engineering/S05-GROUPING-TRACEABILITY-v0.1.json. No architecture C/Frozen Fixed-Point change and no REQ-RNG-03 retest were made.


## LL-AX309-003 — Detection-domain boundaries must follow signal support, not only array shape

**Status:** Accepted engineering observation from S05 CUT geometry audit and connected RTL qualification, 2026-11-12.

The 128x32 stored power-map shape alone geometrically permits 3172 nonwrapped 7x7 CA-CFAR CUTs. However, the 16-sample echo in a 128-sample acquisition has complete-support delay indices 0..112. The approved S02 engineering contract requires the full 7x7 range-side CFAR window to remain in that support, restricting CUTs to r=3..109 and b=3..28: 2782 CUTs. The matched filter computes a full 143-output convolution and extracts 128 aligned outputs; it does not produce only 113 outputs. Treating allocated array dimensions as the acceptance domain would silently change the Pfa denominator and detector coverage.

The connected CFAR–Grouping test additionally showed that the scanner and grouping engines use distinct completion events. Fatal grouping overflow can leave the scanner stalled; a later system controller must explicitly reset/abort both engines while preserving the reported invalid-frame status to the host.

**Plugin design implication:** track three independent quantities: stored map shape, physically supported/approved signal-valid domain, and validated CUT domain. Require approved evidence before expanding a CUT region, and require a documented fatal-frame abort protocol when joining valid/ready blocks. Neither module-level oracle equivalence nor connected-subsystem XST fit proves full radar-chain performance or resource fit.

**Evidence:** engineering/S05-CUT-GEOMETRY-AUDIT-v0.1.md; engineering/S05-CFAR-GROUPING-INTEGRATION-REPORT-v0.1.md. No S04 carryover disposition is changed.

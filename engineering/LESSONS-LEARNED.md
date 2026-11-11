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

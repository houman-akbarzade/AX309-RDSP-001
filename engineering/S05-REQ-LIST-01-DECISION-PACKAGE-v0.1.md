# AX309-RDSP-001 | S05 REQ-LIST-01 Engineer Decision Package v0.1

**Status: AWAITING SYSTEM-ENGINEER DECISION.** Baseline bbcac98. No numerical architecture or approved acceptance criterion changed.

## 1. Approved contract

The approved S02 requirement matrix (REQ-LIST-01) and S02-D22 require variable-length target records with count and stable IDs, explicit overflow reporting, deterministic selection and no silent discard. The physical output capacity and what to do on overflow were expressly deferred to S05.

The frozen valid detection grid is 107x26. Its maximum independent 8-connected component count is ceil(107/2)*ceil(26/2)=54*13=702. Current grouping_8conn already reserves at most 702 internal labels (10-bit IDs) and emits each detected component in deterministic range/signed-Doppler order through valid/ready. **702 is the proven component bound, not an approved external list capacity or target-detection guarantee.**

## 2. Explicit options for engineering decision

| Option | List limit | Over-limit behavior | Engineering consequences |
|---|---|---|---|
| **A (recommended)** | Complete variable-length list, 0..702 components; no lower cap | No normal truncation. Any impossible internal/protocol overflow invalidates the entire CPI, with explicit fault and no successful output list | Closest to approved C05 oracle, no new top-K selector, existing 702-label engine reusable |
| B | Engineer-approved K < 702 | Deterministic top-K by integer stored-power and approved tie order; report dropped count | Needs new selection RTL, memory/transport handling and fresh oracle qualification; may discard detections |
| C | Engineer-approved K < 702 | Entire CPI invalid if components exceed K, report fault/count; emit zero valid records | Simpler than top-K but rejects legitimate many-cluster frames; needs explicit engineer approval |

**Recommended approval: Option A.** Stream all recorded clusters, with stable record IDs, a final committed record count and CPI ID. The receiving host must treat records as provisional until explicit successful completion; on a fatal fault, it discards records from that CPI and receives an invalid/status message. An empty successful CPI (count=0) is distinct from a failed CPI.

No external record buffer is needed if each record is consumed through back-pressure. The exact UART framing, buffering and host status/commit schema remain separate S05 ICD obligations; S02 already limits UART payload to 512 bytes.

The RTL's tested fail-stop internal capacity diagnostic is **not** automatic acceptance of REQ-LIST-01. Even if Option A is approved, requirement PASS still needs output-count, record-ID, maximum-capacity, invalidation, recovery and host serialization tests. The existing 11 independent grouping cases and 5 connected cases are only partial evidence.

## 3. One engineering decision requested

**Approve Option A:** maximum external component-list capacity 702, no truncation/selection in normal operation, and deterministic whole-CPI rejection with explicit fault status upon an impossible capacity/protocol/internal overflow?

Until approved, **REQ-LIST-01 = OPEN_ENGINEERING_DECISION_REQUIRED**. The Frame Controller must not hard-code an unapproved smaller capacity, silently select targets or treat internal fail-stop as full requirement PASS.

**References:** engineering/S02-requirements-matrix-APPROVED-AMENDMENT-v1.1.json; engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json; decisions/S02-decisions.json S02-D22; rtl/grouping/grouping_8conn.v; engineering/S05-GROUPING-RTL-VERIFICATION-REPORT-v0.1.md.

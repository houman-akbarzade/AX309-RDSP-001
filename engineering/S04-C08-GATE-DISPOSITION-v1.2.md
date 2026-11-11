# AX309-RDSP-001 | S04-C08 Engineer Disposition v1.2

**Decision date:** 2026-11-12
**Authority:** Project system engineer
**Disposition:** CLOSED BY ENGINEER DECISION WITH OPEN ITEMS TRANSFERRED
**Next stage:** S05 RTL implementation

## 1. Decision

The system engineer explicitly authorizes S04 exit and S05 commencement without changing the technical result of REQ-RNG-03 and without claiming statistical Fixed-Point performance acceptance.

This is a stage-transition decision. It is **not** a technical waiver that changes a failed requirement to PASS, and it does not declare the outstanding Fixed-Point statistical qualification complete.

## 2. Preserved technical dispositions

| Item | Preserved technical result | Final-evaluation disposition |
|---|---|---|
| REQ-RNG-03 | **FAIL**; 4 of 8 mandatory cases passed; 4 failed; 50% | Carried open |
| S04-C02-RISK-PERFORMANCE | **OPEN**; Fixed-Point statistical performance qualification incomplete | Carried open |
| REQ-SCR-01 | PASS within its explicitly approved 11-case scope | Accepted within scope |

REQ-RNG-03 retains its original 8/8 mandatory acceptance criterion. Its measured 4/8 result and the associated evidence remain unchanged. No REQ-RNG-03 retest, CPI reprocessing, threshold adjustment, algorithm retuning, architecture change or Fixed-Point contract change is authorized or performed under this decision.

The statistical Fixed-Point performance item remains OPEN. Deterministic C06 evidence is not relabelled as statistical Pfa/Pd qualification. No statistical campaign is authorized or performed under this decision.

## 3. Gate-S04 exit

C08 is completed by this explicit engineer disposition. Gate-S04 is therefore **CLOSED_BY_ENGINEER_DISPOSITION_WITH_OPEN_ITEMS**.

The two unresolved items above are removed from the list of blockers to S05 entry and transferred to the project final-evaluation carryover register:

- engineering/S04-OPEN-ITEMS-CARRYOVER-v1.0.json

The approved S02 requirement baseline and the REQ-RNG-03 acceptance criterion are not edited. The carryover register supplements the approved traceability baseline; it does not replace it.

S04 progress is recorded as 8/8 gate criteria complete (100%). This records completion of the stage-exit decision, not 100% technical satisfaction of every requirement. Overall stage-weighted project progress is 4/12 = 33.33%.

## 4. S05 authorization and constraints

S05 RTL implementation is authorized to proceed.

The following remain frozen:

- Architecture C.
- Approved Fixed-Point widths, signedness, binary-point positions and narrowing rules.
- RNE and saturation behaviour.
- CFAR alpha and strict comparison rule.
- FFT stage shifts [0,1,0,1,1].

S05 may use RTL simulation and synthesis for implementation verification. No REQ-RNG-03 acceptance retest, statistical Fixed-Point performance campaign, or board/hardware qualification is authorized by this decision.

## 5. Traceability and lessons

- Decision record: decisions/S04-C08-S05-TRANSITION-2026-11-12.json
- Carryover register: engineering/S04-OPEN-ITEMS-CARRYOVER-v1.0.json
- REQ-RNG-03 evidence: engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-RESULTS-v1.0.json
- Prior Gate disposition: engineering/S04-C08-GATE-DISPOSITION-v1.1.md
- Lessons learned: engineering/LESSONS-LEARNED.md, LL-AX309-002

**Final Gate decision: S04 CLOSED WITH EXPLICIT OPEN-ITEM CARRYOVER; S05 AUTHORIZED. No technical PASS is created for either carried item.**

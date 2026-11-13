# S05 Architecture and Interfaces: review entry

Status: REVIEW_ALLOWED / NOT_FINAL_GATE_ACCEPTANCE. Entry is already authorized by decisions/S04-C08-S05-TRANSITION-2026-11-12.json. New statistical evidence is reviewed in S04-STATISTICAL-INDEPENDENT-REVIEW-20261114.md; no need to hold read-only S05 review for the running hardware campaign.

| S05 subject | Evidence starting point | Review/decision still required |
|---|---|---|
| Numeric architecture | engineering/S05-RTL-ARCHITECTURE-v0.1.md; final FFT-IP sources and as-built archived reports | Preserve historical DIT architecture; separately approve as-built FFT-IP numeric configuration and correspondence |
| Interfaces and formats | engineering/S05-UART-ICD-v1.0-ENGINEER-REVIEW.md; session R1 addenda; pc_link codec/IQ/board driver | Reconcile actual session/epoch/frame semantics, widths, scale, flags and stage schemas with candidate ICD |
| Resource/data lifetime | S05 resource lifetime, symbolic evidence and 702-component proof | Match actual buffers, backpressure and complete target-list behavior |
| Clock/reset/constraints | Final IP implementation logs, RTL/UCF | Confirm applied clock domain and external/unconstrained limitations |
| UART/GUI laboratory mission | Owner decisions, historical development and hardware evidence | Retain lab CPI stop-and-wait scope; do not infer continuous real-time operational acceptance |
| Observability | Stage Lab and archived full-chain Power/input/record captures | Distinguish separate stage images from simultaneous full-chain observability; no false seven-stage claim |
| Final Gate | Explicit owner stage decision | No final S05 Gate record located by prior audit; do not infer signature from PASS |

S05 architecture and interface acceptance is distinct from S06 RTL, S07 simulation, S08 synthesis, S09 STA, S10 integration and S11 physical acceptance. Review these stages sequentially as directed by the engineer. No implementation or test change is authorized by this entry document.

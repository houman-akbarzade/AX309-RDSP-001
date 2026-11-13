# Current Requirement Evidence Audit — v3

REQ-RNG-03 has an engineer-approved Power-only scope amendment. Its quantitative acceptance definition remains pending. Other21 requirement rows are unchanged from v2. Original requirement matrices/results are preserved.

| Requirement | Scope-specific verdict | Supported scope | Limitation |
|---|---|---|---|
| REQ-IO-01 | EVIDENCE_SUFFICIENT | Finite board IQ byte readback and finite Lab input-word hashes | Complete negative-case qualification and final transport acceptance not inferred. |
| REQ-LFM-01 | EVIDENCE_SUFFICIENT | S03 chirp support/phase, direct MF and accepted reference scope | Reference-model scope; not a new hardware waveform/population acceptance. |
| REQ-SNR-01 | EVIDENCE_SUFFICIENT | S03 SNR definition and real/imag noise-variance tests | Model convention verified; do not transfer population claims to physical hardware. |
| REQ-RNG-01 | EVIDENCE_SUFFICIENT | S03 boundary MF across all 113 contained integer delays | This is full-echo containment and reference indexing, not two-target resolution. |
| REQ-MF-01 | EVIDENCE_SUFFICIENT | S03 zero-error MF/index tests and finite Lab Fixed equality | No exhaustive physical-input-space acceptance inferred. |
| REQ-RNG-02 | EVIDENCE_INCOMPLETE | S03 fixed-scene range scoring and finite board associations | One accepted fixed scene does not establish all population/scene range-accuracy conditions. |
| REQ-RNG-03 | CRITERION_NOT_DEFINED | Engineer-approved Power-only observation point; exact operational acceptance predicate pending | Historical final-record result remains FAIL4/8. Retained Float/C02 Power supports8/8 under proposed two-local-peak criterion and2/8 under illustrative3dB criterion. Neither criterion nor new PASS is approved. |
| REQ-MTI-01 | EVIDENCE_SUFFICIENT | S03 DC/Nyquist tests and finite stationary/slow/moving Lab evidence | Scoped functional/numeric result; blanket physical suppression qualification not inferred. |
| REQ-DOP-01 | EVIDENCE_SUFFICIENT | S03 signed/on/off-bin/tie reference tests and finite FFT Lab equality | Accuracy claims restricted to declared eligible isolated-target/reference cases. |
| REQ-CFAR-01 | EVIDENCE_SUFFICIENT | S03 geometry/strict comparison/manual 40-cell sum; finite Lab decision equality | Finite verified configurations; not general statistical acceptance. |
| REQ-CFAR-02 | EVIDENCE_SUFFICIENT | Approved S03 noise-only N=20000 Pfa aggregate independently recalculated | Software model only; Fixed-Point/IP/physical statistical qualification remains OPEN. |
| REQ-PD-01 | EVIDENCE_SUFFICIENT | Approved S03 fixed-scene N=1000 Pd aggregate independently checked | SNR20 single on-bin no-clutter model; full original IQ/power arrays not archived. |
| REQ-SCR-01 | EVIDENCE_SUFFICIENT | Explicit owner-accepted eleven-case S04 scope | Accepted historical eleven-case scope; not automatically physical/IP statistical acceptance. |
| REQ-DET-01 | EVIDENCE_SUFFICIENT | S03 grouping/tie and one-to-one rules; finite Lab/board records | Equality to stored references in measured cases; not final all-scenario detection acceptance. |
| REQ-MATCH-01 | EVIDENCE_SUFFICIENT | S03 one-to-one assignment unit evidence | Association gates are distinct from estimator acceptance tolerances. |
| REQ-POWER-01 | EVIDENCE_SUFFICIENT | Finite archived Power Fixed equality and nine-case integrated board records | Scaling/configuration-specific archived comparisons; no unbounded-input claim. |
| REQ-LIST-01 | EVIDENCE_INCOMPLETE | 702 logical policy approved; finite capacity and board records retained | Full final transport maximum-capacity/error/recovery acceptance remains OPEN. |
| REQ-OBS-01 | EVIDENCE_INCOMPLETE | Per-stage Lab observability implemented and archived | Separate injection images are not proof of every finalized seven-output contract in one continuous full-chain image. |
| REQ-UART-01 | EVIDENCE_INCOMPLETE | Finite protocol ISim and real board COMMIT/RELEASE evidence | New-SID interrupted-session recovery unsupported; final ICD disposition pending. |
| REQ-RES-01 | EVIDENCE_INCOMPLETE | Final IP full-chain MAP fit and applied 20ns internal timing evidence | Complete external/unconstrained-path review and final numeric configuration acceptance remain open. |
| REQ-TIME-01 | EVIDENCE_INCOMPLETE | Host transfer/wait/elapsed timings recorded in retained board journals | Host timings alone do not establish every required FPGA cycle-counter/rollover measurement. |
| REQ-EVID-01 | EVIDENCE_INCOMPLETE | Physical full-chain and separate block evidence exist | Final requirement-by-configuration and Gate acceptance still need reconciliation. |

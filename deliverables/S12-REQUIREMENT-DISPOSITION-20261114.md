# S12 requirement disposition for private laboratory handover

The historical 22-row audit `engineering/audit/REQUIREMENTS-CURRENT-AUDIT-v4.json` predates the individual S05–S11 approvals. Its EVIDENCE_SUFFICIENT means sufficient only in the stated bounded scope. The original contract and all historic results remain available.

| Requirements | Delivery disposition |
|---|---|
| REQ-IO-01, LFM-01, SNR-01, RNG-01, MF-01, MTI-01, DOP-01, CFAR-01, SCR-01, DET-01, MATCH-01, POWER-01 | Accepted bounded reference, RTL, or physical evidence per source Gate decisions; no all-population qualification claim. |
| REQ-RNG-02, PD-01 | Design targets, not separately binding physical S11 criteria. Pd board 1000/1000 for the tested population. |
| REQ-RNG-03 | Final-image board Power 8/8 PASS under current criterion. Historical clustering/final-record 4/8 preserved. |
| REQ-CFAR-02 | S11 approved substitute: fixed FFT-IP model 20000 CPI 95% EB upper 0.0014529047 <= 0.0015. Physical 1174/20000 incomplete, formal physical PASS not demonstrated. |
| REQ-LIST-01 | 702/702 records physically tested on separate Grouping image; full-chain finite transfers. No 702-record final-image end-to-end claim. |
| REQ-OBS-01, EVID-01 | Six distinct stage readbacks plus IQ and full-chain physical evidence in bounded configurations. No universal bitwise equivalence. |
| REQ-UART-01 | Finite physical malformed/bootstrap/recovery checks and integration simulation; exhaustive active fault matrix not claimed. |
| REQ-RES-01 | Selected bitstream resource fit and 50 MHz routed STA accepted by S08/S09; no revised hardware image. |
| REQ-TIME-01 | ISE STA, board host/UART timings, and separately reported RTL/IP simulation cycle count under approved S11 method. No physical cycle counter or realtime deadline. |

The S11 laboratory Gate is closed with explicit exceptions, not with unqualified PASS of every historical method. The scoped amendments in `engineering/S02-S11-LAB-PFA-TIMING-LIMITED-AMENDMENT-20261114.md` and Gate records control the current interpretation. S12 acceptance covers only the stated private laboratory handover.

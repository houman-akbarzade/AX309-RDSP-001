# AX309-RDSP-001 — S02 Pfa/Pd change-control screening v0.1

**STATUS: NO_NUMERIC_AMENDMENT_JUSTIFIED.** This is a change-control proposal/rejection, NOT an adopted S02 v1.2 performance revision.

| Performance item | Existing approved limit | Proposed limit | Rationale |
|---|---|---|---|
| Pfa noise-only per valid CUT design target | 0.001 | UNCHANGED 0.001 | No independent valid detector-performance Pfa FAIL exists |
| Pfa binding one-sided 95% upper limit | U<=0.0015 (4096 fresh CPI) | UNCHANGED U<=0.0015 | Failed spatial-transfer check addresses METHOD validity, not this limit |
| Pd single-target, SNR20, no clutter | >=0.90 DESIGN GOAL, not binding yet | UNCHANGED >=0.90 DESIGN GOAL | No valid independent Pd study or CI |

**Numeric justification:** The strongest post-alpha descriptive diagnostic is raw observed rate 0.0010033284563713157 (4096 CPI, 2782 CUT/CPI), but its independently predeclared spatial transfer requirement FAILed at |z|=43.5754456676879 >2.5758293035489004, and it has provenance overlap with earlier exploratory data. No main Pfa confidence limit was computed under an authorized acceptance protocol. The strongest v1.1 method qualification passed 15/15 *synthetic count* models and worst Wilson lower coverage 0.9515520667104338; it is not radar Pfa. The only SNR20 three-target deterministic case matched 3/3 targets, with seven extra detections; this cannot estimate Pd or establish failure to reach 0.9.

**Engineer-facing disposition:** Approve **NO CHANGE** to numerical Pfa/Pd limits. Maintain Pfa final trial BLOCKED, Pd independent population trial NOT_RUN, Gate-S03 OPEN, progress 75% and 22.9167%. Continue a separate methodology amendment/research track to address 2D CA-CFAR spatial anisotropy and prospective sample-based transfer, rather than weakening the detector-performance requirement without evidence.

Only if a future **fresh, method-valid, independent, preregistered** Pfa OR Pd performance study fails a numerical limit may a new one-criterion-only amendment quantify the minimum relaxation and require a new independent confirmation dataset.

Complete evidence inventory, data provenance, numerical fields and hashes are in the companion audit JSON and the S03 audit report.

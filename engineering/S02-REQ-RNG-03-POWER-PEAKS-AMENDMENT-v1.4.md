# REQ-RNG-03: approved Power-peak acceptance, limited S02 v1.4 amendment

Engineer authority: current exact message AX309-20261113-RNG03-PEAKS-STAT-engineer, responding to AX309-20261113-RNG03-POWER-SCOPE-agent. Decision REQ-RNG-03-POWER-PEAKS-ACCEPTANCE-001. Recording date: 2026-11-13.

This limited amendment completes the Power-only v1.3 amendment. The original S02 v1.2 files and all historical decisions remain immutable; the other 21 requirements are unchanged.

For the existing eight mandatory noise-free equal-amplitude two-target cases (4/5-sample separation; relative phase 0/90/180/270 degrees; natural Doppler bin4), REQ-RNG-03 is satisfied by two distinct strict local maxima in the Power range profile before CFAR/Grouping. Each maximum must lie within one range sample of its corresponding truth. Peaks must be distinct and ordered; at least one intervening sample must have power strictly below both. No additional 3dB valley criterion applies.

Separate CFAR components and separate final cluster records are not conditions of this requirement. Independent CFAR/record/power arithmetic requirements remain binding.

## Reassessment and acceptance scope

Read-only re-evaluation of original archived arrays gives Float PASS8/8 and historical selected-C/C02 Fixed PASS8/8. See engineering/audit/REQ-RNG-03-POWER-APPROVED-REASSESSMENT-v1.0.json for source hashes, exact method and all sixteen per-model rows. This is an accepted criterion applied to existing evidence, not a new experiment.

The revised requirement is PASS in this archived model/test population. No transfer to the final FFT-IP implementation, physical board, noisy target populations, statistical Pd/Pfa or general overflow qualification is asserted. The historical final-record result remains FAIL4/8 under its historical criterion.

S03 approval and S04 owner closure remain unchanged. No model, algorithm, testbench, numeric format, threshold or approved historical result is edited.

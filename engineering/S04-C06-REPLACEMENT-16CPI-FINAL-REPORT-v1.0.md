# AX309-RDSP-001 | S04-C06 Replacement 16-CPI Final Report v1.0

**Disposition:** PASS for the bounded A–E replacement execution; independent sign-off pending.
**Official criterion state:** C06 remains OPEN pending independent review of this evidence.
**Gate recommendation:** Keep Gate-S04 OPEN / NO-GO because REQ-SCR-01 and REQ-RNG-03 remain binding blockers.

## 1. Executive result

The separately authorized replacement campaign completed all 16 prelocked CPI exactly once. All 16 were classified PASS: 8/8 NOISE_ONLY_UNIT at g=5 and 8/8 SINGLE_TARGET_REFERENCE_LIKE_LAB at g=1. There were no FAIL or INCONCLUSIVE results. No CPI was removed, replaced, or retried.

This is bounded deterministic/numerical evidence under approved criteria A–E. It is not a statistical Pfa/Pd campaign and does not close the separate SCR or two-target requirements.

| Profile | g | Fixed denominator | PASS | FAIL | INCONCLUSIVE |
|---|---:|---:|---:|---:|---:|
| NOISE_ONLY_UNIT | 5 | 8 | 8 | 0 | 0 |
| SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 8 | 8 | 0 | 0 |
| **Total** | — | **16** | **16** | **0** | **0** |

## 2. Execution lock and identity

- Replacement campaign: C06-REPLACEMENT-2026-11-11.
- Prelock commit: 631c65c; prelock SHA-256: fb2adccd5365f60ceb0509de6121d9f97fe4ca9465bfc6173c3c18cf80c780ed.
- Input/package/runner lock commit: 3842f6af6b8beb567b1896ec5600b885dcc32f2a.
- Repaired Runner source accepted at commit 857c7909dd980021fdf7bcb6e9186db5ae3b493f.
- Replacement wrapper SHA-256: 68d405193e88f03b205f0a951a74e3ba29fffb89478d14fbeb143348ea341e40.
- Input manifest SHA-256: 8d8d5ad4037ac905a773b84bd3e96a29e4e644064903a2d28a5d57eb538974e0.
- Fixed denominator: 8+8=16; 16 unique CPI IDs and 16 unique child seeds.
- Manifest filename handling: the pinned preparation script emitted its standard C06-16CPI-INPUT-MANIFEST-v1.0.json filename; an exact byte-for-byte copy was preserved under the replacement manifest filename declared in the prelock. Both files have the same SHA-256; no manifest content or CPI input was altered.
- Seed masters: 83111001 (noise), 83111002 (lab); no overlap with prior C06 child seeds or accepted S03 seed masters.
- A–E criteria decision: decisions/S04-C06-CRITERIA-INDEPENDENT-DECISION-v1.0.md; no criterion or cap was changed.

### Per-CPI result

| CPI ID | Profile | g | Child seed | Status | FFT5 MAX |
|---|---|---:|---:|---|---:|
| C06R2-NOISE-001 | NOISE_ONLY_UNIT | 5 | 2012805448334265449 | PASS | 0.0110939817 |
| C06R2-NOISE-002 | NOISE_ONLY_UNIT | 5 | 18162294254475347580 | PASS | 0.0114935342 |
| C06R2-NOISE-003 | NOISE_ONLY_UNIT | 5 | 3979726421365413046 | PASS | 0.0116090574 |
| C06R2-NOISE-004 | NOISE_ONLY_UNIT | 5 | 6518530905334955677 | PASS | 0.0133372306 |
| C06R2-NOISE-005 | NOISE_ONLY_UNIT | 5 | 8207257837617807726 | PASS | 0.0104019683 |
| C06R2-NOISE-006 | NOISE_ONLY_UNIT | 5 | 8856890129862335181 | PASS | 0.0105292924 |
| C06R2-NOISE-007 | NOISE_ONLY_UNIT | 5 | 12221500842114680316 | PASS | 0.0108187685 |
| C06R2-NOISE-008 | NOISE_ONLY_UNIT | 5 | 15118745826006173506 | PASS | 0.01125379 |
| C06R2-LAB-001 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 13833116037735353598 | PASS | 0.0040465573 |
| C06R2-LAB-002 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 7683962101233347255 | PASS | 0.00400705428 |
| C06R2-LAB-003 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 12386715436824358369 | PASS | 0.00424493289 |
| C06R2-LAB-004 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 4164276440279276488 | PASS | 0.0040246859 |
| C06R2-LAB-005 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 1870107050591730872 | PASS | 0.00404182096 |
| C06R2-LAB-006 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 5480793303136962092 | PASS | 0.00394997312 |
| C06R2-LAB-007 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 13008896790343389047 | PASS | 0.00434850507 |
| C06R2-LAB-008 | SINGLE_TARGET_REFERENCE_LIKE_LAB | 1 | 4093538051797926354 | PASS | 0.00416358487 |

## 3. A — Stagewise numerical safety ceilings

All 112 CPI-stage checks (16 CPI × 7 stages) passed. MAX and RMS were both checked against the approved stage ceiling for the applicable gain. Values below are the worst observed across the eight CPIs in each profile. Units are original complex Float amplitude.

| Stage | g=1 cap | g=1 worst MAX | g=1 worst RMS | g=5 cap | g=5 worst MAX | g=5 worst RMS |
|---|---:|---:|---:|---:|---:|---:|
| MF | 0.00074 | 0.000173641073 | 5.10810777e-05 | 0.00366 | 0.000814809971 | 0.000257243288 |
| MTI | 0.00147 | 0.000230096306 | 7.14947217e-05 | 0.00731 | 0.00118580082 | 0.000363533371 |
| FFT1 | 0.00468 | 0.000336763716 | 0.000102015025 | 0.02337 | 0.00190576485 | 0.000551934465 |
| FFT2 | 0.01286 | 0.000557300819 | 0.000149868679 | 0.06428 | 0.00286607639 | 0.000833179778 |
| FFT3 | 0.03267 | 0.00116149199 | 0.000217416616 | 0.16335 | 0.00425449706 | 0.00124910308 |
| FFT4 | 0.07926 | 0.00207272359 | 0.00031256636 | 0.39629 | 0.00715807584 | 0.00184521686 |
| FFT5 | 0.18636 | 0.00434850507 | 0.000459972893 | 0.93177 | 0.0133372306 | 0.00269286964 |

**A result: PASS.** No stage exceeded its approved MAX or RMS ceiling. These ceilings remain deterministic numerical safety screens, not radar-performance or statistical limits.

## 4. B — Exact independent integer-oracle equality

- Power cells compared: 65,536 (4,096 per CPI); mismatches: 0.
- Valid CFAR CUTs compared: 44,512 (2,782 per CPI); mismatches: 0.
- Training-cell comparisons: 1,780,480 (40 per CUT); mismatches: 0.
- Alarm, exact integer margin, cluster membership, peak/tie selection and complete target-record mismatches: 0.
- Independent stage oracle mismatch count: 0 for every CPI.

**B result: PASS.** The independent C03 integer/rational oracle and C05 independent grouping oracle matched the selected-C implementation throughout the replacement set.

## 5. C — Float/Fixed CFAR margin policy

- Fixed denominator: 2,782 CUTs per CPI; 44,512 total CUT records.
- Float/Fixed changed CUTs: 0 (both directions).
- Ambiguous changed CUTs: 0.
- Changed CUTs outside the approved uncertainty envelope: 0.
- Exact Fixed-vs-Oracle comparisons remained mandatory and had zero mismatches.

**C result: PASS.** No Float/Fixed alarm disagreement occurred; the repaired CUT-local uncertainty computation completed for every CPI.

## 6. D — Peak and historical exact-tie classification

- New replacement CPI peak-coordinate symmetric differences: 0.
- New replacement CPI cluster/target-record mismatches: 0.
- The two mandatory historical phase-interference vectors were replayed separately and both satisfied the approved narrow exception conditions.

| Historical vector | Float exact-tie power at (3,20)/(4,20) | Fixed stored powers | Fixed winner | Classification |
|---|---:|---:|---|---|
| g1:phase_interference | 2003.740740417848 / 2003.740740417848 | 33612372401 / 33612427349 | (4,20) | FLOAT_REFERENCE_EXACT_TIE_SPLIT_BY_QUANTIZATION |
| g5:phase_interference | 50093.51851044622 / 50093.51851044622 | 33612372401 / 33612427349 | (4,20) | FLOAT_REFERENCE_EXACT_TIE_SPLIT_BY_QUANTIZATION |

For both historical cases, the two competitor cells were in the same unchanged 107-cell alarm component, the Float and Fixed masks were identical, and independent integer grouping and records matched. The fixed integer winner followed the frozen stored-power rule. No general peak-location tolerance was introduced. Full evidence is in engineering/s04_numeric/c06_replacement_16cpi_inputs_v1/D-HISTORICAL-PHASE-INTERFERENCE-REPLAY-v1.0.json.

**D result: PASS.** The approved exception is limited to these two exactly tied historical cases.

## 7. E — CPI disposition, denominator and Full Trace

- All 16 inputs passed envelope, signed-Q15 fit, zero input clipping and static headroom checks.
- Runtime input saturation events: 0; internal overflow/saturation events: 0.
- Full Trace: 16 CPI × 2 scopes = 32 scope manifests; all manifests and both JSONL scope files per CPI were read back and hash-verified.
- Trace truncation: none; event count: 0. The two scope files per CPI exist and are empty because no guard/saturation/overflow events occurred.
- Every CPI was attempted exactly once; 0 retries, 0 replacements, 0 omissions.

**E result: PASS.** All predeclared metadata, input and trace conditions were satisfied.

## 8. Prior campaign preservation and exclusions

- The prior 16 CPI remain INCONCLUSIVE with one attempt each. Their attempt ledger SHA-256 remains 91655e63a84e185b8c6b947064a713f29474994661601b52318c2e99c91402ee.
- The prior input manifest SHA-256 remains 59365ab6aadb1e2c9203415fe5f5b48b4d3298c9d9cb31c4c649f621ecadddb1.
- No prior CPI or accepted S03 seed was reused.
- No alpha, architecture, coefficient, RNE, narrowing, FFT shift or numeric-contract change occurred.
- No statistical Pfa/Pd campaign, RTL, synthesis, FPGA or hardware test was run.
- The C01 0.1% / 20,000-CPI noise-only statistical rule was not run or inferred from this 16-CPI campaign.

## 9. Final C06 disposition

**Evidence outcome:** A=PASS, B=PASS, C=PASS, D=PASS, E=PASS; all 16 CPI=PASS.

**Recommended C06 decision:** Accept the bounded A–E replacement evidence after independent review of the exact execution lock, per-CPI results, Full Trace manifests, independent oracle records and D replay evidence. Do not self-issue final C06 sign-off from this execution report alone.

## 10. Gate-S04 recommendation

**Recommendation: KEEP GATE-S04 OPEN / NO-GO.** The bounded C06 A–E evidence is complete and has no failed or inconclusive CPI, but REQ-SCR-01 and REQ-RNG-03 remain binding open blockers. This campaign did not test SCR at +10 dB/−10 dB, clutter, or two-target resolution near 600 m. Their measurement region, generator envelope, amplitude/phase conditions, truth association and success metrics still require independent approval and separate evidence.

Do not increase S04 progress or mark Gate-S04 closed until the independent C06 A–E review is signed and the F blockers are separately specified, authorized, executed and accepted.

## 11. Evidence references

- Aggregate: engineering/s04_numeric/c06_replacement_16cpi_qualification_v1/S04-C06-REPLACEMENT-16CPI-QUALIFICATION-AGGREGATE-v1.0.json; SHA-256 d1609c708abff971c9a8d26918270318bbd71b350218d2f09991a7a302655308.
- Attempt ledger: engineering/s04_numeric/c06_replacement_16cpi_qualification_v1/attempt_ledger.json; SHA-256 e9d562f8b902e70f58c3909512e23a89f07d3a81a2036606292d6b6f7191a3f0.
- Evidence manifest: engineering/s04_numeric/c06_replacement_16cpi_qualification_v1/S04-C06-REPLACEMENT-16CPI-FINAL-EVIDENCE-MANIFEST-v1.0.json; SHA-256 f5b7f8dbf91727d9f0f808ec2c3d257bdc37926f980a498dabeac61ed98a0e52.
- Replacement execution lock: engineering/S04-C06-REPLACEMENT-EXECUTION-LOCK-v1.0.json.
- Official S04 progress file was not modified; S04 remains 62.5%, overall project 30.2083%, Gate-S04 OPEN.

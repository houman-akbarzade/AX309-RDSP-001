# AX309-RDSP-001 | S04-C02 Paired Architecture Comparison and Design Decision Package v0.6

**DESIGN EVIDENCE ONLY — C02 OPEN, NO AUTOMATIC ARCHITECTURE APPROVAL.** C01 PASS BOUNDED; Gate-S04 OPEN; S04 12.5%, overall 26.0416667%. No statistical CPI, historical acceptance seeds, RTL, synthesis or FPGA tests.

## 1. Baseline and strict evidence provenance

The analysis uses the approved C01 two input scaling factors (g=1 for lab single-target-reference-like source; g=5 for noise-only) **only as original-amplitude reconstruction scales**. The deterministic rational patterns used here are not stochastic samples from those classes, and do not introduce new target or clutter models. Input and numeric operation contracts are the v0.5 candidate integer prototype, frozen S03 chirp/MF/MTI/FFT and the corrected v0.3.1 CFAR widths.

**Critical reference correction:** S03 model's default CA-CFAR alpha of 40*(0.001^(-1/40)-1) is a design initializer, NOT the frozen approved alpha. The final comparison uses the S02/S03 approved value **7.476912055027923**, loaded from `decisions/S02-C-CFAR-02-v1.2-approved-amendment.json`, with an explicit alpha argument passed to `S03.cfar_2d`. An early provisional comparison that used the default was rejected, and the full 216-run study was regenerated before evidence freeze.

The v0.5 file remains unmodified. The v0.6 capture model differs only in returning full stored RD power and FFT IQ maps and the exact integer CUT comparison records. This enables complete-map comparisons without altering the mathematical candidate datapath.

## 2. Pairing, denominators and reasons for non-eligibility

All **12 combinations** use the same 18 stable deterministic vector IDs: 9 rational patterns × 2 approved scaling values. That gives **216 full fixed arithmetic executions**. Each full sample has 33×128 complex input points, a 128×32 RD map and 2782 valid CFAR CUT. The program recorded **66 unordered candidate pairs ×18 vector IDs =1188 paired-vector comparisons**, at MF, MTI, five FFT stages and each of 4096 final FFT cells.

- Full set: 18/18 vectors per candidate, 9/9 per g, including clipped inputs and internal saturation.
- Common non-saturation intersection across **all 12** candidates: 14/18, with exactly 7/9 for each g.
- Common-excluded `g1:near_clip` and `g5:near_clip`: B and C at zero FFT shift saturate FFT5 and power even though input does not clip. These cases are still retained for every candidate in the full set.
- Common-excluded `g1:overrange_stress` and `g5:overrange_stress`: 8448 input I/Q components clipped for every candidate, and B/C zero-shift also saturate internally.

Every reason, per-candidate count, first event and digest is available in JSON. The common set is **not** an approved performance denominator or a right to discard, replace or repeat any statistical CPI. Unlike v0.5 candidate-specific 14/16 denominators, all paired accuracy claims below use the identical 14 IDs.

## 3. MAX/RMS and stagewise errors in original normalized Float amplitude

The following results use the **common 7-vector set for each g**. Complex absolute error MAX and RMS are in original unshifted normalized Float amplitude after applying g and all inverse FFT stage scaling. They are neither estimated population RMS nor statistical performance. Complete nine-vector (including saturated samples) MF/MTI/FFT1–FFT5 MAX/RMS values are retained in the JSON alongside the common-set values.

| Option | shift | g | MF MAX / RMS | MTI MAX / RMS | FFT5 MAX / RMS | CFAR changed CUT 7 / 9 | internal events 9 |
|---|---|---:|---:|---:|---:|---:|---:|
| A | ZERO | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0195229 / 0.00122606 | 0 / 0 | 0 |
| A | ZERO | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0976146 / 0.00613032 | 0 / 0 | 0 |
| A | EARLY_3 | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0192767 / 0.00130568 | 160 / 374 | 0 |
| A | EARLY_3 | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0963833 / 0.00652839 | 160 / 374 | 0 |
| A | DISTRIBUTED_3 | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0194995 / 0.00121106 | 0 / 0 | 0 |
| A | DISTRIBUTED_3 | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0974975 / 0.0060553 | 0 / 0 | 0 |
| A | ALL_5 | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0190481 / 0.00138062 | 214 / 214 | 0 |
| A | ALL_5 | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0952403 / 0.0069031 | 214 / 214 | 0 |
| B | ZERO | 1 | 0.000457187 / 0.000212004 | 0.000381085 / 0.000129776 | 0.0733855 / 0.00445966 | 0 / 0 | 466 |
| B | ZERO | 5 | 0.00228594 / 0.00106002 | 0.00190542 / 0.000648878 | 0.366927 / 0.0222983 | 0 / 0 | 466 |
| B | EARLY_3 | 1 | 0.000457187 / 0.000212004 | 0.000381085 / 0.000129776 | 0.0721154 / 0.00479402 | 160 / 374 | 0 |
| B | EARLY_3 | 5 | 0.00228594 / 0.00106002 | 0.00190542 / 0.000648878 | 0.360577 / 0.0239701 | 160 / 374 | 0 |
| B | DISTRIBUTED_3 | 1 | 0.000457187 / 0.000212004 | 0.000381085 / 0.000129776 | 0.0732975 / 0.00441196 | 0 / 0 | 0 |
| B | DISTRIBUTED_3 | 5 | 0.00228594 / 0.00106002 | 0.00190542 / 0.000648878 | 0.366488 / 0.0220598 | 0 / 0 | 0 |
| B | ALL_5 | 1 | 0.000457187 / 0.000212004 | 0.000381085 / 0.000129776 | 0.0710076 / 0.00506832 | 321 / 321 | 0 |
| B | ALL_5 | 5 | 0.00228594 / 0.00106002 | 0.00190542 / 0.000648878 | 0.355038 / 0.0253416 | 321 / 321 | 0 |
| C_hypothetical | ZERO | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0195229 / 0.00122606 | 0 / 0 | 472 |
| C_hypothetical | ZERO | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0976146 / 0.00613032 | 0 / 0 | 472 |
| C_hypothetical | EARLY_3 | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0192767 / 0.00130568 | 160 / 374 | 0 |
| C_hypothetical | EARLY_3 | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0963833 / 0.00652839 | 160 / 374 | 0 |
| C_hypothetical | DISTRIBUTED_3 | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0194995 / 0.00121106 | 0 / 0 | 0 |
| C_hypothetical | DISTRIBUTED_3 | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0974975 / 0.0060553 | 0 / 0 | 0 |
| C_hypothetical | ALL_5 | 1 | 0.000187257 / 5.80122e-05 | 0.000374513 / 8.96206e-05 | 0.0190481 / 0.00138062 | 214 / 214 | 0 |
| C_hypothetical | ALL_5 | 5 | 0.000936283 / 0.000290061 | 0.00187257 / 0.000448103 | 0.0952403 / 0.0069031 | 214 / 214 | 0 |

The full input set shows very large error in intentional `overrange_stress`; these results remain in the data and must not be hidden to favor a candidate. Stagewise errors of all seven stages are included separately for both g and both denominators. Input clipping and processing clipping are distinct event classes.

## 4. Matched-vector paired deltas and the C distributed-three-shift hypothesis

For each of 66 candidate pairs, JSON stores 18 source-ID-matched differences of both per-vector MAX and RMS errors for MF, MTI and FFT1 through FFT5. It additionally stores the 4096-cell per-bin absolute FFT error difference summary and the number of cells in which A or B is better, or both tie. A negative paired `MAX_A−MAX_B` or `RMS_A−RMS_B` means a smaller value for the first named candidate on **that very same vector**, never on unmatched denominators.

For A DISTRIBUTED_3 versus C DISTRIBUTED_3, on the 14-vector intersection the observed FFT absolute errors are **identical for all 4096 bins per vector**, 28,672 bins at each g, or 57,344 bins total. Both use Q15 coefficient and Twiddle formats and the same distributed shift plan; C has less proposed FFT/power headroom, which was not exhausted in this common set. Identical results here do not establish universal A/C equivalence or a C sign-off.

For B DISTRIBUTED_3 versus C DISTRIBUTED_3, at each g in 28,672 paired bins, **B is better in 779 bins**, **C is better in 9469 bins**, and **18,424 are equal**. This supports considering C a design *candidate* for continued review, but B sometimes has lower per-bin error and no decision weighting/accuracy threshold exists. The complete per-vector distribution and MAX/RMS delta evidence are inspectable. No rank is assigned.

## 5. Complete power maps, 2D CFAR masks, alpha and margins

For all 216 executions, the analysis compared **every 128×32 reconstructed Float-domain power cell** to the S03 RD power map and recorded per-map MAX/RMS and content SHA256 (both raw stored-power sequence and reconstructed float64 array). All 2782 valid CUTs were checked with the exact strict integer CFAR expression `40*Pcut*2^Fa > Aalpha*SUM40`. Candidate alpha for A/C is 490007/2^16 and for B is 30625/2^12; neither is approved. The original S03 Float alpha remains 7.476912055027923. Integer full-map mask digests, alarm counts, all changed CUT coordinates and directions, unbounded comparator margin and corresponding reconstructed Float-domain margins are preserved.

| Option | shift | changed CUT all 18 | 0→1 / 1→0 | min |Float margin| (original power) | alpha-only changed CUT | host cluster count / peak-signature disagreement cases |
|---|---|---:|---|---:|---:|---|
| A | ZERO | 0 | 0 / 0 | — | 0 ref, 0 fixed | 0 / 2 |
| A | EARLY_3 | 748 | 748 / 0 | 0 | 0 ref, 0 fixed | 6 / 6 |
| A | DISTRIBUTED_3 | 0 | 0 / 0 | — | 0 ref, 0 fixed | 0 / 2 |
| A | ALL_5 | 428 | 428 / 0 | 0 | 0 ref, 0 fixed | 2 / 2 |
| B | ZERO | 0 | 0 / 0 | — | 0 ref, 0 fixed | 0 / 2 |
| B | EARLY_3 | 748 | 748 / 0 | 0 | 0 ref, 0 fixed | 6 / 6 |
| B | DISTRIBUTED_3 | 0 | 0 / 0 | — | 0 ref, 0 fixed | 0 / 2 |
| B | ALL_5 | 642 | 642 / 0 | 0 | 0 ref, 0 fixed | 4 / 6 |
| C_hypothetical | ZERO | 0 | 0 / 0 | — | 0 ref, 0 fixed | 0 / 2 |
| C_hypothetical | EARLY_3 | 748 | 748 / 0 | 0 | 0 ref, 0 fixed | 6 / 6 |
| C_hypothetical | DISTRIBUTED_3 | 0 | 0 / 0 | — | 0 ref, 0 fixed | 0 / 2 |
| C_hypothetical | ALL_5 | 428 | 428 / 0 | 0 | 0 ref, 0 fixed | 2 / 2 |

Where masks change, this vector collection produced changes from **0 to 1**, not from 1 to 0. For example, some Float-reference threshold margins are **exactly zero** and small positive integer-domain margins after stage quantization trigger a strict alarm; the cut-by-cut margin records make that traceable. The alpha-only substitution checks on **the same original power map** and on **the same fixed power map** each had no CUT flips for these vectors. It is therefore unwarranted to attribute the observed mask differences to alpha quantization. All alpha sensitivity results are deterministic, not Pfa/Pd evidence.

### Cluster/output agreement — OPEN

The v0.5/v0.6 prototype does **not implement native integer bit-true 8-connected clustering, peak tie resolution or target-list serialization**. A host diagnostic applies the unchanged S03 Float `clusters_8` routine to the candidate mask and reconstructed power, recording cluster counts and the first 20 peak signatures. This is a host **comparison**, not a new fixed-point clustering implementation. Importantly, A/C DISTRIBUTED_3 have **zero changed CFAR CUT**, yet two of the 18 host cases have changed cluster peak signatures due to power/tie differences. Accordingly, **full chain cluster and target-record bit-true agreement is OPEN**, regardless of mask agreement.

## 6. Non-weighted engineering decision matrix

No candidate ranking, automatic selection, fixed error threshold, resource budget or acceptance criterion is introduced.

| Option | MF raw accumulator W | FFT W/F | FFT complex storage bits | RD power storage bits | input / internal overflow concern | numeric/control status | S02 obligation |
|---|---:|---|---:|---:|---|---|---|
| A (distributed-three illustrative) | 37 | 28/15 | 229376 | 212992 | 0 internal events for distributed; 0 for zero shift on all inputs; input stress clips all options | unapproved RNE/FFT stage widths, pipeline, performance margins and cost | REQ-SCR-01, REQ-RNG-03 OPEN |
| B (distributed-three illustrative) | 35 | 23/13 | 188416 | 176128 | 0 internal events for distributed; 932 for zero shift on all inputs; input stress clips all options | unapproved RNE/FFT stage widths, pipeline, performance margins and cost | REQ-SCR-01, REQ-RNG-03 OPEN |
| C_hypothetical (distributed-three illustrative) | 37 | 25/15 | 204800 | 188416 | 0 internal events for distributed; 944 for zero shift on all inputs; input stress clips all options | unapproved RNE/FFT stage widths, pipeline, performance margins and cost | REQ-SCR-01, REQ-RNG-03 OPEN |

Widths here are proposed and memory is a hypothetical full 128×32 FFT-complex/output power bit count, **not** synthesis evidence or measured register/DSP/BRAM usage. FFT butterfly ordering, internal narrowing/saturation and timing/control architecture remain C02 decisions. The original v0.5 output clipping on B/C zero-shift stress cases is retained in the complete evidence; a low error on an architecture-specific smaller denominator is not a valid reason to prefer that candidate.

**REQ-SCR-01** (SCR ±10 dB clutter) and **REQ-RNG-03** (two equal-power targets near 600m separation) remain binding OPEN requirements from S02. C02 must design numeric coverage and C06 independently verify before Gate-S04. No absolute clutter amplitude, multi-target amplitude, covariance, phase or new input scale is assumed or approved.

## 7. Reproducibility and engineering HOLD

Run at repository root using system Python /usr/bin/python3 (3.14.4):

`/usr/bin/python3 -B engineering/s04_numeric/s04_c02_paired_analysis_v06.py`

`/usr/bin/python3 -B engineering/s04_numeric/s04_c02_v06_decision_summary.py`

`/usr/bin/python3 -B -m unittest discover -s tests -p test_s04_c02_paired_v06.py -v`

Primary source: `engineering/s04_numeric/s04_c02_paired_analysis_v06.py` and integer-map capture `engineering/s04_numeric/s04_c02_integer_maps_v06.py`. Detailed evidence: `engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json` (216 outputs, 1188 paired records); compact decision matrix: `engineering/s04_numeric/S04-C02-paired-decision-summary-v0.6.json`. Tests and complete run transcripts are stored in `engineering/`. Historical source and accepted evidence remain unchanged.

**Decisions still OPEN:** C02 architecture and numeric error criterion, independent bit-true native clustering, formal margin and alpha/CFAR error budgets, actual internal pipeline widths, physical FPGA cost and independent C06 acceptance. C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN, S04=12.5%, overall 26.04%.

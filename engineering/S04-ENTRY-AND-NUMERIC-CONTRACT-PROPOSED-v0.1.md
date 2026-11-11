# AX309-RDSP-001 | S04 ENTRY AND BIT-TRUE FIXED-POINT CONTRACT PROPOSAL v0.1

STATUS: PROPOSED / NOT APPROVED. S04 ENTRY AUTHORIZED by Gate-S03, numeric architecture NOT chosen, no RTL or hardware tests. Eight S04 criteria remain NOT_STARTED.

## 1. Inherited frozen design
- S03 Gate approved, model is a Python floating functional reference, NOT a bit-true implementation.
- 33x128 complex IQ, LFM16, linear matched filter, MTI first difference (33 to 32), unshifted Doppler FFT32, nonnegative RD-power 128x32, 7x7 / 3x3 CA-CFAR 40 training cells and 2782 valid CUT, strict comparison, 8-connected clusters, deterministic target list.
- Keep source alpha=7.476912055027923 as the floating reference. A fixed coefficient representation and loss-of-precision behavior are S04 decisions.
- Host IQ input layout from S02: pulse-major, little-endian I/Q signed int16 interleaved 16896 bytes/CPI. Signed Q1.15 conversion using ties-to-even is a previously documented candidate; internal Q formats NOT approved.
- Signed Doppler bins and nominal c_ref 3e8 m/s; actual physical range reporting exact c as required. No S02/S03 approved source modification.

## 2. Candidate choices — engineer must decide before freezing

| Numerical boundary | Proposed options/constraints, not final |
|---|---|
| Input IQ | Evaluate candidate Q1.15 signed int16, observed clipping, headroom and per-stage normalization; do not treat full-scale fit as proven |
| LFM/MF coefficients | Compare candidate signed coefficient width/fraction and conjugate-reverse tap order. Freeze phase, input and coefficient quantization oracle before model execution |
| Add/multiply | Record per-stage word length W, fractional F, signedness, binary-point shifts, complex multiply intermediate width, rounding and post-operation clipping; no common universal Q format assumed |
| Rounding | Compare nearest-even versus truncation internally; host Q1.15 nearest-even already specified. Freeze negative half-LSB handling, every rescale point and signed shift semantics |
| Overflow policy | Saturation with explicit flags vs wrap with wider accumulators as documented alternatives, not a selected decision; guard-bit analysis mandatory |
| MF | Worst-case 16 coherent additions and coefficient quantization; preserve delay alignment q=k+15 and clean-peak oracle |
| MTI and Doppler | Worst-case difference gain up to 2, unnormalized 32-term FFT growth up to 32. Decide per-butterfly/block-floating or end-shift schedule, guard bits and overflow before choosing widths |
| RD power | Explicit scale for real-square + imag-square; positive integer accumulator, truncation/rounding location and tie behavior |
| CA-CFAR | Preserve strict CUT > alpha times mean of 40 training cells; compare integer cross-multiply with quantized alpha and explicit division rounding. Verify power and 40-sum overflow; no silent threshold equivalence claim |
| Peak/list | Exact quantized tie rule (minimum signed Doppler bin then unshifted bin), all-zero flag, 8-neighbor connectivity, deterministic ordering; variable list capacity and priority reserved for S05 |
| Output diagnostics | Explicit saturation/overflow and effective-scale flags, full stage readback, signed velocity convention and fixed/float comparison units |

## 3. Numeric error budget and acceptance proposal — no selected numeric thresholds yet

1. For each interface: choose W, F, input scale, LSB=2^(-F) in stage units, maximum absolute error and RMS error against float, plus bound on headroom/saturation incidence. Where nearest rounding is used and no saturation occurs, quantization error for a single conversion is bounded by half an LSB; propagation through correlated DSP operations needs explicit bound.
2. Distinguish analytically justified worst-case bit growth (MF16, MTI2, FFT32, power squares, CFAR sum40) from measured distribution of fixed input vectors. Neither alone establishes acceptable hardware behavior.
3. Per-CFAR-CUT float decision margin M=P_cut-alpha*mean40 must be compared against an error bound on quantized power and threshold; define zones where a binary alarm decision must be exact versus where float-to-fixed disagreement is tolerable. Preserve strict equality semantics and positive nonnegative power.
4. Preserve D association, R range accuracy, V eligible Doppler half-bin accuracy, E eligibility, J composite and additional target clusters as DIFFERENT metrics. Define a separate bit-true-vs-float mismatch budget for exact flags, peak bins, masks, list order and numeric quantities. No automatic reuse of Pd acceptance seed/data for numeric tuning.
5. All numeric pass/fail/invalid criteria and development/independent acceptance datasets must be predeclared and engineer-approved before executing the bit-true model. Do not retroactively accept thresholds based on favorable results. S04 does not certify S05 architecture, resource fit, RTL, timing or board performance.

## 4. Proposed reproducible deterministic cases
- Signed zero, extrema, two's-complement minimum, negative/positive half-LSB ties, near-overflow, saturated and wrap candidates.
- Clean LFM/MF range k=0,40,112; MTI cancellation; bin +/-4, off-bin, DC, Nyquist; exact peak power ties; all-zero Doppler.
- Power scale extremes; CFAR strict equality, near-positive/negative margin, edges and guard regions, all 40 training values, 2782 valid-CUT mask.
- Target-list cardinality, global one-to-one association, no match, duplicate IDs, overflow status, extra clusters. Stagewise independent integer/rational test oracle required.
- Data: new development vectors and distinct future fixed test data with pinned seeds/hashes. Do not sample accepted Pd main stream or use it to choose formats.

## 5. Eight acceptance criteria (all currently OPEN)

| ID | Completion required before PASS |
|---|---|
| S04-C01 | Baseline and requirements traceability: S02/S03 approved source hashes, numeric interfaces, limits and verification oracle independently audited and approved |
| S04-C02 | Engineer-approved fixed-point numeric contract: Per-stage W/F, sign, scales, shifts, rounding, saturation/overflow, coefficients and accepted numeric thresholds approved and version locked |
| S04-C03 | Bit-true arithmetic primitive qualification: Exact independent integer/rational oracle for IQ packing, coefficient encoding, complex arithmetic, rounding ties, negative extremes and overflow |
| S04-C04 | Bit-true MF/MTI/Doppler qualification: Independent self-checking signed, normal/extreme, DC, bin, off-bin, tie/zero vectors, error and overflow evidence |
| S04-C05 | Bit-true power, CFAR and grouping qualification: Power bit growth, 40 training-cell mean, alpha representation, strict comparison, threshold boundary, peak/tie, clustering/target-list flags |
| S04-C06 | Float-to-bittrue numeric error-budget acceptance: Preapproved per-stage max/RMS tolerances and analytic bounds, decisions/flag exactness and no post-hoc criterion adjustment |
| S04-C07 | Reproducible corpus and independent evidence review: Frozen code, seed separation, source/IO SHA, environment, complete traces, inherited risk audit and failure handling |
| S04-C08 | Independent final S04 engineering Gate approval: All preceding criteria evidenced; engineer issues explicit approval and preserves unresolved risks |

Status: 0/8; S04 0%. Completing this proposal does not satisfy C01/C02 or authorize model implementation. S04 Gate OPEN.

## 6. Inherited risks (not closed)
- Pd limited to fixed SNR20 no-clutter on-bin single target. Not a proof of general Pd, clutter, off-bin targets, fixed point, RTL or hardware.
- 4135 target-present extra unmatched clusters are an output multiplicity measure, NOT Pfa. No target-absent denominator is available here.
- Full input 33x128 IQ arrays and full 128x32 power arrays are not archived; hash evidence allows verification of separately authorized reproduction, not recovery of original bytes.
- Historical Student-t 7/15 and spatial transfer FAIL remain immutable. S02 v1.2 Pfa acceptance uses a different bounded-CPI EB method.
- Resource margins, RTL architecture, memory, target-list overflow capacity and physical timing belong to separately reviewed future stages.

## 7. Review request and SHA evidence
Prioritize approval of the numerical interface map and design alternatives, error-budget criteria, tie/overflow rules, and independent validation plan. No architecture freeze without explicit approval. 
- decisions/GATE-S03-approved-baseline.json SHA256 95319a82738c1bf508b1f417b8e0cc6a9de90de0f51a644d196234ba206f9427
- engineering/S03-FINAL-GATE-READINESS-v1.0.md SHA256 53c6840c98e5743c8432e0155329966256cba44d740c778b8f3483897f56b8fc
- engineering/S02-C-CFAR-02-CONTRACT-APPROVED-v1.2.md SHA256 6e07ab218cd76f8358d56e3de0bbbc57dc62eff82b702222c0bb47f3b9ca1f3e
- engineering/S02-engineering-contracts-FINAL-PROPOSED-v1.0.md SHA256 8faccf7f89d03a9885fbde43dd7e42577ca4092f4202c2107f927e8da81be13e
- s03_reference/model.py SHA256 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b
- engineering/S04-progress.json SHA256 8cf5a31dc8a6bb69d315c37f0fe8cff2f553d46e84819619d010367ddeb912e4
- engineering/S04-inherited-risk-register-v0.1.json SHA256 2fd9595ad33c24d2e87266723b7474e20da3637e521eff10bbffc846910c777e

S04 starting commit: 883e161d36af5dab2464ad24255a226c39b8ea00; recorded UTC: 2026-11-11T08:36:17.696741+00:00

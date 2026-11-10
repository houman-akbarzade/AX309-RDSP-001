# AX309-RDSP-001 — S03 Pd independent test readiness GO/NO-GO v0.2

**Decision: GO FOR FORMAL PROTOCOL REVIEW; NO-GO FOR MAIN Pd TEST.**
The engineer accepts fixed-source Python Pfa PASS, S02 v1.2 active, but the Pd binding population protocol remains PROPOSED. No Pd CPI has been generated and master seed 411091704 remains reserved. Gate-S03 OPEN, S03 75% and project 22.9167%.

## Evidence-integrity and deterministic preflight
- Approved S02 v1.2 C-CFAR-02 and all historical S02 v1.0/v1.1 SHA-256, Student-t 7/15 FAIL, spatial anisotropy FAIL checked byte-for-byte unchanged.
- Final Pfa: PASS U95=0.0014491445035750084 using 20000 CPI, evidence SHA256 6dab2a8a6669b698a53e74f88105b61169c02f819ac72d3674a94d34aca9cc7f; no Pd inference.
- Independent Pd proposal source frozen BEFORE stochastic data at Git commit **564b5e6fc2dfbd2fd5131139ded1616fe719d9d7**. Pd contract SHA256 416982f71d275f2a0ee23c88862a4b9a07301ba84581baf5a0267fc4d4f21986, JSON SHA256 cde5b6efa467cbcf1450798a963555a48a08318e52f8c9d9065ba20105ef6da1; candidate scoring implementation SHA256 a0f846f9bc9b0b21185402b9e121c231bbc3ac3c19b6b4194599c72d746724b9; full model source SHA256 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b; exact unit test source SHA256 918ed024dde59c703ca12cf15f8a05e589d5c329e18ab013a51af7c6809c2e22.
- **67/67 deterministic NumPy and scorer unit tests PASS**, including matched-but-outside-range and matched-but-outside-velocity accuracy, exact Clopper-Pearson 915/916, invalid record, cluster extras and peak tie eligibility. These tests do NOT generate any target CPI or measure Pd; runtime and test transcript in engineering/S03-Pd-deterministic-protocol-tests-v0.2.log.
- Proposed independent CPI master **411091704** and fixed N=1000, phase0, amplitude0.18, k40,b4,v+1.875m/s,input SNR20dB, no clutter; CN(0,0.000324) noise (each component variance0.000162); frozen alpha7.476912055027923.
- No global PRNG state in intended generator; fresh PCG64 SeedSequence([411091704,i,191]) per complete CPI. Actual source uniqueness and inter-CPI state checks require approved future stochastic run; cannot be claimed observed in this deterministic review.

## Acceptance semantics and mandatory separate metrics
- D_i: true target detected and associated globally 1:1 under loose 2-sample/1-bin truth-match gate.
- R_i: matched range peak within 1 sample (150m nominal), a *design target* distinct from association.
- V_i: matched Doppler eligible unique positive peak strictly above neighbors and within half bin 0.234375m/s, with not-eligible/tie/zero flags never silently excluded.
- J_i: all D,R,V and eligibility simultaneously; composite STRICTLY STRONGER than raw Pd detection/association. Missing matched 32-bin power row is INCONCLUSIVE and cannot be quietly assumed V-eligible. All extra clusters and CFAR power/training thresholds must be retained.
- Primary proposed Pd=Pr(D=1) >=0.90 at one fixed scene. One-sided exact 95% Clopper-Pearson lower at n=1000: k915 L=0.8990676705833044 FAIL; k916 L=0.9001427009482232 PASS. Independent binomial tail test agrees: Pr_p=.9[K>=916]=0.04850250689914629<=.05.
- **Unresolved engineering decision:** whether J_i>=0.90 with separate exact CP bound is made an additional binding accuracy-qualified performance guard. Since S02 RNG-02 is currently a DESIGN GOAL and not a prescribed population fraction, adding a binding composite 90% threshold requires explicit engineer approval. Association PASS must never be represented as estimator accuracy PASS.

## Fixed-scene claim boundary
The proposed study covers ONLY single target k=40/b=+4, fixed phase0/amplitude0.18 at theoretical input SNR20, noise-only no clutter, current floating Python chain. No claims for off-bin Doppler leakage, DC/MTI null, unknown velocities, different target ranges, target interference, different noise/clutter, multiple targets, fixed-point arithmetic or FPGA hardware.

## Failure mode and future reproducibility checklist
- MTI: DC suppression and first-difference behavior; on-bin +4 deliberately nonstationary. Doppler: bin sign, ties, zero, adjacent peaks and off-bin leakage as separate diagnostic scopes.
- MF: known range sidelobes near k±13 and false associated cluster risks; track all clusters, independent truth assignment, do not use total cluster count as Pd.
- CFAR: strict calibrated threshold and 40 training values, interference/self-masking, boundary validity; store GT CUT, mean40 and threshold for each CPI.
- 8-neighbor clustering: split/merge and repeated detections, one-to-one association and selected-power tie flags.
- Before any new target sample: source locks, dependency versions, exact seed and i partition, log schema, exact pairing and accuracy flags, source reproducibility, no state reuse. Incomplete/invalid CPI => INCONCLUSIVE, not silent exclusion. Exactly 1000 CPI and one approved final outcome; no stopping or reruns without separate decision.
- Before sampling engineer must **approve Pd protocol** and explicitly decide proposed joint guard, and then grant **separate execution authorization**.

**Verdict: technical protocol mathematics/scoring preflight GO; main Pd test NO-GO.** Preserve all S02/Pfa/historical failed evidence, official stage progression unchanged.

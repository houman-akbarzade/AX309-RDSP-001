# AX309-RDSP-001 | S03 | Independent Pd Acceptance Protocol v0.2

STATUS: FROZEN PROPOSAL; NOT APPROVED; NO STOCHASTIC Pd CPI GENERATED.
Existing final Pfa PASS under approved S02 v1.2 is accepted for the reference Python model. S03 Gate OPEN; official progress 75%, overall 22.9167%.

## 1. S02 requirements traceability
REQ-PD-01: Pd>=0.90 is a DESIGN TARGET for ONE isolated target at input SNR 20dB, no clutter; SNR 0/10dB only report without acceptance minimum.
REQ-RNG-02: <=1 range sample (150m nominal) at SNR20 is a DESIGN TARGET, NOT a previously ratified statistical criterion.
REQ-DOP-01: for eligible dominant targets, velocity error relative to nearest signed Doppler-bin reference <=0.234375m/s (half bin); all ties, all-zero and ineligible statuses recorded, never silently discarded.
REQ-MATCH-01: the one-to-one truth assignment candidate gate is **2 range samples and 1 Doppler bin**; the gate is ONLY for association, not estimator accuracy.
REQ-CFAR-01: strictly P_CUT > alpha times 40-cell training mean; 7x7 outer minus center 3x3; 2782 valid CUT.
REQ-DET-01: deterministic 8-connected cluster output and no many-to-one truth reuse; REQ-SNR-01: theoretical prequantization echo SNR. All other 22-row matrix requirements and prior Pfa approval remain unchanged. The candidate is software reference only, not bittrue RTL or FPGA.

## 2. FIXED proposed future population study: exactly 1000 CPI (not yet run)
Target single, isolated, no clutter, integer range delay k=40 samples, full 16-sample echo in 128, valid CFAR interior, fixed unshifted signed Doppler bin b=+4 => nominal velocity +1.875m/s at c_nominal=300000000m/s, PRI=.001s, fc=10GHz, FFT32. Not stationary/DC/Nyquist, away from ties in deterministic on-bin source.
Complex amplitude 0.18+0j, phase 0rad; 33 coherent pulses of 128 complex input at fs=1MHz; LFM 16 samples B=250kHz. Theoretical input SNR=20dB (relative to |a|^2 on 16 active echo samples); target power .0324 and noise CN(0,sigma2=.000324), real/imag separate variances .000162. Exact per-element noise generation sqrt(.000324/2)*(standard_normal+1j*standard_normal). Do not use realized noisy SNR to include or exclude a trial.
Reserved untouched master seed 411091704: for trial i=0..999 use fresh PCG64(SeedSequence([411091704,i,191])), never global RNG or samples from earlier Pfa, alpha, preflight or scenario data. Independently generate full target echo and add Gaussian noise; fix all code/dependency hashes BEFORE input generation.
Frozen Python model stages: matched filter -> MTI 33-to-32 first difference -> unshifted Doppler 32 FFT -> linear power -> CA-CFAR with APPROVED alpha 7.476912055027923 -> clusters_8 -> truth_match. Never retune alpha, amplitude, SNR, truth, detection thresholds or stage settings after sampling. Historical delta-star stays unchanged and is not used in Pd.

## 3. Freeze distinct outcomes per complete CPI, never confuse association with accuracy
All true target and detections use nominal c=3e8 for association and velocity labels.
D_i =1 iff at least one cluster peak is assigned to the single truth by approved global one-to-one truth_match using ONLY candidate |khat−40|<=2 and |vhat−1.875|<=0.46875m/s; cardinality then normalized squared cost then lexical tie. No match => D_i=0; do not count several clusters as independent trials.
R_i =1 iff matched detection has absolute |khat−40|<=1 sample (150m nominal); at 2 samples an association can succeed but range accuracy FAILS.
V_i =1 iff matched, eligible unique positive Doppler peak is strictly greater than adjacent circular FFT bins AND |vhat−nearest_true_bin_velocity|<=0.234375m/s. One-bin error can pass matching but FAIL velocity. For each CPI record exact tie/zero/eligibility flags, and preserve all ineligible trials in attempted denominator. To score a matched peak, require the *whole 32-bin power row* at its selected range; a missing or nonfinite power row is INCONCLUSIVE, not assumed eligible. The proposed reference scorer explicitly refuses to infer eligibility solely from the cluster record.
J_i = D_i AND R_i AND V_i AND eligibility guard. This COMPOSITE accuracy-qualified event is STRICTER than Pd itself. D_i estimates one-geometry detection-and-association probability; J_i estimates full joint correctness. Record k_D=sum D_i, k_J=sum J_i, range and Doppler conditional hit rates (with denominators), extras/unmatched CFAR clusters, selected peak and GT CUT power, mean40 and local threshold. No silent exclusions or deletion of unfavorable clusters.
Proposal: bare Pd acceptance on k_D, while a separate prospective joint-accuracy guard on k_J is OPTIONAL ONLY IF EXPLICITLY ENGINEER-APPROVED; existing S02 RNG-02 is a design goal and must not be retroactively made a new binding 90%-of-trials requirement. The final summary must never label k_D success as overall range/Doppler accuracy PASS. If the engineer accepts joint guard, the report shows TWO Clopper-Pearson bounds and the distinct overall criterion.

## 4. One-sided EXACT Clopper-Pearson at 95%, fixed N=1000
For k successes in n=1000 independent Bernoulli full CPI, lower L=0 if k=0, otherwise Beta.ppf(0.05,k,1000-k+1). This is an exact one-sided conservative lower confidence bound; no normal/Wilson approximation.
At k=915: L=0.8990676705833044 (<0.9), FAIL.
At k=916: L=0.9001427009482232 (>=0.9), PASS.
Independent binomial null check at p=0.9: Pr(K>=916)=0.04850250689914629 <=.05; Pr(K>=915)=0.060693730517966386 >.05.
Thus prospective Pd-only PASS iff all 1000 CPI valid and k_D>=916. A separately approved joint guard, if any, passes iff k_J>=916, with independent labeling. If k<=915 then FAIL; missing/corrupted/non-independent/modified-protocol CPI => INCONCLUSIVE/BLOCKED, NOT PASS. Exactly 1000 full CPI, never optional stop, add samples or repeat on FAIL.

## 5. Exact scope and restrictions
A PASS only supports detection-and-correct-association probability for isolated target at k40, bin+4, phase0, amplitude.18, input SNR20, no clutter, iid circular Gaussian noise, current Python float reference and frozen alpha. It DOES NOT demonstrate universal Pd for varying range, velocity, phase, amplitude, off-grid Doppler, MTI DC notch, target proximity, clutter SCR, SNR0/10, CFAR edge, FPGA quantization, hardware or multi-target scenes. Additional scenarios require independently preregistered strata and separate confidence/multiplicity policy.

## 6. Preflight failure mechanisms and evidence tags
MTI: stationary/DC notch, first-difference gain. Doppler: off-bin leakage, signed bins, near Nyquist, exact ties, zero and adjacent dominance. MF: known approximate +/-13 range-sample sidelobe groups; wrong-range association or extra clusters. CFAR: frozen alpha, reference sidelobe contamination, self-masking and CUT/training thresholds. Clustering: split/merge, wrong peak selection, 8-neighbor connectivity and duplicate ground-truth match. These are mandatory diagnostics and cannot create post-hoc exclusions from this on-bin single-target population.
Preflight must verify the exact source and theoretical SNR/noise formula, scorer differentiation D/R/V/J, one-to-one matching, half-bin eligibility, binomial exact k_min, seed provenance, output trace schema and immutable S02 hashes. Present GO/NO-GO before any input generation. NO main Pd CPI before explicit engineer approval of this contract and a separate authorization to run. Preserve Pfa PASS and historical spatial FAIL. Gate-S03 OPEN.

## Reference SHA-256 anchors
Approved S02 v1.2 matrix: 23f07e63950c8bd4f3b04a805c37a46792b0068ae918b25d0713dd65a15c51a0
Model source: 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b
Original proposed Pd v0.1: 984d593c774be81abb0408fc67efff4576b1b1146ffe4a814f6b4cfe052f2c09
Final accepted Python Pfa result: 6dab2a8a6669b698a53e74f88105b61169c02f819ac72d3674a94d34aca9cc7f

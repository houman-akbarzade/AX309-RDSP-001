# AX309-RDSP-001 | Pd PRE-EXECUTION AUDIT v0.3

Decision: APPROVED-IN-PRINCIPLE / EXECUTION NO-GO. No target CPI generated; reserved seed 411091704 remains unused in this audit. This is a STATIC inspection plus deterministic arithmetic check, not an executed Pd trial.

## Six pre-execution controls

| Control | Result | Justification |
|---|---|---|
| Input SNR and signal/noise generation | PASS (static) | S02 REQ-SNR-01 active-echo definition. For amplitude 0.18, echo active-sample power 0.0324. At 20dB, complex noise variance E|w|²=0.000324 and each real/imag variance=0.000162. The reference model computes abs(amplitude)^2/10^(SNR/10) and sqrt(sigma²/2) times two standard normals. SNR is not the entire CPI average or post-MF SNR. |
| Independent CPI; pipeline state | PASS structural / empirical untested | New PCG64 per explicit seed argument; proposed SeedSequence([411091704,i,191]) for each complete CPI. Model stages have no persistent filter state; separate CPI processing. No samples from reserved master generated to empirically test this prospectively. This is an assumption about pseudorandom independent streams, not proof of physical independence. |
| Reserved seed and prior use | PASS scoped to visible repository records | Existing documents label 411091704 reserved and disjoint from Pfa 411091703; code refers to seed in constants and deterministic checks. No evidence of earlier run or tuning on this seed in inspected repository records. Cannot certify unobserved external use. |
| Frozen alpha, clusters, matching, outcomes | PASS static with blocker below | CA-CFAR strict threshold alpha=7.476912055027923, 40-cell training, 8-neighbor clustering; global one-to-one association with 2 range-sample/1 velocity-bin gate. Existing source SHA intact; blocker PD-AUD-001 affects V output semantics. |
| D and J compatibility with S02 | FAIL: PD-AUD-001 | D is one-to-one correct association, R is <=1 sample, J explicitly ANDs D, R, Doppler half-bin and eligibility. But the candidate scorer emits doppler_halfbin_accuracy_conditional=dop_ok without AND with eligible, while the v0.2 contract defines V_i success only if matched, eligible and <=half-bin. Thus reported V can disagree with contractual V; revise and deterministically retest before executing. S02 REQ-DOP-01 applies to eligible isolated peaks. S02 REQ-RNG-02 remains design target; not a new binding joint 90% guard. |
| Exact k_min=916 | PASS independent inversion | Beta.ppf(.05,915,86)=0.8990676705833044 <0.90, Beta.ppf(.05,916,85)=0.9001427009482232 >=0.90. Independent binomial tail at p0=.9: Pr(K>=915)=0.060693730517966386 >.05; Pr(K>=916)=0.04850250689914629 <=.05. N fixed 1000. |

## Disposition

- Primary future acceptance: exact one-sided 95% Clopper-Pearson lower bound on D >=0.90, meaning at least 916 successes among exactly 1000 valid CPI.
- J is separately and fully reported, NOT a binding separate J>=0.90 test. Preserve the independently applicable approved S02 range/Doppler accuracy obligations.
- Issue PD-AUD-001 must be resolved in the scorer and regression checks, with new hashes/approval, BEFORE any sample is generated; do not silently reinterpret or re-score.
- Approved in principle does NOT authorize executing samples. Exactly zero of 1000 generated in this review. No retuning, topups, optional stopping, seed reuse.
- Gate-S03 OPEN; S03 6/8=75%; overall 22.916666666666668%; Pfa Python PASS unchanged; Pd NOT_RUN.
- Source locks and historical failed evidence remain unchanged. Existing v0.2 protocol and S02 v1.2 matrix untouched.

## Read-only source audit hashes
- s03_reference/model.py SHA256 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b
- s03_reference/pd_acceptance_candidate.py SHA256 a0f846f9bc9b0b21185402b9e121c231bbc3ac3c19b6b4194599c72d746724b9
- engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json SHA256 23f07e63950c8bd4f3b04a805c37a46792b0068ae918b25d0713dd65a15c51a0
- engineering/S03-Pd-independent-fixed-protocol-PROPOSED-v0.2.json SHA256 cde5b6efa467cbcf1450798a963555a48a08318e52f8c9d9065ba20105ef6da1

Git HEAD before audit: 3c55ab91b57d8f7fa62941910df836f3e1752ac8. UTC record time: 2026-11-11T07:54:20.274866+00:00

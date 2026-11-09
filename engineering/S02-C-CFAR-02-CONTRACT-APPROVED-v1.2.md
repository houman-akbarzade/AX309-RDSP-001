# AX309-RDSP-001 — C-CFAR-02 Limited v1.2 Amendment — FINAL ENGINEER REVIEW

**Status: ENGINEER APPROVED S02 v1.2 / NORMATIVE FOR C-CFAR-02 ONLY.**
The subsequent engineer_message_30 **formally approves v1.2** subject to verification of prior hashes and 16/16 preflight. All those prerequisite checks were verified BEFORE baseline amendment commit. That decision ALSO authorizes **exactly one** future fixed 20000-CPI Pfa acceptance test after successful evidence/byte-integrity check, without any intermediate reapproval. This is not a prior or implied Pfa PASS.

## Exclusive APPROVED changes, effective after integrity-controlled commit
- Keep all other 21 requirement rows unchanged. Pfa design .001; one-sided 95% upper PASS U<=.0015; Pd design >=.90 at SNR20, isolated target, no clutter; 33x128 CPI, MF, MTI, 32-point Doppler FFT, CA-CFAR 7x7 outer /3x3 excluded /40 training /2782 CUT, strict power>alpha*training; frozen alpha=7.476912055027923 all UNCHANGED.
- Supersede only the v1.1 CI interval and operational exchangeable-CUT spatial transfer *prerequisite* by a fixed-sample bounded-CPI empirical Bernstein protocol. Prior spatial z=43.575 FAIL stays valid and unchanged historical evidence, not reclassified as PASS. Historical Delta*=0.28734133322686817 is unchanged, retained but is NOT a term in the proposed EB bound.
- Replace N=4096 by **exactly N=20000** independent and identically distributed full noise-only CPI for future main Pfa acceptance; no sample top-up, optional stop, posthoc invalid exclusions or repeated try to pass. Final Pfa data may be generated exactly once under engineer_message_30 **only after** this normative amendment is committed and the immutable preflight/source SHA-256 checks PASS.

## Active normative formula, mathematical requirements
For CPI i let Fi integer alarms (0<=Fi<=2782) over valid CUTs and Xi=Fi/2782. For independent and identically distributed CPI Xi∈[0,1], with sample mean Xbar, unbiased s²=SUM((Xi-Xbar)²)/(N−1):

U_EB=min(1, Xbar+sqrt(2 s² ln(40)/N)+7ln(40)/(3(N−1))).

At N=20000, one-sided finite-sample coverage >=95% by independent bounded-observation empirical Bernstein (Maurer & Pontil 2009, Theorem 11 after a sign change), regardless of spatial correlations among CUTs within one CPI. Need independent CPI as a joint input/process property and constant distribution across CPI. No claim of optional-stopping coverage. PASS if all 20000 valid and U_EB<=.0015, FAIL if all valid and U_EB>.0015; otherwise INCONCLUSIVE/BLOCKED with provenance and no assertion of achieved Pfa.

## Dataset separation and preflight
- Reference corpus: 4096 CPI, new seed 411091701; separate implementation corpus: 4096 CPI, seed 411091702; main final corpus RESERVED/NOT TOUCHED, 20000 CPI seed 411091703. Different from earlier alpha/CI/synthetic/spatial/Pd seeds. Use PCG64 SeedSequence([master,i,191]) and pin NumPy/SciPy plus all source SHA256.
- No source CPI reused across pools, no pulse overlap or retained pipeline state; each CPI independent Gaussian IQ with E|w|²=1, same fixed shape and filters, no adaptive α. Independently compute Fi by two distinct CA-CFAR paths on the SAME CPI input of each preflight pool; verify count agreement, independently compute mean, s² and U_EB via NumPy and scalar Welford on the SAME count sequence. Check strict threshold / geometry and full 2782 CUT mask. Reference + implementation data are NON-ACCEPTANCE DATA and may never be pooled into final.
- Audit source and seed independence by construction, deterministic reproduction checks and no state retained. ACF/Ljung-Box and zero/tail statistics supplemental ONLY; nonsignificant serial autocorrelation cannot prove independence. Missing, invalid, mismatched pipeline values, unproven independence or failing comparisons => NO-GO, record exact failure, no changing α/criteria.
- Preflight 16/16 succeeded and was recorded before approval. The engineer_message_30 is explicit final-test execution authorization after baseline/sha checks; execute once and preserve results. Regardless of status, Gate-S03 remains OPEN until separate explicit gate approval after final evidence.

## Explicit historical constraints
S02 v1.0 and v1.1 files, SHA-256, S02 Gate, Student-t 7/15 FAIL and spatial anisotropy 43.575 FAIL remain immutable. Original v1.1 15/15 synthetic-model CI qualification remains valid as historical method evidence, not proof of operational Pfa. S03 remains 75%/total project 22.9167% and C06/C08 OPEN. No hardware performance or Pfa/Pd acceptance evidence follows from this proposal.

**Approval:** engineer_message_30; final-test execution conditional on pre-execution SHA-256 checks and separate source-lock Git commit. PASS/FAIL/INCONCLUSIVE determined exclusively by prespecified bound. Gate-S03 remains OPEN; Pd requires its own decision.

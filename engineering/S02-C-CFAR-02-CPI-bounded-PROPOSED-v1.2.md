# AX309-RDSP-001 — S02 C-CFAR-02 proposed limited amendment v1.2 (NOT APPROVED)

**Classification: PROPOSED_FOR_ENGINEER_DECISION_ONLY.**
No historical S02 v1.0/v1.1 approval, historical 7/15 Student-t FAIL, 15/15 C04 v1.1 synthetic-model PASS, or spatial-transfer FAIL is changed. New final Pfa NOT executed.

| Contract field | Existing approved S02 v1.1 | Proposed S02 v1.2 | Change justification |
|---|---|---|---|
| Design Pfa | .001 | .001 unchanged | Performance target preserved |
| Nominal 95% one-sided upper limit | U<=.0015 | U<=.0015 unchanged | Performance acceptance preserved |
| Pd single target/SNR20/no clutter | >=.90 design target | >=.90 unchanged | Unrelated |
| Locked CA-CFAR alpha | 7.476912055027923 | unchanged | Avoid retuning |
| Locked Delta star | .28734133322686817 | unchanged as historical calibration; NOT used by new EB expression | Keep all provenance |
| CI unit | CPI count F_i/2782 | same CPI unit | Preserve all within-map dependence |
| Active interval | calibrated first-order skew Studentized | **Empirical Bernstein finite-sample one-sided** | No assumption of spatial exchangeability / beta-binomial shape |
| Main acceptance size | 4096 CPI | **20000** fresh IID CPI | Power/cost analysis: approx 18058 CPI for 95% proxy power at historical variance, 18940 under 4x |
| Operational transfer requirement | old predeclared directional exchangeability check FAILED z=43.575>|2.576| | PROPOSE: replace with independently audited fixed-generation iid-CPI process/implementation guard | Anisotropy no longer necessary for bounded-mean theorem; change only prospectively, historical FAIL retained |
| Main Pfa | BLOCKED | BLOCKED until new S02 approval, independent method/source preflight and separate readiness authorization | Strict hold |

**Normative candidate to approve, NOT active today:**
For each future iid noise-only CPI i, F_i=sum of strict alarms across 2782 valid CUT and X_i=F_i/2782∈[0,1]. With n=20000 fixed, empirical mean xbar, sample variance s2 with ddof=1, compute
U_EB=min(1,xbar +sqrt(2*s2*ln(40)/20000)+7*ln(40)/(3*(19999))).
With all independent CPI and source-integrity checks passing, PASS iff U_EB<=.0015; FAIL if U_EB>.0015; INCONCLUSIVE/BLOCK if invalid data, unverified IID assumptions, missing CPI, failed code/theorem preflight or unapproved change. NO optional stopping or repeated final tests. One-sided finite sample coverage at least 95% for iid [0,1] CPI rate variables, regardless of within-CPI CUT correlation.

Proposed never-used future PRNG master namespaces: 411091701 for reference (4096 CPI); 411091702 for implementation qualification (4096 CPI); 411091703 for reserved main acceptance (20000 CPI). Lock PCG64 SeedSequence([master,i,191]), mask, pipeline, versions, hashes and distinct datasets before any simulation. No historical alpha, CI or spatial corpus may be reused to claim independent validation. Source-realistic direct code checks and theorem audit must PASS before a readiness report is submitted to the engineer. In no event may S03 Gate be closed or the final Pfa started without explicit subsequent engineer authorization.

Prior 2D spatial anisotropy check stays in all old versions and remains historical FAIL; method validity is a **separate** prospective change, not statistical relaxation of the performance criterion. Any later change should be a new versioned S02 amendment record, leaving approved v1.0/v1.1 SHA unchanged.

Sources: engineering/S03-C04-CPI-bounded-analytical-cost-and-power-v0.1.json, engineering/S03-C04-independent-CPI-bounded-protocol-design-v0.1.md, Maurer & Pontil 2009 empirical Bernstein bound, Chernoff-Hoeffding bounded-variable relative-entropy inequality.

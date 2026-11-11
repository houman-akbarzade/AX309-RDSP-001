# AX309-RDSP-001 | S03 FINAL GATE READINESS v1.0

**Engineer decision:** Pd second main software PASS ACCEPTED with fixed-scene limits. Gate-S03 **OPEN**, no S04 authorization, Pd main NOT reexecuted. This is a proposal for independent engineering Gate decision, NOT a Gate approval.

**Final evidence audit verdict:** 7 of 8 S03 completion criteria supported, one criterion S03-C08 awaits explicit human Gate authorization. The approved S02 requirement matrix and contracts remain unchanged. Statistical Pfa/Pd results apply only to their separately preregistered Python floating-point studies.

## Eight criterion evidence audit

| Criterion | Status | Prior versus newly verified | Technical evidence and limits |
|---|---|---|---|
| S03-C01 | **PASS** | Previously met | Reference model package, execution manifest and frozen hashes. Evidence: engineering/S03-execution-manifest-v0.1.json; s03_reference/model.py |
| S03-C02 | **PASS** | Previously met | LFM/MF analytical and edge index tests; historical model/verification evidence. Evidence: engineering/S03-initial-execution-report-v0.1.md; engineering/S03-unit-tests-v0.5.log |
| S03-C03 | **PASS** | Previously met | 33x128 deterministic generator and defined input noise/SCR, reproducibility source. Evidence: engineering/S03-initial-execution-report-v0.1.md; s03_reference/model.py |
| S03-C04 | **PASS** | Previously met | MTI 33->32, signed Doppler FFT, on/off-bin/zero checks. Evidence: engineering/S03-unit-tests-v0.5.log; engineering/S03-cycle2-evidence-report-v0.2.md |
| S03-C05 | **PASS** | Previously met | 2D CA-CFAR strict 40 training, 2782 valid CUT, 8-neighbor clustering, global 1:1 truth assignment. Evidence: engineering/S03_six_case_reference_smoke.json; engineering/S03-unit-tests-v0.5.log |
| S03-C06 | **PASS** | Newly verified during final gate evidence review (Pfa-approved v1.2, Pd acceptance adds independent evidence) | Originally failed 7/15 Student-t qualification preserved; approved v1.2 empirical Bernstein bounded-CPI theorem replaced incompatible spatial-exchangeability prerequisite. Disjoint 16/16 preflight and N=20000 final noise-only CPI U95=.0014491445035750084 <= .0015; statistical assumptions and limitation documented. Pd separate 1000 CPI accepted D=1000 with CP L95=.9970087504549047. The legacy 15/15 synthetic qualification is NOT reinterpreted as radar spatial qualification.. Evidence: engineering/S02-C-CFAR-02-CONTRACT-APPROVED-v1.2.md; engineering/S03-C04-FINAL-Pfa-EB-evidence-manifest-v1.2.json; engineering/S03-C04-FINAL-Pfa-EB-20000CPI-result-report-v1.2.md; engineering/S03-Pd-MAIN-1000CPI-v1/REPORT.md |
| S03-C07 | **PASS** | Previously met; new Pd extends evidence | Six integrated reference scenarios, result traces and matching metrics preserved; new independent Pd study adds per-CPI clustering/scorer records but does not change previously accepted criterion. Evidence: engineering/S03_six_case_reference_smoke.json; engineering/S03-Pd-MAIN-1000CPI-v1/RAW-CPI-records.jsonl |
| S03-C08 | **INCONCLUSIVE** | OPEN / not approved | Final engineering review report assembled but no explicit independent engineer Gate-S03 approval; stage exit not authorized. Evidence: engineering/S03-progress.json; decisions/ (no GATE-S03 approval) |

## Pfa/Pd and approved S02 consistency

- S02 v1.2 C-CFAR-02 approved SHA-256 contract 6e07ab218cd76f8358d56e3de0bbbc57dc62eff82b702222c0b0... [see full hashes below]. No changes in approved CFAR alpha 7.476912055027923, 40 training, 2782 CUT, strict comparator, or isolated-target SNR definition.
- Main noise-only Pfa: exact N=20000 valid complete CPI; 55919 total alarm CUTs, observed Pfa 0.0010050143781452192 and v1.2 CPI-level EB one-sided U95=0.0014491445035750084 <= 0.0015, PASS. This is NOT a bound obtained by falsely assuming independent CUTs within a CPI.
- Independent Pd second main: 1000/1000 CPI valid, D=1000/1000, exact one-sided CP lower L95=0.9970087504549047 >=0.90, kmin=916, PASS. Accepted by engineer only for one fixed single-target no-clutter scene k40, Doppler bin +4, phase 0, amplitude .18, SNR20dB, current floating Python reference.
- Separate R=1000, V=1000, E=1000, J=1000 and range/Doppler estimation error zero within this one tested scene. J is reported independently WITHOUT a newly binding >=0.90 joint statistical requirement; D PASS is never a universal range/Doppler performance claim.
- Previous Student-t count-method coverage FAIL 7/15 and real-chain spatial exchangeability diagnostic FAIL remain authentic immutable findings, NOT converted into PASS. S02 v1.2 superseded that method/prerequisite with bounded whole-CPI EB; approved assumption scope is entirely different.
- Pd run's 4135 extra unmatched clusters across 1000 target-present CPI are a **clustering/output multiplicity observation** (mean 4.135 extra clusters per target-present CPI), NOT Pfa. This figure has no target-absent/noise-only false-alarm CUT denominator and must not be converted to Pfa. The noise-only Pfa is a separate fixed population study and estimator.

## Data retention and reproducibility limitations

- Pfa evidence records the alarm-count vector, main-source lock, independent preflight, seed, count vector hash, variance and EB bound; historical failed studies remain separately recorded.
- Pd evidence records every CPI's index and seed index, target-associated and unmatched cluster list, D/R/V/E/J, GT CUT and 40-cell training mean and threshold, matched 32-bin Doppler power row, per-CPI SHA-256 of complete input IQ and full power map, and executable/dependency lock.
- **Not retained:** complete 33x128 input-IQ arrays or all 128x32 range-Doppler power-map values per Pd CPI. Hashes permit comparison to an independently, separately authorized regeneration, not direct recovery of originals from archived bytes. This is a reproducibility limitation, not an invalidation of the retained source and summary evidence.
- The chosen pseudo-random CPI indexing and stateless processing provide structural independence by construction; no empirical verification proves statistical independence, and absence of serial correlation would not itself establish independence.
- Earlier Pd first invocation remains **INCONCLUSIVE** with 0 CPI due to Python import failure. It was not silently erased or treated as a statistical trial.
- No bit-true, synthesis, STA, RTL, FPGA-board or multipath/clutter/multi-target generalization supported by Pfa/Pd PASS.

## Open issues / risk register

1. **Gate approval missing:** S03-C08 remains INCONCLUSIVE and OPEN. An independent engineering review and explicit Gate decision are needed; no automatic stage promotion.
2. **Domain coverage:** Pd only one on-bin isolated-target fixed SNR20 case; no population qualification for other ranges, Doppler off-bin, clutter, multiple targets, MTI notch or SNR regimes.
3. **False output multiplicity:** 4135 extra unmatched target-present clusters require independent root-cause analysis if relevant to downstream target-list quality; not reclassified as Pfa or used for tuning the accepted run.
4. **Data archival:** Pd full IQ/power arrays not retained; replay uses per-CPI hashes, score and diagnostic records. Reproduction must be separately authorized without treating reserved acceptance seed as tuning corpus.
5. **Legacy conflicts remain traceable:** failed former Student-t/spatial assumptions, old v1.1 population transfer limitations are historical, while v1.2 approved EB takes precedence for current Pfa verdict.
6. **Engineering dependencies:** fixed-point, RTL, architecture/implementation, resources/timing and hardware validation belong to future authorized stages and are NOT already complete.
7. **Contract-status nuance:** S02 Pd and range goals were originally design targets. The engineer has now accepted the fixed-scenario Pd protocol and observed result as a stage evidence decision; no unauthorized retroactive edit of the S02 requirement matrix was made.

## Progress calculation and hold point

Approved rubric: 12 equal stage weights; eight equal S03 criteria. S01 and S02 already completed, S04-S12 not started. Before this final audit S03: 6/8=75%, total (2+6/8)/12*100=22.916666666666668%.
After evidence review: S03-C06 is newly verified with approved v1.2 methodology, separation/preflight and valid final Pfa and accepted Pd evidence; **7/8=87.5%**. Overall **(2+7/8)/12*100=23.958333333333332%**. S03-C08 remains open and no Gate-S03 approval is granted.
This progress change reflects evidence review of C06 only, not an automatic promotion due solely to Pd PASS.

## Evidence SHA-256
- engineering/S03-execution-manifest-v0.1.json: 630734f64602357dc4af9ee97d1dcedf340ec12eed62561a8178675b39792f55
- engineering/S03-unit-tests-v0.5.log: f25a8371a79157434f6f3ecb8f31f469c04ba87164fd6373ed5117b22408d1e6
- engineering/S03_six_case_reference_smoke.json: a3c97fd8002c3da7d4a2a60e68c8a73bf7d2079e332fc1e9cd4f475c076771ab
- engineering/S03-initial-execution-report-v0.1.md: 14afc789fcbc692c85e6f11dedd591c75510030f4ceb2a1fe24fed30451e01b5
- engineering/S03-C04-EB-preflight-evidence-manifest-v0.1.json: 76738f1cddfe9cc2a1fd430a4f0e35a4ede153a8fd627b41a2cf5bb890e08793
- engineering/S03-C04-FINAL-Pfa-20000CPI-EmpiricalBernstein-v1.2.json: 6dab2a8a6669b698a53e74f88105b61169c02f819ac72d3674a94d34aca9cc7f
- engineering/S03-C04-FINAL-Pfa-EB-20000CPI-result-report-v1.2.md: 9eaeade79f2d31aaf8046197cea32fb99aa9cf308bd721cd2a8ad6a126b7f86e
- engineering/S03-C04-FINAL-Pfa-EB-evidence-manifest-v1.2.json: 33df66af43aba8d083d30ac6a69375c056f9204961b06cebb7e4057bd787e6ef
- engineering/S02-C-CFAR-02-CONTRACT-APPROVED-v1.2.md: 6e07ab218cd76f8358d56e3de0bbbc57dc62eff82b702222c0bb47f3b9ca1f3e
- engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json: 23f07e63950c8bd4f3b04a805c37a46792b0068ae918b25d0713dd65a15c51a0
- engineering/S03-Pd-MAIN-1000CPI-v1/RAW-CPI-records.jsonl: a676ee7f23065e9a72ce14121172805d80cc9a9358b79e9c960809433b70ae55
- engineering/S03-Pd-MAIN-1000CPI-v1/RESULT.json: ee0caae031c1e3dd96264232f07d7a57db4745f2482ec72357df2ba85cbbb510
- engineering/S03-Pd-MAIN-1000CPI-v1/REPORT.md: c3c03df96a1fc0c34c4c758640ae09ec7aeaefe75bcd067377a31f74ee8e35f3
- engineering/S03-Pd-MAIN-1000CPI-v1/STARTED.json: 1253672d24dc84cc14d9f8f8c1a79bc9a9c971b8c9aa4749ab7c0889cb89d23f
- engineering/S03-Pd-MAIN-1000CPI-v1/MANIFEST.json: b01d98e72ee78a81ec551acba0be24b26a5d2cacfda9a7cb08f7529ca8dc5253
- engineering/S03-Pd-MAIN-FIRST-ATTEMPT-INCONCLUSIVE-v1/RESULT.json: 217f6f4bb936f3c01635681075ed972c1ee273bd810b8d2034907db15b6b13ae
- engineering/S03-Pd-independent-fixed-execution-contract-v0.3.json: 602e4fe6132c4d8521b33c61a1c2cd413c3e75cc4325fe8b9bca6dea966bed5f
- s03_reference/model.py: 2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b
- s03_reference/pd_acceptance_candidate.py: aa0661b52aa56a1da3b3b41332f0927eba58f4fcddace12a391c2488404784ea
- engineering/S03-progress.json: 8bb29ac448d27e25c6232ac30eeca3b5db32221e9c8ec2f4d34230aae75dbe59

Git pre-audit HEAD: 1faf1464ec3b5c68cb995686f9f20146ddaaa3f5; UTC review record: 2026-11-11T08:25:57.840669+00:00.

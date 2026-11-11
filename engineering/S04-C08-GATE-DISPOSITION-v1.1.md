# AX309-RDSP-001 | S04-C08 Gate Disposition v1.1

**Current disposition: OPEN / NO-GO.** C01–C07 remain accepted within their approved scopes. REQ-SCR-01 is PASS. The engineer-approved REQ-RNG-03 campaign has completed and is **FAIL (4/8 mandatory cases)**. S04-C02-RISK-PERFORMANCE remains OPEN because the existing contract requires statistical Fixed-Point qualification and no such test was authorized or executed. Gate-S04 is not closed.

## REQ-SCR-01 — engineer decision and qualification

**Approval authority:** Project system engineer, explicit decision supplied 2026-11-12. The engineer approved SCR +10 dB, −10 dB and no-clutter cases; generator tolerance ±0.1 dB; stationary coherent complex clutter; relative phases 0°, 90°, 180° and 270°; and exact-zero MTI output only for the isolated stationary-clutter controls. Execution was expressly authorized. No Float model, architecture, coefficient, numeric contract or FFT schedule change was made.

**Corrected measurement definition:**
- Target range cell: k=40.
- SCR is the ratio of target-only to clutter-only mean power at that single range cell, averaged over all 33 pulses, before noise addition and Q1.15 quantization.
- Range cells [40,56) are output-monitoring support only; they are not the SCR measurement region.
- Clutter phase offsets are defined relative to the target's first sample at k=40, pulse 0. The target Doppler phase then evolves naturally at bin +4.
- Approved target profile: k=40, Doppler +4, amplitude 0.18, initial phase 0, input SNR 20 dB, g=1. The same deterministic noise realization is paired across the nine target cases.

**Executed scenarios:** one no-clutter target control; four phases at SCR +10 dB; four phases at SCR −10 dB; and one isolated clutter-only control at each SCR level. Total 11. The clutter-only controls have no target and no added noise.

**Results:**
- All 11 scenarios completed PASS.
- Maximum measured SCR deviation: 1.78e-15 dB, within ±0.1 dB.
- All nine target scenarios: target correctly associated at (range 40, Doppler +4) in both Float and Fixed.
- Float and Fixed cluster-peak coordinates identical in all 11 cases; changed CFAR CUTs: zero.
- Both isolated clutter-only cases: exactly zero MTI output in Float and Fixed; zero CFAR clusters.
- Input saturation: zero across all 11 inputs.
- Fixed internal arithmetic and power overflow: zero across all 11 cases.
- Independent C03 Fraction oracle: zero integer mismatches in MF (8,448 components), MTI (8,192), and each of FFT1–FFT5 (8,192 per stage), for every case.
- Independent C03 oracle: all 4,096 power cells and 2,782 valid CFAR CUT decisions per case PASS.
- Independent C05 union-find grouping oracle: PASS for all cases.

**Float/Fixed diagnostic errors in original-amplitude units (maximum across cases):** MF MAX 1.836e-4, RMS 1.384e-4; MTI MAX 2.765e-4, RMS 7.151e-5; final FFT MAX 4.807e-3, RMS 4.583e-4. Power MAX difference 0.6782 and RMS 0.01605 in original power units. No separate numeric Float/Fixed error threshold was approved for this requirement; these values are reported, not used to invent a new tolerance. Each target-present case yielded six clusters in both models, with identical peak coordinates. A separate false-cluster/Pfa threshold was not part of this SCR approval, so this deterministic run makes no Pfa/Pd claim.

**Evidence:**
- Reproducible runner: `engineering/s04_numeric/s04_c08_req_scr01_qualification_v1.py` (SHA-256 `bfd64e2c878ea4ff1b76aa23f0d022328f0e0cee36bc590bfdef389e5f9bb77b`)
- Result and per-case trace: `engineering/s04_numeric/req_scr01_v1/REQ-SCR-01-RESULTS-v1.0.json` (SHA-256 `8039f7cb5b975059ffbbf379d85a740f06cba88447a008952f26c76f2ab2fc2a`)
- Exact Float and Q1.15 input arrays: `engineering/s04_numeric/req_scr01_v1/REQ-SCR-01-INPUTS-v1.0.npz` (SHA-256 `be75904067c6f7204085d001a96d36077c89b7c18fe250a6945725966a6b3136`)
- Float and Fixed stage output arrays: `engineering/s04_numeric/req_scr01_v1/REQ-SCR-01-OUTPUTS-v1.0.npz` (SHA-256 `17aa6b04e9823c34e9a0ead6fbb153fd82dd1d5f5e2e4b804b9c40c5847bcecc`)

**Decision: REQ-SCR-01 = PASS_ENGINEER_APPROVED_11_CASE_FLOAT_FIXED_ORACLE.** The approved scope is limited to this stationary, uniform, coherent clutter envelope and the 11 specified cases. It does not qualify wider correlated/heterogeneous clutter, statistical Pfa/Pd, or other target/source populations.

## REQ-RNG-03 — approved requirement and executed qualification

**Engineer-system approval:** 2026-11-12. The engineer approved two equal-power targets with amplitude 0.18 each, g=1, common Doppler bin +4, no noise, no clutter, range separations of 3/4/5 samples, relative phases 0°/90°/180°/270°, and maximum range error ±1 bin. For 4- and 5-sample separation, both targets must be represented by two distinct cluster records with one-to-one truth association; every one of the eight cases must pass. Any merge into one cluster is FAIL. The 3-sample cases are characterization-only; their failure alone does not fail the requirement.

**Physical reference:** theoretical resolution c/(2B) = 599.584916 m for B=250 kHz. One range sample is 149.896229 m. The tested separations are:
- 3 samples: 449.688687 m (characterization only)
- 4 samples: 599.584916 m (mandatory)
- 5 samples: 749.481145 m (mandatory)

**Execution sequence and frozen conditions:**
- All 12 Float scenarios were generated and processed first using the unchanged S03 Float model and alpha 7.476912055027923.
- The exact complex128 IQ arrays from that Float run were archived. Fixed-Point then read those archived arrays; it did not regenerate the inputs.
- Fixed-Point used the unchanged architecture C, g=1, and FFT shifts [0,1,0,1,1].
- No additional statistical tests, threshold tuning, model changes, architecture changes or contract changes were performed.

**Mandatory 4-/5-sample results:**

| Separation | Relative phase | Float association | Float clusters | Fixed association | Fixed clusters | Changed valid CUTs |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 0° | 1/2 | 9 | 1/2 | 13 | 28 |
| 4 | 90° | 1/2 | 9 | 1/2 | 9 | 32 |
| 4 | 180° | 2/2 | 20 | 2/2 | 16 | 54 |
| 4 | 270° | 1/2 | 9 | 1/2 | 9 | 36 |
| 5 | 0° | 1/2 | 11 | 1/2 | 14 | 30 |
| 5 | 90° | 2/2 | 16 | 2/2 | 16 | 38 |
| 5 | 180° | 2/2 | 20 | 2/2 | 18 | 50 |
| 5 | 270° | 2/2 | 15 | 2/2 | 16 | 41 |

- Float: 4/8 mandatory cases PASS; 4/8 FAIL.
- Fixed: 4/8 mandatory cases PASS; 4/8 FAIL.
- Combined Float-and-Fixed acceptance: 4/8 PASS, not the required 8/8.
- The four passing cases are 4-bin/180° and 5-bin/90°, 180° and 270°. Both targets were associated at their exact truth range bins in these four cases (zero-bin error).
- In each failed mandatory case, only one of the two truths obtained a qualifying cluster association; the other target was missed under the approved one-to-one rule. These are requirement failures regardless of the number of unrelated additional clusters.
- The 3-sample characterization cases produced 1/2, 1/2, 2/2 and 1/2 associations at phases 0°, 90°, 180° and 270°, respectively, in both Float and Fixed. This does not affect the mandatory pass count.

**Fixed-Point/oracle and archive checks:**
- All 12 Fixed cases completed. The execution log records C03 stage arithmetic, C03 power/CFAR and C05 independent grouping oracle PASS for every case.
- C03 stage comparison covers MF (8,448 integer components), MTI (8,192), and each of FFT1–FFT5 (8,192 per stage), with zero mismatches required by the oracle helper.
- All 4,096 power cells and 2,782 valid CUT decisions per case passed the independent C03 Fraction checks; C05 union-find grouping passed.
- Q1.15 input saturation: zero across all 12 inputs. Reconstructed power overflow events: zero. Fixed FFT, power and CFAR archive reconstruction was exact for all 12 cases.
- The first Fixed invocation stopped at preflight, before processing any case, because the script expected 72 Float output arrays instead of the actual 60. After correcting that count, the authorized Fixed run completed all 12 cases and wrote both Fixed archives; only its final JSON assembly stopped on a Python KeyError. The report was recovered from the archived Float/Fixed arrays; no signal-chain or C03/C05 oracle campaign was rerun. The report-assembly source defect was corrected afterward.
- Internal overflow counts for failed and characterization cases were not persisted in the first runner's NPZ. For the four mandatory cases printed PASS, the runner's PASS predicate required zero input saturation, internal overflow and power overflow. No internal-overflow count is claimed for the failed cases. This evidence limitation does not alter the 4/8 requirement failure.

**Float/Fixed diagnostic differences (maximum across all 12 cases, original-amplitude units):** MF MAX 1.171883e-4, RMS 2.651416e-5; MTI MAX 1.668360e-4, RMS 3.896953e-5; final FFT MAX 6.221675e-3, RMS 3.211390e-4; power MAX 1.299246, RMS 4.210561e-2 in original power units. The number of changed valid CFAR CUTs ranged from 28 to 54 per case. No new Float/Fixed numeric error threshold was approved for this requirement; these values are diagnostic only.

**Engineering interpretation:** the Float reference itself fails four of the eight mandatory cases, and Fixed fails the same four. The independent Fixed arithmetic and detection-map oracles pass. Thus these misses are not demonstrated to be caused by a bit-true arithmetic mismatch; they are observed system-level detection/separability failures in the approved deterministic two-target scenarios. The strong phase dependence is recorded as observed behavior. No causal ablation, threshold adjustment or algorithm retuning was authorized or performed.

**Evidence files and SHA-256:**
- Float-first runner: `engineering/s04_numeric/s04_c08_req_rng03_float_first_v1.py` — `c2a5e58d4057c7a6322f26e7b189a6c8154e3b06ae1dac255bd2e82ca7f74369`
- Fixed-from-archive runner: `engineering/s04_numeric/s04_c08_req_rng03_fixed_from_archive_v1.py` — executed source SHA-256 `ac34be652ee728311bce8d79e08ce0b77878deef9988f2bd01de83d7e8d14521`; corrected report-assembly source SHA-256 `e8c24ccfb31fe725c3ca210e3972d50b74b4d054482079e2efe39176de1814c6`
- Archive report recovery utility: `engineering/s04_numeric/s04_c08_req_rng03_recover_report_v1.py` — `699c8b4ab46b5b54567b01a065cafefa7b8fcdf319682f333c50545d774ef03e`
- Combined result: `engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-RESULTS-v1.0.json` — `757dfccf61ddd54f84bdbf82a58e7c36c8b9ea9daf9e0c03bbcd1771bef3f5a2`
- Exact Float IQ inputs: `engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-INPUTS-v1.0.npz` — `c06ae8b87d0f87c80cb7a275af514d6e8f9cdb5628ba7adb9d38c1294a8f2940`
- Float outputs: `engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-FLOAT-OUTPUTS-v1.0.npz` — `363eb534f5c0f1f53ac324306366d82177d8ed976a38708ea6064dc40cec01ea`
- Exact Q1.15 input codes: `engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-Q15-INPUTS-v1.0.npz` — `140da68ded243fcd042462b6b4dc0549288c477651cd01e8c48378d35e2f1b35`
- Fixed outputs: `engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-FIXED-OUTPUTS-v1.0.npz` — `96c2d0d8b727f7ada6d016f91376a3b0d508b9999151ff63771ca55ff6119152`

**Decision: REQ-RNG-03 = FAIL_ENGINEER_APPROVED_12_CASE_QUALIFICATION_4_OF_8.** No acceptance or waiver is recorded. The requirement remains a Gate-S04 blocker.

## S04-C02-RISK-PERFORMANCE — existing-contract review

The selected-C open-obligation contract requires an independently predeclared Integer/Fixed-versus-Float performance protocol, a fixed N, no replacement or optional stopping, valid source-class definitions, seed separation, and independent statistical qualification of the approved S02 performance targets.

Existing C06 evidence is 16/16 PASS on two bounded deterministic populations (8 noise-only, g=5; 8 single-target reference-like, g=1). That evidence is deterministic numeric qualification and does not establish statistical Fixed-Point Pfa/Pd. The accepted S03 statistical Pfa/Pd results are Float-reference results; they do not qualify the Fixed-Point chain.

The engineer instruction expressly prohibited additional statistical tests. No Fixed-Point statistical campaign was generated or run. Under the existing contract, the deterministic C06 evidence cannot be substituted for the missing statistical qualification, and no residual-risk waiver or contract amendment has been approved.

**Disposition: S04-C02-RISK-PERFORMANCE = OPEN_NOT_EXECUTED / GATE-BLOCKING.** This review makes no new test authorization and changes no denominator, seed, acceptance limit or source profile.

## Final Gate-S04 disposition

Two blockers remain:
1. **REQ-RNG-03: FAIL** — only 4/8 mandatory paired-target scenarios pass in both Float and Fixed; required 8/8.
2. **S04-C02-RISK-PERFORMANCE: OPEN** — statistical Fixed-Point qualification remains unexecuted under the existing contract.

**Gate-S04: NO-GO. C08 remains OPEN.** S04 remains 7/8 = 87.5%; overall project progress remains 32.29%. No completion credit is added for documentation or diagnostic evidence.

S05 and RTL implementation are not resumed because Gate-S04 exit conditions are not satisfied. No additional test, retuning, architecture change, Fixed-Point contract change, RTL or synthesis operation was performed or authorized by this decision.

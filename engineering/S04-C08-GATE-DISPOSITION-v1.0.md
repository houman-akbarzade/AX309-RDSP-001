# AX309-RDSP-001 | S04-C08 Gate Disposition v1.0

**Current disposition: OPEN / NO-GO.** C01–C07 remain accepted in their approved scopes. REQ-SCR-01 is now closed by the engineer-approved, 11-scenario Float/Fixed qualification below. C08 remains incomplete because REQ-RNG-03 and S04-C02-RISK-PERFORMANCE are still binding Gate-S04 blockers.

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

## Remaining Gate-S04 blockers

1. **REQ-RNG-03:** equal-power two-target resolution near 600 m. The approved model and numeric criteria still require the relative-phase/separation cases and quantitative resolved-pair rule to be frozen before execution.
2. **S04-C02-RISK-PERFORMANCE:** deterministic fixed-point agreement does not establish statistical Fixed-Point performance. The approved risk-disposition/change-control path or a minimum statistical qualification remains unresolved.

**Gate decision:** NO-GO. C08 remains OPEN; S04 remains 7/8 = 87.5%; overall project progress remains 32.29%. No credit is added for documentation alone. Next work is REQ-RNG-03 only; no S05 work is started.


## REQ-RNG-03 — existing evidence and minimum proposed qualification (not yet authorized)

**Existing S02 decisions:** S01-Q03 provisionally accepted theoretical range resolution of about 600 m for a 250 kHz LFM bandwidth, with measurable acceptance criteria deferred to S02. S02-D06 explicitly separates single-target localization from two-target range resolution, requires integer-sample range estimation and reporting error in bins/metres, and does not require sub-sample interpolation. The approved S02 matrix still defines REQ-RNG-03 as a binding test: sweep paired targets around 600 m and measure resolved clusters. Its acceptance rule is still OPEN: freeze resolved-pair definition, equal received power and success criterion.

**Existing Float evidence (development only):**
- `engineering/S03_extended_boundary_multitarget_cases.json` contains `two_ranges_4bin` and `two_ranges_5bin`: equal-amplitude targets, same velocity 1.5 m/s, no added noise or clutter, zero relative phase, one deterministic scene each, and an uncalibrated CFAR alpha.
- At 4-bin separation, only 1/2 truth targets were matched, 1 was missed, and 4 detections were unmatched. At 5 bins, the result was also 1/2 matched, 1 missed and 4 unmatched. These are developmental characterizations, not formal PASS/FAIL evidence.
- The existing `same_speed_two_ranges` case resolved 2/2 targets at 20-bin separation, about 3 km; it does not establish resolution near 600 m.
- No approved relative-phase sweep, target-amplitude envelope, formal association tolerance or quantitative success rule exists. No existing case closes REQ-RNG-03.

**Physical reference:** theoretical resolution c/(2B) = 599.584916 m; one range sample c/(2Fs) = 149.896229 m. Thus 3, 4 and 5 samples correspond to 449.688687 m, 599.584916 m and 749.481145 m.

**Minimum proposed deterministic Float/Fixed matrix (pending engineer approval):**
- Two targets at range delays k1=40 and k2=40+delta-k, using delta-k values of 3, 4 and 5 samples. Both are within the valid range/CUT domain.
- Equal received power means equal target-only input component power, measured separately before coherent summation, noise and Q1.15. Proposed amplitude is 0.18 for each target, reusing the existing C01 single-target lab amplitude; proposed input gain g=1.
- Both targets use the same on-bin Doppler bin +4 (1.875 m/s nominal), with no noise and no clutter. This isolates range separability; it makes no statistical Pd/Pfa claim.
- Set target 1 phase to 0 and target 2 relative phase to 0°, 90°, 180° and 270° at pulse 0. Total: 3 separations × 4 relative phases = 12 deterministic cases.
- Use the existing S03 Float chain and approved S03 alpha 7.476912055027923. Feed the exact same generated IQ arrays to frozen C Fixed-Point with unchanged architecture C and FFT shifts [0,1,0,1,1]. Check C03 stage arithmetic oracle, C03 power/CFAR oracle and C05 independent grouping oracle.

**Proposed quantitative resolved-pair rule (requires approval):**
- For the nominal 4-bin and above-resolution 5-bin separations, require both Float and Fixed to produce two distinct target-associated cluster records, one-to-one with the two truths; each associated peak must be within ±1 range bin of its target and at Doppler bin +4. Require 8/8 cases to pass (4 phases at each of 4 and 5 bins).
- The 3-bin/450 m cases are below nominal theoretical resolution and are characterization-only; report matched/missed/extra clusters and range errors, but do not count them as PASS/FAIL.
- Additional clusters are reported separately and are not assigned an invented false-cluster limit. Any input clipping or internal/power overflow is a failure of that fixed-point case. Float/Fixed MAX/RMS and mask/record differences are reported; no unapproved numerical error tolerance is invented.

**Only engineer decisions required before execution:** approve (1) the two-target amplitude 0.18 each and g=1 envelope, (2) noise-free/no-clutter and common Doppler +4, (3) the 3/4/5-bin spacing matrix and four relative phases, and (4) the ±1-bin one-to-one association rule and 8/8 pass criterion at 4/5 bins. These choices define a narrow deterministic resolution qualification only; they do not claim general performance over amplitude, SNR, Doppler or clutter populations.

**Current status:** REQ-RNG-03 remains BINDING OPEN. No RNG scenario has been run under this proposal and no acceptance parameter has been changed. Await engineer approval before generating the 12 inputs or executing Float/Fixed.

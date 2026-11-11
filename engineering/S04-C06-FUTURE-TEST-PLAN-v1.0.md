# AX309-RDSP-001 | S04-C06 Prospective Test Plan v1.0

**Preparation only. No acceptance tests, vectors, CPIs, or statistical campaign have been executed or authorized by the current order.** This plan implements the independent decision `e8a89dd8472cfbbb4859f924c18ca8386709db44`; the controlling contract is `engineering/S04-C06-EXECUTION-CONTRACT-v1.0.md`.

## 1. Entry gates

A future C06 execution requires a separate explicit engineering authorization naming the permitted deterministic/numerical test package, source population, test-vector manifest, fixed N/denominators, and execution environment. Approval of criteria A–E alone is not execution permission.

Before accepting any test package, freeze and hash:
- independent decision and execution contract;
- selected-C arithmetic contract, selected-C implementation, Float S03 reference, independent integer/rational oracle and their version/commit IDs;
- C01 profile/g registry and source generator specification;
- every input/vector/CPI ID, complete source bytes/hash, source/profile/g metadata and scenario class;
- environment/dependency manifest, test procedure, exact output schema and event-log schema;
- predeclared fixed N, all denominators, and any prospective seed IDs. Accepted S03 seeds must not be reused.

No alpha calibration, alpha change, architecture/format/shift modification, post-hoc tuning or denominator adjustment is part of this plan.

## 2. Mandatory pre-test applicability gate (run separately for each candidate CPI)

The preflight reviewer must record PASS/FAIL/INCONCLUSIVE for every item. Any missing or unprovable mandatory item blocks the CPI from VALID_PERFORMANCE.

| ID | Pre-test evidence required | Gate |
|---|---|---|
| PF-01 | Decision SHA and execution-contract SHA pinned; current selected-C contract and source implementation hashes match the approved manifest | Required |
| PF-02 | Architecture C; all W/F formats, coefficients, alpha, RNE/narrowing, full-width arithmetic and shifts [0,1,0,1,1] match the frozen C contract exactly | Required |
| PF-03 | Profile/g authorized before IQ generation: NOISE_ONLY_UNIT/g=5/no target/no clutter OR SINGLE_TARGET_REFERENCE_LIKE_LAB/g=1/predeclared single target k=40, Doppler +4, amplitude 0.18, phase 0, noise power 0.000324, no clutter | Required |
| PF-04 | Full 33×128 complex IQ payload (4224 complex / 8448 scalar components), byte order, source/generator identity, dimensions, source SHA and immutable metadata validate | Required |
| PF-05 | Every pre-quantized component satisfies abs(Re(x/g)), abs(Im(x/g)) <= 1+2^-15; check every sample, not a statistical estimate | Required |
| PF-06 | Apply C01 thresholds to every original Float component: positive clip if `x >= g*65535/65536`; negative clip if `x < -g*65537/65536`. Require zero input clip events and complete ordered clipping telemetry/counters | Required |
| PF-07 | Conservative input-specific interval/headroom analysis proves all MF products/16-tap accumulators, MTI differences, FFT products/pairs/butterflies, power squares/sums and SUM40 pre-narrow values remain representable in their frozen widths | Required |
| PF-08 | Instrumentation/guard coverage is complete at every pre-narrow boundary; stable event IDs, full pre-limit integers, stage/location/sign, sticky flags and complete ordered logs are available. Runtime must confirm zero events | Required |
| PF-09 | Original-input Float reference, quantized-input Float reference and selected-C output are generated from the identical immutable input; scaling, valid indices and stage denominators are documented | Required |
| PF-10 | Independent integer/rational oracle is separately implemented/reviewed and shares no implementation code or expected outputs with the unit under test | Required |
| PF-11 | Fixed N, all vector/CPI IDs and denominators are frozen before processing; no accepted S03 seeds; all intended records retained | Required |
| PF-12 | A predeclared STRESS_ONLY manifest is separate from VALID_PERFORMANCE; deliberate clipping/tie/overflow cases cannot enter performance denominators | Required |

**Critical distinction:** PF-07 is a pre-run static proof for the actual candidate inputs; PF-08 also requires run-time confirmation. **PF-08 implementation status:** historical C03 artifacts already provide verified complete JSONL readback for 16,896 input-clipping stress events and 159 forced internal-overflow events (17,055 total across seven files); these are deterministic diagnostic fixtures, not C06 CPI evidence. The raw v0.5 `Telemetry` summary itself still retains only a 24-event preview. Static guard inventory now includes IQ, MF products/pairs/accumulator/output, MTI output, all five FFT product/pair/butterfly/output sites, POWER_RAW W51, POWER U46, SUM40 U52, and CFAR left/right products W68/W72. The two previously assertion-only unsigned width checks now call telemetry guards before their original assertions; no arithmetic or assertion semantics were changed. A separate C06 adapter, `engineering/s04_numeric/s04_c06_fulltrace_capture_v1.py`, now streams all events into CPI-scoped input/processing JSONL files with stable UUIDv5 IDs, CPI/profile/g identity, full pre-narrow integer, signed/unsigned bounds, stage/location/sign/sticky flag, per-scope ordering, fsync, readback SHA-256, uniqueness, deterministic-ID and legacy-digest checks. It refuses overwrite and preserves `.partial` traces plus an INCOMPLETE manifest after interruption. Seven focused unit tests cover >24 events, zero-event files, C04 module wrapping, interrupted capture, no-overwrite, C01 profile/g pairing and unsigned POWER/CFAR guard event fields. Three diagnostic-only integration smokes exercised the real telemetry call sites: v0.5 input stress persisted 8,448 events, C04 Stage Capture input stress persisted 8,448 events, and a synthetic internal-overflow injection persisted 159 processing events. All six JSONL files (including three valid empty-scope files) and three manifests are retained under `engineering/s04_numeric/c06_fulltrace_smoke_v3/`; 17,055 records have unique IDs and passed hash/readback/order/field verification. These deterministic stress/injection runs are diagnostics only, not C06 acceptance vectors or CPIs. The Python guard/recorder path is implemented and exercised on both input and processing telemetry paths, but PF-08 remains pending exact C06 executor binding to the final frozen candidate runner, an independently authorized future candidate-CPI capture and independent review. This is an evidence/telemetry requirement, not permission to change the arithmetic. If the conservative static proof cannot establish headroom, do not launch that candidate as VALID_PERFORMANCE. If runtime telemetry reports any input clipping, internal overflow/saturation, or incomplete trace, mark the affected CPI INCONCLUSIVE and preserve it. No result may be retrospectively relabelled to pass.

## 3. Prospective qualification work packages

Execution order is fixed; no work package below has been run under this order.

| Package | Scope and method | Required result |
|---|---|---|
| T-A1 | For each authorized C01 profile, pair original Float, reconstructed-input Float and selected-C stage values; calculate complex MAX/RMS at MF, MTI and FFT1–FFT5 in original amplitude units | All seven MAX and RMS values at or below the exact approved g-specific ceilings; source and processing error contributions separately reported |
| T-B1 | Independent integer/rational comparison of all stored stage outputs and every subsequent integer result | Zero mismatches across MF, MTI, all FFT stages, U46.30 power, U52.30 SUM40, 2782 CUT decisions, components, peak/tie and target records |
| T-C1 | Compare original Float and Fixed CFAR decisions on all 2782 valid CUTs; calculate both signed margins, power uncertainty and alpha quantization contribution; retain every changed CUT | Changed CUT outside its approved uncertainty envelope: FAIL. Within envelope: AMBIGUOUS and affected Float/Fixed comparison INCONCLUSIVE. No allowed ambiguity count currently exists |
| T-D1 | Replay both historical `g1:phase_interference` and `g5:phase_interference` vectors; verify exact Float maximum-power tie, same unchanged alarm/cluster component, frozen Fixed peak rule, exact independent integer grouping and records | Apply only `FLOAT_REFERENCE_EXACT_TIE_SPLIT_BY_QUANTIZATION` if all four decision conditions hold. Any non-tied displacement, split/merge, missed target or record mismatch is not waived |
| T-E1 | Validate immutable pre-CPI metadata, fixed N/denominators, profile/g, payload/reference hashes, complete traces and disposition logic | VALID_PERFORMANCE / INCONCLUSIVE / STRESS_ONLY assigned exactly under the approved contract; no deletion, replacement, rerun, retuning or denominator change |

For T-A1, source quantization is (z_Q-z_F); processing error is (z_C-z_Q); total is (z_C-z_F). Calculate total MAX/RMS from paired total complex errors, not by adding the component maxima/RMS values. Shift scaling is exact under the frozen arithmetic and is included in reconstruction/error propagation; do not introduce a new shift-error tolerance.

For T-C1, the uncertainty envelope is exactly the one in the execution contract. The Fixed-vs-independent-integer-oracle comparison in T-B1 remains exact even if a Float-vs-Fixed CUT is AMBIGUOUS.

For T-D1, no epsilon is permitted when proving the Float tie. Preserve both original vectors and all source/output evidence. This exception is not a general peak-location tolerance and does not establish estimator accuracy.

## 4. Population, fixed N and status handling

Only the two C01 populations in §1 of the execution contract can be considered VALID_PERFORMANCE. A deterministic crafted edge vector, any other g, or an out-of-profile source must be predeclared diagnostic/STRESS_ONLY and cannot expand C01.

Both historical `phase_interference` vectors must be replayed for D. They may be VALID_PERFORMANCE only if their immutable source metadata independently proves exact membership in the relevant C01-authorized population; otherwise they are diagnostic/STRESS_ONLY and cannot extend C01 (in particular, g=5 never authorizes a target-bearing case).

The exact fixed N and vector manifest are deliberately **not chosen in this planning document**. They must be specified, hashed and independently approved before any future run. The existing C01 noise-only 0.1%/20,000-CPI whole-campaign rule is unchanged; this plan does not start that statistical campaign or generalize its stopping rule.

A CPI with missing metadata, invalid profile/g, violated/unproven input envelope, input clipping, internal overflow/saturation, missing telemetry/reference, or unresolved ambiguous Float/Fixed CFAR decision is INCONCLUSIVE. Preserve it and its position in the prelocked records. STRESS_ONLY is declared before processing and excluded from performance denominators. No deletion, replacement, automatic rerun, top-up, optional stopping, or post-hoc reclassification.

## 5. Evidence package and independent review

For every executed package, archive: authorization reference; decision/contract/code/reference/oracle hashes; environment; source and input hashes; immutable profile/g and vector/CPI IDs; fixed N and denominator; all original Float, reconstructed-input Float and Fixed stage values or lossless hashes plus trace access; per-stage MAX/RMS and source/processing decomposition; complete pre-narrow overflow/clipping traces; full 2782-CUT masks/margins/uncertainty classification; cluster membership, peak and target records; all PASS/FAIL/INCONCLUSIVE/STRESS_ONLY statuses; and a SHA-256 manifest.

Independent reviewer must reproduce the oracle and summary metrics from the frozen artifacts, check every denominator and exception, and sign the exact manifest. C06 stays OPEN until this review is complete. A C06 A–E PASS does not close REQ-SCR-01, REQ-RNG-03 or Gate-S04.

## 6. Explicit exclusions / current status

No SCR/clutter +10/−10 dB or two-target 600 m tests are planned here. Their definitions and source authorization are not approved. REQ-SCR-01 and REQ-RNG-03 remain binding OPEN Gate-S04 blockers.

The numeric-criteria approval supersedes the earlier C02 finding that MAX/RMS limits were unapproved, but does not supply execution evidence. The separate full-overflow-trace obligation above remains OPEN. No acceptance tests, CPI, new seeds, statistical main CPI, alpha recalibration, RTL, synthesis, FPGA or hardware test has been run or authorized by this order.

**Current state:** C01–C05 PASS within approved scope; C06 OPEN (A–E criteria approved with conditions; execution pending); F not approved; S04=62.5%; overall=30.2083%; Gate-S04 OPEN.

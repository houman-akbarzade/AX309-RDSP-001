# AX309-RDSP-001 — S04-C01 configurable input policy decision package v0.4

**PROPOSED / NOT APPROVED.** S04-C01 HOLD, S04-C02 OPEN, Gate-S04 OPEN, stage 0%, overall 25%. No numerical format, g, shift schedule or error threshold is ratified. No radar CPI, RTL or hardware tests authorized.

## 1. Candidate pre-CPI admission and selection
The candidate approach is CONFIGURABLE g with explicit metadata. Before receiving/processsing a CPI, a future engineer-approved profile registry determines g from declared input population, frontend normalization, scenario envelope and profile version, NOT from current CPI detection outcomes, accepted Pfa/Pd samples or subsequent performance. Lock profile and g before upload; reject attempts to change g within a CPI.

| Declared source population | Admission proposal | Principal issue |
|---|---|---|
| NOISE_ONLY_UNIT | independent complex CN(0,1), 33x128 | significant saturation at g=1, needs preapproved profile and CPI-level risk |
| FIXED_PD_LIKE | isolated target k40 Doppler+4 amplitude .18, sigma²=.000324, no clutter | historical accepted Pd remains read-only; any new study needs new independent data |
| TARGET_OR_CLUTTER | specified target amplitudes/count, clutter mean/correlation, sigma² and signal normalization | without amplitude/envelope model cannot certify clipping risk |
| SATURATION_STRESS | declared deterministic overloaded arithmetic vector | may pass error-reporting oracle but NEVER counts as valid Pd/Pfa performance CPI |

A fixed g is simpler but may clip high-noise sources or waste precision for weak targets. Configurable g retains explicit reproducibility if selection is prospective and every CPI has immutable metadata. Adaptive g estimated from the same CPI requires its own approved causal rule, buffer/timing and statistical selection-bias qualification; it is NOT included in the configurable proposal.

## 2. Proposed state machine (not approved)
1. UNCONFIGURED: reject input unless input class and profile registry are approved.
2. PROFILE_SELECTED: choose a registry-listed positive rational g by a frozen rule from known metadata BEFORE sampling/processing; proposed comparison values 1,2,4,8 are NOT an approved allowlist.
3. METADATA_LOCKED: record per-CPI ID, profile version/hash, exact g numerator/denominator, selection rule and scenario manifest SHA; forbid changes after this boundary.
4. INPUT_CONVERTED: signed 16-bit I/Q Q1.15, pulse-major LE, 4224 complex samples and 16896 bytes: q=clamp(RNE(32768*x/g), -32768,32767), reconstructed Float-domain sample = g*q/32768.
5. PROCESS: only under complete metadata, byte/dimension validation, counters and stable stage scales.
6. RECONSTRUCT: MF/MTI reconstructed with g, FFT reconstructed with g*sFFT, RD power/40-cell sum/mean/threshold/peak power with g²*sFFT². Ranges, velocities, Boolean flags not multiplied by amplitude scale.
7. COMPLETE: record status, all saturation events/counters and stage/input/metadata hashes.

## 3. Exact proposed host metadata schema
Canonical audit payload is UTF-8 JSON, keys sorted, compact separators, duplicate keys rejected, NaN/Infinity forbidden, scale stored as reduced positive integer fraction. A SHA-256 of the canonical bytes is stored in a separate OUTER envelope to avoid self-hash cycles. This is NOT an approved UART/FPGA wire ICD.

| Field | Required type / constraint |
|---|---|
| schema_version | string S04_INPUT_CONFIG_PROPOSED_V04 |
| project_id | AX309-RDSP-001 |
| cpi_id | nonnegative decimal uint64 string |
| population_id | future engineer-approved enum |
| scenario_manifest_sha256 | lowercase 64-hex |
| profile_registry_sha256 | lowercase 64-hex |
| profile_id / selection_rule_id | versioned nonempty strings |
| gain_num/gain_den | positive JSON integers <=2^63-1, gcd=1, no arbitrary float scale |
| input_format_id | candidate IQ_SIGNED_16_Q15_LE_INTERLEAVED |
| input_sample_count / input_component_count | integers 4224 and 8448 |
| input_payload_sha256 / source_manifest_sha256 | lower-case 64-hex |
| float_reference_cpi_sha256 | 64-hex or explicit null if data not preserved |
| scale_locked_before_sample | boolean true, justified by event time-order evidence |
| stage_scale_manifest_sha256 | lower-case 64-hex; includes numerical W/F, FFT shift vector and physical scale |
| input_saturation_count / input_saturation_any | integer 0..8448 and consistent boolean |
| saturation_count_by_polarity | nonnegative positive/negative integers summing to total |
| saturation_events_sha256 | SHA-256 over canonical *complete ordered* event stream |
| processing_status | VALID_PERFORMANCE, STRESS_ONLY, INCONCLUSIVE |
| invalid_reason_codes | array of standardized string codes |
| created_utc | verified UTC RFC3339 time, no fabricated historical timestamps |
| replay_event_ref / conversation_ref | project audit linkage, separately signed if necessary |

Serialized metadata has mandatory integrity checks; any unrecognized or missing scale causes INCONCLUSIVE, not a default g=1. Input file ordering and source calibration are different from stage-memory/RTL layout; a separate ICD is needed in S05.

## 4. Reconstructed-domain propagation
For arbitrary positive g, stored q in Q(W,F) represents original physical-reference-domain xhat = S_total*q*2^-F. With stage FFT scale sFFT:
- IQ, MF, MTI: S_total=g, except unit-magnitude MF coefficients S=1.
- FFT: S_total=g*sFFT; candidate A sFFT=1, candidate B sFFT=8 (both unapproved).
- Power, training sum, mean, threshold, selected peak power: S_total=(g*sFFT)^2.
- CFAR alpha is dimensionless; strict comparison uses stored CUT/sum under common power scale; quantized rounding and clipping can flip decisions despite ideal scale cancellation.
- Target amplitude expressed in normalized input-reference units reconstructs with g; signed Doppler bin/velocity and range are unaffected by gain.
Example B with g=4: FFT factor32 and power factor1024; this is metadata arithmetic, not an FPGA result.

## 5. Prospective CPI-validity and overload rules (not approved)
Performance CPI VALID only with an authorized, prospectively frozen class/profile/g, correct dimensions, provenance, metadata hashes, no unexpected component clipping/internal stage overflow, and verified scale reconstruction. If scale is missing/altered, payload corrupt, input unexpectedly clipped or arithmetic overflow unhandled: stop the future fixed-N acceptance study, mark INCONCLUSIVE and report completed CPI; do not replace or rerun autonomously. A separately declared SATURATION_STRESS vector can pass a saturation-reporting test while remaining excluded from performance denominators.

Capture saturated component count, ordered event index (pulse,range,I/Q,sign), first event, attempted pre-clamp magnitude, full event-list hash and explicit truncation status; internal MF/MTI/FFT-stage/power/CFAR sticky flags and counts, and counter-overflow status. Never silently wrap saturation counters or assume detection PASS permits clipping.

## 6. Required separate engineer decisions
Before any independent numeric testing: approve admitted input populations and conditioning laws; select a finite g allowlist and pre-CPI profile selection algorithm; fix exact metadata/trace scheme; define intended input saturation risk per CPI versus per component and status/denominator rule; choose A/B/hybrid, FFT shifts and certified numerical MAX/RMS/CFAR near-threshold acceptance; reserve disjoint DEV-NUM and ACCEPT-NUM data. Historical accepted Pfa seed 411091703 and Pd seed 411091704 are read-only and excluded from tuning.

Preserve v0.3 independent input scaling report, 176 deterministic arithmetic assertions, 8 unit checks, 22 Fraction CFAR checks, the 4135 extra unmatched target-present clusters (NOT Pfa), missing full archived IQ/power arrays, past Student-t/spatial failures, and limited Pd applicability.

S04-C01 and C02 OPEN; 0% S04 and 25% project; no architecture freeze, RTL, synthesis, hardware or independent stochastic acceptance run.

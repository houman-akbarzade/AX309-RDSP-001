# AX309-RDSP-001 | S04-C01 Bounded Baseline Contract Approval Package v0.7

STATUS: PROPOSED, NOT APPROVED. Independent engineer decision required. S04-C01 HOLD, S04-C02 OPEN, Gate-S04 OPEN, S04 0% and project 25%. No CPI, RNG, accepted Pfa/Pd seeds, RTL, synthesis or hardware work.

## 1. Limited source populations, S02 conflict

This proposed C01 sub-baseline includes only: (A) NOISE_ONLY_UNIT, 33x128 complex Gaussian CN(0,1) with independent real/imag components, no target or clutter; and (B) SINGLE_TARGET_REFERENCE_LIKE with 33x128, target echo amplitude 0.18, k40, Doppler bin+4, phase0, E|noise|²=.000324, no clutter. It is **not** a repeat or extension of accepted S03 Pd/Pfa evidence.

OUT OF SCOPE of this LIMITED sub-baseline: stochastic clutter (including SCR +10/-10 dB), multiple targets and two-target range separation, correlated clutter, off-grid Doppler, other SNR and amplitude laws. **UPSTREAM CONFLICT:** the approved S02 matrix marks REQ-SCR-01 as BINDING for SCR +10/-10/no clutter and REQ-RNG-03 as BINDING_TEST for two-target range resolution. C-DAT-01 requires per-target masks/SCR and S04 owns arithmetic considerations for the larger processing envelope. Thus this narrow proposal is NOT a waiver or proof of full S02 compliance. Engineer must formally decide that remaining SCR/two-target coverage is deferred to a named later verification task or enlarge C01; otherwise C01 approval is BLOCKED by scope incompatibility. No S02 source or obligation is altered.

## 2. Unapproved per-class candidate profiles

| Population | Input evidence | Proposed candidate, NOT approved | Outstanding decision |
|---|---|---|---|
| NOISE_ONLY_UNIT | exact CN(0,1), 8448 real components per CPI, independent source | N=20000 CPI, candidate g=5, target campaign-wide any-clipping risk ≤0.001 (0.1%) | Approve source admission, g, whole-campaign risk rule and weak-signal precision, or amend |
| SINGLE_TARGET_REFERENCE_LIKE | target amplitude .18, SNR20 at input, complex noise power .000324, no clutter | Compare g=1 vs g=2 separately; g=5 useful resolution comparison only | Select g and minimum allowed reconstruction accuracy, do NOT tune from accepted Pd data |
| SATURATION_STRESS | independent deterministic overload corpus | No normal-performance population status | Approve status/count/flag oracle and deliberate stress scope |

No g, set of allowed gains or numeric format other than the existing S02 *candidate* Q1.15 host encoding is ratified by drafting this proposal.

## 3. Full pre-CPI metadata and Q1.15 admission, proposed

Use configurable positive rational g chosen by declared population and frozen versioned profile BEFORE any CPI bytes are processed. Header records profile/registry hash, source scenario manifest, rule and stage scale IDs, CPI ID, g numerator/denominator, input/source hashes, exact 4224 complex/8448 components and 16896 byte pulse-major little-endian I/Q layout, saturation event locations/count and digest. The v0.4 metadata JSON Schema remains PROPOSED, not a UART ICD. No within-CPI gain change, current-CPI peak search, post-detection selection or silent fallback g=1.

Each Float component x maps to q = SAT16(RNE(32768*x/g)), reconstructed Float-domain xhat = g*q/32768. With RNE ties-to-even, saturation event iff x >= g*(65535/65536) or x < -g*(65537/65536). For unsaturated components |xhat-x| ≤ g/65536; complex |error|≤sqrt2*g/65536. MF/MTI reconstruct scale g, FFT scale g*sFFT, RD power and CFAR threshold scale (g*sFFT)², range/velocity and Boolean flags are unscaled. sFFT and other internal arithmetic remain UNSELECTED C02 decisions.

## 4. Quantitative no-clutter evidence, source-only precision

For noise-only CN(0,1), independent source components and independent CPI imply P_stop(N)=1-(1-p(g))^(8448*N), with p(g) obtained from exact asymmetric Q1.15 Gaussian tails. For candidate g=5 and N=20000, P_stop ≈0.0002597355468073 =0.02597355%, below proposed 0.1%. Candidate g=4 would yield ≈0.92608948946 (92.609%). Neither g nor acceptance ceiling is approved. This formula does not transfer to correlated clutter or unqualified source laws.

For the deterministic reference-like target waveform (NO stochastic realization generated), theoretical input clipping tails are log10 Pr(any clipping per CPI) ≈-901.9848 at g=1 and ≈-4441.0631 at g=2. These tiny probabilities cannot establish bit-true Pd or output performance. Input amplitude .18 is a design definition, not an observed acceptance-test tuning value.

| g candidate | Original-domain LSB g/32768 | max input complex error bound sqrt2*g/65536 | bound / reference amplitude .18 | nominal .18 / LSB |
|---|---:|---:|---:|---:|
| 1 | 3.051758e-5 | 2.157919e-5 | 0.0119884% | 5898.24 |
| 2 | 6.103516e-5 | 4.315837e-5 | 0.0239769% | 2949.12 |
| 4 | 1.220703e-4 | 8.631675e-5 | 0.0479537% | 1474.56 |
| 5 | 1.525879e-4 | 1.078959e-4 | 0.0599422% | 1179.648 |

The bound controls the complex input **sample** (target + source noise) when unsaturated, not separately an estimator of target amplitude after processing. It excludes MF coefficient error, FFT twiddles, overflow, CFAR threshold flips and bit-true detection. There is no approved minimum signal resolution or RMS error criterion.

## 5. Proposed fixed-N VALID / INCONCLUSIVE / STRESS_ONLY rules

VALID_PERFORMANCE only for a prospectively frozen admitted source class and profile/g, input dimensions/hash, complete stage scale metadata, recorded no unexpected input saturation/overflow, and correct reference conversion. Do not adjust sample membership or denominator after seeing any result.

INCONCLUSIVE for unapproved/missing/changed scale or class, unexpected input clipping, arithmetic overflow, corrupt bytes, missing stage evidence or invalid quantizer state. A future strict campaign may be approved to stop on first such event and report attempted and completed counts, with no addition, deletion, replacement, retry, optional stop or retroactive reweighting. An event is a *numerical exception* if forbidden under that contract, even though its source probability is nonzero under an unbounded Gaussian law. Such stop protocol is proposed, NOT operationally approved.

STRESS_ONLY uses separately registered deliberate overrange cases, grades exact saturation count/location/flags, remains excluded from performance denominator by design BEFORE execution. Persist per-event (pulse, range, I/Q, sign), count, first occurrence and complete event digest, plus sticky per-stage overflow flags and counter-wrap flags. Counter overflow must not be silent.

## 6. S02 compatibility and stage ownership matrix

| S02 requirement | Bounded C01 disposition | Future obligation / owner |
|---|---|---|
| REQ-IO-01, C-DAT-01 | IN SCOPE as source/byte interface proposal | Host-source metadata in C01; UART S05/S11 |
| REQ-SNR-01 | IN SCOPE for exact two source noise powers | C01 source convention; numeric error C02/C06 |
| REQ-LFM-01 | IN SCOPE target source definition | MF coefficient/bit-true arithmetic C02 |
| REQ-PD-01 | IN SCOPE source scenario only; no fixed-point Pd claim | Numerical performance and tolerance C06 |
| REQ-CFAR-01/02 | IN SCOPE strict reference geometry and noise-only source | alpha, power and strict integer semantics C02/C06; no main retest |
| REQ-SCR-01 BINDING | OUT OF SCOPE; **CONFLICT/OPEN** | Engineer decide approved deferral, expanded C01 or future multi-class numeric campaign |
| REQ-RNG-03 BINDING_TEST | OUT OF SCOPE; **CONFLICT/OPEN** | Engineer approve future two-target coverage with owner |
| REQ-DOP-01 | Only on-bin source in C01 | Full off-bin/tie and bit-true Doppler C02/C06 |
| REQ-DET-01, REQ-LIST-01 | Input contract does not validate multiple-target list | C02/C06, S05 list overflow |
| REQ-POWER-01, REQ-OBS-01 | Stage unit metadata proposed | Bit-true stage readback C02/C06 and physical later |
| REQ-EVID-01, REQ-RES-01 | No physical test | Future FPGA verification |

## 7. Independent decision request and held criteria

C01 may in principle be approved before MF/FFT widths and complete numerical-error budget **only as an explicitly limited input contract**. It must include a formal engineer-approved disposition of REQ-SCR-01 and REQ-RNG-03 rather than silently waiving them. Outstanding C01 decisions: bounded scope vs full S02 compatibility, source admission class registry, candidate gains per class, campaign clipping risk 0.1% and weak-signal resolution floor, exact metadata format and profile selection, saturation/disposition/fixed-N rules.

C02/C06 own: internal MF/FFT W/F, coefficient/twiddle widths, FFT shifts, alpha encoding, downstream overflow, Float/Fixed RMS/max and decision mismatch limits. None approved. Source-only clipping probability and Q1.15 reconstruction bound are NOT proof of fixed-point Pd.

Preserve S04 v0.3-v0.6, S03 Gate/Pfa/Pd, extra 4135 target-present clusters (NOT Pfa), missing full IQ/power archive and previous Student-t/spatial failure evidence unchanged. No RNG, main CPI, RTL, synthesis or hardware work. Conversation FULL records and replay integrity must be verified in this turn.

**Final status: AWAITING INDEPENDENT ENGINEER DECISION; C01 HOLD; C02 OPEN; Gate-S04 OPEN; S04 0%; project 25%.**
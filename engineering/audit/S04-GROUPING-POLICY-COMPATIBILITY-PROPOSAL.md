# S04 REQ-RNG-03 — Grouping Policy Compatibility Finding and Change Proposal

Status: PROPOSED, NOT APPROVED FOR IMPLEMENTATION. Existing code, test expectations, requirements and Gate decisions are unchanged. Analysis uses archived selected-C/Float outputs; it is not a new radar experiment.

## Finding

Finding ID: S04-SE-GROUPING-001. Classification: requirement-to-algorithm compatibility gap in the tested configuration.

The accepted C05 contract implements nonwrapped eight-connected components of the CFAR mask, with one record at the component's maximum stored Power and deterministic tie priority. The later approved RNG03 protocol requires two separately matched targets in all eight mandatory paired-target cases.

In four failed cases, two local Power maxima near the known true target positions both survive CFAR, but CFAR-positive cells connect them. The component-based reduction keeps one peak record for that connected region. No observation demonstrates that one of these two maxima was rejected by CFAR.

This is not “Grouping deletes a previously established target.” CFAR establishes above-threshold cells, not a physical target count. The existing Grouping algorithm merges connected detection support and represents it by one maximum. It behaves according to its accepted contract but fails the separate paired-target performance criterion.

## Read-only evidence

S04-RNG03-PREGROUPING-PEAK-DIAGNOSTIC.json inspects stored Power at natural Doppler bin +4 and finds strict neighbor maxima within +/-1 range sample of each known truth position. The earlier archived-mask diagnostic confirms both neighborhoods belong to one eight-connected component in every failed case.

| Failed case | Float local peak bins | Both peaks survive CFAR | Float valley depth relative to weaker peak |
|---|---|---|---|
| 4 samples / phase 0 | 41,43 | Yes | 0.03927 dB |
| 4 samples / phase 90 | 40,44 | Yes | 1.28400 dB |
| 4 samples / phase 270 | 40,44 | Yes | 1.28400 dB |
| 5 samples / phase 0 | 40,45 | Yes | 0.67958 dB |

Fixed stored outputs give the same qualitative result, with valley depths approximately 0.03925, 1.28393, 1.28393 and 0.67948 dB. The two maxima are real in these retained profiles, but some are weakly separated in amplitude. This diagnostic uses known truth to locate the relevant peaks; an actual extractor must operate without truth coordinates.

A new 3 dB valley requirement would not resolve these failed cases. It is not the historical RNG03 acceptance criterion and is not adopted here. Numerical local-maxima existence in noise-free cases does not establish reliable physical two-target resolution in noise.

## Engineering interpretation

For the observed connected masks, one record per component cannot provide two records representing the two nearby maxima. The selected algorithm policy and the paired-target success requirement are incompatible for those inputs. This is an allocation/design compatibility problem, not evidence of a faulty implementation of the old component algorithm.

It is not proven that the high-level range requirement itself is intrinsically impossible. The original S02 matrix deferred the separability definition, and a later S04 decision made eight-case acceptance explicit. The compatibility check between that refined criterion and the one-record policy was not resolved by C05 arithmetic/oracle qualification.

No previous PASS signature is rewritten. Correct implementation of a contract and suitability of that contract for a system performance requirement are distinct.

## Recommended candidate direction

Preserve CFAR and its threshold/geometry initially. Treat a connected component as a detection region rather than assuming it contains exactly one physical target. Develop a versioned multi-peak extraction/deblending policy inside a region:

- Identify candidate local maxima in the Power map using only measured data.
- Define plateau/tie handling and minimum peak spacing explicitly.
- Define a justified significance/prominence rule that addresses noise and sidelobes; do not select a threshold merely to pass these four examples.
- Decide whether cells are partitioned into peak-associated subregions or whether multiple peak records share a region. Define cluster_cells, tie flags, ordering and record semantics accordingly.
- Preserve fixed arithmetic/scaling wherever possible. No proposal to retune CFAR against the failed acceptance cases is made.

This is a candidate engineering direction, not an approved algorithm or a promise of eight-of-eight performance.

## Alternatives and trade-offs

| Option | Expected benefit | Main limitation |
|---|---|---|
| Keep current component rule and explicitly accept a demo resolution limitation | Preserves implementation and historical numerical acceptance | RNG03 remains FAIL unless requirement change/waiver is explicitly decided |
| Extract multiple valid peaks within connected regions | Can retain the two detected peaks currently merged | Additional noise/sidelobe records, record semantics, resource and verification implications |
| Change waveform/bandwidth or other detector configuration | May create stronger separation before extraction | Broader design/baseline change; not established or authorized by this analysis |

Recommended first investigation: multi-peak policy, using an isolated new reference/prototype only after explicit scope approval. Do not edit stable code.

## Change-control impact

Potentially affected contracts include post-CFAR grouping and REQ-DET-01, REQ-LIST-01, REQ-RNG-03, numerical reference/oracles, test expectations, RTL and UART/GUI record interpretation. The current maximum-702 proof was for the existing component policy; its applicability must be re-established for a changed extractor rather than assumed invalid or automatically retained.

C02 numerical arithmetic need not be changed merely to investigate the extractor. Both historical C02 and later IP configurations must nevertheless be identified if either is used for acceptance. Existing C05 PASS remains historical within its contract.

## Proposed verification obligations — not executed

1. Lock a complete extractor specification and deterministic arithmetic/record semantics before acceptance use.
2. Keep the existing eight mandatory paired-target cases and original criterion as an unchanged regression source. Do not use their truth coordinates in the runtime extractor.
3. Include independent cases for single-target sidelobes, noise-only, weak/strong pairs, relative phase/amplitude, clutter, on/off-bin targets, plateaus and output capacity.
4. Establish statistical impact on reported detections separately from CFAR per-cell Pfa; additional extracted peaks can change false-target records without changing the CFAR mask.
5. Only after explicit authorization, validate reference, fixed model, RTL, resource/timing and physical outputs for the chosen bounded scope.

## Decision boundary

The engineer can authorize investigation of a new grouping/extraction policy, retain a documented demo limitation, or request further source-based diagnosis. No implementation, test campaign, baseline amendment, waiver or RNG03 PASS is authorized/recorded by this proposal.

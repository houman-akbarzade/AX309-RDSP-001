# AX309-RDSP-001 | S04-C01 Independent baseline-check addendum v0.2

STATUS: REVIEW PENDING; NO GATE OR NUMERIC CONTRACT APPROVAL. Read-only source and arithmetic tests only, no CPI and no reserved acceptance seeds. S04 0/8; project 25%.

## Static / independent checks
- Verified HEAD and clean Git status before inspection: aec5f2990340ec2300b2ace10073c6b87d249826.
- Confirmed current S04 C01 audit, S04 numeric contract v0.2, independent rational-script/json, approved Gate-S03, and S04 criteria. No official stage progress changed.
- Imported numerical calculation module without invoking its file-writing command. Recalculated exact Fraction alpha and 22 integer-vs-rational CFAR strict comparisons in memory. All 22 match archived oracle records.
- Confirmed two options have valid stored W>F>=0, and exact alpha values A=490007/65536=7.4769134521484375 and B=30625/4096=7.476806640625. Exact equality threshold gives NO ALARM for both proposed integer comparators.
- Stored format / integer-product widths are candidates and conservative arithmetic proxies, NOT synthesis evidence or complete twiddle/butterfly/overflow proofs.
- Contract v0.2 SHA256 and C01 audit SHA256 matched the recorded evidence manifest. Original project and historical accepted Pd/Pfa outcomes were not accessed for any simulation or tuning.

## NEW BLOCKING DESIGN QUESTION: input scaling versus noise-only S03 reference
The S03 noise-only Gaussian reference model uses complex CN(0,1) noise; real and imaginary parts are independent N(0,1/2). If its floating IQ components are mapped directly into Q1.15 without a scale factor, the probability that any individual real component exceeds magnitude 1 is:
  Pr(|I|>1)=erfc(1)=0.15729920705028522.
For one 33x128 complex CPI there are 8448 real components. The expected number exceeding magnitude 1 is:
  8448*erfc(1)=1328.8637011608096.
These are theoretical tail and expectation calculations, not measured clipped counts or a new CPI run. Actual nearest-even clipping thresholds differ by approximately one half-LSB and must be used in a final arithmetic implementation.

Hypothetical input division by g before Q1.15 is NOT yet approved. For reference only, using |I|>g as an approximate clipping proxy:
- g=2 -> expected exceedances 39.51750511988734 per noise-only CPI.
- g=4 -> expected exceedances 0.0001302449947415661 per noise-only CPI.
- g=8 -> expected exceedances 9.482286251736112e-26 per noise-only CPI.
These calculations apply to CN(0,1) and do not establish a universal safe input gain for clutter, multiple coherent echoes, other dynamic ranges or finite binary scaling. Determining amplitude normalization and whether to flag/reject clipping is a prerequisite to approving Q1.15 as a universal numeric boundary and to defining Float vs Fixed statistical comparability.

## Independent S04-C01 disposition
- Source traceability / dimensions / ideal bounded postquantizer bit-growth: PASS as analytical inspection.
- Complete admission/gain policy covering the frozen noise-only reference: OPEN, with significant clipping risk for direct Q1.15 mapping.
- Intermediate coefficient/twiddle rounding, FFT shifts, overflow counters, RMS budgets, stable-margin CFAR and independent numeric acceptance procedure: OPEN for engineer-reviewed v0.2 contract decisions.
- S04-C01: NOT APPROVED; S04-C02: NOT APPROVED. No progress earned by analysis-only addendum.
- Next independent engineering decision should prioritize explicit input scaling and admitted Float stimuli, then select candidate A/B/hybrid and certified error and overflow budgets.

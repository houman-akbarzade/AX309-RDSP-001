# S03 C04 post-alpha spatial diagnostic seed-overlap audit (append-only addendum)

A source-level provenance audit after recording the S03 spatial-transfer failure revealed a material qualification.

The post-alpha 4096-CPI diagnostic and earlier exploratory 2048-CPI diagnostic reuse master seed 311091603 with identical PCG64 SeedSequence([seed,i,191]) for each CPI index. Therefore, post-alpha CPI indices 0..2047 contain the SAME base synthetic IQ streams as the earlier exploration, though analyzed with a different frozen alpha. The post-alpha dataset is independently seeded from alpha-calibration (311091604), CI calibration (311091601), CI formal qualification (311091602), and reserved MAIN Pfa (311091605). Those required distinct pools have not mixed.

Consequences:
1. The post-alpha failure is VALID evidence of failing the PREDECLARED S03 anisotropy check for the selected 4096-CPI sample. The observed z=43.5754456676879 cannot be reclassified as a pass.
2. It is NOT a fully fresh blinded confirmation independent of all earlier exploratory diagnostics. The predeclared spatial rule was created after earlier exploratory studies, a further limitation on confirmatory interpretation. The observed failure should remain evidence of a blocker, not as a calibrated p-value for an independently designed hypothesis.
3. No new seed, sample size, significance cutoff, alpha or Delta_star was substituted after the failure. Any future independent confirmation and/or replacement transfer method needs a new engineer-approved, preregistered seed namespace and protocol.
4. The existing report and evidence files remain byte-for-byte unchanged; this addendum supplies provenance correction. Main Pfa remains BLOCKED; Gate-S03 OPEN; S03 75%, project 22.9167%.

This overlap does not mean the alpha calibration corpus leaked into its post-alpha diagnostics, or that v1.1 synthetic count-model formal CI calibration and qualification were contaminated. The main risk is partial re-use of earlier exploratory **spatial** input streams.

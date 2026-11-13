# AX309-RDSP-001

A laboratory FPGA radar DSP project for the ALINX AX309 (Xilinx Spartan-6 XC6SLX9-2FTG256C), developed with Xilinx ISE 14.7. The host supplies synthetic complex IQ in batches. The FPGA processes the batch and returns Power-map and cluster results over USB-UART.

This is a development and verification platform. The retained physical-board results do not establish operational radar acceptance, real-time acquisition, or general detection performance.

## Processing chain and platform

IQ upload/readback → 16-tap complex matched filter → two-pulse MTI → 32-point Doppler FFT → linear Power → 2D CA-CFAR → eight-connected grouping → UART results/COMMIT/RELEASE.

The laboratory input is 33×128 complex signed Q1.15 samples (16,896 bytes); MTI yields 32 slow-time samples. The declared sampling rate is 1 MS/s. The waveform reference uses a 16 µs, 250 kHz LFM pulse. The hypothetical 10 GHz carrier is used for velocity conversion; it does not imply an RF transceiver on the board. No antenna/RF/ADC acquisition chain or FPGA tracking capability is claimed.

The approved CA-CFAR geometry is 7×7 with the central 3×3 excluded: 40 training cells and 2,782 valid CUTs. The comparator is strict greater-than. Consult the normative contract for index and scaling conventions.

## Engineering method and authority

Requirements, numerical models, RTL, tool reports and board evidence are versioned separately from engineer acceptance. AI assisted development, analysis and documentation. The engineer owns design decisions, evidence acceptance and stage gates. A software PASS, simulation PASS, routed design and physical capture are distinct evidence classes.

S01–S03 have explicit approval records. S04 was closed by engineer disposition with open technical items. Later laboratory implementation does not imply automatic closure of S05–S11.

The repository contains historical status files and dated reports. Some project.yaml summaries and replay/stages.json entries predate later work. For the audit's reconciled view and unresolved discrepancies, read [the compliance report](engineering/audit/FPGA-ENGINEERING-COMPLIANCE.md). Historical records have not been rewritten.

## Requirements and architecture

The approved [S02 v1.0 requirement matrix](engineering/S02-requirements-matrix-FINAL-PROPOSED-v1.0.json) is supplemented by approved v1.1 and the limited [C-CFAR-02 v1.2 contract](engineering/S02-C-CFAR-02-CONTRACT-APPROVED-v1.2.md). The [v1.2 matrix](engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json) retains 22 requirement rows; later decision records must be read for scoped changes.

The [S05 architecture](engineering/S05-RTL-ARCHITECTURE-v0.1.md), [UART ICD candidate](engineering/S05-UART-ICD-v1.0-ENGINEER-REVIEW.md) and later [full-IP integration report](engineering/FULL-IP-UART-GUI-INTEGRATION-20261112.md) document different points in development. A candidate ICD is not an approved contract merely because laboratory RTL exists.

## Fixed-point design

The historical selected-C numerical design specifies widths, binary points, RNE/saturation and FFT stage shifts [0,1,0,1,1]. It has bounded deterministic qualification evidence.

The later laboratory chain uses Xilinx FFT v7.1 Radix-2 Lite with a 32-point transform, 25-bit signed I/O and 16-bit phase factors. It is **not bit-exact to the custom C02 FFT**; overflow behavior also differs. The [FFT benchmark](rtl/experiments/fft_ip_20261112/README.md) preserves the equivalence failures. The [Float/IP evaluation](engineering/IP-FLOAT-AND-FULL-CHAIN-EVALUATION-20261112.md) explains measured numerical comparisons and limits. These measurements do not qualify general Fixed-Point Pd/Pfa.

## Source organization

| Path | Purpose |
|---|---|
| s03_reference/ | Floating functional model and scoring |
| engineering/s04_numeric/ | Fixed-point numerical contracts, models and archived results |
| rtl/ | Arithmetic blocks, grouping, integration, UART, testbenches and build tools |
| pc_link/ | Framing, host transport, session/ARQ, software fixtures and board interfaces |
| desktop_app/ | Scenario generation, references and laboratory GUI |
| tests/ | Historical software/unit verification sources |
| engineering/evidence/ | Archived simulation, implementation, integration and board evidence |
| decisions/ | Engineer decisions and scoped approvals |
| engineering/experiences/ | Experience cards and review ledger |
| replay/ | Historical dialogue/events, manifest and projections |
| engineering/audit/ | New audit findings and derived proposals |

## Verification and simulation evidence

The strategy combines analytical/Float references, fixed integer oracles, self-checking RTL simulation, XST/MAP/PAR/TRCE and physical journals. References using the same vendor FFT model are not independent mathematical implementations merely because they run in different languages.

The retained full-IP ISim testbench checks expected serial bytes and terminal flags for two complete CPI, including premature/duplicate RUN, lost acknowledgements and RELEASE/reuse. The archived log reports 72,123 expected UART bytes. The testbench accelerates serial timing; this is not board electrical qualification. The 57-test PC regression is a separate software evidence class.

## Synthesis and timing

The [full-IP integration evidence manifest](engineering/evidence/s10/full_ip_20261112/manifest.json) records the final laboratory design:

| Resource / result | Recorded value |
|---|---:|
| LUT | 5,019 / 5,720 |
| FF | 3,913 / 11,440 |
| DSP48A1 | 14 / 16 |
| RAMB16 / RAMB8 primitives | 25 / 5 |
| Clock constraint | 20 ns (50 MHz) |
| Reported internal minimum period | 19.402 ns |
| Reported setup / hold errors | 0 / 0 |

RAMB8 and RAMB16 are different primitive sizes; do not add them as full BRAM-site counts. Timing applies to the archived build and applied constraints. It does not prove unconstrained paths, external interfaces or real-time CPI throughput. No new tools were run for this documentation audit.

## Hardware validation

The [nine-case board report](engineering/evidence/s11/full_ip_20261112/board-scenario-checks.json) and referenced journals retain 36,864 Power cells and 56 cluster records. The original comparison reported zero Power mismatches and exact record fields against the prior structural-IP/C05 oracle. Journals retain IQ verification, COMMIT and RELEASE. Programming was historically in SRAM; Flash was reported unchanged.

Cases include noise-bearing single/multiple targets, clutter, close targets, low SNR and zero input. In the close-target case only one of two targets was associated. The GUI's CFAR display is reconstructed from returned Power on the PC; it is a derived view.

## Known limitations and open items

- REQ-RNG-03 remains FAIL: 4/8 mandatory cases against an unchanged 8/8 requirement.
- Fixed-Point statistical performance qualification remains OPEN.
- Approved S03 Pfa/Pd studies apply to separately defined Python floating-point populations, not this full FPGA IP chain.
- The 1,000-CPI Pd study retains per-CPI summaries and hashes, not complete original IQ and full Power arrays.
- UART batch transfer is not real-time radar acquisition.
- Automatic recovery of an interrupted hardware session using a new SID is not supported by the final integration report.
- Full intermediate observability and maximum-capacity/no-drop acceptance need requirement-level review.
- Stage Lab uses distinct injection/readback configurations. Selected immutable evidence has now been copied into this preparation branch; active Lab code and images remain separate.
- Final numerical-baseline reconciliation, separate stage-gate closure and public redistribution review remain open.

## Reproducibility

Start from an exact commit and the evidence manifest for the experiment being studied. Check source/data hashes before interpreting results. Historical report commands may generate data, rebuild FPGA products, communicate with UART, or program hardware; review their effects and obtain the relevant authorization before execution.

ISE/vendor IP dependencies and local board configuration are required for hardware reproduction. Source hashes alone do not recreate omitted raw arrays. The audit performed only file reads, hashes and calculations over retained records. It did not rerun models, engineering tests, synthesis or programming.

## Decisions and lessons

Read [decisions/](decisions/), the [lessons register](engineering/LESSONS-LEARNED.md) and [experience ledger](engineering/experiences/index.jsonl). Experience state and engineer approval are distinct. Historical failed statistical methods, FFT equivalence failures and resource/timing failures remain part of the engineering record.

## Repository review status

Documentation preparation is in progress. This branch has not been published and is **not yet READY_FOR_GITHUB_REVIEW**. The compliance report lists unfinished coverage and decisions. Public release requires the owner's approval and review of disclosure scope and vendor IP redistribution.

## Existing-work recovery update

The engineer authorized recovery of completed Stage Lab work. Read [the as-built review package](engineering/audit/EXISTING-WORK-RECOVERY-AND-AS-BUILT-REVIEW.md) for recovered S05–S11 evidence and the exact pending configuration decision. The audit independently checked 94 retained case archives and 184 exact Fixed-reference comparisons without executing project models or tests. These are finite archived-evidence results, not new engineering execution or automatic gate approval.

## Engineering history and mission changes

Read [the engineering development history](engineering/ENGINEERING-DEVELOPMENT-HISTORY.md), [the mission/scope addendum](engineering/MISSION-EVOLUTION-LAB-ADDENDUM-20261113.md), and [the source-backed historical direction register](decisions/HISTORICAL-DEVELOPMENT-DIRECTIONS-20261113.json). They distinguish the owner’s proposals, execution authorizations, observed outcomes and formal acceptance. Original baselines and failed evidence remain intact. Dialogue recovery is partial and preserves explicit source gaps.

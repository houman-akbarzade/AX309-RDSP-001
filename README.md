# AX309-RDSP-001

An engineer-led, AI-assisted FPGA radar DSP laboratory project on the **ALINX AX309 / Xilinx Spartan-6 XC6SLX9-2FTG256C**, using **Xilinx ISE 14.7**. A host supplies synthetic complex IQ in batches; the FPGA processes it and returns Power maps and grouping records over USB-UART.

## Current acceptance status

**S01–S12 are closed within their explicitly approved laboratory scopes.** The latest engineering decisions are dated **14 November 2026**. S12 is an as-built laboratory handover with declared S11 acceptance amendments and limitations; it does not establish operational radar, environmental or production qualification.

The current status is established by the [Gate decisions](decisions/), [S11 amended-criteria verdict](engineering/S11-AMENDED-CRITERIA-VERDICT-20261114.md) and [S12 handover](deliverables/S12-LAB-HANDOVER-20261114.md). Historical draft headers, `project.yaml`, Replay summaries and older audit/status reports may describe earlier OPEN states. Read them as dated evidence, not as overrides of later explicit decisions. Original failed results and superseded criteria are retained.

| Stages | Accepted scope and decision |
|---|---|
| S01–S03 | Approved problem definition, requirements and scoped floating functional-reference evidence; individual approved-baseline records are in `decisions/`. |
| S04 | [Final scoped acceptance](decisions/GATE-S04-FINAL-ACCEPTANCE-20261114.json): current Power-peak criterion and frozen FFT-IP model statistical campaigns; earlier carryovers resolved within the approved scope. |
| S05–S07 | [Architecture/interfaces](decisions/GATE-S05-ARCHITECTURE-INTERFACES-APPROVED-20261114.json), [RTL/testbench](decisions/GATE-S06-RTL-TESTBENCH-APPROVED-20261114.json) and [finite simulation](decisions/GATE-S07-RTL-SIMULATION-APPROVED-20261114.json). |
| S08–S10 | [Exact mapped configuration](decisions/GATE-S08-SYNTHESIS-MAP-APPROVED-20261114.json), [50 MHz routed timing with documented asynchronous boundaries](decisions/GATE-S09-ROUTED-TIMING-APPROVED-20261114.json) and [selected laboratory integration](decisions/GATE-S10-INTEGRATION-BITSTREAM-APPROVED-20261114.json). |
| S11 | [Physical laboratory acceptance with explicit exceptions](decisions/GATE-S11-PHYSICAL-LAB-ACCEPTANCE-WITH-EXCEPTIONS-20261114.json), supplemented by the [amended-criteria PASS verdict](decisions/S11-AMENDED-CRITERIA-PASS-20261114.json). |
| S12 | [Laboratory handover closed](decisions/GATE-S12-PRIVATE-LAB-HANDOVER-APPROVED-20261114.json), preserving S11 boundaries. The historical decision calls this a private handover; it is not a redistribution license. |

## Processing chain and platform

**IQ upload/readback → MF16 → two-pulse MTI → 32-point Doppler FFT-IP → linear Power → 2D CA-CFAR → eight-connected grouping → UART results / COMMIT / RELEASE.**

- Input: **33 × 128** complex signed Q1.15 samples, **16,896 bytes**, pulse-major I/Q. MTI yields 32 slow-time samples; the Power map is **128 × 32 = 4,096 cells**.
- Signal reference: 1 MS/s and a 16 µs / 250 kHz LFM pulse. The hypothetical 10 GHz carrier supports velocity conversion; no antenna/RF/ADC acquisition chain or FPGA tracking is implied.
- CA-CFAR: 7 × 7 window with central 3 × 3 excluded, **40 training cells**, **2,782 valid CUTs**, strict greater-than comparison and frozen index/mask conventions.
- The selected full-chain image exposes IQ readback, actual Power and final records. Intermediate outputs use **separate Stage Lab configurations**, not simultaneous readback of every stage in that image.

Read the selected [as-built functional trace](engineering/S05-FFT-IP-AS-BUILT-TRACE-v1.0.md), [UART ICD](engineering/S05-UART-AS-BUILT-ICD-v1.0.md) and [S05 decision](decisions/GATE-S05-ARCHITECTURE-INTERFACES-APPROVED-20261114.json) together. Proposal headers in the first two predate approval. Older custom-FFT and UART designs remain historical alternatives.

## Engineering method

The workflow connects requirements, numerical contracts, architecture alternatives, RTL, engineering-tool execution, evidence review and explicit engineer acceptance. AI assists analysis, model/RTL/testbench development, tool orchestration and documentation. The engineer directs choices and approves contracts, trade-offs and acceptance.

Evaluation follows **functional behavior, timing and resource use**. Software results, RTL simulation, mapped/routed reports and physical captures are separate evidence classes. Numerical or architectural changes require corresponding reference and acceptance review.

The [development history](engineering/ENGINEERING-DEVELOPMENT-HISTORY.md) documents the engineer's role in resource-allocation studies, proposing FFT-IP, requesting Float comparisons, hardware integration and independent stage observation. It is a dated retrospective; later decisions control current status. Dialogue recovery is partial, not a complete original conversation archive.

## Numerical configuration and architecture choice

Historical selected-C/C02 defines widths, binary points, RNE/saturation and shifts `[0,1,0,1,1]`. The selected image uses **Xilinx FFT v7.1 Radix-2 Lite / BRAM**, 32 points, signed 25-bit I/O and 16-bit phase factors. It is **not bit-exact to C02**; the original mismatch remains documented. Acceptance uses the reference corresponding to the selected IP configuration.

The [standalone FFT MAP comparison](engineering/FFT-IP-TRIAL-REPORT-20261112.md) recorded **5,589 → 537 LUT**, about **90.4% fewer LUT in that standalone comparison**, not a 90.4% reduction in the complete design. The [Float/IP evaluation](engineering/IP-FLOAT-AND-FULL-CHAIN-EVALUATION-20261112.md) assessed numerical and downstream effects separately. Using the same vendor FFT model in different host languages does not establish independent mathematical references.

Requirements start with the 22-row S02 matrices and their approved amendments. Read the [Power-peak amendment](engineering/S02-REQ-RNG-03-POWER-PEAKS-AMENDMENT-v1.4.md), [as-built scope amendment](engineering/S01-S02-RANGE-MATRIX-LIST-OBS-AMENDMENT-v1.0.md) and [S11 limited-method amendment](engineering/S02-S11-LAB-PFA-TIMING-LIMITED-AMENDMENT-20261114.md) with the final decisions.

## Functional and physical evidence

| Evidence | Recorded result | Scope |
|---|---|---|
| Current range-resolution criterion | **8/8** final-image board Power cases pass. | Approved noise-free two-peak population; historical **4/8** final-grouping-record result retained under the former criterion. |
| Paired board/model replay | **2,174/2,174 CPI**: 1,000 target-present plus 1,174 completed noise CPI, exact Power/record comparisons. | Finite populations, not all-input equivalence. |
| FFT-IP fixed-model Pfa | 20,000 independent noise CPI; one-sided 95% empirical-Bernstein upper **0.0014529047 ≤ 0.0015**. | Scoped model PASS and approved S11 laboratory substitute. |
| Physical noise campaign | **1,174/20,000 CPI** completed; observed fraction about 0.000977322; EB upper **0.008370254**. | Does **not** demonstrate the original physical-protocol PASS or a 95% board Pfa guarantee. |
| Physical target campaign | **1,000/1,000** detections; one-sided Clopper–Pearson lower about **0.99700875**. | Defined single-target population, not general radar Pd. |
| Grouping capacity | **702/702** physical records in a separate Grouping image, plus backpressure simulation and finite full-chain transports. | Approved scoped REQ-LIST-01 evidence; no 702-record final-image UART-to-PC claim. |

The [S11 review](engineering/S11-FINAL-REVIEW-AND-ENGINEER-DECISION-PACKAGE-20261114.md) retains original-method gaps. The later [amendment](engineering/S02-S11-LAB-PFA-TIMING-LIMITED-AMENDMENT-20261114.md) and [verdict](engineering/S11-AMENDED-CRITERIA-VERDICT-20261114.md) establish **PASS under approved laboratory methods** for REQ-CFAR-02, REQ-TIME-01 and REQ-LIST-01. They do not relabel unexecuted original tests as executed.

The earlier nine-case board archive retains 36,864 Power cells and 56 records; it is distinct from the later campaigns. GUI CFAR overlays reconstructed on the PC from returned Power are **derived views**, not downloaded full-chain FPGA masks. Separate Stage Lab configurations provide direct stage-specific outputs.

## Simulation, resources and timing

Retained full-chain structural ISim covers two complete CPI, expected Power/record bytes, premature/duplicate RUN, lost ACKs and RELEASE/reuse, with **72,123 expected UART bytes**. Serial timing is accelerated. PC regression and Stage Lab tests are separate evidence; see [S07](engineering/S07-GATE-READINESS-20261114.md) and [Auto Lab](engineering/AUTO-LAB-v0.3-REPORT.md).

The [selected build manifest](engineering/evidence/s10/full_ip_20261112/manifest.json) and accepted S08/S09 records give:

| Resource / timing | Recorded value |
|---|---:|
| LUT | 5,019 / 5,720 (87.7%) |
| Slice registers | 3,913 / 11,440 (34.2%) |
| Occupied slices | 1,407 / 1,430 (98.4%) |
| DSP48A1 | 14 / 16 (87.5%) |
| RAMB16 / RAMB8 primitives | 25 / 5 |
| Clock constraint | 20 ns (50 MHz) |
| Internal minimum period | 19.402 ns |
| Worst setup / hold slack | +0.598 ns / +0.306 ns |
| Reported setup / hold errors | 0 / 0 |

RAMB8 and RAMB16 differ in size and placement; do not add them as full BRAM-site counts. Fit does not promise spare capacity. [S09 constraint review](engineering/audit/S09-UNCONSTRAINED-PATH-DISPOSITION-20261114.md) classified clock-distribution entries and asynchronous UART/reset boundaries. Acceptance follows that interpretation, not a blanket zero-unconstrained claim.

[ISim core cycle estimates](engineering/S11-RTL-IP-CYCLE-ESTIMATE-20261114.md): **744,045 cycles / 14.880900 ms** for zero input and **744,422 cycles / 14.888440 ms** for the selected two-target input at 50 MHz, with `out_ready=1`, excluding UART/host time. These are not physical cycle-counter measurements or a worst-case bound. The approved laboratory method avoids adding a counter to the near-full image.

## Handover and reproducibility

The [S12 handover](deliverables/S12-LAB-HANDOVER-20261114.md), [requirement disposition](deliverables/S12-REQUIREMENT-DISPOSITION-20261114.md) and [delivery manifest](deliverables/S12-DELIVERY-MANIFEST.json) identify configurations, archive hashes and limits. Stage Lab source is pinned at `6c86a2e`; selected bitstream SHA-256: `fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb`.

Start with the exact experiment source/configuration and manifest, verify hashes and inspect dependencies. ISE/CoreGen, vendor IP licensing and local board configuration are required. Original software statistical logs retain summaries/input hashes; physical campaign archives retain fuller IQ/Power/journal data. Not every historical run has complete raw arrays. This README reconciliation did not rerun models, simulations, synthesis, programming or physical tests.

The repository is currently public. Older claims that a preparation branch was unpublished describe historical snapshots. Public visibility and authorization of this documentation update do not themselves establish redistribution rights for every vendor-generated artifact; the historical S12 handover is not a public IP license.

## Source organization

| Path | Purpose |
|---|---|
| `s03_reference/` | Floating functional model and scoring |
| `engineering/s04_numeric/` | Numerical contracts, fixed models and results |
| `rtl/` | Processing, integration, UART, testbenches and tool scripts |
| `pc_link/` / `desktop_app/` | Host protocol, scenario/reference tools and GUI |
| `tests/` / `engineering/evidence/` | Software tests and retained tool/physical evidence |
| `decisions/` | Engineer decisions and scoped approvals |
| `engineering/experiences/` / `engineering/LESSONS-LEARNED.md` | Experience records and lessons |
| `replay/` | Historical dialogue/events with capture-quality limits |
| `engineering/audit/` / `deliverables/` | Dated audits, handover and manifests |

## Remaining boundaries

- Batch USB-UART operation is not continuous real-time acquisition. W5500, RF/ADC input and FPGA tracking are outside this implementation.
- Fail-closed/manual reset or SRAM reload is the accepted recovery policy; automatic recovery across disconnect/power loss is not claimed. Flash was reported unchanged.
- Full-chain and Stage Lab images are separate configurations; resource counts/observations cannot be combined into one simultaneous image.
- General Pd/Pfa, all-input equivalence, hardware overflow telemetry, exhaustive faults, worst-case latency and operational/environmental qualification are not established by laboratory PASS results.
- Historical FAILs, numerical differences, failed resource/timing attempts and incomplete dialogue provenance remain in the record. Later scoped acceptance does not erase them.

## ISE 14.7 graphical project

The [Project Navigator project](rtl/ise_project/AX309_RadarDSP.xise) opens the accepted as-built RTL hierarchy with the Xilinx FFT-IP configuration, board UCF and simulation testbenches. See the [ISE project guide](rtl/ise_project/README.md) for the exact scope and regeneration instructions. Independent GUI XST/Translate/MAP checks passed, but generated IP netlist hashes and MAP resource counts differ from the previously approved command-line build; this is **not** automatic approval of a replacement bitstream.

## MATLAB Float and Fixed-Point reference models

Runnable MATLAB R2024a models for the S03 Float chain and the selected S04 Fixed-Point chain (actual Xilinx FFT v7.1 C-model via a Python bridge), together with saved validation vectors, are in [matlab_model/](matlab_model/README.md). Cross-language CPI checks are finite regression tests; no new gate or statistical qualification is claimed.

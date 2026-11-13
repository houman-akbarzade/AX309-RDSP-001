# AX309-RDSP-001 — Mission Evolution and Laboratory Scope Addendum

Document type: retrospective, source-backed mission addendum. Recorded 2026-11-13. Original platform dates are not inferred. This adds the documented engineer-requested laboratory scope alongside the original S01/S02 baselines; it does not overwrite them or retroactively approve any Gate.

## Why the mission expanded

The original numerical/RTL work evolved into a physical laboratory demonstrator: generate synthetic IQ on a PC, upload and verify it through UART, execute real FPGA DSP, retrieve results and compare them graphically with references. The owner then requested per-stage injection/readback to distinguish block error from accumulated-chain error, followed by automatic testing and readable comparison reports.

Source authority is the engineer's historical instructions, not an agent's assertion of completion. The uploaded export contains a partial original implementation mission and early bring-up reports. Main/Lab Replay provides the later technical requests and responses. The authoritative source mapping is decisions/HISTORICAL-DEVELOPMENT-DIRECTIONS-20261113.json (HD-001 through HD-013).

## Documented additions to mission

| Addition | Engineer source | Evidence/outcome | Acceptance boundary |
|---|---|---|---|
| Physical desktop demonstrator, eight synthetic scenarios, separate Hardware/Reference/Demo modes | AX309-EXPORT-MISSION-20261113 | Main full-IP integration report and GUI evidence | Known trajectories are scenario truth, not FPGA-estimated angles/tracks |
| UART input, full IQ readback and real FPGA result output | Partial mission source; FULL-INTEGRATION engineer messages | Main physical journals and integration manifest | Offline batch transport; no real-time or Ethernet claim |
| Independent stage injection/readback while preserving stable version | STAGE-TEST-FEASIBILITY followed by STAGE-LAB-IMPLEMENT | Stage Lab v0.2 reports and seven image manifests | The first request was feasibility-only; implementation follows the later explicit authorization |
| Python/MATLAB Float/Fixed comparisons; software Float generation after FFT to isolate later blocks | STAGE-LAB-IMPLEMENT engineer message | Per-stage retained references and numerical archive checks | Shared vendor FFT models are not independent mathematical implementations |
| Clear units, PRI/bin/range-cell controls, adjustable velocity/noise and useful records/error tables | STAGE-GUI-021 engineer message | v0.2.1 report, GUI validation and physical Power journal | Display axes follow stage semantics; normalized amplitude/Power is not volts/watts |
| Two-mode application and automatic independent/cumulative testing | AUTO-TEST-PROPOSAL, AUTO-LAB-IMPLEMENT and continuation | v0.3 report and retained suites | Finite tests and small statistical mechanism checks are not general Pd/Pfa qualification |
| Paired maps, common color scale and MATLAB references | PAIRED-MAPS engineer message | Paired-map validation archive | Software-reference recomputation is distinct from new board captures |
| Correct blank Qt rendering, then larger/zoomable vector figures | QT-SVG-FIX and ZOOM engineer messages | Qt render validation, commits 7bb6ef0 and 6c86a2e | Presentation repair does not change radar acceptance or measured samples |

These source-directed additions are recorded as historical scope. The source export is incomplete, so absent passages, original timestamps and a missing screenshot are not supplied by inference.

## Architecture alternatives and final observed implementation

The owner proposed investigating Grouping on PC, then CFAR and Power on PC, to reduce FPGA resource use. These were alternatives and experiments, not proof that all three were finally moved to the PC.

The owner also proposed FFT IP and requested comparison with Float using RMSE and final clustering outcomes, rather than treating difference from the earlier fixed implementation alone as an accuracy verdict. Later work shows the laboratory chain MF → MTI → FFT IP → Power → CFAR → Grouping on FPGA, with UART and GUI on PC.

The historical selected-C model remains distinct from the IP implementation. The owner's provisional IP preference and instruction to finish integration do not by themselves establish a separately signed final numerical-baseline amendment or close every Gate. That formal disposition remains explicitly pending in the as-built review package.

W5500 is a proposed future interface. No implemented Ethernet link, real-rate data transfer or automatically approved migration is recorded.

## Supplemental scope traceability

This is a documentary scope register, not a renumbering of approved REQ-* requirements. Existing requirements remain authoritative.

| Scope item | Requested behavior | Registered verification source | Disposition |
|---|---|---|---|
| HSCOPE-GUI | Real hardware results visibly separated from software/demo outputs | Main integration report/manifest | Implemented within finite laboratory evidence |
| HSCOPE-UART | Upload/readback and real result/session integrity | Nine-case journals; retained ISim protocol tests | Implemented within measured cases; interrupted-session recovery limitation retained |
| HSCOPE-STAGE | Select injection/observation points and preserve old stable version | Stage Lab image/source manifest | Implemented as separate configurations; not continuous one-image stage observability |
| HSCOPE-REF | Compare the same injected bytes against declared software references | JSON/NPZ archives and LAB-ARCHIVED-NUMERICAL-REVIEW.json | 94 retained archives/184 exact Fixed comparisons; scope-specific |
| HSCOPE-AUTO | Independent and cumulative automatic cases with concise summaries | v0.3 reports and suite archives | Implemented finite suites; sample sizes/exclusions retained |
| HSCOPE-VIS | Appropriate range–PRI/Doppler/speed maps, common scales, units and reference panel | GUI/paired-map/Qt evidence | Original display failure and subsequent repair both retained |
| HSCOPE-ZOOM | Larger vector figure window, zoom and pan | Source-backed ZOOM exchange and commit 6c86a2e | Historical implementation reported; no new UI test executed by audit |

## Unchanged technical obligations

REQ-RNG-03 remains FAIL at 4/8 mandatory cases against 8/8. Fixed-Point statistical performance remains OPEN. S03 software statistical acceptance is not generalized to the physical IP chain. Historical failed methods and resource/timing failures remain evidence.

This addendum introduces no new waveform, coefficient, Q-format, threshold, algorithm, test execution or FPGA programming. No progress percentage or Gate state is raised by writing it.

## Dialogue completeness

Sixteen original Lab records were imported unchanged after text-hash and Git-source checks. Five additional early/tail records were preserved as excerpts from the user-supplied copies. FULL/verbatim metadata in an original archived message remains the original claim; the aggregate conversation is not declared complete.

The stopped stationary-target question has no recovered answer and its image is unavailable. It is retained as an open dialogue gap, not converted into a new experiment, an inferred explanation or a defect finding.

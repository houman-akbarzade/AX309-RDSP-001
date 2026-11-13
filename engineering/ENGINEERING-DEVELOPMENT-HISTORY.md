# AX309-RDSP-001 — Engineering Development History

This is a retrospective account of existing evidence. Engineer requests, agent proposals, authorization to execute, measured results and formal acceptance are recorded separately. Source IDs resolve in replay/conversations.jsonl; exact mappings and hashes are in decisions/HISTORICAL-DEVELOPMENT-DIRECTIONS-20261113.json. The original S01/S02 baselines are not replaced.

## 1. From numerical design to a physical demonstrator

The user-supplied early mission expands delivery to a Linux desktop application connected to actual AX309 hardware. It requests eight synthetic scenarios, UART transfer and IQ verification, real FPGA processing, returned results and explicit Hardware/Reference/Demo modes. The task prioritizes working implementation and forbids silently presenting PC detections as hardware results.

The copied early record reports UART permission and JTAG blockers, followed by permission confirmation and volatile programming with a successful 16,896-byte IQ transfer/readback. At that point, the full DSP still did not fit. These are historical reports, not newly executed checks. The uploaded mission is cut mid-sentence and the overall export is partial.

## 2. Resource failure drove an architectural trade study

The retained feasibility exchange reports 11,507 LUT for the original DSP core against 5,720 device LUT. The engineer proposes investigating Grouping on PC and UART optimization. The agent reports a temporary no-Grouping synthesis at 7,761 LUT/12 BRAM, versus 11,507/18 with Grouping. This shows a useful reduction but not a complete fit; UART and IQ memory are outside that core-only comparison.

The engineer then asks about moving CFAR and even Power to PC. The reported core-only CFAR+Grouping-offload alternative is 6,821 LUT, still above capacity before communication. These alternatives remain real engineering history. They are not recorded as the final deployed stage allocation.

## 3. Engineer-proposed FFT IP changed the feasible path

The owner asks whether FFT IP or device DSP resources could reduce consumption, then authorizes an ISE FFT-IP experiment. For a like-for-like MAP comparison, the archived report gives 5,589 LUT for the custom standalone FFT and 537 LUT for Radix-2 Lite with BRAM, a reduction of about 90.4%. The earlier 5,652 number is XST, not the MAP comparator.

The experiment also records failure of strict C02 bit equivalence. The owner therefore asks for both implementations to be compared against Float using RMSE and final clustering, rather than just maximum LSB difference. The owner's preference for IP is explicitly provisional pending that investigation.

The subsequent report shows that Power, CFAR and Grouping can remain on FPGA after IP and memory/clocking optimizations. Its integrated probe reports 4,722 LUT and zero setup/hold errors at the applied 20 ns constraint. An intermediate hold failure and the shared-global-clock remedy remain documented; a failed attempt is not erased by the later successful one.

## 4. Full-chain hardware integration followed

The engineer directs completion of remaining integration and improved GUI controls. The final laboratory report records MF → MTI → FFT IP → Power → CFAR → Grouping on FPGA, with host UART transport and display on PC.

The board configuration reports 5,019 LUT, 14 DSP48A1 and a 19.402 ns internal minimum period. Nine retained consecutive-CPI journals contain 36,864 Power cells and 56 output records. The host's scenario trajectories remain known truth, not FPGA-estimated angle or tracking. GUI CFAR overlays reconstructed from Power remain explicitly derived.

This implementation direction is documented. It does not supply a separately explicit numerical-baseline amendment waiving C02 differences, statistical qualification or final gate approvals.

## 5. The owner added observability and independent testing

First, the owner requests feasibility of MF/MTI/FFT/CFAR/Grouping injection and readback without implementation yet. Later, the owner explicitly authorizes a versioned isolated Stage Lab and adds independent Power testing.

A key engineering instruction is preserved: for downstream blocks, inject the preceding software Float result instead of an IP-matched FFT result, so block error can be separated from inherited FFT error. The same bytes read back from FPGA form the reference input. The original full-chain implementation and separate injection configurations remain distinct.

The owner then requests stage-correct axes and units, PRI/Doppler/range-cell selection, editable velocity/noise, readable error tables, full records and a Persian guide. The archived v0.2.1 report records these changes and a finite real Power test.

## 6. Automatic reports and display failures were also engineering work

The owner proposes two main modes: final IQ-to-cluster comparison and automatic testing with internal injection/observation selection. A later explicit instruction authorizes implementation, including stationary, almost-stationary and moving MTI targets plus concise case summaries and charts.

The retained v0.3 report records 41 functional jobs, 40 distinct captures and 65 Fixed comparisons for the designated quick suite. Three noise CPI and three target CPI exercise a statistical mechanism; they are not a statistical acceptance campaign.

Next, the owner requests paired range–Doppler/speed maps, common color scales and MATLAB comparisons. The recorded response reports 23 MATLAB CFAR/grouping reference cases and 37 paired maps. The following user report says the maps are blank. Commit 7bb6ef0 records replacement of unsupported nested SVG structures for Qt. The next user request asks for larger/zoomable figures; commit 6c86a2e adds the vector viewer.

The copied question about a zero-speed target originally lacked its image. The later 37-page PDF supplies that image on page 34; its chart is explicitly the matched-filter output. The stopped historical answer remains absent. The image is retained as context, not proof of an MTI defect.

## Limits of this history

Sixteen original Lab dialogue records were recovered from Git-backed archive bytes. Five further source fragments are retained as excerpts. The initial uploaded mission, missing screenshot, stopped response and potentially collapsed sections prevent a claim of complete original conversation recovery. Recording/import time is not silently substituted for original platform time.

The engineer's proposals were consequential: they initiated the resource allocation study, IP experiment, Float comparison, full hardware integration, independent observability, automatic testing and usable reporting. Their effect is now traceable without relabeling an investigated option as an approved final architecture.

REQ-RNG-03 remains FAIL 4/8 against required 8/8. Fixed-Point statistical performance remains OPEN. Future W5500, real-time transfer, complete external timing qualification and final numerical/gate disposition are not inferred from these exchanges.

## Fuller PDF source recovery

The later 37-page print supplies the full fourteen-section mission within the printed source, visible IP-evaluation progress, an engineer interruption/finish request, an alternate final probe report, and the missing stationary-question image. Ten PDF-derived records were added as excerpts; 34 printed topic segments corroborate existing records and one empty agent label remains empty. See engineering/audit/PDF-CONVERSATION-RECOVERY.md and the PDF direction supplement. Earlier incompleteness statements describe the first text-copy recovery; PDF coverage improves them without proving a complete platform export.

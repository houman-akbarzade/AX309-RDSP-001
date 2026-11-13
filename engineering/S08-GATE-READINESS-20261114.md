# S08 synthesis and MAP Gate readiness — 2026-11-14

Status: READY_FOR_ENGINEER_DECISION for the selected FFT-IP laboratory configuration; no S08 Gate approval yet. Entry: GATE-S07-RTL-SIMULATION-APPROVED-20261114. Read-only review of retained XST/MAP reports and source; no synthesis rerun or FPGA change.

## Result and resource fit

Full-chain target XC6SLX9-2FTG256C: XST errors 0, MAP errors 0. MAP used 5,019/5,720 LUT (87.7%), 3,913/11,440 slice registers (34.2%), 1,407/1,430 occupied slices (98.4%), 14/16 DSP48A1 (87.5%), 25/32 RAMB16BWER (78.1%) and 5/64 RAMB8BWER (7.8%). The seven separately built Stage Lab images each have reported resource counts and zero setup/hold errors in their pinned manifest; they are not summed as one simultaneous image. RAMB8 and RAMB16 are distinct capacities and placements. No uniform 90% utilization ceiling was approved. The remaining 23 slices and 2 DSP blocks are a concrete modification/headroom risk, not a failure of the currently mapped configuration. S09 separately adjudicates routed timing and applied/external constraints.

## Warning disposition by class

| Retained report | Count / code | Assessment |
|---|---|---|
| XST | 600 warnings across nine codes | 441 Xst:2677 unconnected optimized nodes; 94 Xst:1710 and 43 Xst:1895 constant/trimmed registers; 14 HDLCompiler:413 width truncations; four unused fft_ready notices; one unused dsp_busy; one aggregate constant-register notice. These are synthesis/optimization diagnostics, not individually proven failures. The fixed-width byte extraction and 15-bit byte counters are bounded in the admitted 16,896-byte CPI path; any changed payload sizes require re-review. |
| XST | Xst:3035 frame_ram index range/simulation mismatch | Parser has frame_ram[0:524] for 529-byte maximum frame minus four SOF bytes. Its write_pos=4..528 for validated length <=512; HELD reader uses indices from 9+bounded header/copy offsets. The retained S02 ISim explicitly exercised a 529-byte legal frame and a 513-byte overlength rejection. This is a bounded-reachability disposition, not a formal proof for arbitrary internal corruption; preserve the warning and retest if parser addressing changes. |
| XST | Xst:2254 area target ratio 110 | Area optimization target was unmet, but MAP later completed with 0 errors and 98.4% occupied slices. No spare-capacity margin is claimed. |
| MAP | 37 PhysDesignRules:367 incomplete nets | Reported RAM output nets do not drive loads after mapping; no functional requirement calls for those unused outputs. Preserve for S09/S11 if source changes. |
| MAP | one PhysDesignRules:2410 RAMB8 initialization caveat | Do not assume default/uninitialized RAM contents. Admitted CPI processing requires full IQ upload/readback and Power-map load before result read; targeted reset/error tests remain S11 evidence. |

XST/MAP warnings are disclosed, not silently treated as zero. The full-chain source manifest's 55 source files match their recorded hashes; the seven Stage Lab images belong to the pinned separate configuration. PAR success and internal 50 MHz results already exist, but S09 owns their formal Gate. Further RTL feature growth is risky at 98.4% slice occupancy and should trigger a new resource review.

Recommendation: S08 PASS for synthesis and mapping of the exact existing configuration, with warning dispositions above and no claim of room for added functionality or acceptance of routed/external timing. Explicit engineer Gate decision required.

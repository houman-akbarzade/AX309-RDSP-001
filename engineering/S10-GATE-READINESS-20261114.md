# S10 Gate readiness — integrated FPGA image and desktop test application

Date: 2026-11-14. **READY FOR ENGINEER APPROVAL in the declared laboratory integration scope.** Entry: approved S09 decision `decisions/GATE-S09-ROUTED-TIMING-APPROVED-20261114.json`.

| Acceptance aspect | Evidence / check | Disposition |
|---|---|---|
| Reproducible integrated FPGA image | `engineering/evidence/s10/full_ip_20261112/manifest.json`: 55/55 source and 85/85 evidence hashes verified against files; local SRAM bitstream SHA256 `fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb` matches manifest. Xilinx ISE Bitgen complete, DRC errors 0. | PASS, selected image |
| RTL/PC integrated simulation | Archived ISim two complete CPI transactions and fault/retry cases, 72123 UART bytes; 57/57 PC tests. | PASS within finite cases |
| Seven-stage observation and current GUI | Stage Lab v0.3.0 independent/cumulative reports with 41 functional jobs, 40 unique board captures, 65 Fixed comparisons; three noise and three target CPI only demonstrate statistics UI, not Pd/Pfa qualification. Later Qt fix reports 37 paired maps, four displayed stages, both panels rendered, 23 actual MATLAB reference cases. Current zoom viewer at commit `6c86a2e` was smoke-tested offscreen on retained SVG: valid renderer and zoom action PASS. | PASS in S10 software integration scope |
| Image identity across worktrees | Stage Lab release declares stable full-chain image tag and seven separate stage images. All seven bitstream bytes match release.json SHA256. Full-chain RTL top, FFT-IP adapter, UCF and PC board driver in Stage Lab worktree match S10 manifest hashes. Launcher `ax309-radar-test.desktop` points to Stage Lab worktree and runs `python3 -m stage_lab`. | PASS; current viewer commit is later than the v0.3.0 release tag, separately identified |
| Memory warning | Bitgen warning PhysDesignRules:2410 for RAMB8 initialization retained. IQ is admitted only after complete upload and verified readback; S08 already classifies this caveat. 37 loadless-output warnings retained. No assertion that RAMB8 power-up contents are reliable. | ACCEPTED documented scope; physical robustness remains S11 |
| Timing and physical claims | S09 routed timing approved separately. This package includes finite board demonstrations as integration evidence; S11 owns physical qualification, large independent CPI campaign and board/model equivalence. | Boundary explicit |

No material hash mismatch, missing manifest file, changed RTL image, failed listed test or unresolved S10-scope warning was found. The repository's historical `project.yaml` and `replay/stages.json` are stale snapshots and are not used as current Gate authority; approved `decisions/GATE-S*.json` records control. Do not promote the 3-CPI statistical UI sample to Pd/Pfa acceptance. The first release tag precedes the Qt render/zoom changes; S10's software baseline is Stage Lab HEAD `6c86a2e` with those follow-up commits, not the earlier tag alone.

**Recommendation:** engineer may approve/close S10 for the selected full-chain bitstream and current desktop test application, with S11 board qualification explicitly excluded.

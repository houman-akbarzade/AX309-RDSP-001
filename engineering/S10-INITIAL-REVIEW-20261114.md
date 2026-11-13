# S10 integration and bitstream review — initial readiness

Date: 2026-11-14. Entry: engineer-approved S09 decision `decisions/GATE-S09-ROUTED-TIMING-APPROVED-20261114.json`.

The selected laboratory full-chain image exists at `/home/houman/AX309-RDSP-001/rtl/build/ise_radar_ip_ax309/radar_ip_ax309_top.bit`; SHA256 `fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb` equals the S10 manifest. Archived Bitgen reports successful completion, zero DRC errors and 38 warnings. RAMB8BWER initialization warning 2410 and 37 loadless-output warnings are retained. The design's IQ admission requires complete upload/readback and processing data are loaded before use; this is documented at S08. Do not claim general initialized RAM behavior.

The archived integrated ISim passes two full CPIs and fault/retry cases, with 72123 expected UART bytes. PC regression passes 57/57 tests. S10 manifest also links finite GUI and hardware demonstrations, with physical acceptance reserved to S11. Evidence: `engineering/evidence/s10/full_ip_20261112/manifest.json` and compressed implementation, simulation and PC logs.

**Current assessment:** candidate S10 build/integration evidence exists; formal S10 exit criteria must be traced to the approved stage definition, source and generated IP identity, and any later GUI v0.3 changes before asking for Gate approval. No new S10 Gate approval is inferred from this preliminary review. S11 statistical hardware campaign remains a separate live activity.

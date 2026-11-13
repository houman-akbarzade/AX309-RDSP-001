# Xilinx FFT-IP v7.1 statistical campaigns: scope and evidence

Status: **CANDIDATE / independent approval still OPEN**.

## Correct worktree

- /home/houman/AX309-RDSP-001-docs-audit
- Branch docs/fpga-engineering-repository-audit
- Preserve all historical S03/S04 evidence and unrelated replay/conversations.jsonl edits.

## Baselines

- Selected-C frozen input quantizer Q1.15, gain g=5 for CN(0,1) noise and g=1 for target with SNR=20 dB, absolute amplitude 0.18.
- 33x128 full complex IQ input to fixed matched filter (MF) and pulse-pair difference MTI.
- Xilinx ISE v14.7 bit-accurate FFT v7.1 `libIp_xfft_v7_1_bitacc_cmodel.so`, expected SHA256 `4a8f02f24f269bc947d5f0d3e89a73916f763b8491c7a0f4e68b4bee88a994a9`.
- FFT length 32; architecture 4 (Radix-2 Lite in model ABI), 25-bit words, 16-bit twiddles, convergent rounding, 5 shift stages [0,1,0,1,1].
- Integer-native output Power U46, 40 training-cell CA-CFAR strict compare `40*Pcut*65536 > 490007*SUM40`, and native 8-connected grouping.
- All 2782 valid CFAR CUTs per CPI counted, no training-cell IID assumption.
- New independent seed namespace 811, master seeds 992611141 (Pd) and 992611142 (Pfa), per-CPI SeedSequence([master,i,811]). These masters differ from preliminary interface smoke seed masters and from legacy selected-C campaign.
- Fixed sample count Pd N=1000, Pfa N=20000. No optional stop, adjustment, topping up, replacing clipped/overflow trials, or denominator changes.

## Outcome definitions

- Pfa: independent observational unit = noise-only CPI; Xi is count of CFAR alarms / 2782; one-sided 95% empirical Bernstein upper <= 0.0015. This is *before grouping*.
- Primary Pd: one binary per target CPI, one-to-one ground-truth association on final grouped records, ±2 range and ±1 Doppler attribution gates, exact one-sided 95% CP lower >=0.90 (N1000, >=916 detections).
- Separately record R (accuracy ±1 range sample), V (eligible strict Doppler peak and ±0.234375 m/s), J (joint), and auxiliary **pre-grouping CFAR target-gate hit** (range 38..42, Doppler 3..5); the latter is not substituted for final-record Pd.
- An input clip, MF or MTI saturation, FFT C-model overflow, or Power narrowing event is recorded and prevents acceptance-eligible clean test completion.
- At end the runner writes result `PASS_CANDIDATE`, `FAIL_CANDIDATE` or `INCONCLUSIVE`, plus full RAW, start manifest, checkpoint, SHA hashes, versions/parameters. Formal status stays OPEN until independent approval and full FPGA path correspondence.

## Existing numerical validation

The vendor library has previous **11 cases / 45,056 exact IP-trace matching complex outputs**, in `engineering/evidence/stage_lab_v0.2/fft-cmodel-validation.json`. This is evidence for isolated FFT core on those vectors only. A new test compared MF/MTI of the integrated front end to C04 selected-C on one target input: exact match, maximum integer difference 0. No exhaustive full-chain equivalence test has been claimed.

## Runners / live UI

- `fft_ip_fullchain_v1.py`
- `fft_ip_pd_pfa_campaign_v1.py`
- `fft_ip_pd_pfa_live_dashboard_v1.py`
- `fft_ip_stat_campaign_20261113_pd_v1/`
- `fft_ip_stat_campaign_20261113_pfa_v1/`

The GUI is a read-only local Qt PySide6 dashboard polling each output RAW/RESULT at one-second intervals. Final software decision and formal project disposition remain separate.

## Caveats

The FFT vendor model's overflow reporting is not equivalent to full integer pre-limit trace capture. This candidate specifically forbids silently accepting overflow. The data substantiate only the declared populations, gain, amplitude, target geometry, numerical implementation and seeds. Model-level PASS does not validate the final board interface, numerical version parity of every installed stage, target multiplicity, clutter, off-bin Doppler, or joint confidence.

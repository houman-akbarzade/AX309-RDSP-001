# AX309 Radar Lab — full FPGA DSP

Run: `python3 -m desktop_app` from the repository root. The existing menu/desktop shortcut opens it.

Select CP2102 UART, press **Program FPGA · SRAM** once after power-up, choose Hardware and Run. Flash is untouched. Subsequent completed CPIs need no reprogramming. The application uploads all 16896 IQ bytes, verifies exact readback, sends HOST_VERIFIED_INPUT/RUN, receives every FPGA cluster, validates and durably records COMMIT before ACK, downloads the actual 24576-byte FPGA Power map and RELEASEs the CPI.

The left view shows known scenario trajectories, not FPGA tracks/angle estimates. The right view shows the explicitly selected result source. Hardware Power and final cluster records come from FPGA. CFAR-cell overlays are reconstructed on PC from downloaded Power with exact C05 arithmetic. Float reference uses Float64 on the original source before IQ quantization. GUI RMSE measures **Power**, not complex FFT output.

The Persian **راهنمای نماها و گزینه‌ها** tab and GUI_GUIDE_FA.html explain every option. Views: range–Doppler, max-over-Doppler range profile, selected-range Doppler slice; linear/dB power and colour span; cluster/truth/CFAR overlays; valid CUT region; tie/equal maxima fields; Float comparison; complete JSON/CSV export. Reference and Demo are explicitly host-only.

Nine physical CPIs (eight noisy scenarios plus zero) passed with all 36864 Power cells and every record field exactly equal to the independent direct-IP trace/C05 oracle. A physical GUI two-target run returned nine clusters and matched both truth targets. 57 PC protocol tests, full UART/structural-IP ISim including lost ACKs and CPI reuse, and all GUI views/exports passed.

One CPI takes approximately 13 seconds with UART 115200/8N1, upload, verified readback and Power-map download; this is not real-time acquisition. Path span is drawing-only. The closely-spaced-target limitation and statistical Pd/Pfa obligations remain. Preterminal-session recovery across a new SID is not implemented: a failed/partial result is rejected and a failure journal retained; an explicit SRAM reprogram resets the endpoint.

Full board implementation: 5019 LUT, 3913 FF, 14 DSP48A1, 25 RAMB16 and 5 RAMB8; 20 ns constraint met with zero setup/hold errors. This IP lab path differs from historical C02 arithmetic/overflow behavior; approved historical baseline artifacts are preserved.

Reproduce:
```bash
bash rtl/tools/run_ise_radar_ip_board.sh
bash rtl/tb/run_dsp_uart_isim.sh
python3 -m unittest discover -s tests -p 'test_s05_pc*.py' -v
QT_QPA_PLATFORM=offscreen python3 -m desktop_app.smoke
# Connected and already programmed FPGA:
python3 rtl/tools/verify_dsp_board.py
QT_QPA_PLATFORM=offscreen python3 -m desktop_app.smoke --hardware
# Show a physical two-target result and keep the GUI open:
python3 -m desktop_app --show-hardware
```

Physical journals: engineering/evidence/s11/full_ip_20261112/runs. Implementation/simulation/GUI evidence: engineering/evidence/s10/full_ip_20261112. Do not run multiple processes against the same serial port.

"""Prepare relocatable full board build from committed RTL and FFT XCO."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[2]
B=R/'rtl/build/ise_radar_ip_ax309';B.mkdir(parents=True,exist_ok=True)
I=R/'rtl/build/fft32_ip';I.mkdir(parents=True,exist_ok=True)
shutil.copyfile(R/'rtl/experiments/fft_ip_20261112/configs/lite_bram.xco',I/'fft32_ip.xco')
(I/'coregen.cgp').write_text(''.join(l+'\n' for l in (I/'fft32_ip.xco').read_text().splitlines() if l.startswith('SET ')))
# Reuse the identical previously generated configured IP; otherwise caller runs CoreGen.
if not (I/'fft32_ip.ngc').exists():
 for p in [R/'rtl/build/ip_evaluation_resources/ip/fft32_ip.ngc',Path('/tmp/ax309-fft-ip-20261112/lite_bram/fft32_ip.ngc')]:
  if p.exists():shutil.copyfile(p,I/p.name);break
if not (I/'fft32_ip.v').exists():
 for p in [R/'rtl/build/fft_ip_trial/lite_bram/fft32_ip.v',Path('/tmp/ax309-fft-ip-20261112/lite_bram/fft32_ip.v')]:
  if p.exists():shutil.copyfile(p,I/p.name);break
sources=['common/rne_sat_signed','mf16/mf16_coeff_rom','mf16/mf16_serial_mac','mti/mti2_diff','fft32_ip/fft32_ip_adapter','fft32_ip/ip_stub','power_cfar/power_q25_u46_serial','power_cfar/cfar_compare','power_cfar/cfar_2d_scan','grouping/grouping_8conn','integration/cfar_grouping_subsystem','integration/radar_cpi_core','uart/uart_rx_8n1','uart/uart_tx_8n1','uart/s02_frame_echo','uart/s05_iq_cpi_banked','uart/s05_dsp_session_arq','uart/s05_dsp_reply_tx','uart/uart_s05_dsp_top','uart/radar_ip_ax309_top']
(B/'radar_ip_ax309_top.prj').write_text(''.join(f'verilog work {R}/rtl/{s}.v\n' for s in sources))
(B/'radar_ip_ax309_top.xst').write_text(f'run\n-ifn {B}/radar_ip_ax309_top.prj\n-ifmt mixed\n-ofn {B}/radar_ip_ax309_top.ngc\n-p xc6slx9-2-ftg256\n-top radar_ip_ax309_top\n-opt_mode Area\n-opt_level 2\n-keep_hierarchy No\n-rtlview No\n')
print(B)

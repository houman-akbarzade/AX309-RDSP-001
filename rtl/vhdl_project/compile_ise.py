#!/usr/bin/env python3
"""Compile VHDL in dependency order using ISE 14.7 ISim vhpcomp.

Artifact-independent syntax/elaboration gate. Does not synthesize or
program FPGA. Record all errors rather than hiding failures.
"""
import subprocess, os, pathlib, json, datetime
HERE=pathlib.Path(__file__).resolve().parent
compile_dir=HERE/'check'
compile_dir.mkdir(exist_ok=True)
ORDER=[
'common/rne_sat_signed.vhd',
'mf16/mf16_coeff_rom.vhd',
'mf16/mf16_serial_mac.vhd',
'mti/mti2_diff.vhd',
'power_cfar/cfar_compare.vhd',
'power_cfar/power_q25_u46_serial.vhd',
'power_cfar/cfar_2d_scan.vhd',
'grouping/grouping_8conn.vhd',
'integration/cfar_grouping_subsystem.vhd',
'fft32_ip/fft32_ip.vhd',
'fft32_ip/fft32_ip_adapter.vhd',
'integration/radar_cpi_core.vhd',
'uart/uart_rx_8n1.vhd',
'uart/uart_tx_8n1.vhd',
'uart/s02_frame_echo.vhd',
'uart/s05_iq_cpi_banked.vhd',
'uart/s05_dsp_session_arq.vhd',
'uart/s05_dsp_reply_tx.vhd',
'uart/uart_s05_dsp_top.vhd',
'uart/radar_ip_ax309_top.vhd',
]
COMPILER='/opt/Xilinx/14.7/ISE_DS/ISE/bin/lin64/vhpcomp'
report={}
for rel in ORDER:
 src=HERE/'src'/rel
 p=subprocess.run([COMPILER,str(src)],cwd=compile_dir,text=True,
                  stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=35)
 err=[x for x in p.stdout.splitlines() if 'ERROR:' in x or 'error:' in x or 'ignored due to errors' in x]
 report[rel]={'status':'PASS' if p.returncode==0 else 'FAIL','returncode':p.returncode,
              'error_count':len(err),'first_errors':err[:12]}
 print(f'{rel:46} {"OK" if p.returncode==0 else "FAIL"} {len(err)}')
 for x in err[:3]:print('   ',x[:200])
(HERE/'ise_compile_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print('TOTAL',sum(v['status']=='PASS' for v in report.values()),'/',len(ORDER))

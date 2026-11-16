#!/usr/bin/env python3
"""Controlled one-time conversion from frozen accepted Verilog.

This script requires the optional FPGA Discovery Verilog-to-VHDL Translator v1.0.0
to be installed outside the repository and specified with --translator-root.
Only the generated HDL is retained. License details: external tool's own LICENSE.
The source patches are temporary syntax normalizations and MUST NOT change the
accepted Verilog. All generated files require synthesis and equivalence review.
"""
import argparse, pathlib, sys, hashlib, json, re
HERE=pathlib.Path(__file__).resolve().parent
RTL=HERE.parent
FILES=[
'common/rne_sat_signed.v',
'mf16/mf16_coeff_rom.v','mf16/mf16_serial_mac.v','mti/mti2_diff.v',
'fft32_ip/fft32_ip_adapter.v',
'power_cfar/power_q25_u46_serial.v','power_cfar/cfar_compare.v','power_cfar/cfar_2d_scan.v',
'grouping/grouping_8conn.v','integration/cfar_grouping_subsystem.v','integration/radar_cpi_core.v',
'uart/uart_rx_8n1.v','uart/uart_tx_8n1.v','uart/s02_frame_echo.v',
'uart/s05_iq_cpi_banked.v','uart/s05_dsp_session_arq.v',
'uart/s05_dsp_reply_tx.v','uart/uart_s05_dsp_top.v',
]
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--translator-root',required=True)
 args=p.parse_args()
 sys.path.insert(0,str(pathlib.Path(args.translator_root).resolve()))
 from translator_core import VerilogToVHDLTranslator
 destination=HERE/'src'
 destination.mkdir(exist_ok=True)
 report={}
 for rel in FILES:
  src=RTL/rel
  text=src.read_text()
  if rel=='common/rne_sat_signed.v':
   assert "minimum = -(64'sd1 << (OUT_W-1));" in text
   text=text.replace("minimum = -(64'sd1 << (OUT_W-1));","minimum = ~maximum;")
  if rel=='grouping/grouping_8conn.v':
   assert 'localparam integer RAM_LAST_ADDRESS = 1023;' in text
   text=text.replace(' [0:RAM_LAST_ADDRESS]',' [0:1023]')
  result=VerilogToVHDLTranslator().translate_text(text,src)
  diagnostics=[d.format() for d in result.diagnostics]
  report[rel]={'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
               'errors':diagnostics,'translated_ok':result.ok}
  if not result.ok:raise SystemExit(rel+' fails translation: '+str(diagnostics[:5]))
  outfile=destination/pathlib.Path(rel).with_suffix('.vhd')
  outfile.parent.mkdir(parents=True,exist_ok=True)
  outfile.write_text('-- AUTO-TRANSLATED from '+rel+'; independent validation REQUIRED.\n'
                     +'-- Source SHA256: '+report[rel]['input_sha256']+'\n'
                     +result.vhdl)
  print(outfile.relative_to(HERE),len(result.vhdl))
 (HERE/'translation_report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print('TRANSLATION OK',len(FILES),'source units')
if __name__=='__main__':main()

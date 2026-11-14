"""Focused physical fail-closed recovery and fresh full-chain CPI check."""
import json,sys,hashlib,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from pc_link.board_dsp import run_board_dsp,program_sram,BITSTREAM
PORT='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_f4d179353796ed11aa2f634ce259fb3e-if00-port0'
OUT=ROOT/'engineering/evidence/s11/focused_recovery_20261114'
OUT.mkdir(parents=True,exist_ok=True)
report=dict(expected_hash='fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb',before_reset={},after_reset={})
assert hashlib.sha256(BITSTREAM.read_bytes()).hexdigest()==report['expected_hash']
# Interrupted CPI from shortened campaign may retain terminal state; no previous result accepted here.
try:
 r=run_board_dsp(bytes(16896),PORT,cpi_id=390000001,journal_dir=OUT)
 report['before_reset']=dict(outcome='ACCEPTED_FRESH_CPI',journal=r['journal_path'],terminal=r['terminal'],released=r['released'])
except Exception as e:
 report['before_reset']=dict(outcome='FAIL_CLOSED',error=str(e))
# Explicit volatile reprogram is approved recovery path. Flash is untouched.
p=program_sram()
assert p['bitstream_sha256']==report['expected_hash']
report['reprogram']=dict(bitstream_sha256=p['bitstream_sha256'],success='Done' in p['log'])
r=run_board_dsp(bytes(16896),PORT,cpi_id=390000002,journal_dir=OUT)
assert r['terminal']=='COMMIT' and r['released'] and r['input_bytewise_verified'] and r['power_bytes']==24576
report['after_reset']=dict(outcome='PASS',journal=r['journal_path'],records=r['terminal_count'],power_bytes=r['power_bytes'],transfer_s=r['transfer_s'],result_wait_s=r['result_wait_s'],elapsed_s=r['elapsed_s'])
(OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)

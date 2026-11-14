"""Physical malformed bootstrap frame rejection followed by clean full-chain CPI."""
import json,sys,hashlib,time,secrets
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from pc_link.board_dsp import run_board_dsp,BITSTREAM
from pc_link.serial_io import connect_serial_port
from pc_link.session import PCSession
PORT='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_f4d179353796ed11aa2f634ce259fb3e-if00-port0'
OUT=R/'engineering/evidence/s11/uart_fault_20261114';OUT.mkdir(exist_ok=False)
assert hashlib.sha256(BITSTREAM.read_bytes()).hexdigest()=='fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb'
u=connect_serial_port(PORT)
try:
 hello=PCSession(secrets.token_bytes(16),mode=0,max_retries=3).start()
 bad=bytearray(hello);bad[-1]^=0x01
 u.write(bytes(bad));bad_reply=u.read_frame(.3)
 u.write(hello[:10]);partial_reply=u.read_frame(.3)
finally:u.io.close()
# Neither malformed frame is accepted as a complete handshake; a clean session starts afresh.
r=run_board_dsp(bytes(16896),PORT,cpi_id=393000001,journal_dir=OUT)
assert r['terminal']=='COMMIT' and r['released'] and r['input_bytewise_verified']
result=dict(corrupt_crc_response=repr(bad_reply),truncated_frame_response=repr(partial_reply),fresh_cpi='PASS',journal=r['journal_path'],bitstream_sha256=r['bitstream_sha256'])
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

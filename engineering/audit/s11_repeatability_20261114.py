"""S11 same-input repeatability of final full-chain image, separate CPI identities."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from pc_link.board_dsp import run_board_dsp,BITSTREAM
OUT=R/'engineering/evidence/s11/repeatability_20261114';OUT.mkdir(exist_ok=False)
PORT='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_f4d179353796ed11aa2f634ce259fb3e-if00-port0'
assert hashlib.sha256(BITSTREAM.read_bytes()).hexdigest()=='fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb'
raw=bytes(16896)
runs=[run_board_dsp(raw,PORT,cpi_id=392000001+i,journal_dir=OUT) for i in range(2)]
a,b=runs
assert all(x['terminal']=='COMMIT' and x['released'] and x['input_bytewise_verified'] for x in runs)
assert np.array_equal(np.asarray(a['power'],dtype=np.uint64),np.asarray(b['power'],dtype=np.uint64))
assert a['records']==b['records']
result=dict(status='PASS',same_iq_sha256=a['iq_sha256'],power_exact=True,records_exact=True,journals=[x['journal_path'] for x in runs],times_s=[x['elapsed_s'] for x in runs],bitstream_sha256=a['bitstream_sha256'])
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

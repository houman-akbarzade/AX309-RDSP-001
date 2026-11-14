"""S11 physical Power-peak test of approved eight RNG_D4/D5 phase cases."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'engineering/s04_numeric')]
from pc_link.board_dsp import run_board_dsp,BITSTREAM
from hardware_pd_pfa_capture_v1 import quantized_iq
from fft_ip_fullchain_v1 import full_chain
P=R/'engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-INPUTS-v1.0.npz'
OUT=R/'engineering/evidence/s11/range_power_20261114';OUT.mkdir(exist_ok=False)
PORT='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_f4d179353796ed11aa2f634ce259fb3e-if00-port0'
assert hashlib.sha256(BITSTREAM.read_bytes()).hexdigest()=='fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb'
rows=[]
with np.load(P) as z:
 for d in (4,5):
  for phase in (0,90,180,270):
   case=f'RNG_D{d}_PHASE_{phase:03d}';src=z['float_iq_'+case]
   iq,clips=quantized_iq(src,1);assert clips==0
   h=run_board_dsp(iq,PORT,cpi_id=391000000+10*d+phase,journal_dir=OUT)
   m=full_chain(np.frombuffer(iq,dtype='<i2').reshape(33,128,2))
   p=np.asarray(h['power'],dtype=np.uint64);q=np.asarray(m['native']['power'],dtype=np.uint64)
   assert np.array_equal(p,q)
   peaks=[i for i in range(1,127) if p[i,4]>p[i-1,4] and p[i,4]>p[i+1,4]]
   pairs=[(a,b) for a in peaks for b in peaks if abs(a-40)<=1 and abs(b-(40+d))<=1 and a<b and b-a>=2 and np.any(p[a+1:b,4]<min(p[a,4],p[b,4]))]
   row=dict(case=case,truth=[40,40+d],pass_power=bool(pairs),matched_pair=list(pairs[0]) if pairs else None,strict_maxima=peaks,model_power_exact=True,terminal=h['terminal'],released=h['released'],iq_verified=h['input_bytewise_verified'],journal=h['journal_path'],elapsed_s=h['elapsed_s'])
   rows.append(row);(OUT/'RESULT.json').write_text(json.dumps(dict(rows=rows,completed=len(rows),planned=8),indent=2)+'\n')
   print(case,'PASS' if pairs else 'FAIL',pairs[:1],flush=True)
print('FINAL',sum(x['pass_power'] for x in rows),'/',len(rows),flush=True)

"""Independent test oracle vectors, never deriving expected bits from DUT results."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c03_independent_oracle_v1 as O
import s04_c04_fullchain_qualification_v1 as P
MF_POS=[(p,r) for p in (0,8,16,32) for r in (0,40,55,127)]
MT_POS=[(p,r) for p in (0,7,15,31) for r in (0,40,55,127)]
BINS=[0,5,6,16,31]
RANGES=[0,40,55,127]
records={}
for g in (1,5):
 for kind in P.KINDS:
  _,iq,events,digest=P.source(kind,g)
  mf=[[O.mf_at(iq,p,r,P.TAPS) for r in range(128)] for p in range(33)]
  mt=[[O.mti(mf[p][r],mf[p+1][r]) for r in range(128)] for p in range(32)]
  row={'input_rational_SHA256':digest,'input_sat_count':len(events),
       'MF':{f'{p}:{r}':list(mf[p][r]) for p,r in MF_POS},
       'MTI':{f'{p}:{r}':list(mt[p][r]) for p,r in MT_POS},'FFT_stages':{}}
  for r in RANGES:
    st=O.fft32_oracle([mt[p][r] for p in range(32)],P.TW)
    for j in range(5):
      for b in BINS:
       row['FFT_stages'][f'{j+1}:{r}:{b}']=list(st[j][b])
  records[f'g{g}:{kind}']=row
obj={'version':'S04-C04-independent-C03-Fraction-golden-v1.0',
     'origin':'C03 independent Oracle and deterministic arithmetic source, NOT candidate DUT outputs',
     'MF_positions':MF_POS,'MT_positions':MT_POS,'FFT_ranges':RANGES,'FFT_bins':BINS,
     'g':[1,5],'kinds':list(P.KINDS),'records':records,
     'record_count':len(records),'frozen_C_architecture':True,
     'fixed_point_expected_from_independent_oracle_only':True}
p=ROOT/'engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json'
p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('GOLDEN',len(records),'SHA256',hashlib.sha256(p.read_bytes()).hexdigest())

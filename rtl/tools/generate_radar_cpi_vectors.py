#!/usr/bin/env python3
"""Development vectors only; no statistical acceptance campaign."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'engineering/s04_numeric')]
import numpy as np
from s03_reference import model as M
import s04_c04_selected_C_stage_capture_v1 as C
import s04_c05_native_integer_v1 as D
OUT=ROOT/'rtl/tb/vectors/radar_cpi'
OUT.mkdir(parents=True,exist_ok=True)
def pack(i,q,w):return ((q&((1<<w)-1))<<w)|(i&((1<<w)-1))
def save(name,values,width):
 p=OUT/name;p.write_text(''.join(f'{v:0{width}x}\n' for v in values))
 return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=[]
for idx,(name,targets) in enumerate([
 ('zero',[]),('single',[M.Target(40,2.8125,.18)]),
 ('multi',[M.Target(35,2.8125,.18),M.Target(80,-3.75,.12)])]):
 x=M.generate_cpi(targets)
 raw,clips=M.quantize_iq(x);assert clips==0
 a=np.frombuffer(raw,dtype='<i2').reshape(33,128,2)
 iq=[[tuple(map(int,v)) for v in row] for row in a]
 src=a[:,:,0]/32768+1j*a[:,:,1]/32768
 result=C.run_one(src,iq,C.Telemetry(),'C_hypothetical',(0,1,0,1,1),1,capture_stages=True)
 captured=result['captured'];res=D.complete_map(captured['rd'])
 hashes={}
 hashes['iq']=save(f'{idx}_iq.hex',[pack(*v,16) for row in iq for v in row],8)
 for key,w in [('mf',22),('mti',23),('rd',25)]:
  hashes[key]=save(f'{idx}_{key}.hex',[pack(*v,w) for row in captured[key] for v in row],(2*w+3)//4)
 hashes['power']=save(f'{idx}_power.hex',[v for row in res['power'] for v in row],12)
 records=res['clusters']
 values=[]
 for v in records:
  # Internal 99-bit record contract, also compared field by field by TB.
  values.append(v['range_bin'] | (v['doppler_bin']<<7) |
    (v['power_stored_integer']<<12) | (v['cluster_cells']<<58) |
    (int(v['tie_flag'])<<70) | (v['max_equal_power_cells']<<71))
 hashes['records']=save(f'{idx}_records.hex',values or [0],25)
 save(f'{idx}_count.hex',[len(records)],3)
 manifest.append(dict(case=idx,name=name,targets=[t.__dict__|{'amplitude':str(t.amplitude)} for t in targets],
  input_saturations=clips,output_saturations=result['overflow']['total'],clusters=records,hashes=hashes))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str)+'\n')
print('GENERATED 3 deterministic full-chain CPIs:',[(v['name'],len(v['clusters'])) for v in manifest])

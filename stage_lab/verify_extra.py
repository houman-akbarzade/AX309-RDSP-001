import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import numpy as np
from stage_lab.application import Worker
from stage_lab.models import *
from stage_lab.transport import run_stage
from stage_lab.verify import corpus
from stage_lab.verify_references import boundary_power
from pc_link.board_dsp import persist
from desktop_app.reference import prepare_with_source

def main():
 E=R/'engineering/evidence/stage_lab_v0.2'
 c=dict(target=5,input_mode='Software FFT → hardware Power + CFAR',engine='Both',arithmetic='Both',scenario='Two aircraft',noise=.002,seed=20261112,pri_count=33,file='',file_format='Normalized float',port='/dev/ttyUSB1',program=True)
 w=Worker(c);w.progress.connect(lambda s:print(s,flush=True));out=w.execute()
 assert out['metrics']['Python Fixed']['exact_decisions'] and out['metrics']['MATLAB Fixed']['exact_decisions']
 persist(E/'combined-power-cfar.json',{k:v for k,v in out.items() if k not in ('actual_input','output','references','source_input','truth')})
 print('PASS combined software FFT input -> hardware Power and CFAR',out['metrics'],flush=True)
 p=boundary_power();r=run_stage(encode(p,4),5,'/dev/ttyUSB1');got=decode(r['output'],5);ref=reference(p,4,5,True)
 assert np.array_equal(got[1],ref[1]);decisions=[bool(got[1][10,20+j*35]) for j in range(3)];assert decisions==[False,False,True]
 persist(E/'physical-cfar-72bit-boundary.json',dict(decisions=decisions,exact_all_decisions=True,status=r['status'],programming=r['programming']))
 print('PASS physical CFAR 72-bit below/equal/above strict threshold',decisions,flush=True)
 _,_,_,source=prepare_with_source('Single aircraft')
 a,_=software_input(source[:1],0);r=run_stage(encode(a,0),1,'/dev/ttyUSB1');got=decode(r['output'],1,1)
 assert np.array_equal(got,reference(a,0,1,True));persist(E/'physical-single-pri-mf.json',dict(samples=128,exact=True,status=r['status'],programming=r['programming']))
 print('PASS single independent PRI MF',flush=True)

if __name__=='__main__':main()

import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import numpy as np
from scipy.io import savemat
from stage_lab.models import *
from stage_lab.application import Worker
from stage_lab.transport import program
from desktop_app.reference import prepare_with_source
from pc_link.board_dsp import persist

def main():
 E=R/'engineering/evidence/stage_lab_v0.2';T=R/'rtl/build/stage_lab/file-tests';T.mkdir(parents=True,exist_ok=True)
 _,_,_,src=prepare_with_source('Two aircraft');fft=np.fft.fft(np.diff(float_mf(src),axis=0),axis=0)/8
 savemat(T/'fft.mat',{'data':fft})
 savemat(T/'empty.mat',{'power':np.zeros((32,128)),'mask':np.zeros((32,128),bool)})
 np.save(T/'one-pri.npy',src[0])
 results=[]
 for target,path,mode in [(4,T/'fft.mat','File'),(6,T/'empty.mat','File'),(1,T/'one-pri.npy','File raw PRI/CPI through hardware')]:
  c=dict(target=target,input_mode=mode,engine='Python',arithmetic='Both',scenario='Two aircraft',noise=.002,seed=20261112,pri_count=33,file=str(path),file_format='Normalized float',port='/dev/ttyUSB1',program=True)
  o=Worker(c).execute();m=o['metrics']['Python Fixed'];assert m.get('exact_integer',m.get('record_signatures_exact'))
  if target==6:
   assert not o['output'];saved=__import__('json').loads(Path(o['journal']+'.json').read_text());assert saved['hardware_records']==[] and 'reference_records' in saved
  else:
   saved=np.load(o['journal']+'.npz');assert 'Python_Float' in saved and 'Python_Fixed' in saved and 'entry' in saved
  results.append(dict(target=target,file=path.name,input_mode=mode,metrics=o['metrics'],journal=o['journal']))
  print('PASS file roundtrip',target,path.name,m,flush=True)
 persist(E/'file-validation.json',dict(results=results));program('power');print('PASS MAT FFT injection, empty grouping and single-PRI NPY hardware injection; reference outputs persisted',flush=True)

if __name__=='__main__':main()

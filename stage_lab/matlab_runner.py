import subprocess,tempfile,time
from pathlib import Path
import numpy as np
from scipy.io import savemat,loadmat
ROOT=Path(__file__).resolve().parents[1]
def reference_matlab(injected,entry,target,fixed):
 b=ROOT/'rtl/build/stage_lab/matlab';b.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(dir=b) as tmp:
  inp=Path(tmp)/'input.mat';out=Path(tmp)/'output.mat'
  payload={'input_a':injected[0],'input_mask':injected[1]} if entry==5 else {'input_a':injected}
  savemat(inp,payload)
  directory=ROOT/'stage_lab/matlab'
  command=f"addpath('{directory}');stage_lab_ref('{inp}','{out}',{entry},{target},{int(fixed)});"
  p=subprocess.run([str(Path.home()/'.local/bin/matlab'),'-batch',command],capture_output=True,text=True,timeout=240)
  if p.returncode:raise RuntimeError(p.stdout+p.stderr)
  m=loadmat(out,simplify_cells=True)
  if target==5:return (np.asarray(m['result_power']),np.asarray(m['result_mask'],bool))
  if target==6:
   r=m['result']
   if isinstance(r,dict):return [r]
   if np.asarray(r).size==0:return []
   return list(r)
  a=np.asarray(m['result'])
  if a.ndim==1:a=a.reshape(1,128)
  return a

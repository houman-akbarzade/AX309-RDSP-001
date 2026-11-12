"""Executed Python/MATLAB comparisons and independent FFT trace validation."""
import gzip,json,hashlib
import numpy as np
from pathlib import Path
from .models import *
from .verify import corpus
from .matlab_runner import reference_matlab
from .fft_model import fft_codes,LIB
from pc_link.board_dsp import persist
def boundary_power():
 p=np.zeros((32,128),np.uint64);k=((1<<46)-1)//490007-1
 for j,delta in enumerate([-1,0,1]):
  r=20+j*35;b=10
  for dr in range(-3,4):
   for db in range(-3,4):
    if abs(dr)<=1 and abs(db)<=1:continue
    p[b+db,r+dr]=65536*k
  p[b,r]=490007*k+delta
 return p
def main():
 E=ROOT/'engineering/evidence/stage_lab_v0.2';rows=[]
 for target in range(1,7):
  a,_=corpus(target)
  for fixed in [False,True]:
   py=reference(a,target-1,target,fixed);ml=reference_matlab(a,target-1,target,fixed)
   if target<=4:
    delta=float(np.max(np.abs(np.asarray(py)-np.asarray(ml))))
    assert delta==0 if fixed else delta<1e-9
    result=dict(max_abs_delta=delta,exact=delta==0)
   else:
    result=compare(py,ml,target,fixed)
    assert result.get('exact_decisions',result.get('record_signatures_exact'))
   row=dict(stage=target,fixed=fixed,comparison=result,backend='Actual MATLAB R2024a batch execution vs Python');rows.append(row);print(row,flush=True)
   persist(E/'reference-validation.json',dict(results=rows))
 p=boundary_power();py=reference(p,4,5,True);ml=reference_matlab(p,4,5,True)
 assert np.array_equal(py[1],ml[1])
 assert [bool(py[1][10,20+j*35]) for j in range(3)]==[False,False,True]
 rows.append(dict(stage=5,test='72-bit boundary: below/equal/above',decisions=[False,False,True],matlab_python_exact=True))
 persist(E/'reference-validation.json',dict(results=rows))
 traces={}
 for rel in ['engineering/evidence/s05/fft_ip_20261112/lite_bram/fft-ip-output.txt.gz','engineering/evidence/s05/ip_evaluation_20261112/numeric/more-ip-output.txt.gz']:
  for l in gzip.open(ROOT/rel,'rt'):
   c,r,b,v=l.split();word=int(v,16);re=word&((1<<25)-1);im=(word>>25)&((1<<25)-1)
   traces[(int(c),int(b),int(r))]=(re-(1<<25) if re&(1<<24) else re)+1j*(im-(1<<25) if im&(1<<24) else im)
 mismatches=0;count=0
 for case in range(11):
  x=np.load(ROOT/f'engineering/evidence/s05/ip_evaluation_20261112/numeric/{case}_arrays.npz')['fixed_mti']
  a=x[:,:,0]+1j*x[:,:,1];got,ov=fft_codes(a)
  expected=np.array([[traces[(case,b,r)] for r in range(128)] for b in range(32)])
  mismatches+=int(np.count_nonzero(got!=expected));count+=got.size;assert ov==0
 assert mismatches==0
 persist(E/'fft-cmodel-validation.json',dict(cases=11,complex_words=count,integer_mismatches=mismatches,overflow_cases=0,library=str(LIB/'libIp_xfft_v7_1_bitacc_cmodel.so'),library_sha256=hashlib.sha256((LIB/'libIp_xfft_v7_1_bitacc_cmodel.so').read_bytes()).hexdigest(),scope='Independent prior structural ISim traces, not legacy FFT RTL'))
 print('PASS 12 actual MATLAB reference checks, 72-bit CFAR boundary, 45056 independent FFT trace words',flush=True)
if __name__=='__main__':main()

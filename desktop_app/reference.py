"""Float64 reference independent of both fixed FFT implementations."""
import numpy as np
from s03_reference import model as M
from .scenarios import prepare,exact_reference,score,ROOT
def prepare_with_source(*args,**kwargs):
 capture={};original=M.quantize_iq
 def quantize(x):
  capture['source']=np.array(x,copy=True)
  return original(x)
 M.quantize_iq=quantize
 try:raw,targets,meta=prepare(*args,**kwargs)
 finally:M.quantize_iq=original
 return raw,targets,meta,capture['source']
def float_reference(source):
 rd=M.doppler(M.mti(M.pulse_compress(source)))/8
 power=np.abs(rd)**2
 mask,valid,noise=M.cfar_2d(power,alpha=7.476912055027923)
 records=M.clusters_8(mask,power)
 for r in records:
  b=r['doppler_bin'];r['signed_doppler_bin']=b if b<16 else b-32
  r['peak_power_linear']=r['power_linear']
 return dict(power=power,mask=mask,records=records)
def native_from_power(power):
 import sys
 sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
 import s04_c05_native_integer_v1 as C
 p=[[int(v) for v in row] for row in power]
 mask,_=C.native_cfar(p);records=C.native_clusters(mask,p)
 return np.array(mask,bool),records
def compare_geometry(actual,reference):
 fields=['range_bin','doppler_bin','cluster_cells']
 a=[tuple(r[k] for k in fields) for r in actual];b=[tuple(r[k] for k in fields) for r in reference]
 return dict(actual_clusters=len(a),float_clusters=len(b),same_peak_and_cell_signatures=(a==b),
  same_peak_coordinates=sorted(x[:2] for x in a)==sorted(x[:2] for x in b),
  note='Peak/cell signatures only; downloaded final records do not contain full component membership.')

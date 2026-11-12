"""Independent stage references; injection defaults to SOFTWARE FLOAT FFT, not IP FFT."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
from s03_reference import model as M
import s04_c04_selected_C_stage_capture_v1 as C04
import s04_c05_native_integer_v1 as C05
NAMES={0:'Raw IQ',1:'MF',2:'MTI',3:'FFT',4:'Power',5:'CFAR',6:'Grouping'}
WIDTH={0:16,1:22,2:23,3:25}
def quantize(a,stage):
 a=np.asarray(a);
 if not np.all(np.isfinite(a)):raise ValueError('Nonfinite input samples')
 w=WIDTH[stage];re=np.rint(a.real*32768);im=np.rint(a.imag*32768)
 clips=int(np.count_nonzero((re<-(1<<(w-1)))|(re>((1<<(w-1))-1)))+np.count_nonzero((im<-(1<<(w-1)))|(im>((1<<(w-1))-1))))
 re=np.clip(re,-(1<<(w-1)),(1<<(w-1))-1).astype(np.int64);im=np.clip(im,-(1<<(w-1)),(1<<(w-1))-1).astype(np.int64)
 return re+1j*im,clips
def pack_complex(codes):
 a=np.asarray(codes);re=a.real.astype(np.int64);im=a.imag.astype(np.int64)
 return ((re.astype(np.uint64)&np.uint64(0xffffffff))|((im.astype(np.uint64)&np.uint64(0xffffffff))<<np.uint64(32))).reshape(-1).astype('<u8')
def unpack_complex(words,rows):
 a=np.asarray(words,dtype='<u8').reshape(rows,128)
 re=(a&np.uint64(0xffffffff)).astype(np.uint32).view(np.int32).astype(float)
 im=(a>>np.uint64(32)).astype(np.uint32).view(np.int32).astype(float)
 return re+1j*im
def encode(a,stage):
 if stage<=3:return pack_complex(a)
 if stage==4:return np.asarray(a,dtype=np.uint64).reshape(-1)
 if stage==5:
  power,mask=a
  return (np.asarray(power,dtype=np.uint64)|(np.asarray(mask,dtype=np.uint64)<<np.uint64(63))).reshape(-1)
 raise ValueError(stage)
def decode(words,stage,rows=32):
 words=np.asarray(words,dtype=np.uint64)
 if stage<=3:return unpack_complex(words,rows)
 if stage==4:return words.reshape(32,128)
 if stage==5:return (words.reshape(32,128)&np.uint64((1<<46)-1),(words.reshape(32,128)>>np.uint64(63)).astype(bool))
 if stage==6:
  from pc_link.iq import Record
  rec=[]
  for i in range(0,len(words),2):
   v=int(words[i])|(int(words[i+1])<<64);r=Record.unpack(v.to_bytes(13,'little'));rec.append(dict(record_id=r.record_id,range_bin=r.range_bin,doppler_bin=r.doppler_bin,signed_doppler_bin=r.signed_doppler,power_stored_integer=r.peak_power,cluster_cells=r.cluster_cells,tie_flag=bool(r.peak_tie),max_equal_power_cells=r.equal_power_cells))
  return rec
def float_mf(a):
 h=M.matched_filter()
 return np.array([np.convolve(row,h,'full')[15:143] for row in a])
def fixed_mf(a):
 taps,_=C04.coefficients('C_hypothetical');out=np.zeros(a.shape,complex)
 for p in range(a.shape[0]):
  for r in range(128):
   re=im=0
   for k,(hr,hi) in enumerate(taps):
    idx=r+15-k
    if idx>=128:continue
    ir=int(a[p,idx].real);ii=int(a[p,idx].imag);re+=ir*hr-ii*hi;im+=ir*hi+ii*hr
   rr=C04.rne(re,32768);ri=C04.rne(im,32768)
   out[p,r]=max(-(1<<21),min((1<<21)-1,rr))+1j*max(-(1<<21),min((1<<21)-1,ri))
 return out
def step(a,target,fixed):
 if target==1:return fixed_mf(a) if fixed else float_mf(a)
 if target==2:return a[1:]-a[:-1]
 if target==3:
  if fixed:
   from .fft_model import fft_codes
   return fft_codes(a)[0]
  return np.fft.fft(a,axis=0)/8
 if target==4:
  if fixed:
   rr=a.real.astype(np.int64);ii=a.imag.astype(np.int64)
   return np.minimum(rr*rr+ii*ii,(1<<46)-1).astype(np.uint64)
  return np.abs(a)**2
 if target==5:
  power=np.asarray(a)
  if fixed:
   mask,_=C05.native_cfar(power.T.tolist());return power,np.array(mask,bool).T
  mask,_,_=M.cfar_2d(power.T,alpha=7.476912055027923);return power,mask.T
 if target==6:
  power,mask=a
  if fixed:return C05.native_clusters(np.asarray(mask).T.tolist(),np.asarray(power).T.tolist())
  rec=M.clusters_8(np.asarray(mask).T,np.asarray(power).T)
  for r in rec:
   b=r['doppler_bin'];r['signed_doppler_bin']=b if b<16 else b-32
  return rec
def reference(injected,entry,target,fixed=True):
 a=injected
 if not fixed:
  if entry<=3:a=np.asarray(a)/32768
  elif entry==4:a=np.asarray(a)/(1<<30)
  elif entry==5:a=(np.asarray(a[0])/(1<<30),a[1])
 for stage in range(entry+1,target+1):a=step(a,stage,fixed)
 return a
def software_input(raw_source,entry):
 """Generate injection independently of the IP: full Float chain up to requested entry."""
 a=np.asarray(raw_source,complex)
 for stage in range(1,entry+1):a=step(a,stage,False)
 if entry<=3:
  q,clips=quantize(a,entry)
  if clips:raise ValueError(f'{clips} input components clipped; reduce amplitude')
  return q,dict(origin='Software Float FFT/chain (no IP model)',input_quantization_RMSE=float(np.sqrt(np.mean(np.abs(q/32768-a)**2))),input_clips=clips)
 if entry==4:
  p=np.rint(a*(1<<30))
  if np.any(p<0) or np.any(p>((1<<46)-1)):raise ValueError('Power input out of U46.30 range')
  return p.astype(np.uint64),dict(origin='Software Float Power after software Float FFT',input_quantization_RMSE=float(np.sqrt(np.mean((p/(1<<30)-a)**2))))
 if entry==5:
  p,mask=a;power=np.rint(p*(1<<30))
  if np.any(power>((1<<46)-1)):raise ValueError('CFAR Power input out of range')
  return (power.astype(np.uint64),mask),dict(origin='Software Float CFAR mask plus Power',input_quantization_RMSE=float(np.sqrt(np.mean((power/(1<<30)-p)**2))))
def compare(got,ref,target,fixed):
 if target<=3:
  a=np.asarray(got)/32768;b=np.asarray(ref)/(32768 if fixed else 1)
 elif target==4:
  a=np.asarray(got,dtype=float)/(1<<30);b=np.asarray(ref,dtype=float)/((1<<30) if fixed else 1)
 elif target==5:
  return dict(decision_mismatches=int(np.count_nonzero(got[1]!=ref[1])),extra_alarms_vs_reference=int(np.count_nonzero(got[1]&~ref[1])),missing_alarms_vs_reference=int(np.count_nonzero(~got[1]&ref[1])),valid_CUTs=2782,exact_decisions=bool(np.array_equal(got[1],ref[1])))
 else:
  fields=['range_bin','doppler_bin','cluster_cells']
  if fixed:fields+=['power_stored_integer','tie_flag','max_equal_power_cells']
  gpeaks={(int(r['range_bin']),int(r['doppler_bin'])) for r in got};rpeaks={(int(r['range_bin']),int(r['doppler_bin'])) for r in ref}
  return dict(hardware_clusters=len(got),reference_clusters=len(ref),common_peak_coordinates=len(gpeaks&rpeaks),hardware_only_peaks=sorted(gpeaks-rpeaks),reference_only_peaks=sorted(rpeaks-gpeaks),record_signatures_exact=[[r[k] for k in fields] for r in got]==[[r[k] for k in fields] for r in ref])
 err=a-b;rmse=float(np.sqrt(np.mean(np.abs(err)**2)));rms=float(np.sqrt(np.mean(np.abs(b)**2)))
 return dict(RMSE=rmse,NRMSE_percent=100*rmse/rms if rms else None,max_abs_error=float(np.max(np.abs(err))),units='normalized amplitude' if target<=3 else 'normalized Power',exact_integer=bool(np.array_equal(np.asarray(got),np.asarray(ref))) if fixed else None)

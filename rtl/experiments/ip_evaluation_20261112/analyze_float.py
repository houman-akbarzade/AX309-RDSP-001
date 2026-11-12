#!/usr/bin/env python3
"""Compare both FFTs to independent Float64 FFT and complete Float pipeline."""
from pathlib import Path
import sys,json,math
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'engineering/s04_numeric')]
from s03_reference import model as M
import s04_c05_native_integer_v1 as C05
B=ROOT/'rtl/build/ip_evaluation_numeric'
ALPHA=7.476912055027923
def signed(v,w):return v-(1<<w) if v&(1<<(w-1)) else v
def load_trace(path,data):
 for line in Path(path).read_text().splitlines():
  c,r,b,v=line.split();c,r,b=map(int,(c,r,b));v=int(v,16)
  assert data[c][r][b] is None
  data[c][r][b]=(signed(v&((1<<25)-1),25),signed((v>>25)&((1<<25)-1),25))
def stats(got,ref):
 error=np.asarray(got)-np.asarray(ref)
 mse=float(np.mean(np.abs(error)**2))
 rms=float(np.sqrt(np.mean(np.abs(ref)**2)))
 return dict(complex_RMSE=math.sqrt(mse),NRMSE_percent=100*math.sqrt(mse)/rms if rms else None,
  float_RMS=rms,max_abs_complex_error=float(np.max(np.abs(error))),
  I_RMSE=float(np.sqrt(np.mean(np.real(error)**2))),Q_RMSE=float(np.sqrt(np.mean(np.imag(error)**2))))
def components(mask,power):
 pts={tuple(map(int,v)) for v in np.argwhere(mask)};out=[]
 while pts:
  todo=[min(pts)];pts.remove(todo[0]);cells=set(todo)
  while todo:
   r,b=todo.pop()
   for rr in range(max(0,r-1),min(128,r+2)):
    for bb in range(max(0,b-1),min(32,b+2)):
     v=(rr,bb)
     if v in pts:pts.remove(v);cells.add(v);todo.append(v)
  peak=min(cells,key=lambda v:(-power[v],v[1] if v[1]<=15 else v[1]-32,v[0],v[1]))
  out.append((frozenset(cells),peak))
 return sorted(out,key=lambda v:(v[1][0],v[1][1] if v[1][1]<=15 else v[1][1]-32))
def topology(reference,actual):
 a=[[j for j,(c,p) in enumerate(actual) if f&c] for f,peak in reference]
 b=[[i for i,(c,p) in enumerate(reference) if f&c] for f,peak in actual]
 return dict(unchanged_membership=sum(any(f==g for g,p in actual) for f,peak in reference),
  reference_components_without_overlap=sum(not v for v in a),
  new_components_without_reference_overlap=sum(not v for v in b),
  split_reference_components=sum(len(v)>1 for v in a),merged_output_components=sum(len(v)>1 for v in b),
  identical_peak_coordinates=len({p for c,p in reference}&{p for c,p in actual}),
  one_to_one_peak_changes=[dict(float_peak=list(reference[i][1]),actual_peak=list(actual[v[0]][1]))
   for i,v in enumerate(a) if len(v)==1 and len(b[v[0]])==1 and reference[i][1]!=actual[v[0]][1]])
def float_post(rd):
 power=np.abs(rd)**2
 mask,valid,noise=M.cfar_2d(power,alpha=ALPHA)
 records=M.clusters_8(mask,power)
 return power,mask,records
def fixed_post(codes):
 result=C05.complete_map(codes)
 power=np.asarray(result['power'],float)/(1<<30);mask=np.asarray(result['mask'],bool)
 records=[dict(v,velocity_m_s_nominal=float(M.bin_velocity(v['doppler_bin']))) for v in result['clusters']]
 return power,mask,records
def aggregate(cases,field,branch):
 rows=[c[field][branch] for c in cases]
 mse=sum(v['complex_RMSE']**2 for v in rows)/len(rows)
 refmse=sum(v['float_RMS']**2 for v in rows)/len(rows)
 return dict(complex_RMSE=math.sqrt(mse),NRMSE_percent=100*math.sqrt(mse/refmse) if refmse else None,
  case_count=len(rows),complex_words=len(rows)*4096)
def main():
 cases=json.loads((B/'cases.json').read_text())
 data=[[[None]*32 for _ in range(128)] for _ in cases]
 old_trace=ROOT/'engineering/evidence/s05/fft_ip_20261112/lite_bram/fft-ip-output.txt.gz'
 import gzip
 # Load old immutable structural trace and the new complete development trace.
 old_lines=gzip.open(old_trace,'rt').read()
 old_tmp=B/'old-ip-trace.txt';old_tmp.write_text(old_lines)
 load_trace(old_tmp,data);load_trace(B/'sim/more-ip-output.txt',data)
 output=[]
 for c in cases:
  idx=c['case'];assert all(v is not None for row in data[idx] for v in row)
  z=np.load(B/f'{idx}_arrays.npz')
  old_codes=z['fixed_fft'];ip_codes=np.asarray(data[idx],dtype=np.int64)
  old=(old_codes[:,:,0]+1j*old_codes[:,:,1])/32768
  ip=(ip_codes[:,:,0]+1j*ip_codes[:,:,1])/32768
  float_source=z['float_source'];float_adc=z['float_full'];float_fft=z['float_isolated']
  pfloat,mfloat,rfloat=float_post(float_source)
  padc,madc,radc=float_post(float_adc)
  pold,mold,rold=fixed_post(old_codes.tolist())
  pip,mip,rip=fixed_post(ip_codes.tolist())
  refs=components(mfloat,pfloat)
  truth=[dict(id=t['id'],range_m_nominal=t['delay']*M.C_NOMINAL/(2*M.FS),velocity_m_s=t['velocity']) for t in c['truth']]
  def signature(mask,power):
   return [dict(range_bin=peak[0],doppler_bin=peak[1],cells=len(cells),
    equal_peak_cells=sum(power[v]==power[peak] for v in cells))
    for cells,peak in components(mask,power)]
  signature_float=signature(mfloat,pfloat)
  branch_info={}
  for branch,power,mask,records in [('float',pfloat,mfloat,rfloat),('fixed',pold,mold,rold),('ip',pip,mip,rip),('float_on_quantized_IQ',padc,madc,radc)]:
   sig=signature(mask,power)
   branch_info[branch]=dict(cluster_count=len(records),alarm_cells=int(mask.sum()),
    geometry_tie_signature=sig,geometry_tie_signature_matches_source_float=(sig==signature_float),
    truth_comparison=M.separation_metrics(records,truth),
    cluster_records=records,
    topology_vs_source_float=topology(refs,components(mask,power)),
    CFAR_cells_disagreeing_with_source_float=int(np.count_nonzero(mask!=mfloat)))
  output.append(dict(case=idx,name=c['name'],truth=c['truth'],metadata=c['metadata'],
   isolated_FFT=dict(fixed=stats(old,float_fft),ip=stats(ip,float_fft)),
   end_to_end_source_float=dict(fixed=stats(old,float_source),ip=stats(ip,float_source)),
   end_to_end_common_ADC_float=dict(fixed=stats(old,float_adc),ip=stats(ip,float_adc)),
   power_vs_source_float=dict(fixed=stats(pold,pfloat),ip=stats(pip,pfloat)),
   clustering=branch_info))
 result=dict(project='AX309-RDSP-001',scope='Finite deterministic development set; NOT statistical acceptance',
  definitions=dict(primary_float='S03 Float64 MF/MTI/FFT on the original pre-IQ-quantization samples, scaled by 1/8',
   isolated_FFT_float='NumPy FFT on identical frozen fixed MTI input codes divided by 32768; scaled by 1/8',
   auxiliary_float='S03 Float64 full chain on the same quantized ADC IQ, isolating ADC quantization effects',
   complex_RMSE='sqrt(mean(abs(Y-Y_float)^2)); normalized signal units, NOT LSB',
   NRMSE_percent='100*RMSE/sqrt(mean(abs(Y_float)^2)); null if reference energy is zero',
   alpha_float=ALPHA,alpha_fixed=[490007,65536],truth_gate='Existing S03 scorer: ±2 range bins, ±1 Doppler bin; development association, not final acceptance',
   fixed_power='Exact C05 U46.30 squared magnitude and saturation for both fixed FFT variants',
   missing_contract='IP overflow wraps and does not provide C02 prelimit traces; nonoverflow cases only in this corpus'),
  aggregate={},cases=output)
 for subset,rows in [('all_11',output),('noisy_development_8',output[3:])]:
  result['aggregate'][subset]={field:{branch:aggregate(rows,field,branch) for branch in ['fixed','ip']} for field in ['isolated_FFT','end_to_end_source_float','end_to_end_common_ADC_float']}
 (B/'float-comparison.json').write_text(json.dumps(result,indent=2,default=lambda v: v.item() if hasattr(v,'item') else str(v))+'\n')
 print(json.dumps(result['aggregate'],indent=2))
 for c in output:
  print(c['case'],c['name'],'clusters Float/fixed/IP',
   [c['clustering'][b]['cluster_count'] for b in ['float','fixed','ip']],
   'truth matched',[c['clustering'][b]['truth_comparison']['matched'] for b in ['float','fixed','ip']],
   'FFT RMSE',[c['isolated_FFT'][b]['complex_RMSE'] for b in ['fixed','ip']])
if __name__=='__main__':main()

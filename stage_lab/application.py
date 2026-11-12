"""Stage execution and comparison. Stable DSP modules are reused, never reimplemented in GUI."""
import json,time,hashlib,traceback
from pathlib import Path
import numpy as np
from PySide6.QtCore import QThread,Signal
from .models import *
from .transport import run_stage,program,PROGRAMMER
from .matlab_runner import reference_matlab
from desktop_app.reference import prepare_with_source
from pc_link.board_dsp import persist
class Worker(QThread):
 completed=Signal(object);failed=Signal(str);progress=Signal(str)
 def __init__(self,config):super().__init__();self.config=config
 def run(self):
  try:self.completed.emit(self.execute())
  except Exception:self.failed.emit(traceback.format_exc())
 def execute(self):
  c=self.config;target=c['target'];started=time.monotonic()
  if c['scenario']=='Noise only':
   from s03_reference import model as M
   rng=np.random.default_rng(c['seed']);source=M.generate_cpi([])+c['noise']/np.sqrt(2)*(rng.normal(size=(33,128))+1j*rng.normal(size=(33,128)))
   truth=[];metadata=dict(scenario='Noise only',noise_rms=c['noise'],seed=c['seed'])
  else:_,truth,metadata,source=prepare_with_source(c['scenario'],noise_rms=c['noise'],seed=c['seed'])
  if c.get('target_velocities') is not None and truth:
   from dataclasses import replace
   from s03_reference import model as M
   velocities=c['target_velocities']
   if len(velocities)!=len(truth) or any(not np.isfinite(v) or not -7.5<=v<7.5 for v in velocities):raise ValueError('One radial velocity per target in [-7.5,7.5) m/s is required')
   adjusted=[replace(t,velocity=float(v)) for t,v in zip(truth,velocities)]
   def signal(ts):return M.generate_cpi([M.Target(t.delay,t.velocity,t.amplitude) for t in ts])
   if any(a.velocity!=b.velocity for a,b in zip(adjusted,truth)):source=source+(signal(adjusted)-signal(truth))
   truth=adjusted
   metadata['target_velocities_m_s']=velocities
  if target in (1,2):source=source[:c['pri_count']]
  input_mode=c['input_mode'];raw_chain=input_mode in ('Raw PRI/CPI through hardware','File raw PRI/CPI through hardware')
  traces=[];engine_results=[];initial=None
  if input_mode.startswith('File'):
   entry=0 if raw_chain else 3 if input_mode=='File FFT → hardware Power + CFAR' else target-1;p=Path(c['file'])
   if p.suffix.lower()=='.mat':
    from scipy.io import loadmat
    z=loadmat(p,simplify_cells=True)
   else:z=np.load(p,allow_pickle=False)
   if isinstance(z,np.ndarray):a=z
   else:
    if 'input_words' in z:
     key='initial_words' if raw_chain and 'initial_words' in z else 'input_words'
     stored_entry=int(z['initial_entry']) if key=='initial_words' and 'initial_entry' in z else int(z['entry'])
     if stored_entry!=entry:raise ValueError('Export entry stage differs from selected file mode')
     a=decode(z[key],entry,rows=z[key].size//128)
     c=dict(c,file_format='Stored codes')
    elif entry==5:a=(z['power'],z['mask'])
    else:a=z['data'] if 'data' in z else z['power'] if entry==4 and 'power' in z else z['codes']
   ideal_for_quant=np.asarray(a[0] if entry==5 else a).copy()
   if c['file_format']=='Normalized float':
    if entry<=3:a,clips=quantize(a,entry);assert clips==0,'File input clips; select valid scale'
    elif entry==4:
     a=np.rint(np.asarray(a)*(1<<30))
     if np.any(a<0) or np.any(a>((1<<46)-1)):raise ValueError('Power file out of U46.30 range')
     a=a.astype(np.uint64)
    else:
     pwr,mask=a;pwr=np.rint(pwr*(1<<30))
     if np.any(pwr<0) or np.any(pwr>((1<<46)-1)):raise ValueError('CFAR Power file out of range')
     a=(pwr.astype(np.uint64),mask)
   else:
    if entry<=3:
     a=np.asarray(a,complex);w=WIDTH[entry]
     if np.any(a.real!=np.rint(a.real)) or np.any(a.imag!=np.rint(a.imag)) or np.any(a.real<-(1<<(w-1))) or np.any(a.real>((1<<(w-1))-1)) or np.any(a.imag<-(1<<(w-1))) or np.any(a.imag>((1<<(w-1))-1)):raise ValueError('Complex stored codes outside selected stage format')
    elif entry==4:
     if not np.all(np.isfinite(a)) or np.any(np.asarray(a)!=np.rint(a)) or np.any(np.asarray(a)<0) or np.any(np.asarray(a)>((1<<46)-1)):raise ValueError('Power codes out of range')
     a=np.asarray(a,np.uint64)
    else:a=(np.asarray(a[0]),np.asarray(a[1]))
   truth=[];metadata=dict(scenario='User file',truth='Not supplied');info=dict(origin='User file',path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
   qnorm=(np.asarray(a)/32768) if entry<=3 else (np.asarray(a[0] if entry==5 else a)/(1<<30))
   info['input_quantization_RMSE']=float(np.sqrt(np.mean(np.abs(qnorm-ideal_for_quant)**2))) if c['file_format']=='Normalized float' else 0.0
  else:
   entry=0 if raw_chain else 3 if input_mode=='Software FFT → hardware Power + CFAR' else target-1
   if c.get('injection_engine','Python Float')=='MATLAB Float' and entry>0 and not raw_chain:
    ideal=reference_matlab(source*32768,0,entry,False)
    if entry<=3:
     a,clips=quantize(ideal,entry)
     if clips:raise ValueError('MATLAB source clipped at injection quantizer')
     info=dict(origin='MATLAB Float chain (no IP model)',input_quantization_RMSE=float(np.sqrt(np.mean(np.abs(a/32768-ideal)**2))))
    elif entry==4:
     pwr=np.rint(np.asarray(ideal)*(1<<30))
     if np.any(pwr<0) or np.any(pwr>((1<<46)-1)):raise ValueError('MATLAB Power out of range')
     a=pwr.astype(np.uint64);info=dict(origin='MATLAB Float Power after MATLAB Float FFT',input_quantization_RMSE=float(np.sqrt(np.mean((a/(1<<30)-ideal)**2))))
    else:
     pwr,mask=ideal;pwr=np.rint(pwr*(1<<30))
     if np.any(pwr<0) or np.any(pwr>((1<<46)-1)):raise ValueError('MATLAB CFAR Power out of range')
     a=(pwr.astype(np.uint64),mask);info=dict(origin='MATLAB Float CFAR plus Power',input_quantization_RMSE=float(np.sqrt(np.mean((pwr/(1<<30)-ideal[0])**2))))
   else:a,info=software_input(source,entry)
  if entry<=3:
   a=np.asarray(a,complex)
   if a.ndim==1 and a.size%128==0:a=a.reshape(-1,128)
   if a.ndim!=2 or a.shape[1]!=128:raise ValueError('Complex input must have 128 range columns')
  if entry>=4:
   pwr=np.asarray(a[0] if entry==5 else a)
   if pwr.shape!=(32,128):raise ValueError('Power/CFAR input must be 32 Doppler rows x 128 range columns')
   if not np.all(np.isfinite(pwr)) or np.any(pwr<0) or np.any(pwr>((1<<46)-1)) or np.any(pwr!=np.rint(pwr)):raise ValueError('Invalid injected U46.30 Power codes')
   if entry==5 and (np.asarray(a[1]).shape!=pwr.shape or not np.all((np.asarray(a[1])==0)|(np.asarray(a[1])==1))):raise ValueError('CFAR mask must contain 0/1 and match Power shape')
  if entry==5:
   outside=np.asarray(a[1],bool).copy();outside[3:29,3:110]=False
   if np.any(outside):raise ValueError('CFAR mask outside valid 107x26 CUT raster')
   a=(np.asarray(a[0],np.uint64),np.asarray(a[1],bool))
  if entry==0 and target>=3 and np.asarray(a).shape!=(33,128):raise ValueError('Raw CPI for FFT and later stages must have 33x128 samples')
  initial=a;initial_entry=entry
  targets=list(range(1,target+1)) if raw_chain else [target]
  for stage in targets:
   injected=a;in_stage=stage-1 if raw_chain else entry
   words=encode(injected,in_stage)
   rows=words.size//128
   if words.size>4224 or words.size%128:raise ValueError('Input must have 128 range cells per row')
   expected_rows=32 if stage>=3 else rows
   if stage==2 and not 2<=rows<=33:raise ValueError('MTI expects 2..33 PRI rows')
   if stage>=3 and rows!=expected_rows:raise ValueError(f'Stage {NAMES[stage]} expects {expected_rows} rows')
   self.progress.emit('Hardware '+NAMES[stage])
   r=run_stage(words,stage,c['port'],entry=in_stage,do_program=c['program'],progress=self.progress.emit)
   out_rows=rows-1 if stage==2 else rows
   got=decode(r['output'],stage,rows=out_rows)
   traces.append(dict(stage=stage,input_stage=in_stage,input_sha256=r['input_sha256'],output_sha256=r['output_sha256'],elapsed_s=r['elapsed_s'],status=r['status'],programming=r['programming'],trace=r['trace']))
   engine_results.append(r)
   a=got
  references={};metrics={}
  for engine in (['Python','MATLAB'] if c['engine']=='Both' else [c['engine']]):
   for fixed in ([False,True] if c['arithmetic']=='Both' else [c['arithmetic']=='Fixed']):
    label=engine+(' Fixed' if fixed else ' Float')
    self.progress.emit('Reference '+label)
    ref=reference(injected,in_stage,target,fixed) if engine=='Python' else reference_matlab(injected,in_stage,target,fixed)
    references[label]=ref;metrics[label]=compare(got,ref,target,fixed)
  full_chain={}
  if raw_chain:
   for fixed in [False,True]:
    ref=reference(initial,initial_entry,target,fixed)
    full_chain['Python '+('Fixed' if fixed else 'Float')]=compare(got,ref,target,fixed)
  out=dict(version='0.2.1',target=target,entry=in_stage,input_mode=input_mode,origin=info,metadata=metadata,
   truth=truth,actual_input=decode(engine_results[-1]['input_echo'],in_stage,rows=(engine_results[-1]['input_echo'].size//128)),
   output=got,references=references,metrics=metrics,full_chain_metrics=full_chain,transport=traces,
   elapsed_s=time.monotonic()-started,source_input=initial,source_entry=initial_entry)
  if target in (3,4):
   from .statistics import sweep
   pwr=np.abs(np.asarray(got)/32768)**2 if target==3 else np.asarray(got,float)/(1<<30)
   out['threshold_exploration']=sweep(pwr,truth,noise_only=c['scenario']=='Noise only' and not input_mode.startswith('File'))
  stamp=time.strftime('%Y%m%dT%H%M%S',time.gmtime());p=ROOT/'engineering/evidence/stage_lab_v0.2.1/runs'/f'{stamp}-target{target}'
  p.parent.mkdir(parents=True,exist_ok=True)
  arrays=dict(input_words=engine_results[-1]['input_echo'],output_words=engine_results[-1]['output'],initial_words=encode(initial,initial_entry),initial_entry=np.array(initial_entry),entry=np.array(in_stage),target=np.array(target))
  for label,ref in references.items():
   key=label.replace(' ','_')
   if target<=4:arrays[key]=np.asarray(ref)
   elif target==5:arrays[key+'_power']=ref[0];arrays[key+'_mask']=ref[1]
  np.savez_compressed(p.with_suffix('.npz'),**arrays)
  summary={k:v for k,v in out.items() if k not in ('actual_input','output','references','source_input','truth')}
  if target==6:
   def clean(v):
    if isinstance(v,np.generic):return v.item()
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [clean(x) for x in v]
    return v
   summary['hardware_records']=got;summary['reference_records']=clean(references)
  persist(p.with_suffix('.json'),summary);out['journal']=str(p)
  return out

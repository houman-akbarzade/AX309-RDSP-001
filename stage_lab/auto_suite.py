"""Bounded automatic hardware verification. Every accepted output comes from UART."""
import json,time,hashlib,traceback,subprocess,os
from pathlib import Path
from dataclasses import asdict
import numpy as np
from PySide6.QtCore import QThread,Signal
from .models import ROOT,NAMES,encode,decode,quantize,software_input,reference,compare
from .transport import run_stage,program,PROGRAMMER,stable_bitstream
from .matlab_runner import reference_matlab
from .auto_cases import spec,quick_cases,build_source
from .auto_metrics import functional,cfar_observation,aggregate,association
from pc_link.board_dsp import persist
VERSION='0.3.0'
def jsonable(x):
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,dict):return {k:jsonable(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [jsonable(v) for v in x]
 return x
def new_directory():
 import uuid
 d=ROOT/'engineering/evidence/auto_lab_v0.3/runs'/(time.strftime('%Y%m%dT%H%M%S',time.gmtime())+'-'+uuid.uuid4().hex[:6]);d.mkdir(parents=True);return d
def selected_engines(engine):
 return ['Python','MATLAB'] if engine=='Both' else [engine]
def references(a,entry,target,engine):
 refs={}
 for e in selected_engines(engine):
  for fixed in [False,True]:
   refs[e+(' Fixed' if fixed else ' Float')]=reference(a,entry,target,fixed) if e=='Python' else reference_matlab(a,entry,target,fixed)
 return refs
def array_package(path,job):
 arrays=dict(input_words=job.pop('_input_words'),output_words=job.pop('_output_words'))
 for prefix,refs in [('ref',job.pop('_reference_arrays')),('chain',job.pop('_chain_arrays',{}))]:
  for label,a in refs.items():
   key=prefix+'_'+label.replace(' ','_');t=job['stage']
   if t<=4:arrays[key]=np.asarray(a)
   elif t==5:arrays[key+'_power']=a[0];arrays[key+'_mask']=a[1]
   else:job.setdefault('record_references',{})[prefix+' '+label]=jsonable(a)
 np.savez_compressed(path.with_suffix('.npz'),**arrays)
 persist(path.with_suffix('.json'),jsonable(job))
def plan(level='quick',repeats=32,seed=20261112):
 cases=quick_cases(seed);jobs=[]
 # All stages of four distinct raw-IQ scenarios; interstage data stays hardware-produced.
 for name in ['Two aircraft','MTI mixed','Aircraft in clutter','Weak target near strong']:
  for stage in range(1,7):jobs.append(dict(case=name,scope='accumulated',stage=stage))
 for stage in range(1,7):jobs.append(dict(case='Two aircraft',scope='isolated',stage=stage))
 for name in ['MTI stationary','MTI near-stationary','MTI moving']:jobs.append(dict(case=name,scope='isolated',stage=2))
 for name in cases:
  if name.startswith('Range separation'):jobs.append(dict(case=name,scope='isolated',stage=1))
  if name.startswith('Velocity separation') or name=='Off-bin Doppler':jobs.append(dict(case=name,scope='isolated',stage=3))
 jobs.append(dict(case='Low SNR',scope='isolated',stage=6))
 if level=='statistics':
  cases={};jobs=[]
  if repeats<2:raise ValueError('At least two independent CPIs required')
  for k in range(repeats):
   for kind in ['noise','target']:
    name=f'Stat {kind} {k+1}';cases[name]=spec('Noise only' if kind=='noise' else 'Single aircraft',noise=.02,seed=seed+10000+2*k+(kind=='target'));cases[name].update(name=name,stat_kind=kind)
    jobs.extend([dict(case=name,scope='statistics',stage=5),dict(case=name,scope='statistics',stage=6)])
 jobs.sort(key=lambda j:(j['stage'],j['scope']!='accumulated',j['case']))
 return cases,jobs
def execute_suite(config,progress=lambda text:None,cancel=lambda:False):
 from .auto_report import render_report
 d=new_directory();cases,jobs=plan(config.get('level','quick'),config.get('repeats',32),config.get('seed',20261112))
 state=dict(version=VERSION,kind='automatic',status='RUNNING',configuration=config,planned_jobs=len(jobs),jobs=[],cases=cases,started_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),directory=str(d),statistical_claim='Development estimates only')
 sources={};truth={};chain={};stat_cfar={};cache={};image=None;started=time.monotonic()
 try:
  for name,case in cases.items():
   src,ts,meta=build_source(case);sources[name]=src;truth[name]=ts
  for index,j in enumerate(jobs):
   if cancel():state['status']='CANCELLED';break
   name=j['case'];case=cases[name];stage=j['stage'];scope=j['scope'];entry=stage-1
   progress(f"{index+1}/{len(jobs)} | {name} | {scope} | {NAMES[entry]} → {NAMES[stage]}")
   if scope=='accumulated':
    if stage==1:injected,info=software_input(sources[name],0);chain[name]=dict(raw=injected)
    else:injected=chain[name]['output'];info=dict(origin='Previous actual hardware stage; no host DSP substitution')
   elif scope=='statistics' and stage==6:
    injected=stat_cfar[name]['output'];info=dict(origin='Actual hardware CFAR output and retained input Power')
   else:
    source=sources[name][:1] if stage==1 and name.startswith('Range separation') else sources[name]
    if stage==2 and name.startswith('MTI ') and scope=='isolated':source=source[:2]
    injected,info=software_input(source,entry)
   words=encode(injected,entry);key=(stage,entry,hashlib.sha256(words.tobytes()).hexdigest());reused=key in cache
   if reused:r=cache[key]
   else:
    wanted={1:'mf',2:'mti',3:'fft',4:'power',5:'cfar',6:'grouping'}[stage]
    if image!=wanted:program(wanted,progress);image=wanted
    r=run_stage(words,stage,config.get('port','/dev/ttyUSB1'),entry=entry,do_program=False,progress=lambda s:None);cache[key]=r
   rows=words.size//128;got=decode(r['output'],stage,rows-1 if stage==2 else rows)
   refs=references(injected,entry,stage,'Both' if stage>=5 else config.get('engine','Python'));metrics={k:compare(got,v,stage,'Fixed' in k) for k,v in refs.items()}
   full_refs={};full_metrics={}
   if scope=='accumulated':
    chain[name]['output']=got
    full_refs=references(chain[name]['raw'],0,stage,'Both' if stage>=5 else config.get('engine','Python'))
    full_metrics={k:compare(got,v,stage,'Fixed' in k) for k,v in full_refs.items()}
   if scope=='statistics' and stage==5:stat_cfar[name]=dict(output=got)
   if scope=='statistics' and stage==6:stat_cfar[name]['observation']=cfar_observation(stat_cfar[name]['output'][1],got,truth[name])
   fun=functional(case,stage,entry,injected,got,True,truth[name]);ref_fun={k:functional(case,stage,entry,injected,v,'Fixed' in k,truth[name]) for k,v in refs.items()}
   n=f'case-{index+1:03d}';job=dict(id=n,case=name,scope=scope,stage=stage,entry=entry,targets=[asdict(t) for t in truth[name]],noise_rms=case['noise'],seed=case['seed'],origin=info,metrics=metrics,full_chain_metrics=full_metrics,functional=fun,reference_functional=ref_fun,hardware_records=got if stage==6 else None,status=r['status'],physical_UART=True,reused_identical_capture=reused,input_sha256=r['input_sha256'],output_sha256=r['output_sha256'],input_echo_verified=True,elapsed_s=r['elapsed_s'],transport_trace=r['trace'],artifact=n+'.npz',_input_words=r['input_echo'],_output_words=r['output'],_reference_arrays=refs,_chain_arrays=full_refs)
   array_package(d/n,job);state['jobs'].append(job);persist(d/'suite.json',jsonable(state))
  else:state['status']='COMPLETE'
 except Exception:
  state['status']='FAILED';state['error']=traceback.format_exc();progress(state['error'])
 state['elapsed_s']=time.monotonic()-started
 noise=[];target=[]
 for name,v in stat_cfar.items():
  if 'observation' in v:(noise if cases[name]['stat_kind']=='noise' else target).append(v['observation'])
 if noise or target:state['statistics']=aggregate(noise,target);state['statistics']['noise_RMS']=.02;state['statistics']['target_amplitude']=.18;state['statistics']['active_echo_SNR_dB']=float(20*np.log10(.18/.02));state['statistics']['observations']=dict(noise=noise,target=target)
 persist(d/'suite.json',jsonable(state));report=render_report(state,d)
 return dict(report=str(report),directory=str(d),status=state['status'],jobs=len(state['jobs']),planned=len(jobs),statistics=state.get('statistics'),error=state.get('error'))
def execute_normal(config,progress=lambda s:None):
 from .auto_report import render_normal
 from pc_link import board_dsp as B
 case=config['case'];src,truth,meta=build_source(case);codes,info=software_input(src,0)
 if config.get('file'):
  path=Path(config['file'])
  if path.suffix.lower()=='.mat':
   from scipy.io import loadmat
   z=loadmat(path,simplify_cells=True)
  else:z=np.load(path,allow_pickle=False)
  stored=config.get('file_format')=='Stored codes'
  if isinstance(z,np.ndarray):a=z
  elif 'initial_words' in z:
   if int(z['initial_entry'])!=0:raise ValueError('Saved file must contain raw IQ at entry 0')
   a=decode(z['initial_words'],0,33);stored=True
  elif 'input_words' in z:
   if int(z['entry'])!=0:raise ValueError('Saved input is not raw IQ')
   a=decode(z['input_words'],0,33);stored=True
  elif 'raw_codes' in z:a=z['raw_codes'];stored=True
  else:a=z['data'] if 'data' in z else z['codes']
  a=np.asarray(a)
  if a.shape==(33,128,2):a=a[:,:,0]+1j*a[:,:,1]
  if a.shape!=(33,128) or not np.all(np.isfinite(a)):raise ValueError('Raw IQ file must be finite complex 33x128')
  if stored:
   if np.any(a.real!=np.rint(a.real)) or np.any(a.imag!=np.rint(a.imag)) or np.any(a.real<-32768) or np.any(a.real>32767) or np.any(a.imag<-32768) or np.any(a.imag>32767):raise ValueError('Stored raw IQ codes must be signed 16-bit integers')
   codes=a;src=a/32768;info=dict(origin='Raw IQ file stored Q1.15 codes',input_quantization_RMSE=0)
  else:src=a;codes,info=software_input(src,0)
  truth=[];meta=dict(scenario='User IQ file',noise_rms=None,seed=None,targets=[],file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),truth='Not supplied')
 xy=np.stack([codes.real,codes.imag],axis=-1).astype('<i2');raw=xy.tobytes()
 d=new_directory();progress('Programming stable full pipeline into SRAM')
 path=stable_bitstream();env=os.environ.copy();env['LD_LIBRARY_PATH']=str(PROGRAMMER.parents[1]/'lib/x86_64-linux-gnu')
 p=subprocess.run([str(PROGRAMMER),'-c','digilent_hs2','--freq','1000000','-m',str(path)],env=env,capture_output=True,text=True,timeout=40)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 original=B.BITSTREAM;B.BITSTREAM=path
 try:r=B.run_board_dsp(raw,config.get('port','/dev/ttyUSB1'),progress=progress,download_power=True,journal_dir=d/'transport')
 finally:B.BITSTREAM=original
 refs=references(codes,0,6,config.get('engine','Python'));metrics={k:compare(r['records'],v,6,'Fixed' in k) for k,v in refs.items()}
 power=np.asarray(r['power'],np.uint64).T;np.savez_compressed(d/'normal.npz',raw_codes=codes,power=power)
 state=dict(version=VERSION,kind='normal',status='COMPLETE',configuration=config,case=case,metadata=meta,origin=info,hardware_records=r['records'],references=jsonable(refs),metrics=metrics,association=association(r['records'],truth),reference_association={k:association(v,truth) for k,v in refs.items()},physical_UART=True,input_echo_verified=r['input_bytewise_verified'],terminal=r['terminal'],released=r['released'],elapsed_s=r['elapsed_s'],bitstream_sha256=r['bitstream_sha256'],directory=str(d))
 persist(d/'suite.json',jsonable(state));return dict(report=str(render_normal(state,d,power,codes,truth,refs)),directory=str(d),status='COMPLETE',jobs=1,planned=1)
class AutoWorker(QThread):
 progress=Signal(str);completed=Signal(object);failed=Signal(str)
 def __init__(self,config):super().__init__();self.config=config;self.cancelled=False
 def run(self):
  try:self.completed.emit(execute_normal(self.config,self.progress.emit) if self.config['mode']=='normal' else execute_suite(self.config,self.progress.emit,lambda:self.cancelled))
  except Exception:self.failed.emit(traceback.format_exc())

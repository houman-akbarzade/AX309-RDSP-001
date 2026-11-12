"""Scenario source of truth: existing S03 waveform, no alternative radar."""
from dataclasses import dataclass,asdict
import sys,time
from pathlib import Path
import numpy as np
from s03_reference import model as M
ROOT=Path(__file__).resolve().parents[1]
@dataclass(frozen=True)
class Flight:
 name:str
 delay:int
 velocity:float
 amplitude:float
 bearing:float=0.
 tangential:float=180.
LIBRARY={
 'Single aircraft':[Flight('A1',40,2.8125,.18)],
 'Two aircraft':[Flight('A1',35,2.8125,.18,-.25),Flight('A2',80,-3.75,.12,.25)],
 'Crossing trajectories':[Flight('A1',55,2.8125,.16,0.,180.),Flight('A2',55,-3.75,.16,0.,-180.)],
 'Multiple aircraft':[Flight('A1',22,2.8125,.12,-.4),Flight('A2',48,-3.75,.14,.2),
   Flight('A3',78,5.15625,.09,.4),Flight('A4',99,-5.625,.11,-.2)],
 'Weak target near strong':[Flight('Strong',45,2.8125,.26),Flight('Weak',55,3.75,.026)],
 'Aircraft in clutter':[Flight('A1',65,2.8125,.12)],
 'Closely spaced targets':[Flight('A1',50,2.8125,.15),Flight('A2',52,3.28125,.15)],
 'Low SNR':[Flight('A1',60,2.8125,.06)]}
RANGE_STEP=M.C/(2*M.FS)
VELOCITY_STEP=M.C_NOMINAL/(2*M.FC*32*M.PRI)
def prepare(name,range_shift=0,velocity_shift=0.,amplitude_scale=1.,noise_rms=.002,seed=20261112):
 targets=[]
 for t in LIBRARY[name]:
  d=t.delay+int(range_shift);v=t.velocity+float(velocity_shift)
  if not 3<=d<=109:raise ValueError('Target delay outside valid CFAR range 3..109')
  if not -7.5<=v<7.5:raise ValueError('Radial velocity exceeds the current unambiguous interval [-7.5,7.5) m/s')
  targets.append(Flight(t.name,d,v,t.amplitude*amplitude_scale,t.bearing,t.tangential))
 x=M.generate_cpi([M.Target(t.delay,t.velocity,t.amplitude) for t in targets])
 if name=='Aircraft in clutter':
  # Same stationary complex profile on all pulses, as in S03 clutter contract.
  profile=np.zeros(128,dtype=complex)
  profile[20:36]=.12*M.chirp()
  profile[64:80]+=.22*M.chirp()
  x+=profile[None,:]
 rng=np.random.Generator(np.random.PCG64(seed))
 if noise_rms:
  x+=noise_rms/np.sqrt(2)*(rng.normal(size=x.shape)+1j*rng.normal(size=x.shape))
 raw,clips=M.quantize_iq(x)
 if clips:raise ValueError(f'Input clipping ({clips} components); reduce amplitude/noise')
 return raw,targets,dict(scenario=name,seed=seed,noise_rms=noise_rms,
  input_saturations=clips,radar=dict(fs=M.FS,fc=M.FC,pri=M.PRI,pulses=33,samples=128,fft=32),
  note='Single CPI: narrowband stop-and-hop; range is quantized to sample delay. Tangential trajectories are commanded illustration only.')
def exact_reference(raw):
 sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
 import s04_c04_selected_C_stage_capture_v1 as C
 import s04_c05_native_integer_v1 as D
 a=np.frombuffer(raw,dtype='<i2').reshape(33,128,2)
 iq=[[tuple(map(int,v)) for v in row] for row in a]
 src=a[:,:,0]/32768+1j*a[:,:,1]/32768
 out=C.run_one(src,iq,C.Telemetry(),'C_hypothetical',(0,1,0,1,1),1,capture_stages=True)
 result=D.complete_map(out['captured']['rd'])
 return result,out['overflow']
def score(records,targets):
 # Association is scoring only; it never changes or hides hardware records.
 used=set();matches=[]
 for t in targets:
  b=int(np.rint(t.velocity/VELOCITY_STEP))%32
  choices=[(abs(v['range_bin']-t.delay),abs((v['doppler_bin']-b+16)%32-16),i,v)
   for i,v in enumerate(records) if i not in used]
  eligible=[v for v in choices if v[0]<=2 and v[1]<=1]
  if eligible:
   dr,db,i,v=min(eligible,key=lambda v:(v[0]+v[1],-v[3].get('power_stored_integer',v[3].get('peak_power_linear',0))))
   used.add(i);matches.append(dict(target=t.name,matched=True,record=i,range_error_m=(v['range_bin']-t.delay)*RANGE_STEP,
    velocity_error_m_s=(v['signed_doppler_bin']*VELOCITY_STEP-t.velocity)))
  else:matches.append(dict(target=t.name,matched=False))
 return dict(matches=matches,unassociated_record_count=len(records)-len(used),
  criterion='Development association: ±2 range bins and ±1 Doppler bin; not final engineering acceptance',
  all_targets_matched=all(v['matched'] for v in matches))

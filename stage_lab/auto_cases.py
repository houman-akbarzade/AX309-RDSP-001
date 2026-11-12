"""Explicit bounded radar scenarios. Reuses the frozen S03 waveform and radar constants."""
from dataclasses import asdict
import numpy as np
from desktop_app.scenarios import LIBRARY,Flight,RANGE_STEP,VELOCITY_STEP
from s03_reference import model as M
SCENARIOS={k:[asdict(t) for t in ts] for k,ts in LIBRARY.items()}
SCENARIOS.update({
 'MTI stationary':[dict(name='Stationary',delay=40,velocity=0.,amplitude=.12)],
 'MTI near-stationary':[dict(name='Slow',delay=65,velocity=.05,amplitude=.12)],
 'MTI moving':[dict(name='Moving',delay=95,velocity=2.8125,amplitude=.12)],
 'MTI mixed':[dict(name='Stationary',delay=25,velocity=0.,amplitude=.12),dict(name='Slow',delay=65,velocity=.05,amplitude=.12),dict(name='Moving',delay=98,velocity=2.8125,amplitude=.12)],
 'Off-bin Doppler':[dict(name='Off-bin',delay=55,velocity=2.578125,amplitude=.15)],
 'Noise only':[]})
def spec(name,noise=.002,seed=20261112,**kwargs):
 return dict(name=name,targets=[dict(t) for t in SCENARIOS[name]],noise=float(noise),seed=int(seed),clutter=name=='Aircraft in clutter',**kwargs)
def build_source(case):
 targets=[Flight(**t) for t in case['targets']]
 if any(not 0<=t.delay<=112 or not -7.5<=t.velocity<7.5 or not 0<=t.amplitude<1 for t in targets):raise ValueError('Invalid target: delay 0..112, velocity [-7.5,7.5), amplitude [0,1)')
 if not np.isfinite(case['noise']) or case['noise']<0:raise ValueError('Noise RMS must be finite and nonnegative')
 x=M.generate_cpi([M.Target(t.delay,t.velocity,t.amplitude) for t in targets])
 if case.get('clutter'):
  profile=np.zeros(128,complex);profile[20:36]=.12*M.chirp();profile[64:80]+=.22*M.chirp();x+=profile[None,:]
 rng=np.random.default_rng(case['seed'])
 x+=case['noise']/np.sqrt(2)*(rng.normal(size=x.shape)+1j*rng.normal(size=x.shape))
 raw,clips=M.quantize_iq(x)
 if clips:raise ValueError(f'Input clips at {clips} I/Q components; reduce amplitude/noise')
 return x,targets,dict(scenario=case['name'],noise_rms=case['noise'],seed=case['seed'],input_clips=clips,targets=[asdict(t) for t in targets],radar=dict(fs=M.FS,fc=M.FC,pri=M.PRI,pulses=33,samples=128))
def quick_cases(seed=20261112):
 cases={}
 for name in ['Two aircraft','MTI mixed','Aircraft in clutter','Weak target near strong']:
  cases[name]=spec(name,noise=0 if name=='MTI mixed' else .002,seed=seed)
 for name in ['MTI stationary','MTI near-stationary','MTI moving']:cases[name]=spec(name,noise=0,seed=seed)
 for delta in [2,4,8]:
  name=f'Range separation {delta} cells';cases[name]=dict(name=name,targets=[dict(name='R1',delay=45,velocity=2.8125,amplitude=.12),dict(name='R2',delay=45+delta,velocity=2.8125,amplitude=.12)],noise=0.,seed=seed,range_separation_cells=delta)
 for delta in [1,2,4]:
  name=f'Velocity separation {delta} bins';cases[name]=dict(name=name,targets=[dict(name='V1',delay=55,velocity=2.8125,amplitude=.12),dict(name='V2',delay=55,velocity=2.8125+delta*VELOCITY_STEP,amplitude=.12)],noise=0.,seed=seed,velocity_separation_bins=delta)
 cases['Off-bin Doppler']=spec('Off-bin Doppler',noise=.002,seed=seed)
 cases['Low SNR']=spec('Low SNR',noise=.06,seed=seed)
 return cases

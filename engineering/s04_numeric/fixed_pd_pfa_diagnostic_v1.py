"""Isolated diagnostic full-chain selected-C statistical harness.
No official S04/C06 acceptance authorization, no historical result mutation.
Full N mode is deliberately blocked pending separate protocol signoff.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path
import numpy as np
from scipy.stats import beta
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from s03_reference import model as s03
from s03_reference import pd_acceptance_candidate as pd
import s04_c04_selected_C_stage_capture_v1 as engine
import s04_c05_native_integer_v1 as native

SHIFTS=(0,1,0,1,1)
PROFILES={
 'pfa':dict(g=5,master=841120261,limit=0.0015,N=20000),
 'pd':dict(g=1,master=841120262,limit=0.90,N=1000)
}
CONTRACT=ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json'
FILES=[CONTRACT,Path(engine.__file__),Path(native.__file__),Path(s03.__file__),Path(pd.__file__),Path(__file__)]
def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source_for(profile,i):
 seed=np.random.SeedSequence([PROFILES[profile]['master'],i,941])
 if profile=='pfa':return s03.noise_only_cpi(sigma2=1.,seed=seed)
 return s03.generate_cpi(targets=[s03.Target(40,1.875,0.18+0j,0.)],snr_db=20.,seed=seed,clutter=None)
def prepare(source,g):
 norm=np.stack((source.real/g,source.imag/g),axis=-1)
 raw=np.rint(norm*32768).astype(np.int64)
 clips=int(np.count_nonzero((raw< -32768)|(raw>32767)))
 bounded=np.clip(raw,-32768,32767).astype(np.int64)
 iq=[[tuple(map(int,bounded[p,r])) for r in range(128)] for p in range(33)]
 return iq,clips
def one(profile,i):
 cfg=PROFILES[profile]
 src=source_for(profile,i)
 iq,clips=prepare(src,cfg['g'])
 tel=engine.Telemetry()
 out=engine.run_one(src,iq,tel,'C_hypothetical',SHIFTS,cfg['g'],capture_stages=True)
 mapped=native.complete_map(out['captured']['rd'])
 assert len(mapped['cut_records'])==2782
 assert len(mapped['clusters'])==len(set(c['record_id'] for c in mapped['clusters']))
 assert sum(v['alarm'] for v in mapped['cut_records'])==out['cfar_alarm_count']
 events=out['overflow']['total']
 rec=dict(i=i,profile=profile,clips=clips,internal_events=events,
          overflow_counts=out['overflow']['counts'],alarms=out['cfar_alarm_count'],
          cluster_count=len(mapped['clusters']),valid_cut_count=2782,
          input_sha256=hashlib.sha256(np.asarray(src,dtype=np.complex128).tobytes()).hexdigest())
 if profile=='pd':
  det=[]
  for x in mapped['clusters']:
   det.append(dict(record_id=x['record_id'],range_bin=x['range_bin'],
                   doppler_bin=x['doppler_bin'],
                   velocity_m_s_nominal=float(s03.bin_velocity(x['doppler_bin']))))
  pairs=s03.truth_match(det,[pd.fixed_target_truth()])
  rec['D']=len(pairs)==1
  match=next((x for x in det if pairs and x['record_id']==pairs[0][1]),None)
  rec['R']=bool(match and abs(match['range_bin']-40)<=1)
  rec['V']=False
  if match:
   powerrow=mapped['power'][match['range_bin']]
   eligibility=pd.doppler_peak_eligibility(powerrow,match['doppler_bin'])
   assert eligibility['status']=='VALID'
   rec['V']=bool(eligibility['eligible'] and abs(match['velocity_m_s_nominal']-1.875)<=.234375)
  rec['J']=rec['D'] and rec['R'] and rec['V']
 return rec
def empirical_bernstein(counts):
 n=len(counts)
 if n<2:return None
 vals=np.asarray(counts,dtype=np.float64)/2782.
 mean=float(vals.mean());var=float(vals.var(ddof=1))
 import math
 bound=min(1.,mean+math.sqrt(2*var*math.log(40)/n)+7*math.log(40)/(3*(n-1)))
 return dict(estimate=mean,variance_CPI=var,upper95=bound,limit=.0015,
             descriptive_pass=bound<=.0015)
def summary(profile,records,complete):
 valid=[r for r in records if r['clips']==0 and r['internal_events']==0]
 data=dict(mode='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',profile=profile,
           executed=len(records),planned=PROFILES[profile]['N'],
           valid=len(valid),invalid=len(records)-len(valid),
           total_input_clips=sum(r['clips'] for r in records),
           total_internal_events=sum(r['internal_events'] for r in records),
           source_sha256={str(p.relative_to(ROOT)):sha(p) for p in FILES},
           implementation='software selected-C bittrue candidate; not FFT IP/RTL/board',
           official_disposition='OPEN_NOT_STATISTICALLY_QUALIFIED')
 if profile=='pfa':
  data['alarm_count']=sum(r['alarms'] for r in records)
  data['pfa_diagnostic']=empirical_bernstein([r['alarms'] for r in records])
 else:
  k=sum(r['D'] for r in records)
  data['successes_D']=k
  data['lower95_CP_D']=float(beta.ppf(.05,k,len(records)-k+1)) if k else 0.
  data['successes_RVJ']={x:sum(r[x] for r in records) for x in ('R','V','J')}
 data['claim_eligibility']='NONE_DIAGNOSTIC' if not complete or len(valid)!=len(records) else 'NOT_AUTHORIZED_FORMAL_ACCEPTANCE'
 return data
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--profile',choices=PROFILES,required=True)
 parser.add_argument('--count',type=int,default=1)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args()
 if not 1<=args.count<=3:parser.error('Diagnostic limited to at most 3 CPI per invocation; formal 20000/1000 approval is separate.')
 cfg=json.loads(CONTRACT.read_text())
 assert cfg['architecture']=='C' and cfg['schedule']==list(SHIFTS)
 if args.output.exists():parser.error('Output exists; never overwrite prior evidence')
 args.output.mkdir(parents=True,exist_ok=False)
 t=time.monotonic()
 records=[]
 try:
  with (args.output/'records.jsonl').open('x',encoding='utf8') as f:
   for i in range(args.count):
    record=one(args.profile,i)
    f.write(json.dumps(record,sort_keys=True)+'\n');f.flush()
    records.append(record)
    print('CPI',i,'alarm',record['alarms'],'clip',record['clips'],'internal',record['internal_events'],flush=True)
 finally:
  result=summary(args.profile,records,len(records)==args.count)
  result['elapsed_seconds']=time.monotonic()-t
  (args.output/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()

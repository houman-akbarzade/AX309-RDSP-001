"""Independent full-IQ Xilinx FFT-IP bit-accurate C-model statistical candidate campaign.
Fixed N, independent seed namespace, complete CPI logs. Does not claim hardware qualification.
"""
import argparse, datetime, hashlib, json, os, subprocess, sys, time, traceback
from pathlib import Path
import numpy as np
from scipy.stats import beta
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from s03_reference import model as s03
from s03_reference import pd_acceptance_candidate as pd
from fixed_pd_pfa_diagnostic_v1 import (ROOT,CONTRACT,FILES,sha,empirical_bernstein)
from fft_ip_fullchain_v1 import full_chain,VENDOR,library_sha256,EXPECTED_LIB_SHA
PROFILES={'pd':dict(master=992611141,N=1000,g=1), 'pfa':dict(master=992611142,N=20000,g=5)}
def write(path,obj):
 tmp=path.with_suffix(path.suffix+'.tmp')
 with tmp.open('w',encoding='utf8') as f:
  json.dump(obj,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 tmp.replace(path)
def simulate(profile,i):
 cfg=PROFILES[profile]
 ss=np.random.SeedSequence([cfg['master'],i,811])
 if profile=='pd':
  src=s03.generate_cpi(targets=[s03.Target(40,1.875,0.18+0j,0.)],snr_db=20.,seed=ss,clutter=None)
 else:src=s03.noise_only_cpi(sigma2=1.,seed=ss)
 norm=np.stack((src.real/cfg['g'],src.imag/cfg['g']),axis=-1)
 raw=np.rint(norm*32768).astype(np.int64)
 clip=int(np.count_nonzero((raw< -32768)|(raw>32767)))
 packed=np.clip(raw,-32768,32767)
 z=full_chain(packed)
 counts=z['mf_clip']+z['mti_clip']+z['fft_overflow']+z['power_clip']
 rec=dict(i=i,profile=profile,alarms=z['alarms'],valid_cut_count=2782,
          clips=clip,internal_events=counts,
          mf_clip=z['mf_clip'],mti_clip=z['mti_clip'],fft_overflow=z['fft_overflow'],
          power_clip=z['power_clip'],cluster_count=len(z['native']['clusters']),
          input_sha256=hashlib.sha256(src.tobytes()).hexdigest())
 if profile=='pd':
  det=[dict(record_id=c['record_id'],range_bin=c['range_bin'],doppler_bin=c['doppler_bin'],
            velocity_m_s_nominal=float(s03.bin_velocity(c['doppler_bin'])))
       for c in z['native']['clusters']]
  pairs=s03.truth_match(det,[pd.fixed_target_truth()])
  rec['D']=len(pairs)==1
  matched=next((x for x in det if pairs and x['record_id']==pairs[0][1]),None)
  rec['R']=bool(matched and abs(matched['range_bin']-40)<=1)
  rec['V']=False
  if matched:
   row=z['native']['power'][matched['range_bin']]
   eligibility=pd.doppler_peak_eligibility(row,matched['doppler_bin'])
   if eligibility['status']!='VALID':raise ValueError('bad Doppler eligibility')
   rec['V']=bool(eligibility['eligible'] and abs(matched['velocity_m_s_nominal']-1.875)<=.234375)
  rec['J']=rec['D'] and rec['R'] and rec['V']
  # Additional pre-grouping statistic: CFAR detection within declared ±2 range/±1 Doppler gate.
  rec['pre_grouping_cfar_target_alarm']=any(
   bool(z['native']['mask'][r][b]) for r in range(38,43) for b in range(3,6))
 return rec
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--profile',choices=('pd','pfa'),required=True)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();cfg=PROFILES[args.profile];N=cfg['N']
 if library_sha256()!=EXPECTED_LIB_SHA:raise RuntimeError('Unfrozen vendor library!')
 c=json.loads(CONTRACT.read_text())
 assert c['architecture']=='C' and c['schedule']==[0,1,0,1,1]
 out=args.output.resolve()
 if out.exists():parser.error('Refusing existing output (no top-up/rerun)')
 out.mkdir(parents=True,exist_ok=False)
 sources={str(f.relative_to(ROOT)):sha(f) for f in FILES+[Path(__file__),Path(__file__).with_name('fft_ip_fullchain_v1.py')]}
 sources[str(VENDOR)]=library_sha256()
 write(out/'STARTED.json',dict(profile=args.profile,N=N,master_seed=cfg['master'],seed_namespace=811,
  source_sha256=sources,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  numeric_path='33x128 IQ Q1.15 -> C02 frozen MF/MTI -> Xilinx FFT v7.1 bitacc C-model -> exact U46 Power/CFAR/Grouping',
  input_gain=cfg['g'],alpha='490007/65536',valid_cuts=2782,
  test_status='CANDIDATE_NOT_OFFICIAL',
  criterion='Pd one-sided 95% CP L>=0.90, N1000' if args.profile=='pd' else 'Pfa one-sided 95% CPI EB U<=0.0015, N20000',
  no_replacements=True,no_retuning=True,source_population='S03 fixed on-bin target SNR20' if args.profile=='pd' else 'CN(0,1) noise only'))
 records=0;alarm_counts=[];good=0;pre=0;R=V=J=0;clipped=events=0;error=None;t0=time.monotonic()
 try:
  with (out/'RAW.jsonl').open('x') as f:
   for i in range(N):
    r=simulate(args.profile,i)
    assert r['i']==i and r['valid_cut_count']==2782
    f.write(json.dumps(r,sort_keys=True)+'\n');f.flush()
    alarm_counts.append(r['alarms']);records+=1
    clipped+=r['clips'];events+=r['internal_events']
    if args.profile=='pd':
     good+=int(r['D']);R+=int(r['R']);V+=int(r['V']);J+=int(r['J'])
     pre+=int(r['pre_grouping_cfar_target_alarm'])
    if records%100==0 or records==N:
     write(out/'CHECKPOINT.json',dict(completed=records,planned=N,alarms=sum(alarm_counts),
       clips=clipped,internal_events=events,successes_D=good,pre_grouping_hits=pre,
       elapsed_seconds=time.monotonic()-t0))
     print(f'XILINX FFT-IP {args.profile}: {records}/{N} alarms={sum(alarm_counts)} clipped={clipped} overflow={events}',flush=True)
 except BaseException:
  error=traceback.format_exc()
 result=dict(profile=args.profile,N=N,completed=records,error=error,
             total_alarms=sum(alarm_counts),invalid_input_clips=clipped,internal_overflow_events=events,
             elapsed_seconds=time.monotonic()-t0,source_sha256=sources,
             raw_sha256=sha(out/'RAW.jsonl'),model='Xilinx FFT IP v7.1 bit-accurate C-model with native fixed integer MF/MTI/Power/CFAR/Grouping')
 if args.profile=='pd':
  low=float(beta.ppf(.05,good,N-good+1)) if good else 0.
  result.update(successes_D=good,successes_R=R,successes_V=V,successes_J=J,
                pre_grouping_Cfar_detection_count=pre,lower95_CP_D=low)
  satisfied=low>=.9 and good>=916
 else:
  bound=empirical_bernstein(alarm_counts)
  result['empirical_bernstein']=bound
  satisfied=bool(bound and bound['upper95']<=.0015)
 complete=error is None and records==N and clipped==0 and events==0
 result['software_candidate_statistical_result']=('PASS_CANDIDATE' if satisfied else 'FAIL_CANDIDATE') if complete else 'INCONCLUSIVE'
 result['formal_acceptance']='OPEN_PENDING_INDEPENDENT_APPROVAL_AND_FPGA_CORRESPONDENCE'
 write(out/'RESULT.json',result)
 print(json.dumps(result,indent=2),flush=True)
 if not complete:sys.exit(2)
if __name__=='__main__':
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
 main()

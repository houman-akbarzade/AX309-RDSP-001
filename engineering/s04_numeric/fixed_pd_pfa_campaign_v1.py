"""Fixed-sample selected-C software bittrue Pd/Pfa evaluation.
Standalone candidate evidence, never a C06 release or official FPGA acceptance.
Predeclare population, counts, seed, threshold before invocation. No retuning.
"""
import argparse, datetime, hashlib, json, math, os, subprocess, sys, time, traceback
from pathlib import Path
import numpy as np
from scipy.stats import beta
from fixed_pd_pfa_diagnostic_v1 import (ROOT,CONTRACT,PROFILES,FILES,SHIFTS,
                                       one,sha,empirical_bernstein)
def dump(path,data):
 temp=path.with_suffix(path.suffix+'.tmp')
 with temp.open('w') as f:
  json.dump(data,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
 temp.replace(path)
def main():
 p=argparse.ArgumentParser(description='Fixed full statistical candidate evaluation, software only')
 p.add_argument('--profile',choices=('pd','pfa'),required=True)
 p.add_argument('--output',type=Path,required=True)
 args=p.parse_args()
 cfg=PROFILES[args.profile]; n=cfg['N']
 con=json.loads(CONTRACT.read_text())
 assert con['architecture']=='C' and con['schedule']==list(SHIFTS)
 output=args.output.resolve()
 if output.exists():p.error('Refuse to overwrite an existing output folder')
 output.mkdir(parents=True,exist_ok=False)
 start=dict(mode='FULL_FIXED_SAMPLE_SOFTWARE_CANDIDATE_NOT_OFFICIAL_ACCEPTANCE',
            profile=args.profile,N=n,master_seed=cfg['master'],seed_namespace=941,
            seed_derivation='SeedSequence([master,index,941]); index 0..N-1',
            model='selected-C Python bittrue reference; not FFT-IP/RTL/board',
            binary_input='RNE Q1.15 with g=5 noise, g=1 target',
            cfar='40*Pcut*65536 > 490007*SUM40; 2782 CUT per CPI',
            criterion=('Pd CP one-sided 95pct >= 0.90, N=1000, k>=916' if args.profile=='pd'
                       else 'Pfa CPI-level empirical Bernstein 95pct <= 0.0015, N=20000'),
            censoring='none; any input clip/internal saturation remains in denominator and invalidates formal candidate eligibility',
            source_sha256={str(x.relative_to(ROOT)):sha(x) for x in FILES+[Path(__file__)]},
            repository_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 dump(output/'STARTED.json',start)
 counts=[]; success=0; rtotal=vtotal=jtotal=0; clips=events=0; attempted=0;error=None
 t0=time.monotonic()
 with (output/'RAW.jsonl').open('x') as f:
  try:
   for i in range(n):
    attempted+=1
    r=one(args.profile,i)
    assert r['i']==i and r['valid_cut_count']==2782
    f.write(json.dumps(r,sort_keys=True)+'\n');f.flush()
    counts.append(int(r['alarms']))
    clips+=r['clips'];events+=r['internal_events']
    if args.profile=='pd':
     success+=int(r['D']);rtotal+=int(r['R']);vtotal+=int(r['V']);jtotal+=int(r['J'])
    if (i+1)%100==0 or i+1==n:
     dump(output/'CHECKPOINT.json',dict(completed=i+1,planned=n,clips=clips,internal_events=events,
                                       successes_D=success,alarms=sum(counts),
                                       elapsed_seconds=time.monotonic()-t0))
     print(f'{args.profile}: {i+1}/{n}; clipping={clips}; internal={events}; elapsed={time.monotonic()-t0:.1f}s',flush=True)
  except BaseException as e:
   error=repr(e)+'\n'+traceback.format_exc()
 result=dict(mode=start['mode'],profile=args.profile,N=n,attempted=attempted,
             completed=len(counts),invalid_input_clips=clips,internal_overflow_events=events,
             elapsed_seconds=time.monotonic()-t0,raw_sha256=sha(output/'RAW.jsonl'),
             source_sha256=start['source_sha256'], error=error)
 if args.profile=='pfa':
  result['total_alarms']=sum(counts)
  result['empirical_bernstein']=empirical_bernstein(counts)
  candidate_pass=bool(result['empirical_bernstein'] and result['empirical_bernstein']['upper95']<=.0015)
 else:
  lower=float(beta.ppf(.05,success,n-success+1)) if success else 0.
  result.update(successes_D=success,successes_R=rtotal,successes_V=vtotal,
                successes_J=jtotal,lower95_CP_D=lower,threshold_success_count=916)
  candidate_pass=bool(success>=916 and lower>=.90)
 complete=error is None and len(counts)==n and clips==0 and events==0
 result['software_candidate_statistical_result']=('PASS_CANDIDATE' if candidate_pass else 'FAIL_CANDIDATE') if complete else 'INCONCLUSIVE'
 result['formal_acceptance']='OPEN_PENDING_INDEPENDENT_REVIEW_AND_FINAL_IMPLEMENTATION_EQUIVALENCE'
 dump(output/'RESULT.json',result)
 print(json.dumps(result,indent=2,sort_keys=True),flush=True)
 if error or not complete:sys.exit(2)
if __name__=='__main__':main()

"""Single prespecified larger CPI G=16384, independent exploratory A method study.
The choice G=4*4096 follows sqrt-n approximation error scaling, NOT pilot tuning.
Not a change to S02; formal qualification remains blocked.
"""
from pathlib import Path
import numpy as np
from scipy.stats import t,norm
import json,sys,hashlib
SEED=82711026
G=16384;M=2782;NOUT=800;BATCH=16
RHOS=(0.,.001,.01,.03,.05);PS=(.0005,.001,.0015)
TCRIT=t.ppf(.95,G-1);Z=norm.ppf(.95)
def run(outdir):
 results=[]
 for i,(rho,p) in enumerate((r,prob) for r in RHOS for prob in PS):
  rng=np.random.default_rng(np.random.SeedSequence([SEED,i,4096]))
  validcnt=covered=accepted=0
  for j in range(0,NOUT,BATCH):
   batch=min(BATCH,NOUT-j)
   if rho==0:ct=rng.binomial(M,p,size=(batch,G))
   else:
    a=p*(1/rho-1);b=(1-p)*(1/rho-1)
    ct=rng.binomial(M,rng.beta(a,b,size=(batch,G)))
   x=ct/M;mean=x.mean(axis=1);d=x-mean[:,None]
   m2=np.mean(d**2,axis=1);m3=np.mean(d**3,axis=1)
   s=np.sqrt(m2*G/(G-1));gamma=m3/np.maximum(m2,1e-300)**1.5
   valid=(np.count_nonzero(ct,axis=1)>=100)&(ct.sum(axis=1)>=100)&(s>0)&np.isfinite(gamma)
   U=np.clip(mean+TCRIT*s/np.sqrt(G)+gamma*s*(2*Z**2+1)/(6*G),0,1)
   validcnt+=int(valid.sum());covered+=int((valid&(U>=p)).sum());accepted+=int((valid&(U<=.0015)).sum())
  results.append({'rho':rho,'p_true':p,'valid':validcnt,'N_outer':NOUT,'coverage_observed':covered/validcnt if validcnt else None,
                  'acceptance_fraction_observed':accepted/NOUT,'seeds':[SEED,i,4096]})
  print('G16K',i+1,'rho',rho,'p',p,'cov',results[-1]['coverage_observed'],'accept',results[-1]['acceptance_fraction_observed'],flush=True)
 data={'purpose':'INDEPENDENT_DEVELOPMENT_ONLY_NOT_QUALIFICATION','G_CPI':G,'model_count':15,'outer_per_condition':NOUT,
       'choice_of_G':'factor four from approved G=4096 chosen theoretically before pilot data generation; sample-size amendment would require engineer approval',
       'original_G':4096,'original_15_conditions_unchanged':True,'Pfa_thresholds_unchanged':True,
       'master_seed':SEED,'results':results,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'not_main_Pfa':True,'no_alpha_calibration':True}
 (Path(outdir)/'S03_independent_skew_G16384_800x15_DEVELOPMENT.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':run(sys.argv[1])

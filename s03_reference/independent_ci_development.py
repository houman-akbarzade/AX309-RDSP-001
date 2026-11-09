"""Independent S03 development-only study for theory-fixed skew-corrected method.
NOT formal C04 qualification. No changes to approved S02 methods/thresholds.
Different master seed than prior official test 20261109 and previous pilot 370091001.
"""
import json,sys,hashlib,platform
from pathlib import Path
import numpy as np
from scipy.stats import norm,t
from .skew_formula_audit import Z

MASTER_SEED=629112611
N_OUTER=1200
G=4096
M=2782
BATCH=32
P_VALUES=(.0005,.001,.0015)
RHO_VALUES=(0.,.001,.01,.03,.05)
TCRIT=t.ppf(.95,G-1)
def bounds(arr):
    x=np.asarray(arr,np.float64)/M
    mean=np.mean(x,axis=1)
    d=x-mean[:,None]
    m2=np.mean(d*d,axis=1)
    m3=np.mean(d**3,axis=1)
    sample_s=np.sqrt(m2*G/(G-1))
    gamma=np.divide(m3,np.maximum(m2,1e-300)**1.5)
    u_t=np.clip(mean+TCRIT*sample_s/np.sqrt(G),0,1)
    u_corr=np.clip(u_t+gamma*sample_s*(2*Z*Z+1)/(6*G),0,1)
    valid=(np.count_nonzero(arr,axis=1)>=100)&(arr.sum(axis=1)>=100)&(sample_s>0)&np.isfinite(gamma)
    return valid,u_t,u_corr,gamma
def run_one(rho,p,idx):
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([MASTER_SEED,idx,77])))
    valid_cnt=covered_t=covered_corr=pass_t=pass_corr=0
    gamma_sum=0
    for start in range(0,N_OUTER,BATCH):
        batch=min(BATCH,N_OUTER-start)
        if rho==0:
            counts=rng.binomial(M,p,size=(batch,G))
        else:
            a=p*(1/rho-1);b=(1-p)*(1/rho-1)
            counts=rng.binomial(M,rng.beta(a,b,size=(batch,G)))
        valid,ut,uc,gamma=bounds(counts)
        valid_cnt+=int(valid.sum())
        covered_t+=int((valid&(ut>=p)).sum())
        covered_corr+=int((valid&(uc>=p)).sum())
        pass_t+=int((valid&(ut<=.0015)).sum())
        pass_corr+=int((valid&(uc<=.0015)).sum())
        gamma_sum+=float(np.sum(gamma))
    return {'p_true':p,'rho':rho,'outer_count':N_OUTER,'valid_studies':valid_cnt,
            'coverage_t_conditional':covered_t/valid_cnt if valid_cnt else None,
            'coverage_corrected_conditional':covered_corr/valid_cnt if valid_cnt else None,
            'pass_criterion_t_fraction_of_all_development_studies':pass_t/N_OUTER,
            'pass_criterion_corrected_fraction_of_all_development_studies':pass_corr/N_OUTER,
            'mean_sample_skewness':gamma_sum/N_OUTER,
            'seed_components':[MASTER_SEED,idx,77],
            'not_official_qualification':True}
def main(folder):
    folder=Path(folder);folder.mkdir(exist_ok=True)
    results=[]
    for i,(rho,p) in enumerate((rho,p) for rho in RHO_VALUES for p in P_VALUES):
        r=run_one(rho,p,i)
        results.append(r)
        print(f'DEV {i+1:02d}/15 rho={rho} p={p} original={r["coverage_t_conditional"]:.4f} corrected={r["coverage_corrected_conditional"]:.4f} acceptanceRate={r["pass_criterion_corrected_fraction_of_all_development_studies"]:.3f}',flush=True)
    data={'classification':'S03 independent method development study, NOT full C04 qualification','N_outer_per_condition':N_OUTER,
          'G_independent_CPI':G,'valid_CUT_per_CPI':M,'master_seed':MASTER_SEED,'conditions_count':15,
          'new_seed_domain_separate_from_approved_failed_and_previous_pilots':True,
          'sources':['engineering/S02-engineering-contracts-FINAL-PROPOSED-v1.0.md','s03_reference/skew_formula_audit.py'],
          'results':results,'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'numpy_version':np.__version__,
          'limitations':['Fixed development sample sizes are below original approved 3000 outer formal test; cannot count as qualification','No new main Pfa, no threshold changes, no alpha calibration','Mathematical formula was fixed by Edgeworth derivation before generating this dataset']}
    (folder/'S03_independent_skew_method_development_1200x15.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main(sys.argv[1])

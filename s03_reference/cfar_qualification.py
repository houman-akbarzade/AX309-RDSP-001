"""Pre-registered C-CFAR-02 S03 prospective qualification, not main Pfa test.

Exact active baseline: engineering/S02-engineering-contracts-FINAL-PROPOSED-v1.0.md
Do not change conditions or thresholds after seeing any qualification output.
This script generates CPI COUNT SURROGATES, not real radar maps.
"""
import json,sys,hashlib,platform
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import t as student, norm
from scipy.special import ndtri

NOUT=3000
NCPI=4096
NCUT=2782
P_VALUES=(.0005,.001,.0015)
RHO_VALUES=(0.,.001,.01,.03,.05)
MASTER_SEED=20261109
BATCH=32
Z=float(ndtri(.95))

def wilson_bounds(k,n):
    h=k/n
    denominator=1+Z**2/n
    root=Z*np.sqrt(h*(1-h)/n+Z**2/(4*n*n))
    return (h+Z**2/(2*n)-root)/denominator,(h+Z**2/(2*n)+root)/denominator

def classify_count_array(counts,p):
    """counts shape outer studies x independent CPIs; return valid, covered."""
    counts=np.asarray(counts)
    x=counts/NCUT
    nonzero=np.count_nonzero(counts,axis=1)
    total=np.sum(counts,axis=1)
    mean=np.mean(x,axis=1)
    std=np.std(x,axis=1,ddof=1)
    valid=(nonzero>=100)&(total>=100)&np.isfinite(std)&(std>0)
    upper=np.minimum(1,np.maximum(0,mean+student.ppf(.95,NCPI-1)*std/np.sqrt(NCPI)))
    covered=valid&(upper>=p)
    return valid,covered

def one_condition(rho,p,condition_id):
    # fixed independent condition stream and distinct from the on-board source IQ
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([MASTER_SEED,condition_id,991])))
    nvalid=0;ncovered=0
    for start in range(0,NOUT,BATCH):
        batch=min(BATCH,NOUT-start)
        if rho==0:
            counts=rng.binomial(NCUT,p,size=(batch,NCPI))
        else:
            a=p*(1/rho-1);b=(1-p)*(1/rho-1)
            latent=rng.beta(a,b,size=(batch,NCPI))
            counts=rng.binomial(NCUT,latent)
        valid,covered=classify_count_array(counts,p)
        nvalid+=int(np.count_nonzero(valid))
        ncovered+=int(np.count_nonzero(covered))
    invalid=NOUT-nvalid
    lcond=wilson_bounds(ncovered,nvalid)[0] if nvalid else 0.
    luncond=wilson_bounds(ncovered,NOUT)[0]
    uinvalid=wilson_bounds(invalid,NOUT)[1]
    passed=(lcond>=.93) and (luncond>=.90) and (uinvalid<=.05)
    return dict(model='IID_binomial' if rho==0 else 'beta_binomial',rho=rho,p_true=p,
                outer_studies=NOUT,CPI_each=NCPI,CUT_each=NCUT,
                valid_studies=nvalid,inconclusive_studies=invalid,covered_valid_studies=ncovered,
                conditional_coverage=ncovered/nvalid if nvalid else None,
                unconditional_valid_and_covered=ncovered/NOUT,
                inconclusive_rate=invalid/NOUT,
                wilson_lower_conditional=lcond,wilson_lower_unconditional=luncond,
                wilson_upper_inconclusive=uinvalid,qualified=bool(passed),
                fixed_condition_seed_components=[MASTER_SEED,condition_id,991])

def run(outdir):
    outdir=Path(outdir)
    outdir.mkdir(parents=True,exist_ok=True)
    results=[]
    for i,(rho,p) in enumerate((r,p) for r in RHO_VALUES for p in P_VALUES):
        r=one_condition(rho,p,i)
        results.append(r)
        print('QUAL',i+1,'of 15','rho',rho,'p',p,'valid',r['valid_studies'],
              'covered',r['covered_valid_studies'],'qual',r['qualified'],flush=True)
    passed=all(r['qualified'] for r in results)
    result={'qualification_protocol':'S02 C-CFAR-02 approved baseline v1.0',
            'source_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
            'master_seed':MASTER_SEED,
            'study_type':'S03 count-based IID/Beta-binomial surrogate coverage qualification ONLY',
            'not_main_Pfa_test':True,
            'not_real_Radar_Doppler_spatial_check':True,
            'no_statistical_threshold_changes':True,
            'conditions':results,'all_15_qualified':passed,
            'next_gates':['real radar-chain spatial correlation diagnostic must pass before main Pfa',
                          'independent calibration alpha and final 4096-CPI main test are NOT executed']}
    (outdir/'s03_C04_count_qualification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('ALL_QUALIFIED',passed,flush=True)
    return passed

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: python -m s03_reference.cfar_qualification OUTPUT_DIR')
    run(sys.argv[1])

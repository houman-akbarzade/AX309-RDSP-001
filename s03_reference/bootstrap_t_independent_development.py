"""Independently seeded small bootstrap-t development across ALL 15 original conditions.
Not an official C04 qualification, not main Pfa acceptance.
"""
from pathlib import Path
import numpy as np
import json,hashlib,sys
M=2782;G=4096
SEED=77193011
NOUT=120
B=199
RHO=(0.,.001,.01,.03,.05)
P=(.0005,.001,.0015)

def boot_upper(counts,rng):
    x=np.asarray(counts,dtype=np.float64)/M
    mean=float(x.mean());s=float(x.std(ddof=1));se=s/np.sqrt(G)
    if np.count_nonzero(counts)<100 or counts.sum()<100 or s<=0 or not np.isfinite(s):
        return None
    pivots=[]
    for batchstart in range(0,B,25):
        k=min(25,B-batchstart)
        idx=rng.integers(0,G,size=(k,G),dtype=np.int32)
        samples=x[idx]
        means=samples.mean(axis=1);stds=samples.std(axis=1,ddof=1)/np.sqrt(G)
        if not np.all(stds>0):return None
        pivots.extend(((means-mean)/stds).tolist())
    q=float(np.quantile(pivots,.05,method='linear'))
    return float(np.clip(mean-q*se,0,1))

def run(folder):
    results=[]
    for i,(rho,p) in enumerate((r,p) for r in RHO for p in P):
        rng=np.random.default_rng(np.random.SeedSequence([SEED,i,13]))
        cv=valid=passed=0
        for j in range(NOUT):
            if rho==0:counts=rng.binomial(M,p,size=G)
            else:
                a=p*(1/rho-1);b=(1-p)*(1/rho-1)
                counts=rng.binomial(M,rng.beta(a,b,size=G))
            U=boot_upper(counts,rng)
            if U is None:continue
            valid+=1;cv+=int(U>=p);passed+=int(U<=.0015)
        results.append({'rho':rho,'p_true':p,'outer_studies':NOUT,'bootstrap_replicates_per_study':B,
                        'valid':valid,'covered_valid':cv,'conditional_coverage':cv/valid if valid else None,
                        'fraction_valid_and_U_le_0_0015':passed/NOUT,
                        'qualification_status':'NOT_QUALIFICATION'})
        print(f'BOOTDEV {i+1}/15 rho={rho} p={p} valid={valid} coverage={cv/valid if valid else None:.4f} boundpass={passed/NOUT:.3f}',flush=True)
    obj={'scope':'independent small exploratory bootstrap-t pilot only, not approved contract or formal qualification',
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'master_seed':SEED,
         'outer_per_condition':NOUT,'B':B,'CPI_per_study':G,'results':results,
         'warning':'120 outer studies and 199 bootstrap replicates per condition give highly uncertain rare-tail coverage; cannot decide formal qualification from this result'}
    file=Path(folder)/'S03_bootstrap_t_independent_120x15_DEVELOPMENT.json'
    file.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':run(sys.argv[1])

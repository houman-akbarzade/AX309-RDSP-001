"""Independent CPI empirical-likelihood signed-root development, not C04 qualification.

Owen 1988/1990 empirical likelihood signed log likelihood root asymptotic
normal; independent CPI cluster alarm fractions only, not iid CUT.
No finite sample guarantee, no main Pfa, no alpha calibration.
"""
from pathlib import Path
import numpy as np
from scipy.stats import norm
import sys,json,hashlib,platform
G=4096;M=2782;NOUT=300;BATCH=8
SEED=11920717
PS=(.0005,.001,.0015)
RHOS=(0.,.001,.01,.03,.05)
Z=float(norm.ppf(.95))
def signed_el_root(arr,mu):
    x=np.asarray(arr,np.float64)/M
    d=x-float(mu)
    avg=d.mean(axis=1)
    dmin=d.min(axis=1)
    dmax=d.max(axis=1)
    positive_only=dmin>=0
    negative_only=dmax<=0
    # bracket for Lagrange multiplier, lambda positive if mean>mu
    limit_pos=1/np.maximum(-dmin,1e-300)
    limit_neg=-1/np.maximum(dmax,1e-300)
    lo=np.where(avg>=0,0,limit_neg*(1-1e-12))
    hi=np.where(avg>=0,limit_pos*(1-1e-12),0)
    interior=~(positive_only|negative_only)
    # avoid overflow in off-domain rows by set lambda=0, replaced with infinities later
    lo=np.where(interior,lo,0);hi=np.where(interior,hi,0)
    for _ in range(38):
        mid=(lo+hi)/2
        den=1+mid[:,None]*d
        val=np.sum(d/np.maximum(den,1e-300),axis=1)
        lo=np.where(val>0,mid,lo)
        hi=np.where(val>0,hi,mid)
    lam=(lo+hi)/2
    inside=np.sum(np.log(np.maximum(1+lam[:,None]*d,1e-300)),axis=1)
    root=np.sign(avg)*np.sqrt(np.maximum(0,2*inside))
    root=np.where(positive_only,np.inf,root)
    root=np.where(negative_only,-np.inf,root)
    root=np.where(np.isclose(avg,0,rtol=0,atol=1e-16),0,root)
    return root
def run(dest):
    results=[]
    for idx,(rho,p) in enumerate((rho,p) for rho in RHOS for p in PS):
        rng=np.random.default_rng(np.random.SeedSequence([SEED,idx,191]))
        valid_count=covered=pass_bound=0
        for off in range(0,NOUT,BATCH):
            n=min(BATCH,NOUT-off)
            if rho==0:counts=rng.binomial(M,p,size=(n,G))
            else:
                a=p*(1/rho-1);b=(1-p)*(1/rho-1)
                counts=rng.binomial(M,rng.beta(a,b,size=(n,G)))
            valid=(np.count_nonzero(counts,axis=1)>=100)&(np.sum(counts,axis=1)>=100)&(np.std(counts,axis=1,ddof=1)>0)
            roots_true=signed_el_root(counts,p)
            roots_ceil=signed_el_root(counts,.0015)
            valid_count+=int(valid.sum())
            covered+=int((valid&(roots_true>=-Z)).sum())
            pass_bound+=int((valid&(roots_ceil<=-Z)).sum())
        r={'rho':rho,'p_true':p,'outer_reps':NOUT,'valid':valid_count,
           'conditional_coverage':covered/valid_count if valid_count else None,
           'valid_and_bound_pass_fraction':pass_bound/NOUT}
        results.append(r)
        print(f'ELDEV {idx+1}/15 rho={rho} p={p} cov={r["conditional_coverage"]} boundPass={r["valid_and_bound_pass_fraction"]:.3f}',flush=True)
    result={'scope':'independent development only not approved method or qualification','formula':'signed root r(mu)=sign(xbar-mu)*sqrt(2 sum ln(1+lambda*(xi-mu))); sum (xi-mu)/(1+lambda*(xi-mu))=0; upper 95% CI U is mu solving r(mu)=-z_95',
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'independent_CPI_count':G,'N_dev_outer_each':NOUT,'seed_master':SEED,
            'results':results,'assumptions':'IID CPI clusters with nondegenerate mean and empirical likelihood Wilks approximation; NOT exact finite sample',
            'citations':['https://doi.org/10.1214/aos/1176347494','https://doi.org/10.1093/biomet/75.2.237'],
            'not_selected_for_normative_contract':True,'no_main_Pfa':True}
    (Path(dest)/'S03_empirical_likelihood_independent_DEVELOPMENT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':run(sys.argv[1])

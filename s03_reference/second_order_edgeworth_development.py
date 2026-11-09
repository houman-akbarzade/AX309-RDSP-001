"""Theory-locked second-order Cornish-Fisher/Edgeworth development-only test.

Studentized statistic T=sqrt(n)*(xbar-p)/S. From second-order quantile:
q_a=z_a - gamma(2*z_a²+1)/(6sqrt(n))
 + z_a/n [5 gamma²(4z_a²-1)/72 - kappa(z_a²-3)/12 + (z_a²+3)/4].
For one-sided upper mean bound use q_.05. Base t_.95 already incorporates
the last symmetric (z²+3)/4/n term, so add ONLY skewness/kurtosis terms
on top of t critical (avoid double counting the Student-t symmetric term).

Prespecified analytic formula, not chosen after looking at any new results.
This file is DEVELOPMENT ONLY and cannot replace approved S02 C04.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.stats import norm,t
G=4096;M=2782;NOUT=1200;BATCH=32
SEED=97112609
PS=(.0005,.001,.0015)
RHOS=(0.,.001,.01,.03,.05)
Z=norm.ppf(.95);TCRIT=t.ppf(.95,G-1)
def interval(arr):
    X=np.asarray(arr,np.float64)/M
    means=X.mean(axis=1)
    centered=X-means[:,None]
    m2=np.mean(centered**2,axis=1)
    m3=np.mean(centered**3,axis=1)
    m4=np.mean(centered**4,axis=1)
    valid=(np.count_nonzero(arr,axis=1)>=100)&(np.sum(arr,axis=1)>=100)&(m2>0)&np.isfinite(m4)
    sd=np.sqrt(m2*G/(G-1))
    skew=m3/np.maximum(m2,1e-300)**1.5
    excess=m4/np.maximum(m2,1e-300)**2-3
    first=means+TCRIT*sd/np.sqrt(G)+skew*sd*(2*Z**2+1)/(6*G)
    additional=Z*sd/(G*np.sqrt(G))*(5*skew**2*(4*Z**2-1)/72-excess*(Z**2-3)/12)
    second=first+additional
    valid&=np.isfinite(second)
    return valid,np.clip(first,0,1),np.clip(second,0,1)
def run(outdir):
    results=[]
    for idx,(rho,p) in enumerate((rho,p) for rho in RHOS for p in PS):
        rng=np.random.default_rng(np.random.SeedSequence([SEED,idx,31]))
        v=c1=c2=a1=a2=0
        for start in range(0,NOUT,BATCH):
            batch=min(BATCH,NOUT-start)
            if rho==0:ct=rng.binomial(M,p,size=(batch,G))
            else:
                a=p*(1/rho-1);b=(1-p)*(1/rho-1)
                ct=rng.binomial(M,rng.beta(a,b,size=(batch,G)))
            good,u1,u2=interval(ct)
            v+=int(good.sum());c1+=int((good&(u1>=p)).sum());c2+=int((good&(u2>=p)).sum())
            a1+=int((good&(u1<=.0015)).sum());a2+=int((good&(u2<=.0015)).sum())
        row={'rho':rho,'p_true':p,'n_outer':NOUT,'valid':v,
             'coverage_first_order':c1/v if v else None,'coverage_second_order':c2/v if v else None,
             'acceptance_rate_first_order':a1/NOUT,'acceptance_rate_second_order':a2/NOUT,
             'seed_components':[SEED,idx,31]}
        results.append(row)
        print(f'ORDER2 {idx+1}/15 rho={rho} p={p} first={row["coverage_first_order"]:.4f} second={row["coverage_second_order"]:.4f} accept2={row["acceptance_rate_second_order"]:.3f}',flush=True)
    output={'status':'INDEPENDENT DEVELOPMENT ONLY NOT C04 QUALIFICATION','assumptions':'Second-order studentized Edgeworth plus symmetric Student-t correction already included in t critical',
            'gamma_definition':'m3/m2^(3/2) with m2,m3 1/n; sample sd ddof=1',
            'kappa':'m4/m2^2 -3, with 1/n central moments',
            'formula':'mean+t_crit*s/sqrt(G)+gamma*s*(2z²+1)/(6G)+z*s/(G sqrt(G))*(5gamma²(4z²-1)/72-kappa(z²-3)/12)',
            'seed_master':SEED,'n_outer_each':NOUT,'results':results,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'citations':['https://www.mdpi.com/2073-8994/16/11/1424','https://link.springer.com/book/10.1007/978-1-4612-4384-7'],
            'not_main_Pfa_or_alpha_calibration':True,
            'risk':'Second order Edgeworth is nonuniform for very skewed heavy tails; numerical instability and coverage qualification still required'}
    (Path(outdir)/'S03_second_order_edgeworth_independent_DEVELOPMENT.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':run(sys.argv[1])

"""Prospective only: formula for separately calibrated CPI skew-Studentized CI.
DO NOT RUN CI calibration or official qualification until engineer approves v1.1.
No data from failed 7/15 official Student-t study or any prior development pilots
may be used to compute the prospective critical delta_star.
"""
import numpy as np
from scipy.stats import t,norm,binom
G=4096
M=2782
N_CAL=5000
P_VALUES=(.0005,.001,.0015)
RHO_VALUES=(0.,.001,.01,.03,.05)
N_QUAL_OUTER=3000
FAMILY_ALPHA=.05
P_COVER=.95
Z=float(norm.ppf(.95))
TCRIT=float(t.ppf(.95,G-1))
CAL_MASTER_SEED=311091601
QUAL_MASTER_SEED=311091602
SPATIAL_MASTER_SEED=311091603
ALPHA_MASTER_SEED=311091604
MAIN_MASTER_SEED=311091605

def moments(x):
    x=np.asarray(x,dtype=float)
    if x.shape!=(G,):raise ValueError("expected exactly 4096 independent CPI rates")
    if not np.all(np.isfinite(x)) or np.any(x<0) or np.any(x>1):
        raise ValueError("invalid CPI rates")
    mean=float(np.mean(x))
    d=x-mean
    m2=float(np.mean(d*d))
    if m2<=0:raise ValueError("nonpositive variance")
    m3=float(np.mean(d*d*d))
    sd=float(np.std(x,ddof=1))
    gamma=m3/m2**1.5
    return mean,sd,gamma

def candidate_upper(counts,delta_star):
    """No PASS claims; δ* must be determined on independent *future* calibration."""
    a=np.asarray(counts)
    if a.shape!=(G,) or not np.all(np.isfinite(a)) or np.any(a<0) or np.any(a>M) or np.any(a!=np.floor(a)):
        raise ValueError("invalid counts")
    if not np.isfinite(delta_star) or delta_star<0:raise ValueError("invalid calibrated critical delta")
    n_nonzero=int(np.count_nonzero(a))
    total=int(np.sum(a))
    if n_nonzero<100 or total<100:return None
    try:
        x,sd,gamma=moments(a/M)
    except ValueError:
        return None
    U=x+(TCRIT+delta_star)*sd/np.sqrt(G)+gamma*sd*(2*Z**2+1)/(6*G)
    return float(np.clip(U,0,1)) if np.isfinite(U) else None

def adverse_score(counts,true_p):
    """Calibrate 95th upper quantile of a score using independent simulated CPI blocks."""
    a=np.asarray(counts)
    if a.shape!=(G,) or np.any(a<0) or np.any(a>M):raise ValueError("invalid counts")
    if np.count_nonzero(a)<100 or a.sum()<100:return None
    try:
        mean,sd,gamma=moments(a/M)
    except ValueError:return None
    return float((true_p-mean)/(sd/np.sqrt(G))-gamma*(2*Z**2+1)/(6*np.sqrt(G)))

def familywise_order_stat_rank(num_valid):
    """One-sided nonparametric order-statistic upper quantile confidence >=1-.05/15.

    If q is the population 95%-quantile of adverse score A:
    Pr[A_(r) >= q]=Pr[Binomial(m,.95) <= r-1].
    Choose the smallest r satisfying that inequality.
    """
    if not isinstance(num_valid,(int,np.integer)) or num_valid<1:raise ValueError("positive calibration size")
    r=int(binom.ppf(1-FAMILY_ALPHA/15,num_valid,P_COVER))+1
    if r>num_valid:return None
    assert binom.cdf(r-1,num_valid,P_COVER)>=1-FAMILY_ALPHA/15-1e-12
    return r

def prospective_delta_star(adverse_arrays):
    """Pure algebraic rule; inputs must be FUTURE calibration-only independent data.

    No actual calibration data is generated or processed in S03 current turn.
    All 15 conditions required; any condition with >5% invalid calibration studies
    is blocked instead of filtering away unfavorable cases.
    """
    if len(adverse_arrays)!=15:raise ValueError("all 15 models required")
    q95=[]
    for arr in adverse_arrays:
        a=np.asarray(arr,dtype=float)
        if a.shape!=(N_CAL,):raise ValueError("exact 5000 independent outer calibration studies")
        valid=a[np.isfinite(a)]
        if len(valid)<4750:raise ValueError("too many inconclusive calibration studies")
        r=familywise_order_stat_rank(len(valid))
        if r is None:raise ValueError("insufficient order-statistical rank")
        q95.append(float(np.partition(valid,r-1)[r-1]))
    delta_star=max(0.,max(q95)-TCRIT)
    if not np.isfinite(delta_star):raise ValueError("invalid delta critical")
    return float(delta_star),q95

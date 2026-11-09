"""S03 candidate only: theory-audited one-sided Studentized Edgeworth CPI interval.
NOT approved S02 acceptance method; cannot issue Pfa PASS. If accepted, requires
new version and independent 15-condition qualification with 3000 outer trials.
"""
import numpy as np
from scipy.stats import t,norm
G_PROPOSED=16384
M=2782
PFA_UPPER_LIMIT=.0015
Z=float(norm.ppf(.95))

def upper_and_diagnostics(counts):
    """Return U and diagnostics for G independent CPI counts; invalid => None.

    First-order Studentized Edgeworth (Cornish-Fisher) upper bound, gamma_hat
    computed using 1/G population-style central moments of the observed sample.
    Sample SD used in studentization has ddof=1. Positive sample skew => U rises.
    """
    a=np.asarray(counts)
    if a.ndim!=1 or len(a)!=G_PROPOSED:raise ValueError("candidate G=16384")
    if np.any(a<0) or np.any(a>M) or not np.all(np.isfinite(a)) or np.any(a!=np.floor(a)):
        raise ValueError("invalid CPI alarm counts")
    X=a.astype(np.float64)/M
    pos=int(np.count_nonzero(a));alarms=int(np.sum(a))
    if pos<100 or alarms<100:
        return None,{'reason':'insufficient counts','positive_CPI':pos,'total_alarms':alarms}
    mean=float(np.mean(X))
    d=X-mean
    m2=float(np.mean(d*d));m3=float(np.mean(d*d*d))
    if m2<=0 or not np.isfinite(m2) or not np.isfinite(m3):
        return None,{'reason':'zero or invalid variance/moments'}
    gamma=m3/m2**1.5
    sd=float(np.std(X,ddof=1))
    base=mean+float(t.ppf(.95,G_PROPOSED-1))*sd/np.sqrt(G_PROPOSED)
    correction=gamma*sd*(2*Z*Z+1)/(6*G_PROPOSED)
    upper=float(np.clip(base+correction,0,1))
    if not np.isfinite(upper):
        return None,{'reason':'invalid upper'}
    return upper,{'valid':True,'mean':mean,'sd_ddof1':sd,'sample_skew_m3_over_m2pow1_5':gamma,
                  'base_t_upper':base,'positive_skew_correction':correction,
                  'positive_CPI':pos,'total_alarms':alarms,'NOT_APPROVED_FOR_PFA':True}

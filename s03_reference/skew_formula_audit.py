"""Independent algebraic audit of first-order studentized Edgeworth correction.

No statistical coverage qualification. Citation equation: for T=sqrt(n)*(Xbar-mu)/S,
F_T(x)=Phi(x)+(gamma/(6sqrt(n)))*(2x*x+1)*phi(x)+O(n^-1).
Inverted 0.05 quantile: q_.05=z_.05-gamma*(2*z_.05**2+1)/(6sqrt(n)).
Upper mu=Xbar-q_.05*S/sqrt(n) so skew correction POSITIVE if gamma>0.
"""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from scipy.stats import norm,t
Z=norm.ppf(.95)
def moment_skew(x):
    a=np.asarray(x,dtype=float)
    d=a-a.mean()
    m2=float(np.mean(d*d))
    if m2<=0:raise ValueError('zero variance')
    m3=float(np.mean(d**3))
    return m3/m2**1.5

def corrected_upper(x):
    x=np.asarray(x,float);G=len(x);gamma=moment_skew(x)
    s=float(x.std(ddof=1))
    return np.clip(float(x.mean()+t.ppf(.95,G-1)*s/np.sqrt(G)
                   +gamma*s*(2*Z**2+1)/(6*G)),0,1)

def main(outdir):
    # Synthetic algebraic test only, no coverage experiments:
    # n=4096 fixed positive-skew population x ~ exponential, seeded once.
    rng=np.random.default_rng(620261109)
    vals=rng.exponential(scale=.001,size=4096)
    gamma=moment_skew(vals);c=(2*Z*Z+1)/6
    q_lower=norm.ppf(.05)-gamma*(2*Z**2+1)/(6*np.sqrt(len(vals)))
    naive=float(vals.mean()+t.ppf(.95,4095)*vals.std(ddof=1)/np.sqrt(4096))
    corrected=float(corrected_upper(vals))
    direct=naive+gamma*vals.std(ddof=1)*(2*Z**2+1)/(6*4096)
    assert gamma>0 and q_lower<norm.ppf(.05) and corrected>naive
    assert np.isclose(corrected,direct,rtol=2e-15)
    # Invariance to affine rescale for positive scaling
    assert np.isclose(corrected_upper(vals*2),corrected_upper(vals)*2,rtol=1e-12)
    out={'scope':'algebraic formula audit only, not coverage testing',
         'sample_seed':620261109,'n':4096,'gamma_hat_definition':'m3/m2^(3/2), m2/m3 use 1/n denominators; S uses ddof=1',
         'studentized_CDF_first_order_term':'+gamma*(2*x^2+1)*phi(x)/(6*sqrt(n))',
         'lower_studentized_quantile_correction':'-gamma*(2*z_0.95^2+1)/(6*sqrt(n))',
         'upper_mean_bound_correction':'+gamma_hat*S*(2*z_0.95^2+1)/(6*n)',
         'numeric_multiplier_C':c,'pilot_sample_skewness':gamma,
         'uncorrected_upper_one_sample':naive,'corrected_upper_one_sample':corrected,
         'conclusion':'The sign and 1/(6n) coefficient of the prior proposed formula are consistent with FIRST-ORDER Studentized Edgeworth/Cornish-Fisher; not Johnson symmetric interval nor exact finite-n correction',
         'citation_urls':['https://pmc.ncbi.nlm.nih.gov/articles/PMC6360137/','https://www.mdpi.com/2073-8994/16/11/1424','https://itl.nist.gov/div898/handbook/eda/section3/eda35b.htm'],
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    file=Path(outdir)/'S03_skew_studentized_formula_audit.json'
    file.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('CORRECTION_SIGN',gamma>0,'C',c,'GAMMA',gamma,'DELTA',corrected-naive)
if __name__=='__main__':main(sys.argv[1])

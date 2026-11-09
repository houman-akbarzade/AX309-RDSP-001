"""Exploratory candidate-CI pilot, NOT a preregistered qualification and NOT Pfa validation.
Development-only seeds entirely separate from approved C04 qualification and spatial diagnostics.
No thresholds in immutable S02 baseline are modified.
"""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from scipy.stats import t,norm
from . import cfar_qualification as contract
G=4096;M=2782;N=250;P_VALUES=(.0005,.001,.0015)
RHOS=(0.,.001,.01,.03,.05)
SEED=370091001
Z=norm.ppf(.95)
B=256

def bounds_skew_corrected(counts):
    x=np.asarray(counts,dtype=np.float64)/M
    mu=x.mean(axis=-1)
    center=x-mu[...,None]
    s=np.std(x,ddof=1,axis=-1)
    gamma=np.mean(center**3,axis=-1)/np.maximum(np.mean(center**2,axis=-1),1e-300)**1.5
    tcrit=t.ppf(.95,G-1)
    upper_t=mu+tcrit*s/np.sqrt(G)
    # Studentized one-sided first-order Edgeworth correction; asymptotic only
    upper_skew=upper_t+gamma*s*(2*Z*Z+1)/(6*G)
    return np.clip(upper_t,0,1),np.clip(upper_skew,0,1)

def empirical_bernstein_bound(x):
    """Theorem 4 empirical Bernstein, conservative two-sided δ=.05 for [0,1]."""
    n=len(x); mean=np.mean(x);v=np.var(x,ddof=1)
    return min(1,mean+np.sqrt(2*v*np.log(2/.05)/n)+7*np.log(2/.05)/(3*(n-1)))

def one_case(rho,p,idx):
    rng=np.random.default_rng(np.random.SeedSequence([SEED,idx]))
    covered_t=covered_sk=0
    pass_t=pass_sk=0
    means=[]
    eb_width=[]
    for j in range(N):
        if rho==0:cs=rng.binomial(M,p,size=G)
        else:
            a=p*(1/rho-1);b=(1-p)*(1/rho-1)
            cs=rng.binomial(M,rng.beta(a,b,size=G))
        tval,sval=bounds_skew_corrected(cs)
        covered_t+=bool(tval>=p);covered_sk+=bool(sval>=p)
        pass_t+=bool(tval<=.0015);pass_sk+=bool(sval<=.0015)
        means.append(float(np.mean(cs)/M))
        eb_width.append(float(empirical_bernstein_bound(cs/M)-np.mean(cs)/M))
    return {'p':p,'rho':rho,'N_pilot':N,
            't_coverage':covered_t/N,'skew_corrected_coverage':covered_sk/N,
            't_probability_pass_bound':pass_t/N,'skew_probability_pass_bound':pass_sk/N,
            'avg_empirical_Bernstein_halfwidth':float(np.mean(eb_width)),
            'average_observed_rate':float(np.mean(means))}
def bootstrap_t_pilot():
    # separate small pilot only; 4 scenarios * 80 studies * 256 resamples
    out=[]
    for i,rho in enumerate((0.,.01,.03,.05)):
        rng=np.random.default_rng(np.random.SeedSequence([SEED,500+i]))
        ncover=ntpass=0; nb=80
        for j in range(nb):
            p=.001
            if rho==0:counts=rng.binomial(M,p,size=G)
            else:
                a=p*(1/rho-1);b=(1-p)*(1/rho-1)
                counts=rng.binomial(M,rng.beta(a,b,size=G))
            x=counts/M;mu=float(x.mean());s=float(x.std(ddof=1));se=s/np.sqrt(G)
            indices=rng.integers(0,G,size=(B,G),dtype=np.int32)
            reps=x[indices]
            rm=reps.mean(axis=1)
            rs=reps.std(axis=1,ddof=1)/np.sqrt(G)
            Tstar=(rm-mu)/np.maximum(rs,1e-300)
            q=float(np.quantile(Tstar,.05))
            U=max(0.,min(1.,mu-q*se))
            ncover+=int(U>=p);ntpass+=int(U<=.0015)
        out.append({'rho':rho,'p_true':.001,'N_outer':nb,'B_bootstrap':B,
                    'covered_count':ncover,'estimated_coverage':ncover/nb,
                    'fraction_bound_le_0_0015':ntpass/nb,
                    'note':'very small exploratory pilot; no inferential qualification'})
    return out
def run(outdir):
    outdir=Path(outdir);outdir.mkdir(exist_ok=True,parents=True)
    estimates=[]
    for j,(rho,p) in enumerate((r,p) for r in RHOS for p in P_VALUES):
        estimates.append(one_case(rho,p,j))
    bs=bootstrap_t_pilot()
    res={'purpose':'development-only qualitative comparison; not formal qualification or main Pfa test',
         'master_seed':SEED,'model_p_values':P_VALUES,'rho_values':RHOS,
         'n_outer_per_condition':N,'bootstrap_t_exploratory_B':B,
         'pilot_t_and_skew_correction':estimates,'pilot_bootstrap_t':bs,
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'caveats':['250 per condition and 80 bootstrap-t outer reps too small to certify coverage','Candidate comparison data cannot be reused as independent final qualification','Empirical Bernstein inequality is distribution free for IID bounded CPI rates but very conservative at G=4096','Future new approved S02 protocol must preregister all 15 conditions and definitive settings before confirmatory study']}
    (outdir/'S03_alternative_CI_development_pilot.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
    print('CASE best/worst coverage, prospective only')
    for row in estimates:
        if row['p']==.001:print('rho',row['rho'],'t_cov',row['t_coverage'],'skew_cov',row['skew_corrected_coverage'],'t_pass',row['t_probability_pass_bound'],'skew_pass',row['skew_probability_pass_bound'],'EB_width',row['avg_empirical_Bernstein_halfwidth'],flush=True)
    for row in bs:print('boot_t',row['rho'],row['estimated_coverage'],row['fraction_bound_le_0_0015'],flush=True)
if __name__=='__main__':run(sys.argv[1])

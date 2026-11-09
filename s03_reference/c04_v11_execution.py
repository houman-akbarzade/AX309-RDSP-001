"""APPROVED C-CFAR-02 v1.1 independent CI calibration then qualification.

Read SHA-pinned engineer-approved amendment; do not change algorithms, constants,
seeds, numerical limits, or model list after outputs. This performs SYNTHETIC
COUNT statistical calibration/qualification, NOT actual radar-chain spatial
diagnostics, CFAR alpha calibration, or final Pfa acceptance.

Usage:
  python3 -m s03_reference.c04_v11_execution preflight OUTPUT_DIR
  python3 -m s03_reference.c04_v11_execution calibrate OUTPUT_DIR
  python3 -m s03_reference.c04_v11_execution qualify OUTPUT_DIR

Qualification deliberately requires a frozen, hashed calibration artifact
and distinct source-seed domain. Status FAIL stops downstream Pfa.
"""
import os,sys,json,hashlib,platform,time,math
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import binom,norm,t
from . import calibrated_critical_candidate as c

G=c.G;M=c.M;N_CAL=c.N_CAL;N_QUAL=c.N_QUAL_OUTER
P=c.P_VALUES;RHO=c.RHO_VALUES;Z=c.Z;TCRIT=c.TCRIT
CONDITIONS=[(rho,p) for rho in RHO for p in P]
assert len(CONDITIONS)==15 and G==4096 and M==2782 and N_CAL==5000 and N_QUAL==3000
BATCH=32
VALID_LIMIT=4750
BASE=Path(__file__).resolve().parents[1]
APPROVAL='decisions/S02-C-CFAR-02-v1.1-approved-amendment.json'
CAL_OUT='S03_C04_v11_independent_15x5000_CI_calibration.json'
QUAL_OUT='S03_C04_v11_independent_15x3000_qualification.json'
Z2COEFF=(2*Z**2+1)/6

def sha(data):return hashlib.sha256(data).hexdigest()
def file_sha(path):return sha(Path(path).read_bytes())
def locked_approval():
    approved=json.loads((BASE/APPROVAL).read_text())
    for f,h in approved['new_files_sha256'].items():
        assert file_sha(BASE/f)==h, f'approved v1.1 artifact unexpectedly modified: {f}'
    for f,h in approved['base_s02_v10_hashes_unchanged'].items():
        assert file_sha(BASE/f)==h, f'approved v1.0 unexpectedly modified: {f}'
    old='engineering/s03_C04_count_qualification.json'
    oldsha=approved['original_failed_student_t_qualification']['sha256']
    assert file_sha(BASE/old)==oldsha
    return approved

def independent_rng(master,idx):
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence([master,idx,191])))
def draw_counts(rng,rho,p,batch):
    if rho==0:
        return rng.binomial(M,p,size=(batch,G))
    a=p*(1/rho-1);b=(1-p)*(1/rho-1)
    latent=rng.beta(a,b,size=(batch,G))
    return rng.binomial(M,latent)

def compute_batch(counts):
    X=np.asarray(counts,dtype=np.float64)/M
    mu=np.mean(X,axis=1)
    d=X-mu[:,None]
    m2=np.mean(d*d,axis=1)
    m3=np.mean(d*d*d,axis=1)
    s=np.sqrt(m2*G/(G-1))
    gamma=m3/np.maximum(m2,1e-300)**1.5
    valid=(np.count_nonzero(counts,axis=1)>=100)&(np.sum(counts,axis=1)>=100)&np.isfinite(m2)&(m2>0)&np.isfinite(m3)&np.isfinite(s)&np.isfinite(gamma)
    skewshift=gamma*Z2COEFF/np.sqrt(G)
    return valid,mu,s,skewshift

def wilson(k,n):
    """Exact score-bound algebra; one-sided 95% normal quantile."""
    if n<=0:return (0.,1.)
    h=k/n; q=Z**2
    root=Z*math.sqrt(h*(1-h)/n+q/(4*n*n))
    denom=1+q/n
    return ((h+q/(2*n)-root)/denom,(h+q/(2*n)+root)/denom)

def preflight(outdir):
    approved=locked_approval()
    from scipy.special import ndtri
    assert Z==float(ndtri(.95))
    assert abs(Z2COEFF-1.0685144846984709)<1e-12
    assert c.familywise_order_stat_rank(5000)==4792
    assert binom.cdf(4791,5000,.95)>=1-.05/15
    assert binom.cdf(4790,5000,.95)<1-.05/15
    assert len({c.CAL_MASTER_SEED,c.QUAL_MASTER_SEED,c.SPATIAL_MASTER_SEED,c.ALPHA_MASTER_SEED,c.MAIN_MASTER_SEED})==5
    assert len({c.CAL_MASTER_SEED,c.QUAL_MASTER_SEED})==2
    for n,cut in ((3000,.93),(3000,.90)):
        lo,up=wilson(2850,n)
        assert lo>cut
    assert wilson(130,3000)[1]<=.05 and wilson(131,3000)[1]>.05
    # algebraically compare scalar preexisting prospective implementation to vector model on fixed deterministic data
    for seed in (901,902):
        rng=independent_rng(seed,3)
        count=draw_counts(rng,.03,.001,1)[0]
        valid,mu,s,sk=compute_batch(count[None,:])
        assert valid[0]
        scalar=c.adverse_score(count,.001)
        vector=(.001-mu[0])/(s[0]/np.sqrt(G))-sk[0]
        assert np.isclose(scalar,vector,rtol=1e-11,atol=1e-11)
        for delta in (0.,1.):
            U=c.candidate_upper(count,delta)
            UV=float(np.clip(mu[0]+(TCRIT+delta)*s[0]/np.sqrt(G)+sk[0]*s[0]/np.sqrt(G),0,1))
            assert np.isclose(U,UV,rtol=1e-11,atol=1e-11)
    zeros=np.zeros((2,G),dtype=np.int32)
    assert not np.any(compute_batch(zeros)[0])
    assert c.candidate_upper(zeros[0],0) is None
    assert all(x not in (20261109,370091001,629112611,97112609,82711026) for x in (c.CAL_MASTER_SEED,c.QUAL_MASTER_SEED))
    report={'status':'PASS_INDEPENDENT_PREFLIGHT','timestamp_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'v11_approved_sha256':approved['new_files_sha256'],'original_fail_sha256':approved['original_failed_student_t_qualification']['sha256'],
            'checked':['Edgeworth sign and coefficient','independent adverse-score implementation equivalence','scalar/vector corrected U equivalence','familywise binomial rank 4792','distinct master seeds','valid/inconclusive zero-variance and 100 alarm guards','Wilson exact thresholds','immutable v1.0 and v1.1 SHA','conditions are fixed at 15','separate data pools'],
            'n_models':15,'outer_calibration':5000,'outer_qualification':3000,'G':G,'M':M,
            'calibration_master':c.CAL_MASTER_SEED,'qualification_master':c.QUAL_MASTER_SEED,
            'script_sha256':file_sha(__file__),'helper_sha256':file_sha(c.__file__),
            'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'python':platform.python_version()}}
    dest=Path(outdir)/'S03_C04_v11_preflight.json'
    dest.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('PREFLIGHT PASS',report['script_sha256'],flush=True)

def run_calibration(outdir):
    approved=locked_approval()
    pre=Path(outdir)/'S03_C04_v11_preflight.json'
    assert pre.exists() and json.loads(pre.read_text())['status']=='PASS_INDEPENDENT_PREFLIGHT'
    assert json.loads(pre.read_text())['script_sha256']==file_sha(__file__)
    out=Path(outdir)/CAL_OUT
    assert not out.exists(),'calibration already exists: do not overwrite locked results'
    started=time.perf_counter()
    full=[]
    for idx,(rho,p) in enumerate(CONDITIONS):
        rng=independent_rng(c.CAL_MASTER_SEED,idx)
        scores=np.empty(N_CAL)
        scores.fill(np.nan)
        for offset in range(0,N_CAL,BATCH):
            batch=min(BATCH,N_CAL-offset)
            counts=draw_counts(rng,rho,p,batch)
            valid,mu,s,sk=compute_batch(counts)
            adverse=np.divide(p-mu,s/np.sqrt(G),out=np.full_like(mu,np.nan),where=s>0)-sk
            adverse[~valid]=np.nan
            scores[offset:offset+batch]=adverse
        nvalid=int(np.isfinite(scores).sum())
        row={'condition_id':idx,'rho':rho,'p_true':p,'seed_components':[c.CAL_MASTER_SEED,idx,191],
             'outer_count':N_CAL,'valid':nvalid,'inconclusive':N_CAL-nvalid}
        if nvalid>=VALID_LIMIT:
            v=scores[np.isfinite(scores)]
            rank=c.familywise_order_stat_rank(nvalid)
            if rank is not None:
                row['rank_1based']=rank
                row['critical_score_order_stat']=float(np.partition(v,rank-1)[rank-1])
            else:row['failure']='no order stat rank'
        else:row['failure']='calibration validity below preregistered minimum'
        full.append(row)
        print('CAL',idx+1,'/15 valid',nvalid,'critical',row.get('critical_score_order_stat'),'elapsed_s',round(time.perf_counter()-started,2),flush=True)
    ok=all('critical_score_order_stat' in r for r in full)
    max_score=max((x['critical_score_order_stat'] for x in full),default=None) if ok else None
    delta=max(0.,max_score-TCRIT) if ok else None
    if delta is not None and not math.isfinite(delta):
        delta=None;ok=False
    output={'stage':'S03','protocol':'ENGINEER_APPROVED_S02_C_CFA R_02_v1.1'.replace(' ',''),'status':'PASS' if ok else 'FAIL',
            'source_script_sha256':file_sha(__file__),'helper_sha256':file_sha(c.__file__),
            'preflight_sha256':file_sha(pre),
            'master_seed':c.CAL_MASTER_SEED,'CPI_per_study':G,'CUT_per_CPI':M,
            'outer_calibration_per_condition':N_CAL,'all_15':full,'familywise_nominal_coverage':.95,
            'target_conditional_cover':.95,'family_alpha':.05,
            'delta_star':float(delta) if delta is not None else None,
            'raw_max_adverse_score':float(max_score) if max_score is not None else None,
            'tcrit':TCRIT,'no_main_Pfa_test':True,'not_real_chain_spatial_test':True,
            'elapsed_seconds_monotonic':time.perf_counter()-started,'numpy_version':np.__version__,'scipy_version':scipy.__version__}
    out.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print('CALIBRATION_RESULT',output['status'],'DELTA_STAR',output['delta_star'],'ELAPSED',output['elapsed_seconds_monotonic'],flush=True)

def run_qualification(outdir):
    approved=locked_approval()
    pre=Path(outdir)/'S03_C04_v11_preflight.json'
    cal=Path(outdir)/CAL_OUT
    dest=Path(outdir)/QUAL_OUT
    assert not dest.exists(),'qualification exists: do not rerun or overwrite'
    assert pre.exists() and cal.exists()
    predata=json.loads(pre.read_text())
    assert predata['status']=='PASS_INDEPENDENT_PREFLIGHT' and predata['script_sha256']==file_sha(__file__)
    cd=json.loads(cal.read_text())
    if cd['status']!='PASS' or cd['delta_star'] is None:
        print('BLOCKED: calibration failed: no qualification allowed',flush=True)
        return
    assert cd['source_script_sha256']==file_sha(__file__) and cd['helper_sha256']==file_sha(c.__file__)
    delta=float(cd['delta_star'])
    started=time.perf_counter()
    results=[]
    for idx,(rho,p) in enumerate(CONDITIONS):
        rng=independent_rng(c.QUAL_MASTER_SEED,idx)
        nvalid=covered=accepted=0
        for offset in range(0,N_QUAL,BATCH):
            batch=min(BATCH,N_QUAL-offset)
            counts=draw_counts(rng,rho,p,batch)
            valid,mu,s,sk=compute_batch(counts)
            U=np.clip(mu+(TCRIT+delta+sk)*s/np.sqrt(G),0,1)
            nvalid+=int(valid.sum())
            covered+=int((valid&(U>=p)).sum())
            accepted+=int((valid&(U<=.0015)).sum())
        ni=N_QUAL-nvalid
        cond_l=wilson(covered,nvalid)[0] if nvalid else 0.
        uncond_l=wilson(covered,N_QUAL)[0]
        invalid_u=wilson(ni,N_QUAL)[1]
        success=cond_l>=.93 and uncond_l>=.90 and invalid_u<=.05
        results.append({'idx':idx,'rho':rho,'p_true':p,'seed_components':[c.QUAL_MASTER_SEED,idx,191],
                        'outer_studies':N_QUAL,'valid':nvalid,'inconclusive':ni,'valid_covered':covered,
                        'conditional_coverage':covered/nvalid if nvalid else None,
                        'unconditional_valid_and_covered':covered/N_QUAL,
                        'inconclusive_rate':ni/N_QUAL,
                        'Wilson_lower_conditional':cond_l,'Wilson_lower_unconditional':uncond_l,
                        'Wilson_upper_inconclusive':invalid_u,
                        'fraction_valid_and_U_le_0_0015':accepted/N_QUAL,
                        'qualification_condition_passed':bool(success)})
        print('QUAL',idx+1,'/15 rho',rho,'p',p,'valid',nvalid,'covered',covered,'L_cond',round(cond_l,6),'pass',bool(success),'elapsed_s',round(time.perf_counter()-started,2),flush=True)
    passed=all(r['qualification_condition_passed'] for r in results)
    out={'scope':'FORMAL_V11_SYNTHETIC_COUNT_MODEL_CI_QUALIFICATION_ONLY',
         'status':'PASS' if passed else 'FAIL',
         'passed_conditions':sum(int(r['qualification_condition_passed']) for r in results),
         'failed_conditions':sum(not r['qualification_condition_passed'] for r in results),
         'total_conditions':15,'G_CPI':G,'M_valid_CUT':M,
         'source_script_sha256':file_sha(__file__),'helper_sha256':file_sha(c.__file__),
         'approved_contract_sha256':approved['new_files_sha256'],
         'calibration_sha256':file_sha(cal),'calibrated_delta_star':delta,
         'master_seed':c.QUAL_MASTER_SEED,'criteria':{'Wilson_conditional_lower_min':.93,'Wilson_unconditional_valid_covered_lower_min':.90,'Wilson_inconclusive_upper_max':.05,'all_conditions_required':True},
         'conditions':results,'no_alpha_calibration':True,'no_main_Pfa_test':True,
         'radar_chain_spatial_validity_not_inferred':True,
         'elapsed_seconds_monotonic':time.perf_counter()-started,
         'numpy_version':np.__version__,'scipy_version':scipy.__version__}
    dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('QUALIFICATION_RESULT',out['status'],'PASSED',out['passed_conditions'],'/15','ELAPSED',out['elapsed_seconds_monotonic'],flush=True)

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: python -m s03_reference.c04_v11_execution {preflight|calibrate|qualify} OUTPUT_DIR')
    mode=sys.argv[1]
    if mode=='preflight':preflight(sys.argv[2])
    elif mode=='calibrate':run_calibration(sys.argv[2])
    elif mode=='qualify':run_qualification(sys.argv[2])
    else:raise SystemExit('unknown mode')

"""Frozen S03 CA-CFAR alpha calibration and independent post-alpha diagnostics.

No statistical CI recalibration, no C04 final Pfa test. Policy was committed
BEFORE producing data. This file must be committed and hashed before execution.
"""
import sys,json,hashlib,math,time,platform
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import chi2,binom,betabinom,norm
from . import model as m

ROOT=Path(__file__).resolve().parents[1]
POLICY='engineering/S03-C04-alpha-and-real-chain-predeclared-protocol-v0.1.json'
CAL_RESULT='engineering/S03-C04-independent-alpha-calibration-v0.1.json'
POST_RESULT='engineering/S03-C04-post-alpha-spatial-diagnostic-v0.1.json'
CLUSTER_RESULT='engineering/S03-C04-post-alpha-cluster-numeric-diagnostic-v0.1.json'
PFA_TARGET=.001
N=4096
M_CUT=2782
BATCH_VALID=(slice(3,110),slice(3,29))
SEED_CAL=311091604
SEED_SPATIAL=311091603
Z99=float(norm.ppf(.995))
RANGE_PAIRS=106*26
DOPPLER_PAIRS=107*25

def sha(f):
    return hashlib.sha256(Path(f).read_bytes()).hexdigest()

def fixed_policy():
    data=json.loads((ROOT/POLICY).read_text())
    assert data['alpha_calibration']['CPI']==N and data['post_alpha_real_chain_diagnostic']['CPI']==N
    assert data['independent_seed_streams']['CFAR_ALPHA']==SEED_CAL
    assert data['independent_seed_streams']['RADAR_SPATIAL_POST_ALPHA']==SEED_SPATIAL
    assert data['CI_delta_star_fixed']==.28734133322686817
    app=json.loads((ROOT/'decisions/S02-C-CFAR-02-v1.1-approved-amendment.json').read_text())
    for f,h in app['new_files_sha256'].items():assert sha(ROOT/f)==h
    old=json.loads((ROOT/'decisions/GATE-S02-approved-baseline.json').read_text())
    for f,h in old['approved_artifacts_sha256'].items():assert sha(ROOT/f)==h
    assert sha(ROOT/'engineering/s03_C04_count_qualification.json')==app['original_failed_student_t_qualification']['sha256']
    qual=json.loads((ROOT/'engineering/S03_C04_v11_independent_15x3000_qualification.json').read_text())
    assert qual['status']=='PASS' and qual['passed_conditions']==15
    return data

def generate(seed,i):
    r=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,i,191])))
    w=(r.standard_normal((33,128))+1j*r.standard_normal((33,128)))/np.sqrt(2)
    return w

def range_doppler_power(x):
    return m.rd_power(m.doppler(m.mti(m.pulse_compress(x))))

def training_mean(power):
    # Independent implementation same 40 offsets; no alpha or future data.
    z=np.zeros((107,26),dtype=np.float64)
    for dr,db in m.TRAIN_OFFSETS:
        z+=power[3+dr:110+dr,3+db:29+db]
    return z/40.0

def wilson99(k,n):
    if n<=0: return (0.0,1.0)
    p=k/n;v=Z99*Z99
    t=Z99*np.sqrt(p*(1-p)/n+v/(4*n*n))
    d=1+v/n
    return (float((p+v/(2*n)-t)/d),float((p+v/(2*n)+t)/d))

def calibrate():
    policy=fixed_policy()
    out=ROOT/CAL_RESULT
    if out.exists():raise RuntimeError('Calibration already exists; no overwrite allowed')
    start=time.perf_counter()
    vals=np.empty(N*M_CUT,dtype=np.float64)
    bad=0
    for i in range(N):
        power=range_doppler_power(generate(SEED_CAL,i))
        z=training_mean(power)
        cut=power[3:110,3:29]
        if np.any(z<=0) or not np.all(np.isfinite(z)) or np.any(cut<0) or not np.all(np.isfinite(cut)):
            bad+=1
            continue
        vals[i*M_CUT:(i+1)*M_CUT]=(cut/z).reshape(-1)
        if (i+1)%1024==0:print('ALPHA_CAL_INPUT',i+1,'/',N,flush=True)
    total=N*M_CUT
    alpha=None;alarm_frac=None
    if bad==0 and np.isfinite(vals).all():
        K=round(PFA_TARGET*total)
        order_index=total-K-1
        alpha=float(np.partition(vals,order_index)[order_index])
        alarm_count=int(np.count_nonzero(vals>alpha))
        alarm_frac=alarm_count/total
        status='PASS' if (np.isfinite(alpha) and 0<=alpha<=100 and abs(alarm_frac-PFA_TARGET)<=.00001) else 'FAIL'
    else:
        alarm_count=None;K=round(PFA_TARGET*total);order_index=total-K-1;status='FAIL'
    outobj={'stage':'S03','type':'PROSPECTIVE_ALPHA_CALIBRATION_NO_PFA_ACCEPTANCE',
            'status':status,'alpha':alpha,'target_Pfa_for_quantile_selection_NOT_ACHIEVED_Pfa':PFA_TARGET,
            'CPI':N,'CUT_per_CPI':M_CUT,'total_ratio_samples':total,
            'target_alarm_count_round':K,'quantile_sorted_index_zero_based':order_index,
            'observed_calibration_alarm_count':alarm_count,
            'observed_calibration_fraction':alarm_frac,'bad_CPI':bad,
            'seed_master':SEED_CAL,'seed_formula':'PCG64 SeedSequence([311091604,i,191])',
            'source_script_SHA256':sha(__file__),'policy_SHA256':sha(ROOT/POLICY),
            'model_SHA256':sha(m.__file__),'elapsed_monotonic_seconds':time.perf_counter()-start,
            'python_version':platform.python_version(),'numpy_version':np.__version__,'scipy_version':scipy.__version__,
            'invalid_or_fail_action':'NO post-alpha diagnostic or main Pfa; record FAIL, do not retune',
            'not_CI_calibration':True,'no_main_Pfa':True}
    out.write_text(json.dumps(outobj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print('ALPHA_CALIBRATION',status,'ALPHA',alpha,'N',total,'FRACTION',alarm_frac,'DURATION',outobj['elapsed_monotonic_seconds'],flush=True)
    return outobj

def diagnostics():
    policy=fixed_policy()
    cal=ROOT/CAL_RESULT
    output=ROOT/POST_RESULT
    if output.exists():raise RuntimeError('Post alpha diagnostic already exists; no overwrite allowed')
    if not cal.exists():raise RuntimeError('Missing alpha calibration')
    c=json.loads(cal.read_text())
    if c['status']!='PASS':raise RuntimeError('Alpha calibration FAIL blocks post-alpha')
    if c['source_script_SHA256']!=sha(__file__) or c['policy_SHA256']!=sha(ROOT/POLICY):
        raise RuntimeError('Frozen source mismatch')
    alpha=float(c['alpha'])
    start=time.perf_counter()
    counts=np.zeros(N,dtype=np.int32)
    pairsR=np.zeros(N,dtype=np.int32);pairsD=np.zeros(N,dtype=np.int32)
    invalid=0
    for i in range(N):
        power=range_doppler_power(generate(SEED_SPATIAL,i))
        z=training_mean(power)
        cut=power[3:110,3:29]
        if np.any(z<=0) or not np.all(np.isfinite(z)) or not np.all(np.isfinite(cut)):
            invalid+=1;continue
        a=cut>alpha*z
        counts[i]=int(a.sum())
        pairsR[i]=int(np.sum(a[:-1,:]&a[1:,:]))
        pairsD[i]=int(np.sum(a[:,:-1]&a[:,1:]))
        if (i+1)%1024==0:print('POST_ALPHA_SPATIAL',i+1,'/',N,flush=True)
    valid=invalid==0
    mean=float(counts.mean());variance=float(counts.var(ddof=1))
    dispersion=variance/(M_CUT*(mean/M_CUT)*(1-mean/M_CUT)) if 0<mean<M_CUT else float('nan')
    # Ljung-Box exact standard asymptotic Q(20), count autocorrelations from all N CPI.
    center=counts-mean
    autocov=float(np.dot(center,center))
    autocorr=[float(np.dot(center[:-k],center[k:])/autocov) if autocov>0 else float('nan') for k in range(1,21)]
    Q=N*(N+2)*sum((r*r)/(N-k) for k,r in enumerate(autocorr,1))
    p_ind=float(chi2.sf(Q,20))
    # CPI paired rate difference; pair-level observations are dependent, use independent CPI as cluster.
    diff=pairsR/RANGE_PAIRS-pairsD/DOPPLER_PAIRS
    diffmean=float(diff.mean());diffsd=float(diff.std(ddof=1))
    z_anis=diffmean/(diffsd/np.sqrt(N)) if diffsd>0 else float('inf')
    p_anis=2*float(norm.sf(abs(z_anis)))
    # check zero and F>=8 frequencies vs predeclared count model envelope p=.001
    p=PFA_TARGET
    zero=[];tail=[]
    for rho in (0.,.001,.01,.03,.05):
        if rho==0:
            zero.append(float(binom.pmf(0,M_CUT,p)))
            tail.append(float(binom.sf(7,M_CUT,p)))
        else:
            a=p*(1/rho-1);b=(1-p)*(1/rho-1)
            zero.append(float(betabinom.pmf(0,M_CUT,a,b)))
            tail.append(float(betabinom.sf(7,M_CUT,a,b)))
    nzero=int(np.count_nonzero(counts==0));ntail=int(np.count_nonzero(counts>=8))
    zero_ci=wilson99(nzero,N);tail_ci=wilson99(ntail,N)
    zero_overlap=zero_ci[1]>=min(zero) and zero_ci[0]<=max(zero)
    tail_overlap=tail_ci[1]>=min(tail) and tail_ci[0]<=max(tail)
    decisions={'independent_CPI_Ljung_Box_p_at_least_0_01':bool(valid and np.isfinite(p_ind) and p_ind>=.01),
               'exchangeable_pair_anisotropy_abs_z_at_most_2_5758293':bool(valid and np.isfinite(z_anis) and abs(z_anis)<=Z99),
               'zero_99CI_overlaps_5_count_models':bool(valid and zero_overlap),
               'tail_ge8_99CI_overlaps_5_count_models':bool(valid and tail_overlap),
               'all_CPI_valid':bool(valid)}
    passed=all(decisions.values())
    obj={'stage':'S03','type':'SEPARATE_RADAR_CHAIN_DIAGNOSTIC_NOT_MAIN_Pfa',
         'status':'PASS_NECESSARY_DIAGNOSTICS_ONLY' if passed else 'FAIL_SPATIAL_TRANSFER_GATE',
         'alpha_frozen':alpha,'alpha_calibration_SHA256':sha(cal),
         'CPI':N,'CUT_per_CPI':M_CUT,'seed_master':SEED_SPATIAL,
         'source_SHA256':sha(__file__),'policy_SHA256':sha(ROOT/POLICY),'model_SHA256':sha(m.__file__),
         'invalid_CPI':invalid,'counts':counts.tolist(),'mean':mean,'sample_variance':variance,
         'dispersion_ratio_vs_equal_p_iid':dispersion,'acf_lags_1_to_20':autocorr,
         'Ljung_Box_Q20':Q,'Ljung_Box_pvalue':p_ind,
         'adjacent_range_pair_total':int(pairsR.sum()),'adjacent_doppler_pair_total':int(pairsD.sum()),
         'range_pair_probability_estimate':float(pairsR.sum()/(N*RANGE_PAIRS)),
         'doppler_pair_probability_estimate':float(pairsD.sum()/(N*DOPPLER_PAIRS)),
         'paired_spatial_anisotropy_mean':diffmean,'paired_spatial_anisotropy_z':float(z_anis),
         'paired_spatial_anisotropy_two_sided_pvalue':p_anis,
         'zero_count':nzero,'tail_ge8_count':ntail,
         'zero_fraction':nzero/N,'tail_ge8_fraction':ntail/N,
         'zero_fraction_Wilson_99pct':zero_ci,'tail_ge8_Wilson_99pct':tail_ci,
         'zero_model_envelope':(min(zero),max(zero)),
         'tail_model_envelope':(min(tail),max(tail)),
         'count_quantiles':{str(v):float(np.quantile(counts,v)) for v in (.5,.9,.95,.99,1.)},
         'predeclared_diagnostic_gate_checks':decisions,
         'predeclared_significance':.01,'delta_star_unchanged':.28734133322686817,
         'elapsed_monotonic_seconds':time.perf_counter()-start,
         'alpha_and_delta_are_not_retuned':True,
         'remaining_requires_engineer_review_even_if_pass':True,
         'main_Pfa_executed':False}
    output.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    print('POST_ALPHA_DIAGNOSTIC',obj['status'],'PASS_GATES',sum(decisions.values()),'of',len(decisions),'ANIS_Z',z_anis,'LJUNG_P',p_ind,'RUNTIME',obj['elapsed_monotonic_seconds'],flush=True)
    return obj

def clusters():
    policy=fixed_policy()
    cal=ROOT/CAL_RESULT
    if not cal.exists() or json.loads(cal.read_text())['status']!='PASS':
        raise RuntimeError('No alpha')
    alpha=json.loads(cal.read_text())['alpha']
    dest=ROOT/CLUSTER_RESULT
    if dest.exists():raise RuntimeError('No overwrite')
    targets=[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)]
    out=[]
    for name,ts in [('one_20',[targets[0]]),('one_40',[targets[1]]),('one_60',[targets[2]]),('three_targets',targets)]:
        p=range_doppler_power(m.generate_cpi(ts))
        alarms,valid,z=m.cfar_2d(p,alpha=alpha)
        clusters=m.clusters_8(alarms,p)
        rows=[]
        for r in clusters:
            k,b=r['range_bin'],r['doppler_bin']
            T=np.array([p[k+dr,b+db] for dr,db in m.TRAIN_OFFSETS])
            assert np.isclose(z[k,b],T.mean(),rtol=1e-12,atol=1e-8)
            rows.append({'k':k,'bin':b,'power_CUT':float(p[k,b]),'mean_40_training':float(T.mean()),
                         'threshold_alpha_mean':float(alpha*T.mean()),'margin_power_minus_threshold':float(p[k,b]-alpha*T.mean()),
                         'training_min':float(T.min()),'training_max':float(T.max()),
                         'cluster_size':r['cluster_cells']})
        out.append({'name':name,'input_targets':len(ts),'clusters':len(clusters),'alarms':int(alarms.sum()),'peak_rows':rows})
        print('POST_ALPHA_CLUSTER',name,'clusters',len(clusters),flush=True)
    dest.write_text(json.dumps({'category':'diagnostic_nonoise_not_Pfa_or_Pd','alpha_frozen':alpha,'scenes':out,'source_SHA256':sha(__file__),
                                'no_processing_change':True},indent=2,sort_keys=True)+'\n')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('calibrate | diagnose | clusters')
    x=sys.argv[1]
    if x=='calibrate':calibrate()
    elif x=='diagnose':diagnostics()
    elif x=='clusters':clusters()
    else:raise SystemExit('unknown action')

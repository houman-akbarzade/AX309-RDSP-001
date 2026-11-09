"""Preapproved engineering preflight ONLY; NO final Pfa/Pd samples or verdict.

Preflight source and protocol must be committed before any new CPI generation.
Independent secondary CA-CFAR alarm arithmetic and scalar online Welford EB.
"""
import json,hashlib,math,time,platform,datetime,sys
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import chi2
from . import model as m

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'engineering/S03-C04-independent-CPI-preflight-protocol-PREFROZEN-v0.1.json'
OUTPUT=ROOT/'engineering/S03-C04-independent-CPI-preflight-results-v0.1.json'
N=4096
M=2782
ALPHA=7.476912055027923
MASTERS=(411091701,411091702)
N_FINAL_RESERVED=20000
LOG40=math.log(40)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def frozen_state():
    x=json.loads(POLICY.read_text())
    assert x['status']=='PRE-FROZEN_BEFORE_NEW_REFERENCE_OR_IMPLEMENTATION_CPI'
    assert x['seed_masters']['reference']==MASTERS[0]
    assert x['seed_masters']['implementation']==MASTERS[1]
    assert x['seed_masters']['final_reserved']==411091703
    assert x['n_reference']==x['n_implementation']==N
    assert x['n_final_reserved_not_generated']==N_FINAL_RESERVED
    assert x['M']==M and x['alpha_frozen']==ALPHA
    approved=json.loads((ROOT/'decisions/S02-C-CFAR-02-v1.1-approved-amendment.json').read_text())
    for name,h in approved['new_files_sha256'].items():assert sha(ROOT/name)==h
    older=json.loads((ROOT/'decisions/GATE-S02-approved-baseline.json').read_text())
    for name,h in older['approved_artifacts_sha256'].items():assert sha(ROOT/name)==h
    assert sha(ROOT/'engineering/s03_C04_count_qualification.json')==approved['original_failed_student_t_qualification']['sha256']
    assert json.loads((ROOT/'engineering/S03-C04-post-alpha-spatial-diagnostic-v0.1.json').read_text())['status']=='FAIL_SPATIAL_TRANSFER_GATE'
    draft=json.loads((ROOT/'engineering/S02-C-CFAR-02-requirements-matrix-FINAL-REVIEW-PROPOSED-v1.2.json').read_text())
    assert draft['status']=='PROPOSED_NOT_NORMATIVE'
    return x

def source_input(master,i):
    # Each CPI generator allocates a fresh generator: no global RNG and no state shared between CPI.
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([master,i,191])))
    x=(rng.standard_normal((33,128))+1j*rng.standard_normal((33,128)))/math.sqrt(2)
    assert x.shape==(33,128) and x.dtype==np.complex128 and np.isfinite(x).all()
    return x

def independent_training_and_count(power):
    # This is an INDEPENDENT CFAR implementation: two-dimensional summed-area table
    # for 7x7 outer minus central 3x3 guard+CUT, no use of m.TRAIN_OFFSETS or m.cfar_2d.
    assert power.shape==(128,32)
    integral=np.pad(power,((1,0),(1,0))).cumsum(axis=0).cumsum(axis=1)
    def windows(radius):
        # centers (k,b) with k=3..109, b=3..28 and inclusive +-radius.
        return (integral[4+radius:111+radius,4+radius:30+radius]
                -integral[3-radius:110-radius,4+radius:30+radius]
                -integral[4+radius:111+radius,3-radius:29-radius]
                +integral[3-radius:110-radius,3-radius:29-radius])
    outer=windows(3)
    guard=windows(1)
    assert outer.shape==(107,26) and guard.shape==(107,26)
    mean=(outer-guard)/40.
    assert np.isfinite(mean).all() and np.all(mean>0)
    cut=power[3:110,3:29]
    a=(cut>ALPHA*mean)
    return int(a.sum()),mean,a

def reference_count(iq):
    power=m.rd_power(m.doppler(m.mti(m.pulse_compress(iq))))
    alarms,valid,training=m.cfar_2d(power,alpha=ALPHA)
    assert int(valid.sum())==M and np.array_equal(valid[3:110,3:29],np.ones((107,26),bool))
    a=int(alarms.sum())
    return a,power,training,alarms[3:110,3:29]

def eb_numpy(counts):
    x=np.asarray(counts,dtype=np.float64)/M
    n=len(x)
    mean=float(np.mean(x))
    var=float(np.var(x,ddof=1))
    return float(min(1.,mean+math.sqrt(2*var*LOG40/n)+7*LOG40/(3*(n-1)))),mean,var

def eb_welford(counts):
    mean=0.
    m2=0.
    n=0
    for f in counts:
        n+=1
        x=float(f)/M
        d=x-mean
        mean+=d/n
        m2+=d*(x-mean)
    var=m2/(n-1)
    return float(min(1.,mean+math.sqrt(2*var*math.log(2/.05)/n)+7*math.log(2/.05)/(3*(n-1)))),mean,var

def spectral_diagnostics(counts):
    vals=counts.astype(float)
    mu=vals.mean()
    d=vals-mu
    den=float(np.dot(d,d))
    a=[float(np.dot(d[:-k],d[k:])/den) if den>0 else float('nan') for k in range(1,21)]
    q=N*(N+2)*sum(a[k-1]**2/(N-k) for k in range(1,21))
    return {'lag1':a[0],'acf_1_20':a,'Ljung_Box_Q20':q,'Ljung_Box_asymptotic_p':float(chi2.sf(q,20)),
            'zero_fraction':float(np.mean(counts==0)),'tail_F_ge8':float(np.mean(counts>=8)),
            'diagnostics_not_proof_of_independence':True}

def run():
    policy=frozen_state()
    if OUTPUT.exists():raise RuntimeError('Preflight output exists: no overwrite allowed')
    start=time.perf_counter()
    assert len(m.TRAIN_OFFSETS)==40 and m.VALID_R==slice(3,110) and m.VALID_D==slice(3,29)
    assert np.array_equal(m.TRAIN_OFFSETS,[(dr,db) for dr in range(-3,4) for db in range(-3,4) if abs(dr)>1 or abs(db)>1])
    assert m.PULSES==33 and m.N==128 and m.FFT_N==32 and m.L==16
    assert ALPHA==float(policy['alpha_frozen'])
    checks={
      'contract_and_historical_hashes_locked':True,
      'source_function_no_global_rng_or_cross_CPI_state':True,
      'independent_explicit_integral_image_CFAR_math':True,
      'fixed_alpha_7x7_3x3_40training_and_2782_mask':True,
      'two_distinct_seed_namespaces_and_final_reserved':True
    }
    pools={}
    identity_hashes=set()
    replay_cases={}
    mismatch_examples=[]
    for kind,master in [('reference',MASTERS[0]),('implementation',MASTERS[1])]:
        counts=np.empty(N,dtype=np.int32)
        firstlast={}
        max_train_error=0.
        sample_mask_mismatch=0
        signature_repeats=0
        for i in range(N):
            iq=source_input(master,i)
            if i in (0,1,2047,4095):
                input_sha=hashlib.sha256(iq.tobytes()).hexdigest()
                if input_sha in identity_hashes:signature_repeats+=1
                identity_hashes.add(input_sha)
                firstlast[str(i)]={'iq_sha256':input_sha}
            count,power,z,alarms=reference_count(iq)
            alt,mean,alt_mask=independent_training_and_count(power)
            if count!=alt or not np.array_equal(alarms,alt_mask):
                mismatch_examples.append({'pool':kind,'CPI_index':i,'reference':count,'alternative':alt})
                sample_mask_mismatch+=1
            if i in (0,1,2047,4095):
                err=float(np.max(np.abs(z[3:110,3:29]-mean)))
                max_train_error=max(max_train_error,err)
            counts[i]=count
            if (i+1)%1024==0:print('PREFLIGHT',kind,i+1,'/',N,flush=True)
        # Re-generation test: fresh RNG object, same CPI bitwise identical.
        for i in (0,1,2047,4095):
            assert hashlib.sha256(source_input(master,i).tobytes()).hexdigest()==firstlast[str(i)]['iq_sha256']
        ub,mu,v=eb_numpy(counts)
        ub2,mu2,v2=eb_welford(counts)
        checks[kind+'_all_CPI_valid_and_independent_counts_match']=bool(not sample_mask_mismatch and counts.min()>=0 and counts.max()<=M)
        checks[kind+'_two_EB_estimators_agree']=bool(math.isclose(ub,ub2,rel_tol=1e-12,abs_tol=1e-14) and math.isclose(mu,mu2,rel_tol=1e-12,abs_tol=1e-14) and math.isclose(v,v2,rel_tol=1e-10,abs_tol=1e-14))
        checks[kind+'_source_replay_bitwise']=bool(signature_repeats==0)
        checks[kind+'_40_training_estimate_matches']=bool(max_train_error<=1e-7)
        pools[kind]={
          'master_seed':master,'CPI_count':N,'M':M,
          'frozen_source_rng':'PCG64(SeedSequence([master,i,191])) fresh per CPI',
          'count_vector_sha256':hashlib.sha256(counts.tobytes()).hexdigest(),
          'count_vector':counts.tolist(),
          'range':(int(counts.min()),int(counts.max())),
          'reference_vs_independent_CUT_mask_mismatch_CPI':sample_mask_mismatch,
          'sampled_absolute_training_estimate_max_error':max_train_error,
          'fresh_rng_seed_regeneration_firstlast_SHA256':firstlast,
          'NumPy_bound_DIAGNOSTIC_NOT_FINAL_Pfa':ub,'Welford_bound_DIAGNOSTIC_NOT_FINAL_Pfa':ub2,
          'mean_DIAGNOSTIC':mu,'sample_variance_DIAGNOSTIC':v,
          'independence_supplementary':spectral_diagnostics(counts)}
        print('POOL',kind,'mismatch',sample_mask_mismatch,'EB_agreement',abs(ub-ub2),'elapsed_s',round(time.perf_counter()-start,3),flush=True)
    checks['no_cross_dataset_signature_overlap']=len(identity_hashes)==8
    checks['distinct_complete_seed_range_no_CPI_state_mutation']=True
    checks['all_counts_4096_each_not_used_as_main_Pfa']=True
    status='PASS_PREFLIGHT_ONLY' if all(checks.values()) else 'FAIL_PREFLIGHT_NO_GO'
    result={
      'stage':'S03','status':status,'checks':checks,
      'source_sha256':sha(__file__),'model_sha256':sha(m.__file__),'protocol_sha256':sha(POLICY),
      'proposed_v12_contract_sha256':sha(ROOT/'engineering/S02-C-CFAR-02-CPI-bounded-CONTRACT-FINAL-REVIEW-v1.2.md'),
      'proposed_v12_matrix_sha256':sha(ROOT/'engineering/S02-C-CFAR-02-requirements-matrix-FINAL-REVIEW-PROPOSED-v1.2.json'),
      'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'full_chain_CPI_source_generation_is_independent_by_constructor':True,
      'caution':'PCG64 separate deterministic streams and no retained state justify procedural independence under PRNG statistical assumptions; p-values do NOT prove it',
      'N_reference':N,'N_implementation':N,'N_main_NOT_GENERATED':N_FINAL_RESERVED,
      'pools':pools,'mismatch_first_10':mismatch_examples[:10],
      'all_IQ_input_data_sha256_of_selected_CPI_unique':len(identity_hashes)==8,
      'alpha':ALPHA,'delta_star_frozen_historical':.28734133322686817,
      'not_main_Pfa_verdict':True,'Pfa_final_not_executed':True,'Pd_final_not_executed':True,
      'elapsed_seconds_monotonic':time.perf_counter()-start,
      'numpy_version':np.__version__,'scipy_version':scipy.__version__,'python_version':platform.python_version(),
      'next_action':'S02 v1.2 formal engineer approval AND separate engineer GO before final Pfa'}
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print('FINAL_PREFLIGHT',status,'SECONDS',result['elapsed_seconds_monotonic'],'CHECKS',len(checks),'FAILS',[k for k,v in checks.items() if not v],flush=True)

if __name__=='__main__':
    if len(sys.argv)!=2 or sys.argv[1]!='run':raise SystemExit('Only preflight run is supported. No final Pfa action exists.')
    run()

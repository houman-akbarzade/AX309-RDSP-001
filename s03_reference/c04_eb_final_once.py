"""Single-run final Pfa acceptance, approved S02 v1.2.
Exactly N=20000 fixed full noise-only CPIs, master 411091703.
Runs ONCE using O_EXCL locked results claim before generation.
No optional stopping, no threshold/alpha retuning, no Pd test.
"""
from pathlib import Path
import json,hashlib,math,os,platform,time,datetime,sys
import numpy as np
import scipy
from . import model as m
from .c04_eb_independent_preflight import independent_training_and_count

ROOT=Path(__file__).resolve().parents[1]
N=20000
M=2782
MASTER=411091703
ALPHA=7.476912055027923
LIMIT=.0015
CI_ERROR=.05
DECISION='decisions/S02-C-CFAR-02-v1.2-approved-amendment.json'
PREFLIGHT='engineering/S03-C04-independent-CPI-preflight-results-v0.1.json'
RESULT='engineering/S03-C04-FINAL-Pfa-20000CPI-EmpiricalBernstein-v1.2.json'
CLAIM='engineering/S03-C04-FINAL-Pfa-20000CPI-EXECUTION-CLAIM-v1.2.json'

def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def source_guard():
    d=json.loads((ROOT/DECISION).read_text())
    assert d['decision_id']=='S02-C-CFAR-02-AMENDMENT-v1.2-APPROVAL-001'
    assert d['one_final_trial_authorized_after_this_commit_and_SHA_guard']
    assert d['final_fixed_CPI_N']==N and d['final_seed_master']==MASTER
    assert d['alpha_frozen']==ALPHA
    for f,h in d['new_approved_artifact_sha256'].items():
        assert sha(ROOT/f)==h, f'approved v1.2 SHA mismatch {f}'
    for f,h in d['approved_v10_unchanged_sha'].items():
        assert sha(ROOT/f)==h, f'approved v1.0 SHA mismatch {f}'
    for f,h in d['approved_v11_unchanged_sha'].items():
        assert sha(ROOT/f)==h, f'approved v1.1 SHA mismatch {f}'
    assert sha(ROOT/'engineering/s03_C04_count_qualification.json')==d['historical_student_t_7_of_15_fail_sha']
    assert sha(ROOT/'engineering/S03-C04-post-alpha-spatial-diagnostic-v0.1.json')==d['historical_spatial_fail_sha']
    pf=json.loads((ROOT/PREFLIGHT).read_text())
    assert pf['status']=='PASS_PREFLIGHT_ONLY' and len(pf['checks'])==16 and all(pf['checks'].values())
    assert sha(ROOT/PREFLIGHT)==d['preflight_16_of_16_sha256']
    assert pf['source_sha256']==sha(ROOT/'s03_reference/c04_eb_independent_preflight.py')
    assert pf['model_sha256']==sha(m.__file__)
    assert pf['N_main_NOT_GENERATED']==N
    assert m.PULSES==33 and m.N==128 and m.FFT_N==32 and m.L==16
    assert len(m.TRAIN_OFFSETS)==40 and m.VALID_R==slice(3,110) and m.VALID_D==slice(3,29)
    return d

def generate(i):
    rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([MASTER,i,191])))
    a=(rng.standard_normal((33,128))+1j*rng.standard_normal((33,128)))/math.sqrt(2)
    if not np.isfinite(a).all():raise ValueError('nonfinite input IQ')
    return a

def eb_welford(counts):
    n=0
    mu=0.
    m2=0.
    for val in counts:
        n+=1
        x=float(val)/M
        delta=x-mu
        mu+=delta/n
        m2+=delta*(x-mu)
    if n!=N or m2<0:return None
    var=m2/(N-1)
    U=min(1.,mu+math.sqrt(2*var*math.log(40)/N)+7*math.log(40)/(3*(N-1)))
    return mu,var,U

def main():
    approval=source_guard()
    # O_EXCL: no rerunning even if error in middle; record INCONCLUSIVE in forensic claim.
    claim_path=ROOT/CLAIM
    result_path=ROOT/RESULT
    if result_path.exists():raise RuntimeError('Already completed, never rerun')
    file_descr=os.open(claim_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    claim={'status':'RUN_CLAIMED_NOT_YET_PROVEN','master_seed':MASTER,'N_fixed':N,
           'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'approval_decision_sha256':sha(ROOT/DECISION),
           'script_sha256':sha(__file__),'preflight_sha256':sha(ROOT/PREFLIGHT),
           'model_sha256':sha(m.__file__),'run_once':True}
    with os.fdopen(file_descr,'w',encoding='utf-8') as h:
        json.dump(claim,h,indent=2,sort_keys=True);h.write('\n');h.flush();os.fsync(h.fileno())
    tic=time.perf_counter()
    counts=[]
    bad=[]
    checksums={}
    result_status='INCONCLUSIVE'
    try:
        for i in range(N):
            inp=generate(i)
            if i in (0,1,9999,N-1):checksums[str(i)]=hashlib.sha256(inp.tobytes()).hexdigest()
            power=m.rd_power(m.doppler(m.mti(m.pulse_compress(inp))))
            # Same frozen reference CA-CFAR as approved preflight
            alarm,valid,z=m.cfar_2d(power,alpha=ALPHA)
            if int(valid.sum())!=M or not np.isfinite(power).all() or not np.isfinite(z[valid]).all() or np.any(z[valid]<=0):
                bad.append({'CPI':i,'reason':'valid CUT/training integrity'});break
            f=int(alarm.sum())
            if f<0 or f>M:
                bad.append({'CPI':i,'reason':'out of range alarm count'});break
            counts.append(f)
            if (i+1)%4000==0:
                print('MAIN_PFA_FIXED_PROGRESS',i+1,'/',N,flush=True)
        valid=len(counts)==N and not bad
        U=mean=variance=None
        check_U=None
        if valid:
            raw=np.array(counts,dtype=np.int64)
            mean=float(raw.mean())/M
            variance=float(np.var(raw/M,ddof=1))
            U=float(min(1.,mean+math.sqrt(2*variance*math.log(40)/N)+7*math.log(40)/(3*(N-1))))
            check=eb_welford(counts)
            check_U=check[2] if check else None
            if check is None or not math.isclose(U,check_U,rel_tol=1e-12,abs_tol=1e-14) or not math.isclose(mean,check[0],rel_tol=1e-12,abs_tol=1e-14):
                bad.append({'reason':'independent Welford EB check disagrees'})
                valid=False
        result_status=('PASS' if U<=LIMIT else 'FAIL') if valid else 'INCONCLUSIVE'
        result={
          'project':'AX309-RDSP-001','stage':'S03','scope':'FINAL_MAIN_Pfa_FIXED_20000CPI_APPROVED_v1.2',
          'status':result_status,'all_20000_CPI_valid':valid,'N_expected':N,'N_processed':len(counts),
          'valid_CUT_per_CPI':M,'observed_alarm_total':int(sum(counts)),
          'observed_alarm_count_mean_per_CPI':float(np.mean(counts)) if counts else None,
          'observed_alarm_count_sample_variance_per_CPI':float(np.var(counts,ddof=1)) if len(counts)>1 else None,
          'observed_alarm_fraction_mean':mean,
          'observed_alarm_fraction_sample_variance':variance,
          'empirical_Bernstein_one_sided_U_95':U,
          'independent_Welford_one_sided_U_95':check_U,
          'Pfa_design':.001,'acceptance_upper_limit':LIMIT,
          'input_generation':'PCG64 SeedSequence([411091703,i,191]), fresh Generator per CPI, Gaussian IQ CN(0,1)',
          'alpha_locked':ALPHA,'Delta_star_historical_unchanged_not_used':.28734133322686817,
          'source_script_sha256':sha(__file__),'preflight_script_sha256':sha(ROOT/'s03_reference/c04_eb_independent_preflight.py'),
          'model_sha256':sha(m.__file__),'approved_v12_contract_sha256':approval['new_approved_artifact_sha256'],
          'authorization_decision_sha256':sha(ROOT/DECISION),
          'preflight_sha256':sha(ROOT/PREFLIGHT),
          'input_IQ_signatures_selected':checksums,
          'alarm_count_vector_int32_sha256':hashlib.sha256(np.array(counts,dtype=np.int32).tobytes()).hexdigest(),
          'alarm_count_vector':counts,
          'invalid_conditions':bad,'elapsed_seconds_monotonic':time.perf_counter()-tic,
          'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
          'no_early_stopping_or_selection':True,
          'other_Pd_acceptance_not_executed':True,'Gate_S03_remains_OPEN':True,
          'interpretation':'software Python radar-chain noise-only Pfa test; NOT physical FPGA hardware performance'
        }
        if result_path.exists():raise RuntimeError('result already exists')
        with open(result_path,'x',encoding='utf-8') as out:
            json.dump(result,out,ensure_ascii=False,indent=2,sort_keys=True);out.write('\n')
        print('FINAL_PFA_RESULT',result_status,'N',len(counts),'TOTAL_ALARMS',sum(counts),'MEAN',mean,'VARIANCE',variance,'U',U,'TIME_SEC',result['elapsed_seconds_monotonic'],flush=True)
        claim['status']='RESULT_WRITTEN_'+result_status
        claim['result_sha256']=sha(result_path)
        claim['elapsed_seconds_monotonic']=result['elapsed_seconds_monotonic']
    except Exception as exc:
        claim['status']='INCONCLUSIVE_EXCEPTION'
        claim['exception_type']=type(exc).__name__
        claim['exception_message']=str(exc)[:1000]
        claim['N_processed']=len(counts)
        claim['elapsed_seconds_monotonic']=time.perf_counter()-tic
        print('MAIN_PFA_INCONCLUSIVE_EXCEPTION',type(exc).__name__,str(exc),flush=True)
    finally:
        with open(claim_path,'w',encoding='utf-8') as out:
            json.dump(claim,out,ensure_ascii=False,indent=2,sort_keys=True);out.write('\n')
    if claim['status']=='INCONCLUSIVE_EXCEPTION':sys.exit(2)

if __name__=='__main__':main()

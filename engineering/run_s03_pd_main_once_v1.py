"""AUTHORIZED one-shot S03 Pd 1000-CPI runner. Do not import to run a study.

This program is intentionally not invoked by unit tests.
Exactly one invocation is permitted; run marker is create-exclusive.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

# Resolve imports against this repository, regardless of the launch directory.
# No scientific-model or scorer source is modified by this bootstrap.
BASE = Path(__file__).resolve().parent.parent
# Prepend unconditionally so this repository wins over any external PYTHONPATH.
sys.path.insert(0, str(BASE))

import numpy as np
import scipy
from scipy.stats import beta

from s03_reference import model as m
from s03_reference import pd_acceptance_candidate as pd

OUTPUT = BASE / 'engineering' / 'S03-Pd-MAIN-1000CPI-v1'
CONTRACT = BASE / 'engineering' / 'S03-Pd-independent-fixed-execution-contract-v0.3.json'
SOURCE = (BASE / 's03_reference' / 'model.py')
SCORER = (BASE / 's03_reference' / 'pd_acceptance_candidate.py')
MATRIX = BASE / 'engineering' / 'S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json'
RUNNER = BASE / 'engineering' / 'run_s03_pd_main_once_v1.py'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def checkpoint_file(path, obj):
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(obj,f,sort_keys=True,ensure_ascii=False,indent=2)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp,path)

def preflight():
    """Read-only startup/source audit: no RNG, CPI, run marker, or main()."""
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    expected = contract['source_locked_SHA256']
    assert Path(m.__file__).resolve() == SOURCE.resolve()
    assert Path(pd.__file__).resolve() == SCORER.resolve()
    assert sha(SOURCE) == expected['model']
    assert sha(SCORER) == expected['pd_scorer']
    assert sha(MATRIX) == expected['approved_S02_matrix']
    assert sha(CONTRACT) == '602e4fe6132c4d8521b33c61a1c2cd413c3e75cc4325fe8b9bca6dea966bed5f'
    assert pd.N == contract['N'] == 1000
    assert pd.MASTER_SEED_RESERVED == contract['master_seed_reserved_not_used'] == 411091704
    assert pd.ALPHA_FIXED == contract['alpha'] == 7.476912055027923
    assert (pd.TRUTH_K, pd.TRUE_BIN, pd.TRUE_VELOCITY) == (40, 4, 1.875)
    assert (pd.TARGET_AMPLITUDE, pd.TARGET_PHASE, pd.SNR_DB) == (0.18+0j, 0.0, 20.0)
    assert (m.N, m.PULSES, m.FFT_N) == (128, 33, 32)
    assert pd.min_success_count() == contract['min_successes_N1000'] == 916
    assert contract['optional_joint_guard'].startswith('NOT_APPROVED')
    assert not OUTPUT.exists(), 'main run output directory exists; preflight cannot assert untouched state'
    print('PREFLIGHT PASS: repository import, frozen hashes, 916 threshold; 0 CPI; no seed use; no run marker')
    return 0


def main():
    # All source/contract checks take place BEFORE run marker and sampling.
    contract=json.loads(CONTRACT.read_text())
    expected=contract['source_locked_SHA256']
    assert sha(SOURCE)==expected['model']
    assert sha(SCORER)==expected['pd_scorer']
    assert sha(MATRIX)==expected['approved_S02_matrix']
    assert sha(CONTRACT)=='602e4fe6132c4d8521b33c61a1c2cd413c3e75cc4325fe8b9bca6dea966bed5f'
    assert pd.N==contract['N']==1000
    assert pd.MASTER_SEED_RESERVED==contract['master_seed_reserved_not_used']==411091704
    assert pd.ALPHA_FIXED==contract['alpha']==7.476912055027923
    assert pd.TRUE_BIN==4 and pd.TRUTH_K==40
    assert pd.TARGET_AMPLITUDE==.18+0j and pd.TARGET_PHASE==0
    assert pd.SNR_DB==20 and pd.TRUE_VELOCITY==1.875
    assert m.N==128 and m.PULSES==33 and m.FFT_N==32
    assert pd.min_success_count()==916
    assert contract['optional_joint_guard'].startswith('NOT_APPROVED')
    if OUTPUT.exists():
        raise RuntimeError('One-shot output directory already exists; no rerun permitted')
    OUTPUT.mkdir(parents=False,exist_ok=False)
    marker=OUTPUT/'STARTED.json'
    info={
      'run_status':'STARTED',
      'started_utc':utc(),
      'source_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=BASE,text=True).strip(),
      'model_sha256':sha(SOURCE),'scorer_sha256':sha(SCORER),
      'contract_sha256':sha(CONTRACT),'matrix_sha256':sha(MATRIX),'runner_sha256':sha(RUNNER),
      'numpy_version':np.__version__,'scipy_version':scipy.__version__,
      'python_version':sys.version,
      'N':1000,'master_seed':411091704,
      'seed_pattern':'np.random.SeedSequence([411091704,i,191]) for i=0..999',
      'requirement':'NO rerun, no extra samples, no optional stopping'
    }
    with marker.open('x',encoding='utf-8') as f:
        json.dump(info,f,sort_keys=True,indent=2)
        f.write('\n');f.flush();os.fsync(f.fileno())

    counts={'D':0,'R':0,'V':0,'E':0,'J':0,'no_match':0,'extra_clusters':0,'CFAR_alarm_cells':0}
    attempted=0
    completed=0
    error=None
    raw=OUTPUT/'RAW-CPI-records.jsonl'
    target=m.Target(pd.TRUTH_K,pd.TRUE_VELOCITY,pd.TARGET_AMPLITUDE,pd.TARGET_PHASE)
    try:
        with raw.open('x',encoding='utf-8') as f:
            for i in range(1000):
                attempted+=1
                seed=np.random.SeedSequence([411091704,i,191])
                iq=m.generate_cpi(targets=[target],snr_db=20,seed=seed,clutter=None)
                assert iq.shape==(33,128) and np.all(np.isfinite(iq))
                z=m.pipeline(iq,alpha=pd.ALPHA_FIXED)
                assert z['power'].shape==(128,32) and np.all(np.isfinite(z['power']))
                assert int(np.count_nonzero(z['valid']))==2782
                assert len(m.TRAIN_OFFSETS)==40
                assert len(z['targets'])==len({t['record_id'] for t in z['targets']})
                truth=m.truth_match(z['targets'],[pd.fixed_target_truth()])
                record_by_id={t['record_id']:t for t in z['targets']}
                match=record_by_id[truth[0][1]] if truth else None
                power_row=z['power'][match['range_bin'],:].tolist() if match else None
                scored=pd.score_detection_records(z['targets'],matched_range_power_bins=power_row)
                if scored['status']!='VALID':
                    raise ValueError('INCONCLUSIVE CPI index '+str(i)+': '+str(scored))
                d=bool(scored['detection_and_one_to_one_association'])
                r=bool(scored['range_accuracy_conditional'])
                v=bool(scored['doppler_halfbin_accuracy_conditional'])
                e=bool(scored['doppler_peak_eligible'])
                j=bool(scored['joint_detection_and_both_accuracies'])
                assert j==(d and r and v)
                assert not v or d and e
                assert scored['matched_record_id']==(match['record_id'] if match else None)
                assert scored['extra_unmatched_cluster_count']==len(z['targets'])-int(d)
                gt_k=pd.TRUTH_K; gt_b=pd.TRUE_BIN
                gt_mean=float(z['noise_estimate'][gt_k,gt_b])
                gt_cut=float(z['power'][gt_k,gt_b])
                gt_threshold=float(pd.ALPHA_FIXED*gt_mean)
                cell_alarms=int(np.count_nonzero(z['cfar']))
                entry={
                  'cpi_index':i,'seed_index':i,'seed_namespace':191,
                  'input_iq_sha256':hashlib.sha256(iq.tobytes(order='C')).hexdigest(),
                  'output_power_sha256':hashlib.sha256(np.ascontiguousarray(z['power']).tobytes()).hexdigest(),
                  'cluster_records':z['targets'],
                  'matched_32bin_doppler_power_row':power_row,
                  'cfar_alarm_cell_count':cell_alarms,
                  'valid_cfar_cut_count':int(np.count_nonzero(z['valid'])),
                  'gt_cut_power_linear':gt_cut,
                  'gt_training_mean40_linear':gt_mean,
                  'gt_threshold_linear':gt_threshold,
                  'gt_alarm':bool(z['cfar'][gt_k,gt_b]),
                  'score':scored,
                  'D':d,'R':r,'V':v,'E':e,'J':j,
                }
                f.write(json.dumps(entry,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n')
                f.flush()
                os.fsync(f.fileno())
                counts['D']+=int(d);counts['R']+=int(r);counts['V']+=int(v)
                counts['E']+=int(e);counts['J']+=int(j)
                counts['no_match']+=int(not d)
                counts['extra_clusters']+=scored['extra_unmatched_cluster_count']
                counts['CFAR_alarm_cells']+=cell_alarms
                completed+=1
    except Exception as exc:
        error={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(limit=8)}
    n=1000
    L=float(beta.ppf(.05,counts['D'],n-counts['D']+1)) if counts['D']>0 else 0.
    disposition='INCONCLUSIVE' if error or completed!=n else ('PASS' if counts['D']>=916 and L>=.9 else 'FAIL')
    result={
      'project':'AX309-RDSP-001','stage':'S03','type':'Pd_MAIN_1000CPI',
      'status':disposition,'completed_utc':utc(),'attempted_CPI':attempted,
      'valid_completed_CPI':completed,'invalid_CPI_count':int(error is not None),
      'sample_denominator_predeclared':n,'source_commit_before_run':info['source_git_commit'],
      'frozen_sources':{k:v for k,v in info.items() if k.endswith('_sha256')},
      'master_seed':411091704,'seed_pattern':info['seed_pattern'],
      'D_success':counts['D'],'D_failure':completed-counts['D'],
      'D_one_sided_95pct_CP_lower':L if disposition!='INCONCLUSIVE' else None,
      'D_min_accept_successes':916,
      'counts':counts,
      'R_success_conditional_on_D':counts['R'],
      'R_denominator_matched_D':counts['D'],
      'V_success_conditional_on_D':counts['V'],
      'V_denominator_matched_D':counts['D'],
      'E_success':counts['E'],
      'J_success':counts['J'],
      'J_CP_95pct_lower_report_only':float(beta.ppf(.05,counts['J'],n-counts['J']+1)) if disposition!='INCONCLUSIVE' and counts['J']>0 else None,
      'J_has_no_new_binding_90pct_acceptance':True,
      'error':error,'raw_records':str(raw.relative_to(BASE)),
      'raw_records_sha256':sha(raw) if raw.exists() else None,
      'hardware_evidence':False,'gate_S03':'OPEN','progress_unchanged':True
    }
    checkpoint_file(OUTPUT/'RESULT.json',result)
    if disposition=='INCONCLUSIVE':
        print('INCONCLUSIVE',json.dumps({'attempted':attempted,'valid':completed,'error':error},ensure_ascii=False))
    else:
        print(disposition,json.dumps({'valid':completed,'D':counts['D'],'D_failure':completed-counts['D'],'L_CP':L,'J':counts['J'],'R':counts['R'],'V':counts['V'],'E':counts['E'],'extra':counts['extra_clusters']},ensure_ascii=False))
    return 0 if disposition in ('PASS','FAIL') else 2

if __name__=='__main__':
    if sys.argv[1:] == ['--preflight']:
        sys.exit(preflight())
    if sys.argv[1:]:
        raise SystemExit('Unsupported arguments. Use --preflight for zero-CPI audit.')
    # Without --preflight this is the one-shot main attempt; never invoke in tests.
    sys.exit(main())

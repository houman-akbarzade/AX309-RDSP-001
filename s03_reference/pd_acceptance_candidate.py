"""PROPOSED Pd scoring and exact CI arithmetic ONLY; NOT authorized Pd execution.

This module has NO input-generation loop or main trial entrypoint.
Score takes already-computed records; synthetic hand-crafted records are
allowed for deterministic unit checks (NO new target CPI generated).
"""
from dataclasses import dataclass
import math
from scipy.stats import beta, binom
from . import model as m

N=1000
MASTER_SEED_RESERVED=411091704
ALPHA_FIXED=7.476912055027923
SNR_DB=20.0
TRUTH_K=40
TRUE_BIN=4
TRUE_VELOCITY=1.875
TARGET_AMPLITUDE=0.18+0j
TARGET_PHASE=0.0
NOISE_VARIANCE=0.000324
ASSOCIATION_RANGE_GATE_BINS=2
ASSOCIATION_DOPPLER_GATE_BINS=1
RANGE_ACCURACY_SAMPLES=1
DOPPLER_ACCURACY_M_S=0.234375
P_D_GOAL=0.9
CONFIDENCE=.95
HALF_BIN_M_S=.234375

def exact_one_sided_lower(k,n=N):
    if not isinstance(k,int) or not isinstance(n,int) or n<1 or not (0<=k<=n):
        raise ValueError('invalid independent Bernoulli count')
    if k==0:return 0.0
    return float(beta.ppf(1-CONFIDENCE,k,n-k+1))

def min_success_count(n=N):
    """Exact beta-quantile inversion; verify with independent binomial SF."""
    if n!=N:raise ValueError('n fixed at 1000')
    for k in range(n+1):
        if exact_one_sided_lower(k,n)>=P_D_GOAL:
            assert binom.sf(k-1,n,P_D_GOAL)<=.05
            if k>0:assert binom.sf(k-2,n,P_D_GOAL)>.05
            return k
    return None

def fixed_target_truth():
    return {'id':0, 'range_m_nominal':TRUTH_K*m.C_NOMINAL/(2*m.FS),
            'velocity_m_s':TRUE_VELOCITY}

def score_detection_records(detections, *, matched_range_power_bins=None, valid_input=True):
    """Score ONE complete CPI already processed by the fixed pipeline.

    Association success D is distinct from range accuracy R, velocity
    accuracy V, and joint success J=D and R and V. Count one CPI only.
    Do not reinterpret association gate as estimator accuracy.
    """
    if not valid_input:
        return {'status':'INCONCLUSIVE','reason':'invalid CPI; no exclusion'}
    if not isinstance(detections,list):
        raise ValueError('detections must be a complete fixed cluster list')
    ids=[r['record_id'] for r in detections]
    if len(ids)!=len(set(ids)):
        return {'status':'INCONCLUSIVE','reason':'duplicate cluster record_id'}
    for r in detections:
        if r['range_bin']<0 or r['range_bin']>=m.N or r['doppler_bin']<0 or r['doppler_bin']>=m.FFT_N:
            return {'status':'INCONCLUSIVE','reason':'invalid bin index'}
        if not math.isfinite(float(r['velocity_m_s_nominal'])):
            return {'status':'INCONCLUSIVE','reason':'nonfinite velocity'}
        expected=float(m.bin_velocity(r['doppler_bin']))
        if abs(expected-float(r['velocity_m_s_nominal']))>1e-12:
            return {'status':'INCONCLUSIVE','reason':'velocity/nominal-bin mismatch'}
    pairs=m.truth_match(detections,[fixed_target_truth()])
    matched=len(pairs)==1
    assoc_ID=pairs[0][1] if matched else None
    candidate=next((r for r in detections if r['record_id']==assoc_ID),None)
    assert not matched or candidate is not None
    dr_samples=abs(candidate['range_bin']-TRUTH_K) if matched else None
    dv_abs=abs(candidate['velocity_m_s_nominal']-float(m.bin_velocity(TRUE_BIN))) if matched else None
    range_ok=bool(matched and dr_samples<=RANGE_ACCURACY_SAMPLES)
    dop_ok=bool(matched and dv_abs<=DOPPLER_ACCURACY_M_S+1e-12)
    if matched and matched_range_power_bins is None:
        return {'status':'INCONCLUSIVE','reason':'matched peak power row missing; Doppler eligibility cannot be inferred from cluster association alone'}
    elig=(doppler_peak_eligibility(matched_range_power_bins, candidate['doppler_bin'])
          if matched else {'status':'VALID','eligible':False,'reason':'NO_MATCH'})
    if elig['status']!='VALID':
        return {'status':'INCONCLUSIVE','reason':'invalid matched Doppler power row'}
    eligible=bool(elig['eligible'])
    return {'status':'VALID','detection_and_one_to_one_association':bool(matched),
            'range_accuracy_conditional':range_ok,
            'doppler_halfbin_accuracy_conditional':dop_ok,
            'joint_detection_and_both_accuracies':bool(matched and range_ok and dop_ok and eligible),
            'doppler_peak_eligible':eligible, 'doppler_peak_status':elig.get('peak_status'),
            'matched_record_id':assoc_ID,'range_error_samples':dr_samples,
            'velocity_error_m_s_nominal':dv_abs,
            'extra_unmatched_cluster_count':len(detections)-(1 if matched else 0),
            'velocity_onbin_eligibility_design':'on-bin truth k40,b+4, away from MTI DC and Nyquist; actual output peak status to be recorded at run time'}

def verify_fixed_parameters():
    t=m.Target(TRUTH_K,TRUE_VELOCITY,TARGET_AMPLITUDE,TARGET_PHASE)
    assert math.isclose(m.noise_variance(t,SNR_DB),NOISE_VARIANCE,rel_tol=1e-12)
    assert math.isclose(float(m.bin_velocity(TRUE_BIN)),TRUE_VELOCITY,rel_tol=1e-12)
    assert min_success_count()==916
    return True


def doppler_peak_eligibility(power_bins, matched_bin):
    """Deterministic S02 eligibility check on an ALREADY COMPUTED 32-bin row.

    This is NOT a stochastic trial generator. Not eligible is reported and
    never silently removed from the fixed 1000-CPI acceptance denominator.
    """
    import numpy as np
    power=np.asarray(power_bins,dtype=np.float64)
    if power.shape!=(m.FFT_N,) or not np.all(np.isfinite(power)) or np.any(power<0):
        return {'status':'INCONCLUSIVE','reason':'invalid power row'}
    chosen,status=m.select_peak(power)
    positive=bool(power[chosen]>0)
    adjacent=bool(positive and power[chosen]>power[(chosen-1)%m.FFT_N]
                  and power[chosen]>power[(chosen+1)%m.FFT_N])
    eligible=bool(status=='OK' and adjacent and chosen==int(matched_bin)
                  and TRUE_BIN not in (0,16))
    return {'status':'VALID','eligible':eligible,'reason':('ELIGIBLE' if eligible else 'NOT_ELIGIBLE'),
            'selected_peak_bin':chosen,'peak_status':status,'strictly_above_adjacent':adjacent}

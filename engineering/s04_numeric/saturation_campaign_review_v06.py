"""Deterministic analytical campaign-saturation risk, no CPI, RNG, or S03 generator.

Uses the previously validated S04 exact Q1.15 threshold and conditional Gaussian
component model; independently cross-checks centered CN(0,1) using erfc.
"""
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from scipy.optimize import brentq

ROOT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('s04_v05_quant_analytical',ROOT/'input_policy_quant_review_v05.py')
v05=importlib.util.module_from_spec(s)
s.loader.exec_module(v05)
v03=v05.v03
SCALES=(1,2,3,4,5,6,8)
NS=(1000,20000)
TARGET_RISKS=(.1,.01,.001)
CLASSES=('NOISE_ONLY_UNIT','PD_REFERENCE_LIKE','ILLUSTRATIVE_CLUTTER_0P8','ILLUSTRATIVE_CLUTTER_1P2')

def campaign_from_logq(logq,N):
    """P(any) given log(q) and N independent exchangeable CPI."""
    if logq>=0:
        return {'probability':1.,'log10_probability':0.,'log_probability':0.}
    # If q is tiny, exact rounding would erase it. Compute log probability
    # of >=1 hit from log(N*q), using asymptotic form for unobservable correction.
    if logq < -36:
        logP=math.log(N)+logq
        p=math.exp(logP) if logP>-744 else 0.
        return {'probability':p,'log10_probability':logP/math.log(10),
                'log_probability':logP,'method':'rare-event asymptotic relative error bounded by O(N*q)'}
    q=math.exp(logq)
    log_no=N*math.log1p(-q)
    p=-math.expm1(log_no)
    logP=math.log(p) if p>0 else -math.inf
    return {'probability':p,'log10_probability':logP/math.log(10),
            'log_probability':logP,'method':'stable exact iid CPI expression via expm1/log1p'}

def independently_crosscheck_unit(g,N):
    a=v05.independent_unit_gaussian(g)['per_component']
    # 8448*N independent Gaussian real noise components, direct campaign formula.
    return -math.expm1((8448*N)*math.log1p(-a))

def campaign_risk_for_unit(g,N):
    return independently_crosscheck_unit(g,N)

def inverse_scale_noise_only(N,risk):
    f=lambda g:campaign_risk_for_unit(g,N)-risk
    assert f(1)>0 and f(16)<0
    root=brentq(f,1,16,xtol=2e-13)
    assert abs(campaign_risk_for_unit(root,N)-risk)<2e-10
    return root

def build():
    audit=json.loads((ROOT/'S04-input-policy-quantitative-v0.5.json').read_text())
    assert tuple(audit['candidates_not_approved'])==SCALES
    result={'project':'AX309-RDSP-001','stage':'S04','version':'v0.6',
      'scope':'analytical prospective design comparison; no sample generation or accepted data',
      'status':'C01_HOLD_C02_OPEN_NOT_APPROVED',
      'recorded_utc':datetime.now(timezone.utc).isoformat(),
      'assumptions':'Full 8448 real components per CPI; v0.5 exact RNE Q1.15 asymmetric clipping; conditional independent Gaussian real/imag source noise. Across CPI, independent and identically distributed with fixed per-CPI q, unless explicitly identified otherwise.',
      'scales_all_unapproved':list(SCALES),'campaign_lengths':list(NS),
      'classes':{},'risk_tiers_not_approved':{},
      'quantization_tradeoff':{str(g):v05.quantization(g) for g in SCALES},
      'independent_closed_form_checks':0,
      'limitations':['iid across CPI is a modeling premise not an empirically proved fact',
       'heterogeneous independent CPI risk equals 1-prod(1-q_i), not 1-(1-q)^N',
       'without independence, Frechet lower max(q_i) and union upper min(1,sum(q_i)); trivial upper remains 1 for many scales',
       'correlated clutter invalidates conditional independent-component product absent specified joint model',
       'no clipping performance rule or approved gain/risk is implied by this analysis']}
    for class_key in CLASSES:
        cases={}
        for g in SCALES:
            curve=audit['classes'][class_key]['candidate_curves'][str(g)]
            logq=curve['log10_prob_at_least_one_saturation']*math.log(10)
            cases[str(g)]={'per_CPI':{
                 'probability':curve['prob_at_least_one_saturation'],
                 'log10_probability':curve['log10_prob_at_least_one_saturation'],
                 'expected_saturated_components':curve['expected_saturated_components'],
                 'log10_expected':curve['log10_expected_saturated_components']},
                 'campaign':{str(N):campaign_from_logq(logq,N) for N in NS}}
            if class_key=='NOISE_ONLY_UNIT':
                for N in NS:
                    direct=independently_crosscheck_unit(g,N)
                    combined=cases[str(g)]['campaign'][str(N)]['probability']
                    assert math.isclose(direct,combined,rel_tol=5e-11,abs_tol=1e-25),(g,N,direct,combined)
                    result['independent_closed_form_checks']+=1
        result['classes'][class_key]={'source_definition':audit['classes'][class_key]['source_definition'],
                                     'comparison':cases,
                                     'approved_population':class_key in ('NOISE_ONLY_UNIT','PD_REFERENCE_LIKE'),
                                     'note':'Pd reference-like mathematical definition is not an approved new fixed point population or re-run authorization'}
    for N in NS:
        tier=[]
        for risk in TARGET_RISKS:
            root=inverse_scale_noise_only(N,risk)
            q=v05.quantization(root)
            # deterministic candidate grid rule: first candidate not exceeding target
            eligible=[g for g in SCALES if campaign_risk_for_unit(g,N)<=risk]
            tier.append({'target_campaign_stop_probability_UNAPPROVED':risk,
               'theoretical_minimum_continuous_g':root,
               'smallest_candidate_in_comparison_grid':eligible[0] if eligible else None,
               'component_LSB_original_float_units':root/32768,
               'component_max_quantization_error_original_float_units':q['component_max_abs_original_units'],
               'component_RMS_uniform_roundoff_hypothesis':q['component_rms_uniform_roundoff_hypothesis']})
        result['risk_tiers_not_approved'][str(N)]=tier
    assert result['independent_closed_form_checks']==14
    return result

if __name__=='__main__':
    r=build()
    out=ROOT/'S04-saturation-campaign-analytic-v0.6.json'
    out.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print('INDEPENDENT_UNIT_GAUSSIAN_CHECKS',r['independent_closed_form_checks'])
    for N in NS:
        print('N',N)
        for risk in r['risk_tiers_not_approved'][str(N)]:
            print('TARGET',risk['target_campaign_stop_probability_UNAPPROVED'],
                  'G_MIN',risk['theoretical_minimum_continuous_g'],
                  'GRID',risk['smallest_candidate_in_comparison_grid'],
                  'MAX_ERR',risk['component_max_quantization_error_original_float_units'])
        for g in SCALES:
            z=r['classes']['NOISE_ONLY_UNIT']['comparison'][str(g)]['campaign'][str(N)]
            print('g=',g,'P(any CPI saturated)',z['probability'],'log10=',z['log10_probability'])
    print('DATA_SHA256',hashlib.sha256(out.read_bytes()).hexdigest())

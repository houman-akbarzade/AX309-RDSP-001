"""Deterministic analytic design calculations only; no PRNG, no CPI sample generation.

This is NOT a statistical acceptance run. Imported S04 v0.3 functions are
deterministic source-mean and exact quantizer helpers, not the S03 generator.
"""
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
from scipy.special import log_ndtr

BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('s04_analysis_v03_dependency',BASE/'input_scaling_analysis_v03.py')
v03=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v03)

def model(class_key):
    z=np.zeros((33,128),dtype=np.complex128)
    if class_key=='NOISE_ONLY_UNIT':
        return v03.to_component_means(z),1.0, 'CN(0,1), independent components, absent target'
    mean=v03.cpi_component_means_pd()
    if class_key=='PD_REFERENCE_LIKE':
        return v03.to_component_means(mean),.000324,'single fixed k40, bin+4 amplitude .18, no clutter; analytic target means only'
    if class_key=='ILLUSTRATIVE_CLUTTER_0P8':
        return v03.to_component_means(mean+.8),.000324,'deterministic uniform real .8 offset, independent small Gaussian noise; illustrative not accepted clutter law'
    if class_key=='ILLUSTRATIVE_CLUTTER_1P2':
        return v03.to_component_means(mean+1.2),.000324,'deterministic uniform real 1.2 offset, independent small Gaussian noise; illustrative not accepted clutter law'
    raise ValueError(class_key)

def independent_unit_gaussian(g):
    # Mathematically independent closed-form alternative to existing log-NDTR vector code.
    u=float(v03.UPPER)*g
    l=float(v03.LOWER)*g
    sigma=math.sqrt(.5)
    p=0.5*math.erfc(u/(math.sqrt(2)*sigma))+0.5*math.erfc(-l/(math.sqrt(2)*sigma))
    return {'per_component':p,'expected_components':8448*p,
            'prob_at_least_one':-math.expm1(8448*math.log1p(-p)),
            'model':'8448 independent centered N(0,1/2) components'}

def quantization(g):
    # exact per-component worst-case bound assuming no saturation.
    absmax=g/65536
    # uniform-error approximation (NOT guaranteed); each component delta=g/32768
    rmshyp=g/(32768*math.sqrt(12))
    return {'component_max_abs_original_units':absmax,
            'complex_max_abs_original_units':math.sqrt(2)*absmax,
            'component_rms_uniform_roundoff_hypothesis':rmshyp,
            'rms_assumption':'only for independent uniform quantization error on [-Delta/2,Delta/2], NOT a proven RMS tolerance'}

def main():
    # No scales/risks below are selected: only design-grid sensitivity analyses.
    candidates=[1,2,3,4,5,6,8]
    classes=['NOISE_ONLY_UNIT','PD_REFERENCE_LIKE','ILLUSTRATIVE_CLUTTER_0P8','ILLUSTRATIVE_CLUTTER_1P2']
    classes_data={}
    for key in classes:
        mu,var,description=model(key)
        curves={}
        for g in candidates:
            row=v03.gaussian_saturation(mu,var,g)
            curves[str(g)]={k:row[k] for k in (
                'expected_saturated_components','log10_expected_saturated_components',
                'prob_at_least_one_saturation','log10_prob_at_least_one_saturation',
                'threshold_float_upper_inclusive','threshold_float_lower_exclusive')}
            curves[str(g)]['quantization']=quantization(g)
            # Per-component probabilities are not identical for a deterministic
            # target/clutter mean; record their range and a complete digest of
            # their 8448 ordered logarithmic probabilities without sampling.
            sigma=math.sqrt(var/2)
            up=float(v03.UPPER)*g
            low=float(v03.LOWER)*g
            logp=np.logaddexp(log_ndtr((mu-up)/sigma),
                              log_ndtr((low-mu)/sigma))
            assert len(logp)==8448
            curves[str(g)]['individual_component_risk']={
               'count':len(logp),'minimum_log10_probability':float(logp.min()/math.log(10)),
               'maximum_log10_probability':float(logp.max()/math.log(10)),
               'component_log_probability_vector_sha256':
                   hashlib.sha256(np.ascontiguousarray(logp,dtype='<f8').tobytes()).hexdigest(),
               'component_order':'pulse-major, range then I,Q for deterministic mean vector',
               'per_component_formula':'Phi((L-mu_i)/sigma)+Phi((mu_i-U)/sigma)'
            }
        classes_data[key]={'source_definition':description,'complex_noise_power':var,
                           'component_count':8448,'candidate_curves':curves}
    for g in candidates:
        independent=independent_unit_gaussian(g)
        recorded=classes_data['NOISE_ONLY_UNIT']['candidate_curves'][str(g)]
        assert math.isclose(independent['expected_components'],recorded['expected_saturated_components'],rel_tol=5e-13,abs_tol=1e-27)
        assert math.isclose(independent['prob_at_least_one'],recorded['prob_at_least_one_saturation'],rel_tol=1e-12,abs_tol=1e-27)
    risk_tiers=[.1,.01,.001,.0001,.000001]
    required=[]
    for risk in risk_tiers:
        f=lambda g:independent_unit_gaussian(g)['prob_at_least_one']-risk
        assert f(1)>0 and f(16)<0
        gstar=brentq(f,1.,16.,xtol=2e-13)
        q=quantization(gstar)
        assert abs(independent_unit_gaussian(gstar)['prob_at_least_one']-risk)<1e-10
        assert f(gstar*.999999)>=0 and f(gstar*1.000001)<=0
        required.append({'candidate_max_P_at_least_one_input_saturation':risk,
                         'theoretical_minimum_continuous_g_noise_only':gstar,
                         'component_absmax_input_error':q['component_max_abs_original_units'],
                         'component_uniform_roundoff_rms_hypothesis':q['component_rms_uniform_roundoff_hypothesis'],
                         'scale_status':'UNAPPROVED theoretical boundary; not registry selection'})
    # deterministic candidate rule, only for fully specified classes and prospective risk:
    # choose smallest approved g with analytic certified P(any clipping) <= approved risk;
    # no selection if model, eligible list or risk is absent.
    def proposed_choose(model_key,approved_values,risk):
        if not approved_values or risk is None or model_key not in classes:
            return None
        mu,var,_=model(model_key)
        eligible=sorted(set(approved_values))
        assert all(g>0 for g in eligible)
        matching=[g for g in eligible if v03.gaussian_saturation(mu,var,g)['prob_at_least_one_saturation']<=risk]
        return matching[0] if matching else None
    oracle_cases=[]
    # Explicitly illustrative hypothetical allowlists and risk, NOT approved configuration.
    for risk in [.1,.01,.001,.0001]:
        for class_key in ['NOISE_ONLY_UNIT','PD_REFERENCE_LIKE','ILLUSTRATIVE_CLUTTER_0P8']:
            choice=proposed_choose(class_key,[1,2,4,8],risk)
            oracle_cases.append({'risk_proposal':risk,'class':class_key,
                'hypothetical_allowlist':[1,2,4,8],'hypothetical_result':choice,
                'status':'ILLUSTRATION_NOT_APPROVED'})
    assert proposed_choose('UNSPECIFIED', [1,2,4,8],.01) is None
    assert proposed_choose('NOISE_ONLY_UNIT',[],.01) is None
    assert proposed_choose('NOISE_ONLY_UNIT',[1,2,4,8],None) is None
    assert all(classes_data['NOISE_ONLY_UNIT']['candidate_curves'][str(a)]['prob_at_least_one_saturation']>=
         classes_data['NOISE_ONLY_UNIT']['candidate_curves'][str(b)]['prob_at_least_one_saturation']
         for a,b in zip(candidates,candidates[1:]))
    rec={'project':'AX309-RDSP-001','stage':'S04','version':'quantitative-review-v0.5',
      'timestamp_utc':datetime.now(timezone.utc).isoformat(),
      'status':'ANALYTICAL_DESIGN_ONLY_S04_C01_HOLD',
      'method':'exact Q15 RNE asymmetric thresholds; Gaussian noncentral tails integrated analytically, conditional independent components',
      'no_prng_no_CPI_no_accepted_seed':True,
      'candidates_not_approved':candidates,
      'classes':classes_data,
      'risk_tiers_not_approved':required,
      'profile_rule':'smallest engineer-approved g satisfying approved CPI risk bound for declared, verified Gaussian conditional class; no choice if class/model/provenance/risk/allowlist missing',
      'illustrative_profile_rule_cases':oracle_cases,
      'independent_gaussian_unit_checks':len(candidates),
      'pending':['approved input classes and clutter correlation laws','approved g allowlist and risk target','independent fixed-point code and population test','numeric A/B/FFT shifts and RMS tolerances','registry schema and validity approval'],
      'S04_completed_criteria':0,'S04_percent':0,'overall_percent':25}
    path=BASE/'S04-input-policy-quantitative-v0.5.json'
    path.write_text(json.dumps(rec,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('ANALYTIC_GRID',len(classes),'classes',len(candidates),'scales')
    print('INDEPENDENT_GAUSSIAN_CROSSCHECKS',len(candidates),'PASS')
    for item in required:
        print('risk',item['candidate_max_P_at_least_one_input_saturation'],
              'g_min_continuous',item['theoretical_minimum_continuous_g_noise_only'],
              'abs_input_err',item['component_absmax_input_error'])
    for key in classes:
        print(key,'g4',classes_data[key]['candidate_curves']['4']['prob_at_least_one_saturation'])
    print('OUTPUT_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    main()

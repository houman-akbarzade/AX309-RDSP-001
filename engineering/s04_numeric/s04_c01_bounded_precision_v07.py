"""Deterministic input admission and quantization analysis; NO RNG and NO CPI samples."""
from pathlib import Path
import importlib.util, json, math, hashlib
from datetime import datetime,timezone
from fractions import Fraction
base=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('s04_c01_policymath_v05',base/'input_policy_quant_review_v05.py')
q=importlib.util.module_from_spec(sp)
sp.loader.exec_module(q)
pd_means,var,_=q.model('PD_REFERENCE_LIKE')
noisy_means,varnoise,_=q.model('NOISE_ONLY_UNIT')
assert len(pd_means)==len(noisy_means)==8448 and var==.000324 and varnoise==1.
scales=[Fraction(1),Fraction(2),Fraction(4),Fraction(5)]
out={'project':'AX309-RDSP-001','version':'v0.7','status':'DESIGN_ANALYSIS_NOT_APPROVED',
 'created_at_utc':datetime.now(timezone.utc).isoformat(),
 'source':'S03 frozen analytical target geometry as deterministic means, no accepted CPI values used',
 'scenario':{'single_target_amplitude':.18,'pulse_count':33,'samples_per_pulse':128,
             'complex_noise_power':.000324,'SNR_dB':20,'clutter':None},
 'candidate_scales_only':{},'N_noise_only':20000,'N_future_pd_study_proposal':1000,
 'numeric_contract_decision_approved':False,'g_approved':False,'no_random_draws_or_CPI_generation':True}
for g in scales:
 G=float(g)
 pd=q.v03.gaussian_saturation(pd_means,var,G)
 noise=q.v03.gaussian_saturation(noisy_means,varnoise,G)
 pnoise=noise['prob_at_least_one_saturation']
 stop=-math.expm1(20000*math.log1p(-pnoise)) if pnoise<1 else 1.
 delta=float(g)/32768
 eps=delta/2
 complex_bound=math.sqrt(2)*eps
 row={'g':str(g),
 'Pd_class_per_CPI_expected_saturated_components':pd['expected_saturated_components'],
 'Pd_class_per_CPI_expected_log10':pd['log10_expected_saturated_components'],
 'Pd_class_per_CPI_any_saturation':pd['prob_at_least_one_saturation'],
 'Pd_class_per_CPI_any_log10':pd['log10_prob_at_least_one_saturation'],
 'noise_only_P_any_in_20000':stop,'input_quantization_step':delta,
 'input_component_max_error_if_not_saturated':eps,
 'input_complex_error_max_if_not_saturated':complex_bound,
 'step_over_isolated_target_amplitude':delta/.18,
 'complex_error_over_isolated_target_amplitude':complex_bound/.18,
 'target_amplitude_in_component_LSB_units':.18/delta,
 'input_quantized_component_rms_uniform_model_only':delta/math.sqrt(12),
 'bit_exact_noiseless_normalized_0p18_source_check':{}}
 # check selected real component quantization, no noise: exact Fraction(9,50)
 amp=Fraction(9,50)
 val,clipped,raw=q.v03.encode_component(amp,g)
 rec=q.v03.decode_component(val,g)
 assert not clipped
 row['bit_exact_noiseless_normalized_0p18_source_check']={'raw_integer':raw,
 'decoded_rational':str(rec),'component_abs_error':float(abs(rec-amp))}
 out['candidate_scales_only'][str(g)]=row
assert out['candidate_scales_only']['5']['noise_only_P_any_in_20000']<.001
assert out['candidate_scales_only']['4']['noise_only_P_any_in_20000']>.001
p=base/'S04-C01-bounded-precision-analysis-v0.7.json'
p.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('NUMERICAL_ANALYTICAL_ONLY:',len(scales),'scales')
for g,row in out['candidate_scales_only'].items():
 print('g',g,'Pd log10(any clip)',row['Pd_class_per_CPI_any_log10'],
 'complex emax/a',row['complex_error_over_isolated_target_amplitude'],
 'LSB/a',row['step_over_isolated_target_amplitude'],
 'q_noiseless_amp',row['bit_exact_noiseless_normalized_0p18_source_check'])
print('SHA256',hashlib.sha256(p.read_bytes()).hexdigest())

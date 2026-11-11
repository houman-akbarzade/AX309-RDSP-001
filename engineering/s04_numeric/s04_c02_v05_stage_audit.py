"""Postprocess completed integer outputs with independently archived v0.4 bounds."""
import json,math,hashlib
from pathlib import Path
from collections import Counter
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c02_integer_bittrue_v05 as bt
dpath=ROOT/'engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json'
a=json.loads(dpath.read_text())
v=json.load(open(ROOT/'engineering/s04_numeric/S04-C02-internal-arithmetic-error-propagation-v0.4.json'))
violations=[]
for name,x in a['per_option_schedule'].items():
 opt,shift=name.split(':')
 b=v['summaries'][opt]
 sc=b['FFT']['schedules'][shift]
 for case in x['cases']:
  g=1 if case['input_profile']=='SINGLE_TARGET_REFERENCE_LIKE_LAB' else 5
  bounded=case['admissible_for_v04_bound']
  checks={}
  for stage in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5'):
   idx=int(stage[3:])-1 if stage.startswith('FFT') else None
   if stage=='MF':limit=g*b['MF']['combined_conditional_error']
   elif stage=='MTI':limit=g*b['MTI']['combined_error_from_MF_plus_MTI_RNE']
   else:limit=g*(1<<sum(sc['shifts'][:idx+1]))*sc['stage_details'][idx]['reference_complex_error_total_stored_units']
   measured=case['full_stage_metrics'][stage]['MAX']
   passed=measured<=limit+max(1e-9,limit*1e-9) if bounded else None
   checks[stage]={'conditional_bound_original_float_complex_amplitude':limit,
        'observed_MAX_original_float_complex_amplitude':measured,
        'pass_if_no_saturation':passed}
   if passed is False:violations.append({'option_schedule':name,'kind':case['kind'],'g':g,'stage':stage,
                              'measured':measured,'bound':limit})
  case['stagewise_v04_bound_audit']=checks
 x['all_stages_within_v04_bound_on_admissible']=all(
    val['pass_if_no_saturation'] is not False
    for c in x['cases'] for val in c['stagewise_v04_bound_audit'].values())
manifest={'project':'AX309-RDSP-001','version':'v0.5','vector_samples_33x128':33*128,
 'source':'Deterministic rational patterns, independent of accepted Pfa/Pd data or random seeds',
 'profiles':{'g1':'SINGLE_TARGET_REFERENCE_LIKE_LAB test scaling only, not stochastic target CPI',
             'g5':'NOISE_ONLY_UNIT test scaling only, not stochastic noise CPI'},
 'rational_pattern_names':list(bt.KINDS),
 'patterns':{},'no_stochastic_samples':True}
for g in (1,5):
 for kind in bt.KINDS:
  h=hashlib.sha256()
  for p in range(33):
   for r in range(128):
    re,im=bt.vector_value(kind,p,r)
    h.update(f'{p},{r},{re.numerator}/{re.denominator},{im.numerator}/{im.denominator}\n'.encode())
  example=[{'pulse':p,'range':r,'inphase':str(bt.vector_value(kind,p,r)[0]),
             'quadrature':str(bt.vector_value(kind,p,r)[1])}
           for p,r in ((0,0),(8,40),(16,63))]
  manifest['patterns'][f'g{g}:{kind}']={'scalar_profile_g':g,'rational_source_vector_sha256':h.hexdigest(),
    'illustrative_coordinates':example,'full_generator':'s04_c02_integer_bittrue_v05.py::vector_value',
    'all_4224_complex_samples_retained_by_deterministic_formula':True}
vpath=ROOT/'engineering/s04_numeric/S04-C02-deterministic-test-vectors-v0.5.json'
vpath.write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
a['full_stage_bound_recheck']={'admissible_stagewise_violations':violations,
 'all_admissible_stages_pass':len(violations)==0,
 'not_applicable_to_saturated_cases':True,
 'provenance':'postprocess exact archived 0.4 stagewise analytical ceilings and captured integer test metrics'}
dpath.write_text(json.dumps(a,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('STAGE_VIOLATIONS',len(violations))
for x in violations[:10]:print(x)
for name,x in a['per_option_schedule'].items():
 print(name,'eligible',x['admissible_case_count'],'all stages pass',x['all_stages_within_v04_bound_on_admissible'])
print('DATA_SHA256',hashlib.sha256(dpath.read_bytes()).hexdigest())
print('VECTORS_SHA256',hashlib.sha256(vpath.read_bytes()).hexdigest())

"""S04 C02 v0.4 arithmetic *candidate* with algebraic bounded-error provenance.

No CPI, no random draws, no rtl. All bounds conditional on unsaturated IQ and
quantized coefficient model, and an exact-arithmetic-then-once-RNE per output site.
"""
from fractions import Fraction
import json, math, hashlib, sys, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=json.loads((ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json').read_text())
CFAR=json.loads((ROOT/'engineering/s04_numeric/S04-C02-cfar-width-arithmetic-audit-v0.3.1.json').read_text())
SQRT2=math.sqrt(2)
SHIFTS={k:v['shifts'] for k,v in DATA['schedules'].items()}

def rne(x):
    x=Fraction(x)
    a,rem=divmod(abs(x.numerator),x.denominator)
    n=a+(2*rem>x.denominator or (2*rem==x.denominator and a%2==1))
    return n if x>=0 else -n

def signed_quant(x,W,F):
    q=rne(Fraction(x)*(1<<F))
    lo=-(1<<(W-1));hi=(1<<(W-1))-1
    return max(lo,min(hi,q)), q<lo or q>hi

def bmax(w,f):
    return ((1<<(w-1))-1)/(1<<f)

def stage_error_step(e,ref_bound,beta,delta,shift,F):
    # Reconstructed stored units; ROUND ONE complex output at each stage.
    return ((1+beta)*e+delta*ref_bound)/(1<<shift)+SQRT2/(2*(1<<F))

def ref_butterfly_mag(m,shift):
    return (2*m)/(1<<shift)

def prof(g,s):
    return {'FFT_amplitude_scale':g*s, 'RD_power_scale':(g*s)**2,
            'input_Float_LSB':g/(1<<15),
            'input_component_error_upper_no_clip':g/(1<<16),
            'input_complex_error_upper_no_clip':g*SQRT2/(1<<16)}

# exact-capture, conservative bounds based on quantized coeffs and no intermediate truncation.
base_formats={
 'A':{'mf':[22,15],'mti':[23,15],'fft':[28,15],'twiddle':[16,15]},
 'B':{'mf':[20,13],'mti':[21,13],'fft':[23,13],'twiddle':[14,13]},
 'C_hypothetical':{'mf':[22,15],'mti':[23,15],'fft':[25,15],'twiddle':[16,15]}}
res={'project':'AX309-RDSP-001','version':'v0.4','status':'PROPOSED_ARITHMETIC_NOT_APPROVED',
 'source_files':['decisions/S04-C01-ENGINEER-CONDITIONAL-SIGNOFF-v1.0.md',
 'engineering/S04-C02-COEFFICIENT-FFT-SHIFT-REVIEW-v0.3.md',
 'engineering/S04-C02-CFAR-AUDIT-REPAIR-v0.3.1.md'],
 'units':'normalized original Float complex amplitude for reconstructed errors; Q stored normalized arithmetic separately',
 'reference_semantics':'Float original x; pre-RNE scaled x/g; q=RNE(32768*x/g), SAT16; all following arithmetic in normalized stored q/32768; compare to unquantized x/g',
 'conditional_assumptions':['input sample component did not saturate; source original |x/g| <=1+2^-15 (loose bound)',
 'MF coefficients exactly the rounded table of v0.3; all internal products/sums untruncated until one output RNE per MF and MTI',
 'FFT radix2 DIT with bit-reversed input for natural bin ordering, quantized twiddles from v0.3, complex product exactly, butterfly sum exactly, shift is exact rational division by 2**s before one RNE',
 'all internal outputs remain representable: if margins are negative, error bound does not imply actual safe saturation',
 'No statistical behavior or RMS conclusion; broad triangle inequality and deterministic maximum bounds only'],
 'rounding_candidate':'RNE ties-to-even once per output, after exact multiply/sum and exact division by 2^shift; no internal saturation except explicitly detected output guard',
 'overflow_detection_candidate':'before narrowing compare unbounded rounded integer to signed W max/min; record tuple stage,index,component,sign,value; sticky flag. Do not permit silent wrap. NOT APPROVED',
 'summaries':{}}

# Unit-scale source error |xhat/g - x/g|, with input I/Q bounded in magnitude ±(1+2^-15) when no clip.
e0=SQRT2/(1<<16)
x0=SQRT2*(1+2**-15)
for name,c in base_formats.items():
 v=DATA['formats'][name]
 hsum=v['mf_coeff_sum_abs']
 e_coeff=x0*sum(x['abs_complex_error'] for x in v['mf16'])
 e_input=e0*hsum
 fmf=c['mf'][1];fmti=c['mti'][1];ffft=c['fft'][1]
 e_mf_round=SQRT2/(2*(1<<fmf));e_mti_round=SQRT2/(2*(1<<fmti))
 components={'input_Q15':e_input,'MF_coefficients':e_coeff,'MF_output_RNE':e_mf_round}
 mf_ref=x0*16
 mf_total=sum(components.values())
 mti_ref=2*mf_ref
 e_stage={'input_Q15':2*e_input,'MF_coefficients':2*e_coeff,
          'MF_output_RNE':2*e_mf_round,'MTI_output_RNE':e_mti_round}
 mti_total=sum(e_stage.values())
 all_sched={}
 for key,shifts in SHIFTS.items():
  comps=dict(e_stage)
  reference=mti_ref
  stage_details=[]
  initial_storage=v['mti_magnitude_growth_upper']+2*e_mf_round+e_mti_round
  storage=initial_storage
  for i,shift in enumerate(shifts):
   beta=v['twiddle_magnitude_by_stage_max'][i]
   delta=v['twiddle_abs_error_by_stage_max'][i]
   for k in list(comps):
    comps[k]*=(1+beta)/(1<<shift)
   new=delta*reference/(1<<shift)
   comps['FFT_twiddle_quantization']=comps.get('FFT_twiddle_quantization',0)+new
   rnd=SQRT2/(2*(1<<ffft))
   comps['FFT_output_RNE']=comps.get('FFT_output_RNE',0)+rnd
   reference=ref_butterfly_mag(reference,shift)
   storage=storage*(1+beta)/(1<<shift)+SQRT2/(2*(1<<ffft))
   headroom=bmax(c['fft'][0],ffft)-storage
   stage_details.append({'stage':i+1,'right_shift_bits':shift,
    'exact_pre_narrow_stored_magnitude_bound':storage,
    'positive_output_component_capacity':bmax(c['fft'][0],ffft),
    'positive_output_headroom_conditional':headroom,
    'candidate_output_W':c['fft'][0],'candidate_output_F':ffft,
    'reference_complex_error_components':dict(comps),
    'reference_complex_error_total_stored_units':sum(comps.values()),
    'rounding_location':'RNE after exact twiddle complex product, full butterfly sum and divide by 2**shift',
    'signed_shift_vs_RNE':'arithmetic right shift alone floors negative quotients and is NOT this RNE rounding rule'})
  s=1<<sum(shifts)
  err=sum(comps.values())
  all_sched[key]={'shifts':shifts,'scale':s,
   'FFT_magnitude_upper_stored_conditional':storage,
   'FFT_max_signed_output_headroom_conditional':stage_details[-1]['positive_output_headroom_conditional'],
   'all_stage_output_guards_positive':all(t['positive_output_headroom_conditional']>=0 for t in stage_details),
   'stage_details':stage_details,
   'error_components_stored_normalized':comps,
   'total_complex_error_stored_normalized':err,
   'reconstructed_original_Float_error_amplitude':{str(g):err*g*s for g in (1,5)},
   'source_reconstruction':{str(g):prof(g,s) for g in (1,5)},
   'input_error_included':True,'saturation_error_included':False,
   'guarantee_scope':'conditional on no clipping/no output guard violation, exact intermediate complex arithmetic, one RNE per stage; not a measured Float-vs-Fixed error'}
 output_W=c['fft'][0];tw_W=c['twiddle'][0]
 # Use per-stage input W: MTI before stage1, FFT result previous for stage2..5.
 stage_ops=[]
 for j in range(5):
  iw=c['mti'][0] if j==0 else c['fft'][0]
  input_F=c['mti'][1] if j==0 else c['fft'][1]
  twf=c['twiddle'][1]
  prodW=iw+tw_W
  pairW=prodW+1
  # align signed u to product fractional precision (Finput+Ftwiddle)
  aligned_u_W=iw+twf
  bfW=max(pairW,aligned_u_W)+1
  stage_ops.append({'stage':j+1,'input_signed_W':iw,'input_F':input_F,
   'twiddle_signed_W':tw_W,'twiddle_F':twf,
   'signed_real_product_W':prodW,'product_F':input_F+twf,
   'complex_real_pair_addsub_W':pairW,
   'u_branch_aligned_W':aligned_u_W,
   'pre_shift_butterfly_addsub_W_conservative':bfW,
   'pre_shift_F':input_F+twf,
   'candidate_output_W':output_W,'candidate_output_F':ffft,
   'intermediate_narrowing':'NONE before post-shift final RNE; proposed only',
   'actual_physical_registers_unapproved':True})
 res['summaries'][name]={'candidate_formats':c,
  'MF':{'signed_input_W_F':[16,15],'signed_coeff_W_F':v['metadata']['mf_coeff'],
   'real_product_signed_W':16+v['metadata']['mf_coeff'][0],
   'real_product_F':15+v['metadata']['mf_coeff'][1],
   'signed_complex_pair_W':17+v['metadata']['mf_coeff'][0],
   'signed_16tap_raw_accumulator_W':21+v['metadata']['mf_coeff'][0],
   'candidate_MF_output_W_F':c['mf'],
   'operation_order':'for each k: complex=(Ir*hr-Ii*hi)+j(Ir*hi+Ii*hr); sum 16 exact products; RNE each I/Q once at output; overflow flag before clip',
   'source_error_component':e_input,'coeff_error_component':e_coeff,
   'once_RNE_output_component':e_mf_round,'combined_conditional_error':mf_total,
   'max_abs_coefficient_model_bound':v['mf_magnitude_growth_upper']},
  'MTI':{'input_signed_W_F':c['mf'],'raw_subtract_W':c['mf'][0]+1,
   'candidate_output_W_F':c['mti'],'operation_order':'subtract consecutive MF complex output exact, then one RNE each component; overflow flag before clip',
   'combined_error_from_MF_plus_MTI_RNE':mti_total,
   'source_error_bound_without_clip':mti_ref},
  'FFT':{'butterfly':'DIT: t=what*v; outplus=u+t; outminus=u-t; full exact complex multiply and add/sub; divide by 2^s then one RNE to candidate output',
   'stage_word_proposals':stage_ops,'schedules':all_sched},
  'CFAR':CFAR['calculations'][name],
  'not_approved':True}
path=ROOT/'engineering/s04_numeric/S04-C02-internal-arithmetic-error-propagation-v0.4.json'
path.write_text(json.dumps(res,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('SHA256',hashlib.sha256(path.read_bytes()).hexdigest())
for opt,v in res['summaries'].items():
 print(opt,'MF-error',v['MF']['combined_conditional_error'],'MTI-error',v['MTI']['combined_error_from_MF_plus_MTI_RNE'])
 for k,x in v['FFT']['schedules'].items():
  print(k,'headroom',round(x['FFT_max_signed_output_headroom_conditional'],5),
   'err g1',round(x['reconstructed_original_Float_error_amplitude']['1'],8),
   'g5',round(x['reconstructed_original_Float_error_amplitude']['5'],8),
   'all stage fit',x['all_stage_output_guards_positive'])

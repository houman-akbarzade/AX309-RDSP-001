"""Deterministic coefficient and FFT bound audit: NO CPI, RNG, RTL or synthesis."""
import json, math, cmath, hashlib, datetime, importlib.util, sys
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from s03_reference import model as ref
import numpy as np

def ceilfrac(x):
    return -(-x.numerator//x.denominator)
def integer_width(bound,F,signed):
    """Include inclusive bound [0,M] or [-M,M] with exact q integer; rational M."""
    assert isinstance(bound,Fraction) and bound>=0 and isinstance(F,int) and F>=0
    limit=ceilfrac(bound*(1<<F))
    if signed: return max(2,1+limit.bit_length()) # signed maximum 2^(W-1)-1; inclusive +2^n requires W=n+2
    return max(1,limit.bit_length())
def bounds(W,F,signed):
    L=-(1<<(W-1)) if signed else 0
    U=(1<<(W-1))-1 if signed else (1<<W)-1
    return Fraction(L,1<<F),Fraction(U,1<<F)
def round_even(x):
    """Independent all-integer rational RNE, including negative half ties."""
    assert isinstance(x,Fraction)
    n,d=x.numerator,x.denominator
    a,r=divmod(abs(n),d)
    q=a+(r*2>d or (r*2==d and a%2==1))
    return int(q if n>=0 else -q)
def encode_component(value,W,F):
    rounded=round_even(Fraction(float(value))*(1<<F))
    return max(-(1<<(W-1)),min((1<<(W-1))-1,rounded))
def qcomp(z,W,F):
    return complex(encode_component(z.real,W,F),encode_component(z.imag,W,F))/(1<<F)
def e_metrics(exact,quant):
    e=quant-exact
    delta_phase=math.atan2(math.sin(cmath.phase(quant)-cmath.phase(exact)),math.cos(cmath.phase(quant)-cmath.phase(exact))) if abs(quant)>0 and abs(exact)>0 else None
    return {'re_error':e.real,'im_error':e.imag,'abs_complex_error':abs(e),
     'modulus_exact':abs(exact),'modulus_quantized':abs(quant),'modulus_error':abs(quant)-abs(exact),
     'phase_error_rad':delta_phase}
SQRT2_UPPER=Fraction(14142135623730951,10**16)
assert SQRT2_UPPER*SQRT2_UPPER>2
profiles={'NOISE_ONLY_UNIT':5,'SINGLE_TARGET_REFERENCE_LIKE_LAB':1}
formats={'A':{'mf_coeff':[16,15],'twiddle_candidate':[16,15],'stage_out':[28,15],'MF':[22,15],'MTI':[23,15],'sum40':[58,30],'power':[52,30],'alpha':[490007,16]},
 'B':{'mf_coeff':[14,13],'twiddle_candidate':[14,13],'stage_out':[23,13],'MF':[20,13],'MTI':[21,13],'sum40':[49,26],'power':[43,26],'alpha':[30625,12]},
 'C_hypothetical':{'mf_coeff':[16,15],'twiddle_candidate':[16,15],'stage_out':[25,15],'MF':[22,15],'MTI':[23,15],'sum40':[52,30],'power':[46,30],'alpha':[490007,16]}}
mf=[complex(x) for x in ref.matched_filter()]
assert len(mf)==16
# Radix2 DIT butterfly twiddles, stage m=2,4,8,16,32. FFT sign negative, numpy fft unnormalized.
tw={}
for stage in range(5):
 m=1<<(stage+1)
 tw[str(stage+1)]=[cmath.exp(-2j*math.pi*j/m) for j in range(m//2)]
schedule={'ZERO':[0,0,0,0,0],
 'EARLY_3':[1,1,1,0,0],
 'DISTRIBUTED_3':[0,1,0,1,1],
 'ALL_5':[1,1,1,1,1]}
res={'project':'AX309-RDSP-001','version':'S04-C02-v0.3','status':'ANALYTICAL_PROPOSED_NO_ARCHITECTURE_APPROVED',
 'sources':['s03_reference/model.py chirp/matched_filter', 'np.fft.fft unnormalized forward exponent negative', 'C01 g5/g1 immutable input'],
 'input_g_approved':profiles,'Q15_scale':'q*2^-15*g', 'rounding':'RNE candidate for coefficients and each post-shift; not engineer approved',
 'twiddle_rule':'Radix2 DIT stage m=2^s; j=0..m/2-1; exp(-i*2*pi*j/m); DIT bitreversal input required for natural order output',
 'reference_coefficients':{'mf16':[{'index':i,'re':z.real,'im':z.imag,'abs':abs(z),'phase_rad':cmath.phase(z)} for i,z in enumerate(mf)],
                          'fft32_twiddles':{key:[{'index':i,'re':z.real,'im':z.imag} for i,z in enumerate(vals)] for key,vals in tw.items()}},
 'formats':{},'schedules':{},'width_corrections':{},'risks':[
 'actual FFT twiddle intermediate multiplication and rounding topology is not approved',
 'coefficient error bounds below are conditional on exact arithmetic apart from indicated rounding sites',
 'REQ-SCR-01 and REQ-RNG-03 binding/open: no absolute clutter/paired-target magnitude or joint model',
 'stored-domain ideal coefficients not a proof of zero saturation or bittrue Pd']}
for name,f in formats.items():
 W,F=f['mf_coeff'];TW,TF=f['twiddle_candidate']
 mch=[qcomp(z,W,F) for z in mf]
 twq={k:[qcomp(z,TW,TF) for z in v] for k,v in tw.items()}
 mf_s=sum(abs(z) for z in mch)
 tw_beta=[max(abs(z) for z in twq[str(s)]) for s in range(1,6)]
 tw_delta=[max(abs(zz-z) for zz,z in zip(twq[str(s)],tw[str(s)])) for s in range(1,6)]
 mf_error=sum(abs(a-b) for a,b in zip(mch,mf))*float(SQRT2_UPPER)
 mf_bound=float(SQRT2_UPPER)*mf_s
 mti_bound=2*mf_bound
 # REAL component headroom must consider complex modulus bound, not percomponent tighter enclosure.
 fmtstage={}
 for k,M in [('MF',mf_bound),('MTI',mti_bound)]:
  w,fr=f[k]
  lim=bounds(w,fr,True)[1]
  fmtstage[k]={'stored_real_limit_max':float(lim),'complex_magnitude_bound':M,
                'fits_conditional_no_operation_rounding':float(lim)>=M,
                'positive_limit_margin':float(lim)-M}
 assert all(x['fits_conditional_no_operation_rounding'] for x in fmtstage.values())
 res['formats'][name]={'metadata':f,
   'mf16':[{'index':i,'stored_integer':[encode_component(z.real,W,F),encode_component(z.imag,W,F)],
             'reference': [z.real,z.imag],
             'decoded':[mch[i].real,mch[i].imag],**e_metrics(z,mch[i])}
            for i,z in enumerate(mf)],
   'twiddle32_by_stage':{str(s):[{'stage':s,'j':j,'stored_integer':[encode_component(z.real,TW,TF),encode_component(z.imag,TW,TF)],
           'decoded':[twq[str(s)][j].real,twq[str(s)][j].imag],**e_metrics(z,twq[str(s)][j])}
           for j,z in enumerate(tw[str(s)])] for s in range(1,6)},
   'mf_coeff_sum_abs':mf_s,'mf_coefficient_complex_abs_error_max':max(abs(z-q) for z,q in zip(mf,mch)),
   'mf_coefficient_error_bound_at_complex_input_magnitude_sqrt2':mf_error,
   'mf_magnitude_max':max(abs(z) for z in mch),
   'mf_magnitude_growth_upper':mf_bound,'mti_magnitude_growth_upper':mti_bound,
   'twiddle_magnitude_by_stage_max':tw_beta,'twiddle_abs_error_by_stage_max':tw_delta,
   'twiddle_max_magnitude':max(tw_beta),'twiddle_max_abs_error':max(tw_delta),
   'stage_output_saturation_margins':fmtstage,
   'raw_mf_component_product_bits':16+W,'raw_mf_real_pair_bits':17+W,
   'raw_mf_accum16_bits':21+W,'raw_mf_accum16_fractional_bits':15+F,
   'raw_fft_twiddle_component_product_bits':f['stage_out'][0]+TW,
   'raw_fft_twiddle_real_pair_bits':f['stage_out'][0]+TW+1,
   'source_reconstruction_factor':{k:g for k,g in profiles.items()},
   'not_approved':True}
 for sched,shifts in schedule.items():
  growth=[mti_bound]; inputs=[]; stage=[]
  nominal_prev=mti_bound
  for idx,sh in enumerate(shifts):
   # quantized coefficient modulus bound, no numerical operation rounding
   upper=nominal_prev*(1+tw_beta[idx])/2**sh
   Wout,Fout=f['stage_out']
   Wmin=integer_width(Fraction.from_float(upper),Fout,True)
   mpos=float(bounds(Wout,Fout,True)[1])
   delta=tw_delta[idx]
   # error recursion: old error amplification and coefficient disturbance; excludes arithmetic rounding
   inputs.append({'previous_max':nominal_prev,'beta':tw_beta[idx],
                  'delta_twiddle_max':delta,'shift':sh})
   stage.append({'stage':idx+1,'shift':sh,'complex_magnitude_upper_if_exact_ops':upper,
      'minimum_signed_W_at_Foutput':Wmin,'candidate_stage_out_W':Wout,
      'candidate_stage_out_F':Fout,'representable_positive_component_max':mpos,
      'candidate_stage_output_margin':mpos-upper,'candidate_stage_fits':upper<=mpos,
      'rounding_sites_per_complex_butterfly_if_implementing_candidate':'post twiddle product and optional right shift; exact order OPEN',
      'error_model_coeff_component_max':delta,'candidate_post_stage_RNE_max_component_error':2**(-Fout-1), 'candidate_post_stage_RNE_max_complex_error':math.sqrt(2)*2**(-Fout-1), 'error_model_operation_rounding':'Exact complex ops then one post-stage RNE only; actual multiplier narrowing topology OPEN'})
   nominal_prev=upper
  # twiddle error to ideal FFT with exact arithmetic except coefficients
  error=0.
  value=mti_bound
  err_trace=[]
  for j,sh in enumerate(shifts):
   err_prev=error
   error=((1+tw_beta[j])*error+tw_delta[j]*value)/2**sh
   value=(1+tw_beta[j])*value/2**sh
   err_trace.append({'stage':j+1,'error_upper_from_twiddle_only':error,'operator_rounding_excluded':True})
  scale=2**sum(shifts)
  # conditional analytic propagated error, assuming exact MF/MTI arithmetic
  # followed by one output RNE, plus exact FFT twiddle product then one RNE/stage.
  mf_err=float(SQRT2_UPPER)*sum(abs(a-b) for a,b in zip(mch,mf))+math.sqrt(2)*2**(-f['MF'][1]-1)
  mti_err=2*mf_err+math.sqrt(2)*2**(-f['MTI'][1]-1)
  e_round=mti_err
  m_ideal=32*float(SQRT2_UPPER)
  e_round_trace=[]
  for j,sh in enumerate(shifts):
   beta_j=tw_beta[j]; delta_j=tw_delta[j]
   e_round=((1+beta_j)*e_round+delta_j*m_ideal)/2**sh+math.sqrt(2)*2**(-f['stage_out'][1]-1)
   m_ideal=2*m_ideal/2**sh
   e_round_trace.append({'stage':j+1,'cumulative_error_conditional':e_round,'ideal_unit_twiddle_input_bound':m_ideal})
  res['schedules'].setdefault(sched,{'shifts':shifts,'FFT_normalization':scale,'reconstruction':{
     k:{'FFT_amplitude_scale':g*scale,'power_scale':(g*scale)**2} for k,g in profiles.items()},'per_architecture':{}})
  res['schedules'][sched]['per_architecture'][name]={
    'stage':stage,'fft_output_magnitude_bound':nominal_prev,
    'twiddle_only_error_bound_from_mti_input':error,
    'twiddle_error_traces':err_trace,'conditional_MF_MTI_quantization_plus_FFT_one_RNE_each_stage_error_bound':e_round,'conditional_error_stage_trace':e_round_trace,
    'all_stages_fit_candidate_output_format':all(s['candidate_stage_fits'] for s in stage)}
# exact maximum when all-real coefficient |x| <=1 magnitude uses modulus based headroom
res['CFAR']={}
for name,f in formats.items():
 WP,FP=f['power']; WS,FS=f['sum40']; A,FA=f['alpha']
 # full squares per signed FFT q: 2*W bit, addition +1; power width may narrow.
 WFFT,Ffft=f['stage_out']
 exact_real_product=2*WFFT
 raw_complex_square_sum=exact_real_product+1
 # alpha coefficient numerator width fixed; crossproduct max bounds conservative
 left_width=WP+6+FA
 right_width=WS+f['alpha'][0]
 cutoff={'A':490007,'B':30625,'C_hypothetical':490007}[name]
 assert cutoff==A
 res['CFAR'][name]={'input_F_FFT':Ffft,
   'power_stored_width':WP,'power_frac':FP,
   'raw_exact_real_square_product_bits':exact_real_product,
   'raw_exact_I2_plus_Q2_bits':raw_complex_square_sum,
   'sum40_stored_width':WS,'sum40_frac':FS,
   'sum40_exact_growth_bits_conservative':WP+math.ceil(math.log2(40)),
   'alpha_numerator':A,'alpha_frac':FA,
   'integer_compare_left_width_conservative':left_width,
   'integer_compare_right_width_conservative':right_width,
   'strict_equality_is_no_alarm':not(40*A*(1<<FA)>A*(40*(1<<FA))),
   'threshold_minus_one': 40*(A-1)*(1<<FA)>A*(40*(1<<FA)),
   'threshold_plus_one': 40*(A+1)*(1<<FA)>A*(40*(1<<FA)),
   'no_float_fixed_decision_qualification':True}
res['width_corrections']={
 'previous_signed_float_log_expression':'F+1+ceil(log2(M+2^-F)), sensitive to float boundary rounding and symmetry constraints',
 'previous_unsigned_expression':'F+floor(log2(M))+1, correct only for positive real M with careful exact powers and boundary handling; floating log can mis-round',
 'correct_exact_continuous_envelope':'Qreq=ceil(M*2^F); unsigned W=max(1,Qreq.bit_length()); signed W=max(2,1+Qreq.bit_length()) for continuous [-M,M] enclosing quantizer values',
 'explicit_quantized_integer_bound':'for raw integer bound K>=0 exact: unsigned W=max(1,K.bit_length()), signed symmetric W=max(2,1+K.bit_length())',
 'negative_minimum_note':'signed min -2^(W-1) representable; +2^(W-1) NOT, hence symmetric +/-2^(W-1) needs W+1',
 'legacy_numeric_tables':'v0.2 computed main ideal numeric boundary widths were rechecked; differences or loose bounds listed in report; v0.2 files preserved'}
out=Path(__file__).with_name('S04-C02-coeff-shift-quant-analysis-v0.3.json')
out.write_text(json.dumps(res,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
print('SHA',hashlib.sha256(out.read_bytes()).hexdigest())
print('MF',[(k,round(v['mf_magnitude_max'],9),round(v['mf_magnitude_growth_upper'],9),round(v['mf_coefficient_abs_error_max'],9) if 'mf_coefficient_abs_error_max' in v else v['mf_coefficient_complex_abs_error_max']) for k,v in res['formats'].items()])
for k,c in res['schedules'].items():
 print('FFT',k,c['FFT_normalization'],[(name,round(v['fft_output_magnitude_bound'],5),v['all_stages_fit_candidate_output_format']) for name,v in c['per_architecture'].items()])

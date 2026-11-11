"""Exact-integer CFAR width repair. No stochastic CPI, no S03 acceptance use."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
from datetime import datetime,timezone

DIR=Path(__file__).resolve().parent
SOURCE=json.loads((DIR/'S04-C02-coeff-shift-quant-analysis-v0.3.json').read_text())
CONFIG={
 'A':{'fftW':28,'F':15,'powerW':52,'sumW':58,'alphaW':20,'alphaNum':490007,'alphaF':16},
 'B':{'fftW':23,'F':13,'powerW':43,'sumW':49,'alphaW':16,'alphaNum':30625,'alphaF':12},
 'C_hypothetical':{'fftW':25,'F':15,'powerW':46,'sumW':52,'alphaW':20,'alphaNum':490007,'alphaF':16}}
def bits(n):
    assert isinstance(n,int) and n>=0
    return max(1,n.bit_length())
def check(x,b):
    return 0<=x<(1<<b)
def oracle(cut,training_sum,a,f):
    return Fraction(40*cut,1)>Fraction(a*training_sum,1<<f)

def build():
 result={'project':'AX309-RDSP-001','version':'v0.3.1','status':'REPAIR_ONLY_NO_NUMERIC_ARCHITECTURE_APPROVED',
  'source_v03_sha256':hashlib.sha256((DIR/'S04-C02-coeff-shift-quant-analysis-v0.3.json').read_bytes()).hexdigest(),
  'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
  'equation':'40*Pcut*(2**alphaF) > alphaNum*SUM40, strict equality false',
  'calculations':{},'error_coverage':{
   'input_Q1_15':'EXCLUDED from reported v0.3 FFT error; reference origin is decoded post-input-Q1.15 stored samples, not original Float IQ',
   'input_g':'Reconstructed scale g*SFFT: approved g=5 noise-only or g=1 lab target; error in reconstructed Float amplitude requires multiply by g*SFFT',
   'MF_coefficient_quantization':'INCLUDED in combined conditional error, excluded in twiddle-only error',
   'MF_output_one_RNE':'INCLUDED in combined conditional estimate assuming exact MF internal products/sum',
   'MTI_one_RNE':'INCLUDED in combined conditional estimate assuming exact MTI subtraction',
   'twiddle_quantization':'INCLUDED in both conditional and twiddle-only estimates',
   'FFT_post_stage_one_RNE':'INCLUDED only in combined conditional estimate',
   'internal_twiddle_multiplication_rounding':'OPEN: exact complex multiply assumed; widths/rounding sites not fixed',
   'butterfly_internal_add_sub_rounding':'OPEN: exact add/sub assumed until one post-stage output RNE',
   'shift_implementation_rounding':'OPEN: modeled ideal divide then one RNE, not proven equivalent to actual signed shift and ties',
   'saturation_and_overflow':'OPEN: conditional no saturation, no wrapped intermediates; neither stage nor full pipeline certified',
   'MF_MTI_intermediate_products_and_accumulators':'OPEN: v0.3 assumes exact operations before one narrowing step',
   'actual_stagewise_fft_W_F':'OPEN: proxy uses final stage W/F at each stage, not a selected internal schedule',
   'float_source_chirp_roundoff':'Not included as independent high-precision oracle; S03 binary64 coefficients treated as reference'
  }}
 for name,c in CONFIG.items():
  w=c['fftW']; p=c['powerW']; s=c['sumW']; aw=c['alphaW']; a=c['alphaNum']; fa=c['alphaF']
  assert bits(a)<=aw
  source=SOURCE['CFAR'][name]
  # Case 1 narrowed candidate-power/SUM40 stored, each treated as unsigned independent legal value
  Pmax=(1<<p)-1; Smax=(1<<s)-1
  Lmax=40*Pmax*(1<<fa); Rmax=a*Smax
  narrow={'Pcut_max':Pmax,'SUM40_max':Smax,
   'max_left_product':Lmax,'max_right_product':Rmax,
   'left_exact_bits':bits(Lmax),'right_exact_bits':bits(Rmax),
   'left_conservative_bits':p+6+fa,'right_conservative_bits':s+aw,
   'left_fits_conservative':check(Lmax,p+6+fa),
   'right_fits_conservative':check(Rmax,s+aw)}
  # Case 2 full precision raw (conservative "two signed W inputs squared + added" W=2w+1).
  # actual max when both signed components equal -2^(w-1), each exactly squared
  X=(1<<(w-1))
  raw_power_max=2*X*X
  raw_sum_max=40*raw_power_max
  raw_power_proxy_bits=2*w+1
  raw_sum_proxy_bits=raw_power_proxy_bits+6
  LRmax=40*raw_power_max*(1<<fa)
  RRmax=a*raw_sum_max
  full={'max_abs_signed_fft_integer':X,'raw_exact_I2_plus_Q2_max':raw_power_max,
   'raw_exact_SUM40_max':raw_sum_max,
   'raw_power_conservative_bits':raw_power_proxy_bits,
   'raw_sum40_conservative_bits':raw_sum_proxy_bits,
   'raw_power_exact_bits':bits(raw_power_max),
   'raw_sum_exact_bits':bits(raw_sum_max),
   'left_exact_bits':bits(LRmax),'right_exact_bits':bits(RRmax),
   'left_conservative_bits':raw_power_proxy_bits+6+fa,
   'right_conservative_bits':raw_sum_proxy_bits+aw,
   'max_left_product':LRmax,'max_right_product':RRmax}
  tests={}
  for cut,S in [(0,0),(0,1),(Pmax,0),(0,Smax),(Pmax,Smax),
                (Pmax,40*Pmax if check(40*Pmax,s) else Smax)]:
   tests[f'CUT{cut}_SUM{S}']={'CUT':cut,'SUM40':S,'integer_decision':40*cut*(1<<fa)>a*S,
    'fraction_oracle':oracle(cut,S,a,fa)}
   assert tests[f'CUT{cut}_SUM{S}']['integer_decision']==tests[f'CUT{cut}_SUM{S}']['fraction_oracle']
  # Near threshold choose SUM40=40*2^fa, CUT=A-1,A,A+1, if CUT fits (all do)
  S=40*(1<<fa)
  for offset in (-1,0,1):
   CUT=a+offset
   assert CUT<=Pmax and S<=Smax
   key=f'exact_threshold_offset_{offset:+d}'
   tests[key]={'CUT':CUT,'SUM40':S,'decision':40*CUT*(1<<fa)>a*S,
    'exact_fraction_oracle':oracle(CUT,S,a,fa)}
   assert tests[key]['decision']==(offset>0)
  assert narrow['left_fits_conservative'] and narrow['right_fits_conservative']
  assert full['left_conservative_bits']>=full['left_exact_bits']
  assert full['right_conservative_bits']>=full['right_exact_bits']
  result['calculations'][name]={
   'config':c,'v03_recorded_left_bits':source['integer_compare_left_width_conservative'],
   'v03_wrong_right_bits':source['integer_compare_right_width_conservative'],
   'root_cause':'right_width=WS+f[alpha][0] added alpha numerator rather than alpha declared W (f[alpha][0]=numerator)',
   'post_narrowing_candidate_operands':narrow,'full_precision_pre_narrowing_path':full,
   'boundary_examples':tests,'fixed_point_qualification':False}
 return result

if __name__=='__main__':
 value=build()
 out=DIR/'S04-C02-cfar-width-arithmetic-audit-v0.3.1.json'
 out.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
 print('SHA256',hashlib.sha256(out.read_bytes()).hexdigest())
 for name,d in value['calculations'].items():
  n=d['post_narrowing_candidate_operands'];f=d['full_precision_pre_narrowing_path']
  print(name,'v03 erroneous',d['v03_wrong_right_bits'],
   'narrow proposed',n['left_conservative_bits'],n['right_conservative_bits'],
   'narrow exact',n['left_exact_bits'],n['right_exact_bits'],
   'full proposed',f['left_conservative_bits'],f['right_conservative_bits'],
   'full exact',f['left_exact_bits'],f['right_exact_bits'])

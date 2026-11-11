"""Only rational/int analytical design arithmetic. Does NOT import S03 generator or use RNG."""
import json
import math
from fractions import Fraction
from pathlib import Path
from datetime import datetime,timezone
import hashlib

def round_even(n,d):
    if d <= 0: raise ValueError('positive denominator needed')
    q,r=divmod(n,d)
    if 2*r> d or (2*r ==d and q%2):q+=1
    return q

def cmp_cross(cut, training_sum, scaled_alpha, frac):
    return 40*cut*(1<<frac)>scaled_alpha*training_sum

def oracle(cut, training_sum, a):
    return Fraction(cut,1)>a*Fraction(training_sum,40)

def calc():
    alpha=Fraction('7.476912055027923')
    assert round_even(-3,2)==-2 and round_even(-1,2)==0
    assert round_even(1,2)==0 and round_even(3,2)==2
    assert (-3 >> 1)==-2 and (-1 >> 1)==-1
    result={
        'purpose':'ANALYTICAL_ONLY_NO_CPI_NO_RNG_NO_BITTRUE_MODEL',
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'source_alpha_decimal':'7.476912055027923',
        'alpha_as_decimal_fraction':str(alpha),
        'float_reference_alpha_warning':'Decimal spelling corresponds to pinned printed value, not exact binary64 multiplier semantics.',
        'frozen_signal_parameters':{'input_component_bound':'[-1,1) for candidate signed Q1.15, NOT a bound on unquantized Gaussian stimulus',
          'mf_taps':16,'mti_difference_terms':2,'fft_points':32,'cfar_training_cells':40,'fft_stages_radix2':5},
        'conservative_magnitude_bounds':{
          'input_complex_magnitude':math.sqrt(2),
          'mf_complex_magnitude':16*math.sqrt(2),
          'mti_complex_magnitude':32*math.sqrt(2),
          'fft_unscaled_complex_magnitude':1024*math.sqrt(2),
          'power':2097152,
          '40cell_power_sum':83886080
        },
        'rounding_examples':{str(k):round_even(k,2) for k in [-5,-3,-1,1,3,5]},
        'arithmetic_right_shift_examples':{str(k):k>>1 for k in [-5,-3,-1,1,3,5]},
        'hardware_cost_is_provisional':True,
        'candidates':{},
        'cfar_integer_oracle_checks':{},
    }
    options={
      'A':{'coefficient_F':15,'signal_stage_F':15,'fft_scale':1,'alpha_F':16,'formats':{'IQ':[16,15],'coeff':[16,15],'MF':[22,15],'MTI':[23,15],'FFT':[28,15],'power':[52,30],'train_sum':[58,30],'alpha':[20,16]}},
      'B':{'coefficient_F':13,'signal_stage_F':13,'fft_scale':8,'alpha_F':12,'formats':{'IQ':[16,15],'coeff':[14,13],'MF':[20,13],'MTI':[21,13],'FFT':[23,13],'power':[43,26],'train_sum':[49,26],'alpha':[16,12]}},
    }
    for name,opt in options.items():
        fac=1<<opt['alpha_F']
        num=round_even(alpha.numerator*fac,alpha.denominator)
        aq=Fraction(num,fac)
        err=aq-alpha
        opt['alpha_integer']=num
        opt['alpha_quantized_rational']=str(aq)
        opt['alpha_error_signed']=float(err)
        opt['alpha_error_bound_nearest']=float(Fraction(1,2*fac))
        opt['cfar_cross_product_bits_conservative']={'left_W':opt['formats']['power'][0]+6+opt['alpha_F'],
           'right_W':opt['formats']['train_sum'][0]+opt['formats']['alpha'][0]}
        # These are only component-amplitude rounding budgets, ignoring TWIDDLE errors,
        # additional stage shifts, saturation and reference-input clipping; NOT acceptance limits.
        xi=math.sqrt(2)*2**(-16)
        hc=math.sqrt(2)*2**(-(opt['coefficient_F']+1))
        e_quant=math.sqrt(2)*2**(-(opt['signal_stage_F']+1))
        mf=16*(xi+math.sqrt(2)*hc+xi*hc+e_quant)
        mt=2*mf+e_quant
        fft=(32/opt['fft_scale'])*mt+31*e_quant
        boundfft=1024*math.sqrt(2)/opt['fft_scale']
        epower=2*boundfft*fft+fft**2
        ealpha=float(abs(err))
        # This is a guide for native-scaled comparator margin; excludes FFT twiddle error.
        emargin=(1+float(alpha))*epower+ealpha*(2097152/(opt['fft_scale']**2)+epower)
        opt['INCOMPLETE_error_calculus_not_for_approval']={
            'mf_component_magnitude_e_upper':mf,
            'mti_component_magnitude_e_upper':mt,
            'fft_component_magnitude_e_upper_missing_twiddle_and_shift_rounding':fft,
            'power_abs_e_upper_missing_twiddle_and_shift_rounding':epower,
            'CFAR_margin_abs_e_upper_missing_twiddle_and_shift_rounding':emargin,
            'reason':'Ignores FFT twiddle quantization, actual butterfly rescale/round sites, saturation and actual distributions; no certified bound or RMS result.'
        }
        result['candidates'][name]=opt
        tests=[]
        for cut,train in [(0,0),(0,40),(1,0),(3,40),(7,40),(8,40),(1000,40),(2048,1000)]:
            exact_integer=cmp_cross(cut,train,num,opt['alpha_F'])
            rat=oracle(cut,train,aq)
            assert exact_integer==rat
            tests.append({'CUT':cut,'train_sum':train,'cross_product':exact_integer,'rational_oracle':rat})
        # exact tie is representable for positive training sum.
        cut_eq=num
        sum_eq=40*fac
        for offset in (-1,0,1):
            cut=cut_eq+offset
            c=cmp_cross(cut,sum_eq,num,opt['alpha_F'])
            rat=oracle(cut,sum_eq,aq)
            assert c==rat and c==(offset>0)
            tests.append({'CUT':cut,'train_sum':sum_eq,'relation':'below' if offset<0 else 'equal' if offset==0 else 'above',
                          'cross_product':c,'rational_oracle':rat,'exact_threshold_tie':offset==0})
        result['cfar_integer_oracle_checks'][name]=tests
    assert len(result['cfar_integer_oracle_checks']['A'])==11
    assert len(result['cfar_integer_oracle_checks']['B'])==11
    result['integer_vs_fraction_checks_passed']=22
    return result

if __name__=='__main__':
    result=calc()
    dest=Path(__file__).parent/'S04-numeric-independent-arithmetic-v0.2.json'
    dest.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
    print('ANALYTICAL_AUDIT_PASS',result['integer_vs_fraction_checks_passed'],'checks')
    for name,c in result['candidates'].items():
        print(name,'alpha',c['alpha_integer'],c['alpha_quantized_rational'],'delta',c['alpha_error_signed'],
              'comparator_widths',c['cfar_cross_product_bits_conservative'])
    print('OUTPUT',dest,'SHA256',hashlib.sha256(dest.read_bytes()).hexdigest())

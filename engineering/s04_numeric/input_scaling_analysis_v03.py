"""S04 input scaling mathematical audit: no RNG, source CPI, or model import."""
import cmath
import hashlib
import json
import math
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.special import log_ndtr, logsumexp

N_PULSES = 33
N_RANGE = 128
N_COMPONENTS = 2*N_PULSES*N_RANGE
IQ_F = 15
IQ_QMAX = (1 << 15)-1
IQ_QMIN = -(1 << 15)
UPPER = Fraction(65535, 65536)
LOWER = Fraction(-65537, 65536)
SIGMA2_NOISE_ONLY_COMPLEX = 1.0
SIGMA2_PD_COMPLEX = 0.000324

def nearest_even_rational(x):
    x=Fraction(x)
    q,r=divmod(x.numerator,x.denominator)
    return q+int(2*r>x.denominator or (2*r==x.denominator and (q&1)==1))

def encode_component(x, g):
    if Fraction(g)<=0:
        raise ValueError('scale must be positive')
    raw=nearest_even_rational(Fraction(x)*32768/Fraction(g))
    clipped=raw < IQ_QMIN or raw > IQ_QMAX
    return max(IQ_QMIN,min(IQ_QMAX,raw)), clipped, raw

def decode_component(q, g):
    return Fraction(g)*Fraction(q,32768)

def cpi_component_means_pd():
    # Fully deterministic means, not stochastic IQ sampling; exactly mirrors the
    # S03 fixed single target waveform and pulse Doppler convention.
    out=np.zeros((N_PULSES,N_RANGE),dtype=np.complex128)
    for m in range(N_PULSES):
        for j in range(16):
            t=(j+.5)/1_000_000.0
            phase=2*math.pi*((-250000/2)*t+.5*(250000/(16/1_000_000))*t*t)
            fd=2*1.875*10_000_000_000/300_000_000
            out[m,40+j]=.18*cmath.exp(1j*(phase+2*math.pi*fd*m*.001))
    return out

def to_component_means(x):
    return np.stack((np.asarray(x).real,np.asarray(x).imag),axis=-1).reshape(-1)

def gaussian_saturation(mu, variance_complex, g):
    sigma=math.sqrt(variance_complex/2)
    u=float(UPPER)*g
    l=float(LOWER)*g
    log_upper=log_ndtr((mu-u)/sigma)  # Pr(X >= u), equality measure zero
    log_lower=log_ndtr((l-mu)/sigma)  # Pr(X < l)
    lp=np.logaddexp(log_upper,log_lower)
    log_expect=float(logsumexp(lp))
    expected=float(math.exp(log_expect)) if log_expect > -740 else 0.0
    p=np.exp(lp)
    # Conditional independence of REAL and IMAG Gaussian noise components and CPI
    # input samples; not a claim about post-DSP independent samples.
    if np.any(p>=1):
        log_prob_any=0.0
    elif log_expect < -36:
        log_prob_any=log_expect
    else:
        log_no=float(np.log1p(-p).sum())
        log_prob_any=math.log(-math.expm1(log_no)) if log_no<0 else -math.inf
    pany=float(math.exp(log_prob_any)) if log_prob_any>-740 else 0.0
    return {'g':g,'threshold_float_upper_inclusive':u,
            'threshold_float_lower_exclusive':l,
            'expected_saturated_components':expected,
            'log10_expected_saturated_components':log_expect/math.log(10),
            'prob_at_least_one_saturation':pany,
            'log10_prob_at_least_one_saturation':log_prob_any/math.log(10),
            'probability_model':'independent Gaussian noise components conditional on deterministic scene',
            'component_count':len(mu)}

def boundary_scale_map(option, g):
    # Maps integer stage to original unscaled Float signal units; power scales
    # must use the squared input and FFT factors. Pure metadata calculation.
    if option not in ('A','B') or Fraction(g)<=0:
        raise ValueError('unsupported candidate or scale')
    gf=Fraction(g)
    sf=Fraction(1 if option=='A' else 8)
    power=gf*gf*sf*sf
    return {'B00_float':Fraction(1), 'B01_IQ':gf, 'B02_tap':Fraction(1),
            'B03_MF':gf, 'B04_MTI':gf,'B05_FFT':gf*sf,
            'B06_RD_power':power,'B07_training_sum40':power,
            'B08_training_mean':power,'B08_threshold':power,
            'B09_alarm_flag':None,'B10_selected_peak_power':power,
            'B11_target_amplitude':gf,'B11_range_m':Fraction(1),
            'B11_velocity_m_s':Fraction(1),'B12_serialization':None}


def test_all_boundary_scales():
    checks=0
    for option in ('A','B'):
        s=1 if option=='A' else 8
        for g in (Fraction(1),Fraction(2),Fraction(4),Fraction(8)):
            m=boundary_scale_map(option,g)
            assert m['B01_IQ']==m['B03_MF']==m['B04_MTI']==g
            assert m['B02_tap']==1
            assert m['B05_FFT']==g*s
            assert m['B06_RD_power']==m['B05_FFT']**2
            assert m['B07_training_sum40']==m['B06_RD_power']
            assert m['B08_training_mean']==m['B08_threshold']==m['B07_training_sum40']
            assert m['B10_selected_peak_power']==m['B06_RD_power']
            assert m['B11_target_amplitude']==g
            assert m['B11_range_m']==m['B11_velocity_m_s']==1
            assert m['B09_alarm_flag'] is None and m['B12_serialization'] is None
            checks+=15
    assert checks==120
    return checks


def test_exact_endpoints():
    checks=0
    delta=Fraction(1,1<<30)
    for g in [Fraction(1),Fraction(4)]:
        for x,sat,want in [
            (g*(UPPER-delta),False,IQ_QMAX),
            (g*UPPER,True,IQ_QMAX),
            (g*(UPPER+delta),True,IQ_QMAX),
            (g*LOWER,False,IQ_QMIN),
            (g*(LOWER-delta),True,IQ_QMIN),
            (g*(LOWER+delta),False,IQ_QMIN)]:
            q,c,raw=encode_component(x,g)
            assert c==sat and q==want,(g,x,q,c,want,sat)
            checks+=1
        for x,qwant in [(Fraction(1,65536),0),(Fraction(-1,65536),0),
                         (Fraction(3,65536),2),(Fraction(-3,65536),-2)]:
            q,c,_=encode_component(x*g,g)
            assert not c and q==qwant
            assert decode_component(q,g)==Fraction(qwant,32768)*g
            checks+=1
    assert checks==20
    return checks

def test_stored_reconstructed():
    tests=0
    # A: stored scalings are IQ g; MF/MTI/FFT g; power and sum g^2.
    # B: IQ/MF/MTI g; FFT g*8; power/sum g^2*64.
    for label,ff,sp in [('A',15,1),('B',13,8)]:
        for g in [Fraction(1),Fraction(4),Fraction(8)]:
            qi,qj=4000,-2000
            stored_complex=complex(qi,qj)/float(1<<ff)
            decoded_complex=stored_complex*float(g*sp)
            stored_power=Fraction(qi*qi+qj*qj,1<<(2*ff))
            decoded_power=stored_power*g*g*sp*sp
            check_complex=Fraction(qi,1<<ff)*g*sp
            assert math.isclose(decoded_complex.real,float(check_complex))
            assert decoded_power == (Fraction(qi,1<<ff)**2+
                                     Fraction(qj,1<<ff)**2)*g*g*sp*sp
            # Integer power encoding (Fpower=2*Ffft) is exact before narrowing.
            # Strict CFAR decisions cancel common power scale algebraically.
            alpha_int=490007 if label=='A' else 30625
            alpha_frac=16 if label=='A' else 12
            for p,t in [(100,40),(0,0),(alpha_int,40*(1<<alpha_frac)),
                        (alpha_int+1,40*(1<<alpha_frac))]:
                c=40*p*(1<<alpha_frac)>alpha_int*t
                reference=Fraction(p)*g*g*sp*sp > (
                    Fraction(alpha_int,1<<alpha_frac)*
                    Fraction(t,40)*g*g*sp*sp)
                assert c==reference
                tests+=1
            tests+=2
    assert tests==36
    return tests

def main():
    iq=np.zeros((N_PULSES,N_RANGE),dtype=np.complex128)
    pd=cpi_component_means_pd()
    sigma=.000324
    # Separate illustrative deterministic clutter offsets; no stochastic scene generated.
    scenes={'noise_only_CN_0_1':(to_component_means(iq),1.0),
            'pd_fixed_scene_analytic_mean_CN_0_000324':(to_component_means(pd),sigma),
            'pd_plus_deterministic_clutter_0p8_complex':(
                to_component_means(pd+(.8+0j)),sigma),
            'pd_plus_deterministic_clutter_1p2_complex':(
                to_component_means(pd+(1.2+0j)),sigma)}
    totals={}
    for scene,(mu,variance) in scenes.items():
        totals[scene]={'variance_complex':variance,
             'mean_definition': 'noise-only zero means' if scene=='noise_only_CN_0_1'
             else ('S03 fixed target waveform analytic mean, no random realization'
                if 'clutter' not in scene else
                'S03 target analytic means plus illustrative deterministic uniform clutter'),
             'scales':{str(g):gaussian_saturation(mu,variance,g) for g in (1,2,4,8)}}
    counts={'exact_quantizer_boundaries':test_exact_endpoints(),
            'stored_reconstructed_domain':test_stored_reconstructed(),
            'boundary_metadata_consistency':test_all_boundary_scales()}
    assert sum(counts.values())==176
    output={'status':'DETERMINISTIC_ANALYSIS_ONLY','timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'no_rng_no_CPI_samples':True,
        'n_complex_samples':N_PULSES*N_RANGE,'n_IQ_real_components':N_COMPONENTS,
        'q15_thresholds_exact':{'upper_inclusive':str(UPPER),
                               'lower_exclusive':str(LOWER),
                               'upper_raw_integer':32768,
                               'lower_raw_integer_at_threshold':-32768},
        'conditional_independence_note':'Probability of any clipping assumes independent Gaussian real/imag noise components conditional on a frozen deterministic mean; stochastic correlated clutter cannot use product formula without conditional model.',
        'scenarios':totals,
        'exact_tests_passed':counts,
        'stored_to_reconstructed_scale_maps':{
            opt:{str(g):{k:(str(v) if v is not None else None)
                  for k,v in boundary_scale_map(opt,Fraction(g)).items()}
                 for g in (1,2,4,8)} for opt in ('A','B')},
        'scale_metadata_options':{'fixed':'frozen g for a declared input population',
                                  'configurable':'explicit pre-CPI g, metadata and calibration',
                                  'adaptive':'data-dependent g must be frozen as an algorithm and retains decision/selection metadata; distribution transfer needs new qualification'},
        'not_approved':['input_scale','A_B_choice','FFT_shift','numeric_acceptance_thresholds']}
    path=Path(__file__).with_name('S04-input-scaling-analytic-v0.3.json')
    path.write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
    print('DETERMINISTIC_TESTS_PASS',counts)
    for k,v in totals.items():
        print('SCENE',k)
        for scale in ['1','2','4','8']:
            a=v['scales'][scale]
            print(' g',scale,'E_clip',a['expected_saturated_components'],
                'log10E',round(a['log10_expected_saturated_components'],4),
                'Pany',a['prob_at_least_one_saturation'],
                'log10Pany',round(a['log10_prob_at_least_one_saturation'],4))
    print('OUTPUT_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    main()

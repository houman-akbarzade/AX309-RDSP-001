"""S04 C02 v0.2 deterministic range, unit, storage and comparator arithmetic.
NO random generator, CPI inputs or hardware/RTL. Design estimates only.
"""
import json,math,hashlib,datetime
from pathlib import Path
from fractions import Fraction

OUT=Path(__file__).with_name('S04-C02-range-bitgrowth-v0.2.json')
L=16; K=2; N=32; TRAIN=40
def signed_w(M,F):
    """Smallest W at F fractional bits for signed representable +/- M envelope."""
    return F+1+math.ceil(math.log2(M+2**(-F))) if M>0 else F+1
def unsigned_w(M,F):
    """Smallest unsigned word W at F fractional bits including nonnegative M."""
    return F+math.floor(math.log2(M))+1 if M>0 else F+1
def stage_bound(g,scale):
    # g is Float-domain reconstruction factor, not integer headroom:
    # input I,Q after SATQ15 each bounded in [-1,1); h is unit modulus.
    x=math.sqrt(2)
    mf=L*x; mti=K*mf; fft=N*mti/scale
    p=fft**2; tsum=TRAIN*p
    return {'g':g,'fft_shift_scale':scale,
     'input_complex_mag_bound_stored':x,'MF_abs_component_conservative_stored':mf,
     'MTI_abs_component_conservative_stored':mti,'FFT_abs_component_conservative_stored':fft,
     'RD_power_conservative_stored':p,'CA_CFAR_sum40_conservative_stored':tsum,
     'MF_min_W_F15':signed_w(mf,15),'MTI_min_W_F15':signed_w(mti,15),
     'FFT_min_W_F15':signed_w(fft,15),'FFT_min_W_F13':signed_w(fft,13),
     'power_min_unsigned_W_F30':unsigned_w(p,30),
     'power_min_unsigned_W_F26':unsigned_w(p,26),
     'sum40_min_unsigned_W_F30':unsigned_w(tsum,30),
     'sum40_min_unsigned_W_F26':unsigned_w(tsum,26),
     'original_MF_amp_bound':mf*g,'original_MTI_amp_bound':mti*g,
     'original_FFT_amp_bound':fft*g*scale,
     'original_power_bound':p*g*g*scale*scale,
     'original_sum40_bound':tsum*g*g*scale*scale}

cands={
 'A':{'coeff':[16,15],'MF':[22,15],'MTI':[23,15],'FFT':[28,15],
      'power':[52,30],'sum40':[58,30],'alpha':[20,16],
      'fft_shift':[0,0,0,0,0]},
 'B':{'coeff':[14,13],'MF':[20,13],'MTI':[21,13],'FFT':[23,13],
      'power':[43,26],'sum40':[49,26],'alpha':[16,12],
      'fft_shift':[1,1,1,0,0]},
 'C_hypothetical':{'coeff':[16,15],'MF':[22,15],'MTI':[23,15],'FFT':[25,15],
      'power':[46,30],'sum40':[52,30],'alpha':[20,16],
      'fft_shift':[1,1,1,0,0]},
}
witness={}
for opt,fmt in cands.items():
    scale=2**sum(fmt['fft_shift'])
    b=stage_bound(1,scale)
    keys={'MF':'MF_abs_component_conservative_stored','MTI':'MTI_abs_component_conservative_stored',
          'FFT':'FFT_abs_component_conservative_stored',
          'power':'RD_power_conservative_stored','sum40':'CA_CFAR_sum40_conservative_stored'}
    storage={}
    for k,name in keys.items():
        W,F=fmt[k]
        maxv=(2**(W-F-1)-2**(-F)) if k in ('MF','MTI','FFT') else 2**(W-F)-2**(-F)
        storage[k]={'W':W,'F':F,'max_representable_stored':maxv,
                    'ideal_bound_stored':b[name],
                    'ideal_bound_fits_stored':maxv>=b[name],
                    'unused_integer_bits_vs_minimum':W-(signed_w(b[name],F) if k in ('MF','MTI','FFT') else unsigned_w(b[name],F))}
        assert storage[k]['ideal_bound_fits_stored'],(opt,k,storage[k])
    # conservative raw widths for exact complex sum of product sign-extended, 16 coefficients
    fi,fc=15,fmt['coeff'][1]
    wi,wc=16,fmt['coeff'][0]
    product=wi+wc
    raw_complex_pair=product+1
    raw_complex_acc16=raw_complex_pair+math.ceil(math.log2(L))
    estimates={'coefficient_rom_bits_16_complex':16*2*wc,
      'RD_complex_FFT_buffer_bits_128x32':128*32*2*fmt['FFT'][0],
      'RD_power_buffer_bits_128x32':128*32*fmt['power'][0],
      'MTI_buffer_bits_32x128':32*128*2*fmt['MTI'][0],
      'full_exact_signed_component_product_bits':product,
      'raw_complex_pair_addsub_bits_conservative':raw_complex_pair,
      'raw_16tap_accumulator_bits_conservative':raw_complex_acc16,
      'raw_16tap_accumulator_fractional_bits':fi+fc,
      'FFT_32_radix2_complex_butterflies':16*5,
      'complex_MF_products_per_128_range_output_if_unshared':16,
      'CFAR_training_cell_additions_per_CUT':39,
      'CFAR_left_crossproduct_unsigned_bits_conservative':fmt['power'][0]+6+fmt['alpha'][1],
      'CFAR_right_crossproduct_unsigned_bits_conservative':fmt['sum40'][0]+fmt['alpha'][0]}
    witness[opt]={'formats':fmt,'net_FFT_scale':scale,'stage_storage':storage,
                  'resource_storage_proxies':estimates,
                  'not_synthesis':True,'twiddle_F_and_internal_fft_rounding':'OPEN'}
# power can be expressed as qI^2+qQ^2 before narrowing, with Fp=2*Ffft
for x in witness.values():
    assert x['formats']['power'][1]==2*x['formats']['FFT'][1]
# exact rational positive common power scaling cancels, but RNE may change detector result
for g in (1,5):
    for o,c in witness.items():
        scale=c['net_FFT_scale']; coeff=Fraction(g*scale)**2
        assert (Fraction(41)*coeff>Fraction(40)*coeff)==(41>40)
        c.setdefault('input_profile_reconstruction',{})[str(g)]={
          'input_normalized_amplitude_scale':g,'MF_MTI_amplitude_scale':g,
          'FFT_amplitude_scale':g*scale,'power_sum_threshold_scale':g*g*scale*scale}
alpha={'A':{'numerator':490007,'frac':16},
       'B':{'numerator':30625,'frac':12},
       'C_hypothetical':{'numerator':490007,'frac':16}}
for name,c in witness.items():
    A=alpha[name]['numerator'];fa=alpha[name]['frac']
    assert not (40*A*2**fa>A*(40*2**fa))
    assert 40*(A+1)*2**fa>A*(40*2**fa)
    assert not (40*(A-1)*2**fa>A*(40*2**fa))
# relative risk: Twiddle approximated as unit modulus, additional gain if |what|>1
# bounds must be recomputed with beta>=1 stage coefficient bound, x and 32 fft N.
robustness={}
for beta in (Fraction(1),Fraction(10001,10000)):
    factor=float(beta)**5
    beta_f=float(beta)
    rigorous_stage_growth=(1+beta_f)**5
    robustness[str(beta)]={'twiddle_abs_bound':beta_f,
       'conservative_unshifted_fft_mag_from_MTI':32*math.sqrt(2)*rigorous_stage_growth,
       'conservative_fft_shift8_mag_from_MTI':32*math.sqrt(2)*rigorous_stage_growth/8,
       'validity':'conditional on input postquantizer bound, ideal MF coefficient norm and exact arithmetic in FFT; quantitative rounding/overflow not covered'}
row={'status':'ANALYSIS_ONLY_NO_ARCH_APPROVAL','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source':'S02 approved reference / S03 Float model / C01 signed bounded profiles, no generated CPI',
 'input_g_profiles_approved':{'NOISE_ONLY_UNIT':5,'SINGLE_TARGET_REFERENCE_LIKE_LAB':1},
 'source_input_complex_noise_variance':{'NOISE_ONLY_UNIT':1,'SINGLE_TARGET_REFERENCE_LIKE_LAB':.000324},
 'input_q15_LSB_original_float':{'g5':5/32768,'g1':1/32768},
 'input_component_error_bound_no_clipping':{'g5':5/65536,'g1':1/65536},
 'assumptions':['postquantizer each signed real component magnitude <=1',
   'ideal matched-filter complex tap |h|<=1; quantized coefficient gain not yet certified',
   'ideal FFT unit modulus twiddles; no arithmetic error or stage saturation',
   'input Gaussian unbounded before clipping; only admission-approved postquantizer has finite bound'],
 'stages':{str(g):{'unshifted':stage_bound(g,1),'shift8':stage_bound(g,8)} for g in (1,5)},
 'candidate_formats_not_approved':witness,
 'quantized_twiddle_growth_risk':robustness,
 'unit_tests_exact_rational':['strict comparator equality false','positive common FFT/power scaling cancels in exact ideal ratio'],
 'S02_open_obligations':['REQ-SCR-01','REQ-RNG-03'],
 'missing_inputs':['target/clutter source amplitude covariance/crest factors for SCR +/-10',
   'two-target coherent overlap phase and power envelope, frozen resolution oracle',
   'FFT twiddle W/F and coefficient modulus bound after quantization',
   'internal rounding topology, actual multiplier/accumulator widths, resource schedule'],
 'hardware_synthesis_evidence':False,'main_CPI_generated':0,'accepted_S03_seeds_touched':False}
OUT.write_text(json.dumps(row,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('ANALYSIS_WRITTEN_SHA',hashlib.sha256(OUT.read_bytes()).hexdigest())
for name,d in witness.items():
 print(name,'scale',d['net_FFT_scale'],'min guards',{k:v['unused_integer_bits_vs_minimum'] for k,v in d['stage_storage'].items()},
       'storage_proxy',d['resource_storage_proxies'])

"""Freeze selected C arithmetic from executed v0.5/v0.6. Never retune or compare candidates."""
from pathlib import Path
import json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
coeffpath=ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json'
source=json.loads(coeffpath.read_text())['formats']['C_hypothetical']
old=json.loads((ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json').read_text())
assert old['native_integer_clustering']=='OPEN_NOT_IMPLEMENTED'
taps=[x['stored_integer'] for x in source['mf16']]
twiddles=[[x['stored_integer'] for x in source['twiddle32_by_stage'][str(j)]] for j in range(1,6)]
assert len(taps)==16 and [len(x) for x in twiddles]==[1,2,4,8,16]
inputW,F=16,15
mfW,mtiW,fftW=22,23,25
coeffW,twW=16,16
def signed(W,F):return {'signed':True,'W':W,'F':F,'min_stored_integer':-(1<<(W-1)),'max_stored_integer':(1<<(W-1))-1,'LSB':[1,1<<F]}
def unsigned(W,F):return {'signed':False,'W':W,'F':F,'min_stored_integer':0,'max_stored_integer':(1<<W)-1,'LSB':[1,1<<F]}
stages=[]
for index,sh in enumerate((0,1,0,1,1),start=1):
    wi=mtiW if index==1 else fftW
    product=wi+twW
    pair=product+1
    pre=max(wi+F,pair)+1
    stages.append({'stage':index,'shift':sh,'signed_input_format':signed(wi,F),
      'twiddle_format':signed(twW,F),'signed_real_product_W':product,
      'signed_real_complex_pair_W':pair,'aligned_u_signed_W':wi+F,
      'pre_shift_butterfly_signed_W':pre,'all_internal_arithmetic_F':30,
      'post_butterfly_output_format':signed(fftW,F),
      'rounding_denom_power_of_two':15+sh,
      'rounding_semantics':'integer RNE ties-to-even on exact butterfly output divided by 2^(15+shift); applied once per component',
      'overflow':'check every intermediate signed fullwidth; on output overflow record prelimit integer, sign, location, sticky flag then SAT signed 25; never wrap',
      'twiddle_stage_stored_pairs':twiddles[index-1]})
paths={'project':'AX309-RDSP-001','criterion':'S04-C02',
 'version':'engineer-selected-C-arithmetic-baseline-v1.0',
 'decision_status':'ENGINEER_SELECTED_BASELINE_NOT_C02_PASS',
 'official_criterion_state':'OPEN_READY_FOR_INDEPENDENT_SIGN_OFF',
 'architecture':'C','schedule':[0,1,0,1,1],'fft_divisor':8,
 'fft_convention':'32 point forward unnormalized radix-2 DIT, bit-reversed MTI input, negative exponent Twiddles, natural FFT output ordering, no Doppler wrap',
 'reference_geometry':'33x128 input IQ, MF16, MTI gives 32x128, 32-bin Doppler FFT at each of 128 ranges',
 'input':{'format':signed(inputW,F),'profiles':{
    'NOISE_ONLY_UNIT':{'g':[5,1],'approved_context':'CN(0,1) noise-only, g5'},
    'SINGLE_TARGET_REFERENCE_LIKE_LAB':{'g':[1,1],'approved_context':'predeclared single-target reference-like lab only, g1'}},
  'logical_metadata':'C01 immutable profile/g/source/hash/admission/saturation events before CPI; UART/FPGA ICD not approved',
  'mapping':'RNE_to_even(32768*x/g) then SAT16; signed interleaved I/Q little endian pulse-major',
  'float_reconstructed_input':'g*code/32768','no_clip_component_max_error_original':[5,65536],
  'on_invalid_or_overflow':'preserve every sample and event; INCONCLUSIVE under approved C01 protocol; STRESS_ONLY only predeclared'},
 'MF':{'input':signed(inputW,F),'coefficient':signed(coeffW,F),
   'coefficients_order':'S03 conjugate reversed LFM16; exact frozen integer pairs in mf16_stored_pairs',
   'mf16_stored_pairs':taps,
   'full_convolution_output':'at range r, index r+15 in full convolution; sample index r+15-k, zero outside [0,127]',
   'four_exact_signed_products_W':inputW+coeffW,'product_F':30,'complex_pair_signed_W':inputW+coeffW+1,
   'raw_16tap_accumulator_signed_W':inputW+coeffW+5,
   'round':'after exact signed sum all 16 tap products, RNE once per complex I/Q from F30 to F15',
   'output':signed(mfW,F),'output_overflow':'pre-narrow guard then SAT signed Q22.15 with sticky per-site telemetry'},
 'MTI':{'operation':'MF[p+1,r]-MF[p,r] for p 0..31, each complex component',
   'input':signed(mfW,F),'raw_subtract_signed_W':mfW+1,'raw_subtract_F':F,
   'output':signed(mtiW,F),'round':'RNE once at F15 -> F15 (identity, no numeric rounding actually needed)',
   'overflow':'full signed 23-bit difference guard, then output saturate with signed bound if needed'},
 'FFT':{'stages':stages,'output':signed(fftW,F),
  'butterfly':'t=(v_re*w_re-v_im*w_im)+j(v_re*w_im+v_im*w_re); output plus=u+t, minus=u-t; align u by <<15; exact full integer products, pair, aligned sum before shift/RNE',
  'single_rounding_location':'after exact butterfly, before narrowing, divide by 2**(15+s_j) with mathematical ties-to-even; do not substitute arithmetic >> for negative values',
  'internal_width_commitment':'the full signed product/pair/butterfly widths specified in each stage must be preserved through the arithmetic; allowed extra guard bits but no pre-RNE narrowing',
  'bit_reversal':[int(f'{i:05b}'[::-1],2) for i in range(32)],
  'saturation':'on every stage output overflow: log unlimited pre-narrow value (or minimum signed width sufficient to hold it), stage/range/bin/component; SAT signed 25, sticky event flag'},
 'power':{'source':signed(fftW,F),'exact_real_multiplication_signed_W':2*fftW,
   'raw_I_squared_plus_Q_squared_unsigned_W':2*fftW+1,'raw_power_F':2*F,
   'stored_power':unsigned(46,30),
   'narrowing':'NO scaling or rounding (F30 stays F30); on raw overflow above U46.30 max, log and SAT to 2^46-1; never wrap'},
 'SUM40':{'training_geometry':'7x7 outer less center 3x3 40 training cells, no wrap',
  'input_power':unsigned(46,30),'raw_sum_unsigned_W':52,
  'stored_sum':unsigned(52,30),'sum_rounding':'none, all training power integers same F30; overflow guard and unsigned SAT if unexpected'},
 'CFAR':{'CUTs':2782,'range_valid':[3,109],'doppler_valid':[3,28],
  'strict_comparison':'40*Pcut*65536 > 490007*SUM40',
  'alpha':{'numerator':490007,'denominator':65536,'alpha_fractional_bits':16,'alpha_unsigned_W':20},
  'float_reference_alpha_S02_S03':7.476912055027923,
  'stored_power_operands':'CUT U46.30; SUM40 U52.30',
  'left_unsigned_fullproduct_conservative_W':68,'right_unsigned_fullproduct_conservative_W':72,
  'left_exact_max_product_W':68,'right_exact_max_product_W':71,
  'pre_power_narrowing_full_product_conservative_W':[73,77],
  'comparison':'unsigned exact cross-multiplication; equality => no alarm; no implicit rounding/truncation'},
 'physical_reconstruction':{'MF_original_float_amplitude':'g*MF_integer/32768',
  'MTI_original_float_amplitude':'g*MTI_integer/32768',
  'FFT_original_float_amplitude':'g*8*FFT_integer/32768',
  'RD_original_float_power':'(g*8/32768)^2 * stored_power_integer',
  'CFAR_alpha_and_comparison':'scale invariance only when both CUT and training operate on same stored-power scale',
  'SFFT':8,'g1_original_fft_amplitude_factor':8,'g5_original_fft_amplitude_factor':40,
  'g1_original_RD_power_factor':64,'g5_original_RD_power_factor':1600},
 'overflow_policy':{'intermediate_signed_guards':True,'signed_output_SAT_not_wrap':True,
   'power_and_SUM_unsigned_SAT_not_wrap':True,'event_fields':['site','stage','range','bin_or_tap','I_or_Q','signedness','full_integer_before_narrowing','signed_min','signed_max','cumulative_count','sticky'],
   'performance_eligibility':'C01 VALID_PERFORMANCE / INCONCLUSIVE / STRESS_ONLY, no deletion/overwrite/retry, no aggregate score after incomplete fixed N'},
 'native_integer_clustering':'NOT_IMPLEMENTED_AS_OF_C02_SELECTION_MUST_VERIFY_C05_C06',
 'unknown_or_external_qualification':['UART_FPGA_ICD','FPGA resources/time/synthesis','noise+clutter SCR +/-10dB','two-target range resolution','numeric error budget and Pd/Pfa'],
 'change_control':'C format schedule coefficients numeric scalar and rounding order frozen to this v1.0; changes require separate engineer-authorized engineering change decision',
 'evidence_references':{'integer_v05':'engineering/s04_numeric/s04_c02_integer_bittrue_v05.py',
  'paired_v06':'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json',
  'source_coefficients_v03':'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json'},
 'evidence_SHA256':{'source_coefficients_v03':sha(coeffpath),
  'paired_v06':sha(ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json'),
  'integer_v05_source':sha(ROOT/'engineering/s04_numeric/s04_c02_integer_bittrue_v05.py')},
 'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
output=ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json'
if output.exists():
    paths['recorded_at_utc']=json.loads(output.read_text())['recorded_at_utc']
output.write_text(json.dumps(paths,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('CONTRACT_SHA256',sha(output))
print('FFT-STAGE-WIDTHS',[(x['signed_real_product_W'],x['signed_real_complex_pair_W'],x['pre_shift_butterfly_signed_W']) for x in stages])
print('TAPS',len(taps),'TWIDDLES',[len(x) for x in twiddles])

"""Independent C selected baseline signoff-readiness tests. No stochastic CPI."""
import unittest,json,sys,hashlib
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c02_integer_bittrue_v05 as B
C=json.loads((ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json').read_text())
SRC=json.loads((ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json').read_text())
PAIRED=json.loads((ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json').read_text())
class SelectedCContract(unittest.TestCase):
 def test_exact_selected_format_and_schedule(self):
  self.assertEqual(C['architecture'],'C')
  self.assertEqual(C['schedule'],[0,1,0,1,1])
  self.assertEqual(C['fft_divisor'],8)
  f=C['MF']['output'];m=C['MTI']['output'];z=C['FFT']['output']
  self.assertEqual([f['W'],f['F'],m['W'],m['F'],z['W'],z['F']],[22,15,23,15,25,15])
  self.assertEqual([C['power']['stored_power']['W'],C['power']['stored_power']['F'],
   C['SUM40']['stored_sum']['W'],C['SUM40']['stored_sum']['F']],[46,30,52,30])
  self.assertEqual(C['CFAR']['strict_comparison'],'40*Pcut*65536 > 490007*SUM40')
 def test_coefficient_tables_locked_bytewise(self):
  v=SRC['formats']['C_hypothetical']
  self.assertEqual(C['MF']['mf16_stored_pairs'],[x['stored_integer'] for x in v['mf16']])
  for stage,x in enumerate(C['FFT']['stages'],1):
   self.assertEqual(x['twiddle_stage_stored_pairs'],[z['stored_integer'] for z in v['twiddle32_by_stage'][str(stage)]])
  self.assertEqual(C['evidence_SHA256']['source_coefficients_v03'],hashlib.sha256((ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json').read_bytes()).hexdigest())
 def test_full_precision_internal_widths(self):
  self.assertEqual((C['MF']['four_exact_signed_products_W'],C['MF']['complex_pair_signed_W'],C['MF']['raw_16tap_accumulator_signed_W']),(32,33,37))
  self.assertEqual(C['MTI']['raw_subtract_signed_W'],23)
  for i,x in enumerate(C['FFT']['stages']):
   self.assertEqual(x['stage'],i+1)
   self.assertEqual(x['shift'],[0,1,0,1,1][i])
   self.assertEqual((x['signed_real_product_W'],x['signed_real_complex_pair_W'],x['pre_shift_butterfly_signed_W']),
                    (39,40,41) if i==0 else (41,42,43))
   self.assertEqual(x['rounding_denom_power_of_two'],15+x['shift'])
   self.assertEqual(x['post_butterfly_output_format']['W'],25)
 def test_signed_RNE_vs_negative_shift_and_overflow(self):
  self.assertEqual(B.rne(-1,2),0)
  self.assertEqual((-1)>>1,-1)
  self.assertEqual(B.rne(-5,2),-2)
  self.assertEqual((-5)>>1,-3)
  for W in (16,22,23,25):
   lo=-(1<<(W-1));hi=(1<<(W-1))-1
   self.assertEqual(C['FFT']['output']['min_stored_integer'] if W==25 else lo,lo)
   self.assertEqual(B.required_width_signed(lo),W)
   self.assertEqual(B.required_width_signed(hi),W)
 def test_exact_cfar_unsigned_and_threshold_ties(self):
  n=490007;den=65536
  for cut,expect in ((n-1,False),(n,False),(n+1,True)):
   t=40*den
   self.assertEqual(40*cut*den>n*t,expect)
   self.assertEqual(Fraction(cut)>Fraction(n,den)*Fraction(t,40),expect)
  self.assertEqual((C['CFAR']['left_unsigned_fullproduct_conservative_W'],C['CFAR']['right_unsigned_fullproduct_conservative_W']),(68,72))
  self.assertEqual(C['CFAR']['pre_power_narrowing_full_product_conservative_W'],[73,77])
 def test_reconstruction_units_and_C01_g_immutable(self):
  self.assertEqual(C['physical_reconstruction']['g1_original_fft_amplitude_factor'],8)
  self.assertEqual(C['physical_reconstruction']['g5_original_fft_amplitude_factor'],40)
  self.assertEqual(C['physical_reconstruction']['g1_original_RD_power_factor'],64)
  self.assertEqual(C['physical_reconstruction']['g5_original_RD_power_factor'],1600)
  self.assertEqual(C['input']['profiles']['NOISE_ONLY_UNIT']['g'],[5,1])
  self.assertEqual(C['input']['profiles']['SINGLE_TARGET_REFERENCE_LIKE_LAB']['g'],[1,1])
 def test_selected_integer_rerun_both_g_and_reference(self):
  for g in (1,5):
   for pattern in ('zero','impulse','alternating','phase_interference'):
    src,iq,events=B.source_vector(pattern,g)
    run=B.run_one(src,iq,events,'C_hypothetical',(0,1,0,1,1),g)
    old=next(x for x in json.loads((ROOT/'engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json').read_text())['per_option_schedule']['C_hypothetical:DISTRIBUTED_3']['cases']
             if x['input_profile']==('SINGLE_TARGET_REFERENCE_LIKE_LAB' if g==1 else 'NOISE_ONLY_UNIT') and x['kind']==pattern)
    self.assertEqual(run['overflow']['total'],0)
    self.assertEqual(run['cfar_valid_cut_count'],2782)
    self.assertAlmostEqual(run['metrics']['FFT5']['MAX'],old['FFT_max'],places=9)
    self.assertEqual(run['cfar_alarm_count'],old['CFAR_alarm_count'])
 def test_twiddle_fft_bit_order_frozen(self):
  self.assertEqual(C['FFT']['bit_reversal'],[B.bitreverse(i) for i in range(32)])
  self.assertEqual([len(x['twiddle_stage_stored_pairs']) for x in C['FFT']['stages']],[1,2,4,8,16])
 def test_open_requirements_and_native_clustering(self):
  self.assertEqual(C['official_criterion_state'],'OPEN_READY_FOR_INDEPENDENT_SIGN_OFF')
  self.assertEqual(C['native_integer_clustering'],'NOT_IMPLEMENTED_AS_OF_C02_SELECTION_MUST_VERIFY_C05_C06')
  self.assertEqual(PAIRED['native_integer_clustering'],'OPEN_NOT_IMPLEMENTED')
  self.assertEqual(len(PAIRED['common_set_ids']),14)
 def test_no_unapproved_statistical_or_hardware_claims(self):
  code=(ROOT/'engineering/s04_numeric/freeze_s04_c02_selected_C_contract_v10.py').read_text()
  for bad in ('default_rng(', 'noise_only_cpi(', 'generate_cpi(', 'SeedSequence(', 'np.random'):
   self.assertNotIn(bad,code)
  self.assertIn('ENGINEER_SELECTED_BASELINE_NOT_C02_PASS',C['decision_status'])
if __name__=='__main__':unittest.main()

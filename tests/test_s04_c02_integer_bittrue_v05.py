"""Independent fixed-int S04 C02 v0.5 deterministic tests, no statistical CPI."""
import unittest,sys,json,math
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c02_integer_bittrue_v05 as bt
D=ROOT/'engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json'
class IntegerBittrueDeterministic(unittest.TestCase):
 def test_signed_RNE_positive_negative_ties(self):
  for n,d,exp in [(1,2,0),(-1,2,0),(3,2,2),(-3,2,-2),(5,2,2),(-5,2,-2),
                  (7,2,4),(-7,2,-4),(-9,4,-2)]:
   self.assertEqual(bt.rne(n,d),exp)
 def test_arithmetic_right_shift_is_not_RNE(self):
  self.assertEqual(-1>>1,-1)
  self.assertEqual(bt.shifted_round(-1,-1),0)
  self.assertEqual(-5>>1,-3)
  self.assertEqual(bt.shifted_round(-5,-1),-2)
 def test_input_borderline_and_stress_telemetry(self):
  _,packed,trace=bt.source_vector('near_clip',1)
  self.assertEqual(trace.summary()['total'],0)
  _,packed,trace=bt.source_vector('overrange_stress',1)
  self.assertEqual(trace.summary()['total'],33*128*2)
  self.assertTrue(trace.summary()['all_event_order_sha256'])
  self.assertIn('pre_narrow_integer',trace.summary()['first_24'][0])
 def test_exact_fullwidth_signed_extrema(self):
  for W in (16,20,21,22,23,25,28,35,37):
   self.assertEqual(bt.required_width_signed(-(1<<(W-1))),W)
   self.assertEqual(bt.required_width_signed((1<<(W-1))-1),W)
   self.assertEqual(bt.required_width_signed(1<<(W-1)),W+1)
 def test_coefficient_tables_no_float_in_fixed_calculator(self):
  for opt,meta in bt.DATA['formats'].items():
   taps,tw=bt.coefficients(opt)
   self.assertEqual(len(taps),16)
   self.assertEqual([len(z) for z in tw],[1,2,4,8,16])
   self.assertTrue(all(isinstance(x,int) for pair in taps for x in pair))
   self.assertTrue(all(isinstance(x,int) for stage in tw for pair in stage for x in pair))
 def test_bitreverse_permutation_exact(self):
  order=[bt.bitreverse(x) for x in range(32)]
  self.assertEqual(sorted(order),list(range(32)))
  self.assertEqual(order[:4],[0,16,8,24])
 def test_zero_source_zero_every_stage_and_no_cfar(self):
  ref,x,inp=bt.source_vector('zero',1)
  z=bt.run_one(ref,x,inp,'A',(0,0,0,0,0),1)
  self.assertEqual(z['overflow']['total'],0)
  self.assertEqual(z['cfar_alarm_count'],0)
  self.assertTrue(all(e['MAX']==0 for e in z['metrics'].values()))
 def test_independent_near_threshold_fraction_oracle(self):
  for opt,c in bt.CFAR['calculations'].items():
   m=c['config'];a=m['alphaNum'];f=m['alphaF']
   total=40*(1<<f)
   for offset in (-1,0,1):
    cut=a+offset
    integer=40*cut*(1<<f)>a*total
    rational=Fraction(cut,1)>Fraction(a,1<<f)*Fraction(total,40)
    self.assertEqual(integer,rational)
    self.assertEqual(integer,offset>0)
    cap=c['post_narrowing_candidate_operands']
    self.assertLess(40*cut*(1<<f),1<<cap['left_conservative_bits'])
    self.assertLess(a*total,1<<cap['right_conservative_bits'])
 def test_full_raw_power_cfars_bounds(self):
  for opt,c in bt.CFAR['calculations'].items():
   conf=c['config'];w=conf['fftW']
   raw=2*(1<<(w-1))**2
   self.assertLess(raw,1<<(2*w+1))
   self.assertLess(40*raw,1<<c['full_precision_pre_narrowing_path']['raw_sum40_conservative_bits'])
 def test_all_12_variants_and_stratified_bound(self):
  x=json.loads(D.read_text())
  self.assertEqual(len(x['per_option_schedule']),12)
  self.assertEqual(len(x['per_profile']),18)
  for key,r in x['per_option_schedule'].items():
   self.assertEqual(r['case_count'],18)
   self.assertEqual(r['admissible_case_count']+sum(not v['admissible_for_v04_bound'] for v in r['cases']),18)
   self.assertTrue(r['conditional_v04_bounds_satisfied_on_all_admissible'],key)
   self.assertEqual(r['aggregated_stage_metrics']['FFT5']['samples'],18*128*32)
   self.assertLessEqual(r['eligible_no_saturation_stage_metrics']['FFT5']['MAX'],
                        r['aggregated_stage_metrics']['FFT5']['MAX'])
   self.assertEqual(sum(r['saturation_by_site'].values()),r['total_output_saturation_count'])
 def test_bittrue_zero_shift_saturation_specific(self):
  x=json.loads(D.read_text())['per_option_schedule']
  self.assertEqual(x['A:ZERO']['total_output_saturation_count'],0)
  self.assertGreater(x['B:ZERO']['total_output_saturation_count'],0)
  self.assertGreater(x['C_hypothetical:ZERO']['total_output_saturation_count'],0)
  for opt in ('A','B','C_hypothetical'):
   for sc in ('EARLY_3','DISTRIBUTED_3','ALL_5'):
    self.assertEqual(x[f'{opt}:{sc}']['total_output_saturation_count'],0)
 def test_all_stagewise_analytical_comparisons_valid_where_applicable(self):
  x=json.loads(D.read_text())
  self.assertTrue(x['full_stage_bound_recheck']['all_admissible_stages_pass'])
  self.assertEqual(x['full_stage_bound_recheck']['admissible_stagewise_violations'],[])
  for k,v in x['per_option_schedule'].items():
   self.assertTrue(v['all_stages_within_v04_bound_on_admissible'],k)
   for c in v['cases']:
    self.assertEqual(len(c['stagewise_v04_bound_audit']),7)
    for stage,ev in c['stagewise_v04_bound_audit'].items():
     if c['admissible_for_v04_bound']: self.assertTrue(ev['pass_if_no_saturation'])
     else:self.assertIsNone(ev['pass_if_no_saturation'])
 def test_FFT_S03_convention_nonzero_and_all_shift_schedules(self):
  ref,iq,tel=bt.source_vector('alternating',1)
  for sch in ((0,0,0,0,0),(1,1,1,0,0),(0,1,0,1,1),(1,1,1,1,1)):
   r=bt.run_one(ref,iq,tel,'A',sch,1)
   self.assertLess(r['fft_float_reference_max_abs_diff'],1e-7)
   self.assertEqual(r['cfar_valid_cut_count'],2782)
   self.assertEqual(r['overflow']['total'],0)
 def test_no_random_main_CPI_or_approval(self):
  txt=(ROOT/'engineering/s04_numeric/s04_c02_integer_bittrue_v05.py').read_text()
  for forbidden in ('default_rng(', 'generate_cpi(', 'noise_only_cpi(', 'SeedSequence(', 'np.random'):
   self.assertNotIn(forbidden,txt)
  self.assertIn('NO_ARCH_APPROVAL',json.loads(D.read_text())['status'])
if __name__=='__main__':unittest.main()

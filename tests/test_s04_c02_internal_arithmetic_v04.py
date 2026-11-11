"""Independent deterministic unit checks for candidate internal arithmetic v0.4."""
import json, math, unittest, sys
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c02_internal_arithmetic_v04 as m
V=json.loads((ROOT/'engineering/s04_numeric/S04-C02-internal-arithmetic-error-propagation-v0.4.json').read_text())
CFAR=json.loads((ROOT/'engineering/s04_numeric/S04-C02-cfar-width-arithmetic-audit-v0.3.1.json').read_text())
class CandidateArithmetic(unittest.TestCase):
 def test_integer_RNE_negative_positive_ties(self):
  for a,b in [(Fraction(-5,2),-2),(Fraction(-3,2),-2),(Fraction(-1,2),0),
              (Fraction(1,2),0),(Fraction(3,2),2),(Fraction(5,2),2),
              (Fraction(-7,2),-4)]:
   self.assertEqual(m.rne(a),b)
 def test_pre_vs_post_sum_narrowing_is_not_equivalent(self):
  F=1
  a=b=Fraction(1,4)
  pre=(m.rne(a*2**F)+m.rne(b*2**F))
  after=m.rne((a+b)*2**F)
  self.assertEqual(pre,0);self.assertEqual(after,1)
 def test_negative_arithmetic_shift_differs_from_RNE(self):
  self.assertEqual(-1>>1,-1)
  self.assertEqual(m.rne(Fraction(-1,2)),0)
  self.assertEqual(-5>>1,-3)
  self.assertEqual(m.rne(Fraction(-5,2)),-2)
 def test_output_saturation_is_detected_not_wrapped(self):
  self.assertEqual(m.signed_quant(Fraction(100),8,4),(127,True))
  self.assertEqual(m.signed_quant(Fraction(-100),8,4),(-128,True))
  self.assertEqual(m.signed_quant(Fraction(1,4),8,4),(4,False))
 def test_A_B_C_word_contract_and_intermediate_fullwidth(self):
  for name,v in V['summaries'].items():
   f=v['candidate_formats'];mf=v['MF']
   self.assertEqual(mf['real_product_signed_W'],16+mf['signed_coeff_W_F'][0])
   self.assertEqual(mf['signed_complex_pair_W'],mf['real_product_signed_W']+1)
   self.assertEqual(mf['signed_16tap_raw_accumulator_W'],mf['real_product_signed_W']+5)
   self.assertEqual(len(v['FFT']['stage_word_proposals']),5)
   for j,x in enumerate(v['FFT']['stage_word_proposals']):
    self.assertEqual(x['signed_real_product_W'],x['input_signed_W']+x['twiddle_signed_W'])
    self.assertEqual(x['complex_real_pair_addsub_W'],x['signed_real_product_W']+1)
    self.assertGreaterEqual(x['pre_shift_butterfly_addsub_W_conservative'],x['complex_real_pair_addsub_W']+1)
    self.assertEqual(x['stage'],j+1)
 def test_all_schedules_reconstruct_exact_scale(self):
  for option,v in V['summaries'].items():
   for name,sc in v['FFT']['schedules'].items():
    scale=2**sum(sc['shifts'])
    self.assertEqual(scale,sc['scale'])
    for g in ('1','5'):
     r=sc['source_reconstruction'][g]
     self.assertEqual(r['FFT_amplitude_scale'],int(g)*scale)
     self.assertEqual(r['RD_power_scale'],(int(g)*scale)**2)
     self.assertAlmostEqual(sc['reconstructed_original_Float_error_amplitude'][g],
      sc['total_complex_error_stored_normalized']*int(g)*scale)
 def test_input_source_float_error_propagated_and_nonzero(self):
  for option,v in V['summaries'].items():
   mf=v['MF'];self.assertGreater(mf['source_error_component'],0)
   for sc in v['FFT']['schedules'].values():
    e=sc['error_components_stored_normalized']
    self.assertGreater(e['input_Q15'],0)
    self.assertGreater(e['MF_coefficients'],0)
    self.assertGreater(e['FFT_twiddle_quantization'],0)
    self.assertAlmostEqual(sum(e.values()),sc['total_complex_error_stored_normalized'])
    self.assertFalse(sc['saturation_error_included'])
 def test_zero_shift_negative_margins_only_B_C(self):
  for name in ('B','C_hypothetical'):
   sc=V['summaries'][name]['FFT']['schedules']['ZERO']
   self.assertFalse(sc['all_stage_output_guards_positive'])
   self.assertLess(sc['FFT_max_signed_output_headroom_conditional'],0)
  self.assertTrue(V['summaries']['A']['FFT']['schedules']['ZERO']['all_stage_output_guards_positive'])
 def test_tightening_input_roundoff_produces_lower_bound(self):
  a=V['summaries']['A']['FFT']['schedules']['EARLY_3']
  e=a['error_components_stored_normalized']
  self.assertGreater(sum(e.values()),sum(v for k,v in e.items() if k!='input_Q15'))
 def test_repaired_Cfar_narrow_and_full_precision_audit_retained(self):
  for name,v in V['summaries'].items():
   c=v['CFAR']
   self.assertEqual(c['post_narrowing_candidate_operands']['right_conservative_bits'],
    CFAR['calculations'][name]['post_narrowing_candidate_operands']['right_conservative_bits'])
   self.assertGreater(c['full_precision_pre_narrowing_path']['left_conservative_bits'],0)
   self.assertGreater(c['full_precision_pre_narrowing_path']['right_conservative_bits'],0)
 def test_status_and_no_sample_sources(self):
  self.assertIn('NOT_APPROVED',V['status'])
  s=(ROOT/'engineering/s04_numeric/s04_c02_internal_arithmetic_v04.py').read_text()
  for x in ('default_rng(', 'generate_cpi(', 'SeedSequence(', 's03_reference/model.py'):
   self.assertNotIn(x,s)
if __name__=='__main__':unittest.main()

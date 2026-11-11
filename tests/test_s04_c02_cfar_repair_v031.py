"""Independent integer and Fraction CFAR audit, no stochastic models."""
import json,unittest,random
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'engineering/s04_numeric/S04-C02-cfar-width-arithmetic-audit-v0.3.1.json'
D=json.loads(SOURCE.read_text())
def nbits(x):return max(1,x.bit_length())
def rcomparison(cut,total,a,f):
 return Fraction(cut,1)>Fraction(a,1<<f)*Fraction(total,40)
class CFARRepair(unittest.TestCase):
 def test_all_three_expected_corrected_widths(self):
  expected={'A':(74,78,79,83),'B':(61,65,65,69),'C_hypothetical':(68,72,73,77)}
  for name,v in D['calculations'].items():
   n=v['post_narrowing_candidate_operands'];f=v['full_precision_pre_narrowing_path']
   self.assertEqual((n['left_conservative_bits'],n['right_conservative_bits'],
                     f['left_conservative_bits'],f['right_conservative_bits']),expected[name])
 def test_max_unsigned_operand_products_overflow_free(self):
  for v in D['calculations'].values():
   n=v['post_narrowing_candidate_operands']
   self.assertEqual(nbits(n['max_left_product']),n['left_exact_bits'])
   self.assertEqual(nbits(n['max_right_product']),n['right_exact_bits'])
   self.assertLess(n['max_left_product'],1<<n['left_conservative_bits'])
   self.assertLess(n['max_right_product'],1<<n['right_conservative_bits'])
   self.assertLessEqual(n['Pcut_max'],(1<<v['config']['powerW'])-1)
   self.assertLessEqual(n['SUM40_max'],(1<<v['config']['sumW'])-1)
 def test_full_precision_before_narrowing_extreme_fft(self):
  for v in D['calculations'].values():
   f=v['full_precision_pre_narrowing_path']
   w=v['config']['fftW']
   self.assertEqual(f['raw_exact_I2_plus_Q2_max'],2*(1<<(w-1))**2)
   self.assertEqual(f['raw_exact_SUM40_max'],40*f['raw_exact_I2_plus_Q2_max'])
   self.assertEqual(nbits(f['max_left_product']),f['left_exact_bits'])
   self.assertEqual(nbits(f['max_right_product']),f['right_exact_bits'])
   self.assertLess(f['max_left_product'],1<<f['left_conservative_bits'])
   self.assertLess(f['max_right_product'],1<<f['right_conservative_bits'])
 def test_deterministic_exact_threshold_below_equal_above(self):
  for v in D['calculations'].values():
   c=v['config'];a=c['alphaNum'];fa=c['alphaF'];total=40*(1<<fa)
   for k in (-1,0,1):
    cut=a+k
    lhs=40*cut*(1<<fa)
    rhs=a*total
    self.assertEqual(lhs>rhs,k>0)
    self.assertEqual(lhs>rhs,rcomparison(cut,total,a,fa))
    self.assertLess(lhs,1<<v['post_narrowing_candidate_operands']['left_conservative_bits'])
    self.assertLess(rhs,1<<v['post_narrowing_candidate_operands']['right_conservative_bits'])
 def test_exact_max_sum_and_cut_independent_oracle(self):
  for v in D['calculations'].values():
   n=v['post_narrowing_candidate_operands'];c=v['config']
   for cut,total in [(0,0),(0,n['SUM40_max']),(n['Pcut_max'],0),(n['Pcut_max'],n['SUM40_max'])]:
    direct=40*cut*(1<<c['alphaF'])>c['alphaNum']*total
    self.assertEqual(direct,rcomparison(cut,total,c['alphaNum'],c['alphaF']))
 def test_small_exhaustive_analogue_no_wrap(self):
  # Independent small-precision analogue of the same strict formula.
  for pw in range(1,6):
   for sw in range(1,6):
    for a in range(1,8):
     for fa in range(0,4):
      Lw=pw+6+fa
      Rw=sw+nbits(a)
      for cut in range(1<<pw):
       for total in range(1<<sw):
        lhs=40*cut*(1<<fa);rhs=a*total
        self.assertLess(lhs,1<<Lw)
        self.assertLess(rhs,1<<Rw)
        self.assertEqual(lhs>rhs,rcomparison(cut,total,a,fa))
 def test_v03_immutable_and_bug_provenance(self):
  src=json.loads((ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json').read_text())
  for name,v in D['calculations'].items():
   self.assertEqual(v['v03_wrong_right_bits'],src['CFAR'][name]['integer_compare_right_width_conservative'])
   self.assertNotEqual(v['v03_wrong_right_bits'],v['post_narrowing_candidate_operands']['right_conservative_bits'])
 def test_error_scope_flags_preserve_open_problems(self):
  e=D['error_coverage']
  self.assertIn('EXCLUDED',e['input_Q1_15'])
  self.assertIn('OPEN',e['internal_twiddle_multiplication_rounding'])
  self.assertIn('OPEN',e['butterfly_internal_add_sub_rounding'])
  self.assertIn('OPEN',e['shift_implementation_rounding'])
  self.assertIn('OPEN',e['MF_MTI_intermediate_products_and_accumulators'])
  self.assertIn('INCLUDED',e['twiddle_quantization'])
 def test_no_architecture_or_seed_claim(self):
  self.assertIn('NO_NUMERIC_ARCHITECTURE_APPROVED',D['status'])
  src=(ROOT/'engineering/s04_numeric/s04_c02_cfar_audit_repair_v031.py').read_text()
  self.assertNotIn('default_rng(',src)
  self.assertNotIn('generate_cpi(',src)
if __name__=='__main__':unittest.main()

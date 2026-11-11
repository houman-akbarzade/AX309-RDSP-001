"""Independent exact-integer/rational bounds and deterministic real coefficient tests."""
import json,math,unittest,subprocess,sys
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
# Import is allowed; module creates deterministic analytic JSON without stochastic CPI
import s04_c02_coeff_shift_v03 as m
from s03_reference import model as ref
DATA=json.load(open(ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json'))
class ExactWidthTests(unittest.TestCase):
 def test_fractions_exact_exhaustive_integer_envelope(self):
  cases=0
  for F in (0,1,2,7,13,15,26,30):
   for W in range(2,20):
    lo,hi=m.bounds(W,F,True)
    assert lo<0 and hi>0
    for M in (Fraction(0), hi,hi+Fraction(1,1<<F), -lo,
              Fraction(1,1<<F), Fraction(3,1<<(F+1)),
              Fraction(2)**max(0,W-F-2)):
     req=m.integer_width(M,F,True)
     n=m.ceilfrac(M*(1<<F))
     self.assertGreaterEqual((1<<(req-1))-1,n,(F,W,M,req))
     if req>2: self.assertLess((1<<(req-2))-1,n,(F,W,M,req))
     cases+=1
  self.assertGreater(cases,900)
 def test_unsigned_exact_boundary_fractions(self):
  for F in (0,1,2,13,15,26,30):
   for W in range(1,50):
    hi=Fraction((1<<W)-1,1<<F)
    for M in (Fraction(0),hi,hi+Fraction(1,1<<F),Fraction(1,1<<F),
              Fraction(1<<max(W-F-1,0))):
     req=m.integer_width(M,F,False)
     n=m.ceilfrac(M*(1<<F))
     self.assertGreaterEqual((1<<req)-1,n)
     if req>1: self.assertLess((1<<(req-1))-1,n)
 def test_signed_two_power_and_negative_minimum(self):
  for F in (0,1,15,26):
   for n in range(0,35):
    M=Fraction(1<<n,1<<F)
    w=m.integer_width(M,F,True)
    self.assertEqual(w,max(2,n+2))
    self.assertEqual(m.integer_width(M,F,False),max(1,n+1))
    lo,hi=m.bounds(w,F,True)
    self.assertLessEqual(lo,-M)
    self.assertGreaterEqual(hi,M)
    if w>2:
     self.assertLess(m.bounds(w-1,F,True)[1],M)
 def test_exact_signed_round_nearest_even_negative(self):
  expected={Fraction(-5,2):-2,Fraction(-3,2):-2,Fraction(-1,2):0,
            Fraction(1,2):0,Fraction(3,2):2,Fraction(5,2):2}
  for x,e in expected.items():self.assertEqual(m.round_even(x),e)
  self.assertEqual((-3)//2,-2)
 def test_mf_matches_approved_reverse_conjugation(self):
  a=ref.chirp()
  h=ref.matched_filter()
  import numpy as np
  np.testing.assert_array_equal(h,np.conjugate(a[::-1]))
  self.assertEqual(len(DATA['reference_coefficients']['mf16']),16)
  for i,z in enumerate(h):
   self.assertAlmostEqual(z.real,DATA['reference_coefficients']['mf16'][i]['re'])
   self.assertAlmostEqual(z.imag,DATA['reference_coefficients']['mf16'][i]['im'])
 def test_twiddle_sign_and_unit_magnitude(self):
  import cmath
  for stage in range(1,6):
   n=2**stage
   x=DATA['reference_coefficients']['fft32_twiddles'][str(stage)]
   self.assertEqual(len(x),n//2)
   for j,z in enumerate(x):
    w=cmath.exp(-2j*math.pi*j/n)
    self.assertAlmostEqual(z['re'],w.real)
    self.assertAlmostEqual(z['im'],w.imag)
 def test_coeff_error_and_formats(self):
  for opt,v in DATA['formats'].items():
   self.assertEqual(len(v['mf16']),16)
   self.assertEqual(sum(len(x) for x in v['twiddle32_by_stage'].values()),31)
   W,F=v['metadata']['mf_coeff']
   for c in v['mf16']:
    self.assertLessEqual(abs(c['re_error']),2**(-F-1)+1e-12)
    self.assertLessEqual(abs(c['im_error']),2**(-F-1)+1e-12)
   self.assertGreaterEqual(v['mf_magnitude_max'],1)
 def test_shift_schedule_reconstruction(self):
  schedules=DATA['schedules']
  self.assertEqual(len(schedules),4)
  for k,item in schedules.items():
   self.assertEqual(len(item['shifts']),5)
   scale=2**sum(item['shifts'])
   self.assertEqual(item['FFT_normalization'],scale)
   for profile,g in [('NOISE_ONLY_UNIT',5),('SINGLE_TARGET_REFERENCE_LIKE_LAB',1)]:
    self.assertEqual(item['reconstruction'][profile]['FFT_amplitude_scale'],g*scale)
    self.assertEqual(item['reconstruction'][profile]['power_scale'],(g*scale)**2)
 def test_uncertified_overflow_detected_for_unshifted_B_C(self):
  for opt in ('B','C_hypothetical'):
   v=DATA['schedules']['ZERO']['per_architecture'][opt]
   self.assertFalse(v['all_stages_fit_candidate_output_format'])
  self.assertTrue(DATA['schedules']['ZERO']['per_architecture']['A']['all_stages_fit_candidate_output_format'])
 def test_fft_stage_error_split_and_no_approval(self):
  for schedule in DATA['schedules'].values():
   for v in schedule['per_architecture'].values():
    self.assertEqual(len(v['stage']),5)
    self.assertEqual(len(v['conditional_error_stage_trace']),5)
    self.assertGreaterEqual(v['conditional_MF_MTI_quantization_plus_FFT_one_RNE_each_stage_error_bound'],
                            v['twiddle_only_error_bound_from_mti_input'])
  self.assertEqual(DATA['status'],'ANALYTICAL_PROPOSED_NO_ARCHITECTURE_APPROVED')
 def test_rational_strict_cfar_equal_and_neighbors(self):
  for q in DATA['CFAR'].values():
   self.assertTrue(q['strict_equality_is_no_alarm'])
   self.assertFalse(q['threshold_minus_one'])
   self.assertTrue(q['threshold_plus_one'])
   self.assertEqual(q['raw_exact_I2_plus_Q2_bits'],q['raw_exact_real_square_product_bits']+1)
 def test_no_rng_hardware_or_real_CPI(self):
  s=(ROOT/'engineering/s04_numeric/s04_c02_coeff_shift_v03.py').read_text()
  for x in ('generate_cpi(', 'noise_only_cpi(', 'SeedSequence(', 'default_rng(', 'Vivado'):
   self.assertNotIn(x,s)
if __name__=='__main__':unittest.main()

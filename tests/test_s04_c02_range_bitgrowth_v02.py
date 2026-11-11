"""Independent deterministic S04 C02 numerical range tests; no CPI/PRNG."""
import importlib.util, unittest,math,json
from pathlib import Path
from fractions import Fraction

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'engineering/s04_numeric/s04_c02_range_bitgrowth_v02.py'
DATA=ROOT/'engineering/s04_numeric/S04-C02-range-bitgrowth-v0.2.json'
class RangeBitgrowthTests(unittest.TestCase):
 def setUp(self):
  self.a=json.loads(DATA.read_text())
 def test_exact_stage_gain_ideal(self):
  for g in (1,5):
   for scale in (1,8):
    b=self.a['stages'][str(g)]['unshifted' if scale==1 else 'shift8']
    self.assertAlmostEqual(b['MF_abs_component_conservative_stored'],16*math.sqrt(2))
    self.assertAlmostEqual(b['MTI_abs_component_conservative_stored'],32*math.sqrt(2))
    self.assertAlmostEqual(b['FFT_abs_component_conservative_stored'],1024*math.sqrt(2)/scale)
    self.assertAlmostEqual(b['original_FFT_amp_bound'],1024*math.sqrt(2)*g)
    self.assertAlmostEqual(b['original_power_bound'],2**21*g*g)
 def test_minimum_widths_ideal(self):
  self.assertEqual(self.a['stages']['1']['unshifted']['MF_min_W_F15'],21)
  self.assertEqual(self.a['stages']['1']['unshifted']['MTI_min_W_F15'],22)
  self.assertEqual(self.a['stages']['1']['unshifted']['FFT_min_W_F15'],27)
  self.assertEqual(self.a['stages']['1']['unshifted']['power_min_unsigned_W_F30'],52)
  self.assertEqual(self.a['stages']['1']['unshifted']['sum40_min_unsigned_W_F30'],57)
  self.assertEqual(self.a['stages']['5']['shift8']['FFT_min_W_F13'],22)
  self.assertEqual(self.a['stages']['5']['shift8']['power_min_unsigned_W_F26'],42)
  self.assertEqual(self.a['stages']['5']['shift8']['sum40_min_unsigned_W_F26'],47)
 def test_candidate_formats_have_at_least_theoretical_headroom(self):
  for name,v in self.a['candidate_formats_not_approved'].items():
   for k,fmt in v['stage_storage'].items():
    self.assertTrue(fmt['ideal_bound_fits_stored'],(name,k))
    self.assertGreaterEqual(fmt['unused_integer_bits_vs_minimum'],0)
  self.assertEqual(self.a['candidate_formats_not_approved']['A']['resource_storage_proxies']['raw_16tap_accumulator_bits_conservative'],37)
  self.assertEqual(self.a['candidate_formats_not_approved']['B']['resource_storage_proxies']['raw_16tap_accumulator_bits_conservative'],35)
 def test_power_scale_and_exact_strict_comparator(self):
  for name,v in self.a['candidate_formats_not_approved'].items():
   F=v['formats']['FFT'][1]
   self.assertEqual(v['formats']['power'][1],2*F)
   for g in (1,5):
    m=v['input_profile_reconstruction'][str(g)]
    self.assertEqual(m['power_sum_threshold_scale'],m['FFT_amplitude_scale']**2)
    self.assertEqual(m['MF_MTI_amplitude_scale'],g)
   A=30625 if name=='B' else 490007
   Fa=12 if name=='B' else 16
   S=40*(1<<Fa)
   self.assertFalse(40*A*(1<<Fa)>A*S)
   self.assertTrue(40*(A+1)*(1<<Fa)>A*S)
   self.assertFalse(40*(A-1)*(1<<Fa)>A*S)
 def test_robust_twiddle_requires_extra_headroom_evidence(self):
  t=self.a['quantized_twiddle_growth_risk']
  hi=t['10001/10000']
  lo=t['1']
  self.assertGreater(hi['conservative_unshifted_fft_mag_from_MTI'],lo['conservative_unshifted_fft_mag_from_MTI'])
  self.assertGreater(hi['conservative_unshifted_fft_mag_from_MTI'],
                     lo['conservative_unshifted_fft_mag_from_MTI'])
 def test_no_architecture_selected_or_main_seed(self):
  self.assertEqual(self.a['status'],'ANALYSIS_ONLY_NO_ARCH_APPROVAL')
  self.assertEqual(self.a['main_CPI_generated'],0)
  self.assertFalse(self.a['accepted_S03_seeds_touched'])
  self.assertFalse(self.a['hardware_synthesis_evidence'])
 def test_store_width_proxy_is_only_bitcount(self):
  c=self.a['candidate_formats_not_approved']
  self.assertLess(c['B']['resource_storage_proxies']['RD_complex_FFT_buffer_bits_128x32'],
                  c['A']['resource_storage_proxies']['RD_complex_FFT_buffer_bits_128x32'])
  self.assertLess(c['B']['resource_storage_proxies']['coefficient_rom_bits_16_complex'],
                  c['C_hypothetical']['resource_storage_proxies']['coefficient_rom_bits_16_complex'])

if __name__=='__main__':unittest.main()

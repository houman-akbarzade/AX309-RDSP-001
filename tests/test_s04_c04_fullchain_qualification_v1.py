"""S04-C04 full-chain independent self-checking tests (not C03 regression)."""
from pathlib import Path
from fractions import Fraction as Q
import sys,unittest,json,hashlib,math
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c04_fullchain_qualification_v1 as C04
import s04_c04_selected_C_stage_capture_v1 as D
import s04_c03_independent_oracle_v1 as O
from s03_reference import model as S03
RESULT=json.loads((ROOT/'engineering/s04_numeric/S04-C04-integrated-fullchain-v1.0.json').read_text())
GOLD=json.loads((ROOT/'engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json').read_text())
CASES={z['vector_id']:z for z in RESULT['vectors']}
class C04_Independent_Qual(unittest.TestCase):
 def test_01_full_eighteen_vector_paired_matrix(self):
  self.assertEqual(len(CASES),18)
  self.assertEqual(len(set(CASES)),18)
  self.assertEqual(set(CASES),set(GOLD['records']))
  self.assertEqual(set(C04.KINDS),set(GOLD['kinds']))
 def test_02_frozen_C_schedule_and_output_interfacing(self):
  self.assertEqual(C04.SHIFT,(0,1,0,1,1))
  self.assertEqual(O.CONTRACT['architecture'],'C')
  self.assertEqual(O.CONTRACT['FFT']['output']['W'],25)
  self.assertEqual(O.CONTRACT['FFT']['output']['F'],15)
  for g in (1,5):
   for k in C04.KINDS:
    self.assertEqual(CASES[f'g{g}:{k}']['reconstruction_final_amplitude_factor'],g*8)
 def test_03_independent_rational_golden_digest_for_all_sources(self):
  for key,case in CASES.items():
   self.assertEqual(case['source_sha256'],GOLD['records'][key]['input_rational_SHA256'])
   self.assertEqual(case['input_saturation_count'],GOLD['records'][key]['input_sat_count'])
   self.assertEqual(len(case['source_sha256']),64)
 def test_04_no_implementation_mismatch_any_full_chain_stage(self):
  for case in CASES.values():
   fields=case['bittrue_stage_agreement']
   self.assertEqual(set(fields),{'MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5'})
   for name,st in fields.items():
    self.assertEqual(st['mismatch_count'],0,(case['vector_id'],name))
    self.assertEqual(st['matched_integer_components'],st['total_integer_components'])
    self.assertIsNone(st['first_mismatch'])
    self.assertEqual(st['total_integer_components'],8448 if name=='MF' else 8192)
 def test_05_candidate_capture_all_fft_range_rows_no_legacy_first_row_gap(self):
  src,iq,events,_=C04.source('half_lsb',1)
  actual=D.run_one(src,iq,D.Telemetry(),'C_hypothetical',C04.SHIFT,1,capture_stages=True)
  stages=actual['captured']['fft_stages_range_major']
  self.assertEqual(len(stages),5)
  self.assertTrue(all(len(stage)==128 and all(len(row)==32 for row in stage) for stage in stages))
  self.assertEqual(len(actual['captured']['mf']),33)
  self.assertEqual(len(actual['captured']['mti']),32)
 def test_06_golden_MF_MTI_multiple_positions_independent(self):
  src,iq,events,_=C04.source('onbin_k5',1)
  res=D.run_one(src,iq,D.Telemetry(),'C_hypothetical',C04.SHIFT,1,capture_stages=True)
  golden=GOLD['records']['g1:onbin_k5']
  for key,v in golden['MF'].items():
   p,r=map(int,key.split(':'));self.assertEqual(res['captured']['mf'][p][r],tuple(v))
  for key,v in golden['MTI'].items():
   p,r=map(int,key.split(':'));self.assertEqual(res['captured']['mti'][p][r],tuple(v))
 def test_07_all_five_FFT_stage_golden_at_natural_bins(self):
  src,iq,events,_=C04.source('offbin_k5p37',5)
  res=D.run_one(src,iq,D.Telemetry(),'C_hypothetical',C04.SHIFT,5,capture_stages=True)
  golden=GOLD['records']['g5:offbin_k5p37']
  for key,v in golden['FFT_stages'].items():
   j,r,b=map(int,key.split(':'))
   self.assertEqual(res['captured']['fft_stages_range_major'][j-1][r][b],tuple(v),(key,v))
 def test_08_zero_input_full_chain_exact_zero(self):
  for g in (1,5):
   x=CASES[f'g{g}:zero']
   self.assertEqual(x['input_saturation_count'],0)
   for name in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5'):
    self.assertEqual(x['float_reference_stage_error_original_amplitude'][name]['MAX'],0)
 def test_09_DC_stationary_cancellation_at_MTI_and_FFT(self):
  for g in (1,5):
   x=CASES[f'g{g}:dc_stationary']
   self.assertEqual(x['float_reference_stage_error_original_amplitude']['MTI']['MAX'],0)
   self.assertEqual(x['float_reference_stage_error_original_amplitude']['FFT5']['MAX'],0)
   self.assertEqual(x['internal_overflow_count'],0)
 def test_10_onbin_offbin_expected_peak_position_and_spectral_leakage(self):
  for g in (1,5):
   for k in ('onbin_k5','offbin_k5p37'):
    x=CASES[f'g{g}:{k}']
    self.assertEqual(x['reference_bin_at_range40'],5)
    self.assertEqual(x['fixed_bin_at_range40'],5)
    self.assertEqual(x['input_saturation_count'],0)
   # Check deterministic original S03 Doppler spectral leakage, not Pd or threshold.
   x_on,_,_,_=C04.source('onbin_k5',g)
   x_off,_,_,_=C04.source('offbin_k5p37',g)
   p_on=np.abs(S03.doppler(S03.mti(S03.pulse_compress(x_on)))[40])
   p_off=np.abs(S03.doppler(S03.mti(S03.pulse_compress(x_off)))[40])
   self.assertLess(p_on[6]/p_on[5],1e-10)
   self.assertGreater(p_off[6]/p_off[5],.1)
 def test_11_signed_boundary_and_negative_half_lsb(self):
  for g in (1,5):
   hi=CASES[f'g{g}:signed_extreme']
   half=CASES[f'g{g}:half_lsb']
   self.assertEqual(hi['input_saturation_count'],0)
   self.assertEqual(half['input_saturation_count'],0)
  self.assertEqual(O.ref_round(Q(-1,2)),0)
  self.assertEqual(O.ref_round(Q(-3,2)),-2)
  self.assertEqual(O.ref_round(Q(3,2)),2)
  self.assertNotEqual((-1)>>1,O.ref_round(Q(-1,2)))
 def test_12_input_saturation_stress_kept_without_exclusion(self):
  for g in (1,5):
   x=CASES[f'g{g}:overrange']
   self.assertEqual(x['input_saturation_count'],8448)
   self.assertEqual(x['internal_overflow_count'],0)
   self.assertGreater(x['float_reference_stage_error_original_amplitude']['FFT5']['MAX'],50*g)
   self.assertEqual(x['bittrue_stage_agreement']['FFT5']['mismatch_count'],0)
 def test_13_normal_vectors_all_no_processing_overflow(self):
  for case in CASES.values():
   self.assertEqual(case['internal_overflow_count'],0,case['vector_id'])
 def test_14_source_and_processing_effect_nonconflation(self):
  for case in CASES.values():
   for name in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5'):
    a=case['source_quantization_effect_stage_original_amplitude'][name]
    b=case['fixed_coefficient_twiddle_arithmetic_effect_stage_original_amplitude'][name]
    total=case['float_reference_stage_error_original_amplitude'][name]
    self.assertLessEqual(total['MAX'],a['MAX']+b['MAX']+1e-7)
    self.assertLessEqual(total['RMS'],a['RMS']+b['RMS']+1e-7)
    self.assertGreaterEqual(total['MAX']+1e-7,total['RMS'])
 def test_15_original_unit_scaling_source_error(self):
  for k in ('signed_extreme','half_lsb','negative_alternating'):
   # Same normalized exact source patterns at both g, hence Float vs fixed
   # input numerical error scales exactly by g; no source population claim.
   a=CASES[f'g1:{k}']['input_float_max_rms']['MAX']
   b=CASES[f'g5:{k}']['input_float_max_rms']['MAX']
   self.assertAlmostEqual(b,5*a,places=9)
 def test_16_deterministic_expected_source_not_candidate_helpers(self):
  code=(ROOT/'engineering/s04_numeric/s04_c04_independent_golden_v1.py').read_text()
  for bad in ('D.run_one(', 'D.rne(', 'D.shifted_round('):
   self.assertNotIn(bad,code)
  self.assertIn('O.fft32_oracle',code)
  self.assertIn('O.mf_at',code)
 def test_17_no_seed_main_CPI_or_hardware(self):
  for name in ('s04_c04_fullchain_qualification_v1.py','s04_c04_independent_golden_v1.py'):
   text=(ROOT/'engineering/s04_numeric'/name).read_text()
   for forbidden in ('noise_only_cpi(', 'generate_cpi(', 'default_rng(', 'np.random', 'SeedSequence('):
    self.assertNotIn(forbidden,text)
  self.assertTrue(RESULT['no_main_statistical_CPI'])
  self.assertTrue(RESULT['no_historic_accepted_seeds'])
 def test_18_C03_PASS_C04_OPEN_and_unchanged_gate(self):
  progress=json.loads((ROOT/'engineering/S04-progress.json').read_text())
  self.assertEqual(progress['completed_count'],3)
  self.assertTrue(progress['criteria'][2]['completed'])
  self.assertFalse(progress['criteria'][3]['completed'])
  self.assertEqual(progress['stage_percent'],37.5)
  self.assertEqual(progress['gate'],'open')
  project=json.loads((ROOT/'project.yaml').read_text())
  self.assertEqual(project['progress']['overall_percent'],28.125)
  self.assertEqual(project['gate_status'],'open')
if __name__=='__main__':unittest.main(verbosity=2)

"""Independent deterministic v0.6 paired audit assertions; no acceptance CPI."""
import json,unittest,sys,math,hashlib
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c02_paired_analysis_v06 as A
import s04_c02_integer_maps_v06 as M
DATA=json.loads((ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json').read_text())
class PairedAudit(unittest.TestCase):
 def test_complete_pair_count_and_stable_id(self):
  self.assertEqual(len(DATA['all_run_metrics']),216)
  self.assertEqual(len(DATA['pairwise_per_vector']),66)
  self.assertEqual(sum(len(x) for x in DATA['pairwise_per_vector'].values()),1188)
  self.assertEqual(len(DATA['all_vector_ids']),18)
  self.assertEqual(len(set(DATA['all_vector_ids'])),18)
 def test_intersection_and_explicit_reasons(self):
  self.assertEqual(DATA['denominators']['all_vectors_per_architecture'],18)
  self.assertEqual(DATA['denominators']['common_no_saturation_per_architecture'],14)
  self.assertEqual(DATA['denominators']['g1_common'],7)
  self.assertEqual(DATA['denominators']['g5_common'],7)
  bad={x['vector_id'] for x in DATA['excluded_from_common_detailed']}
  self.assertEqual(bad,{'g1:near_clip','g5:near_clip','g1:overrange_stress','g5:overrange_stress'})
  for x in DATA['excluded_from_common_detailed']:
   self.assertTrue(x['reasons'])
  self.assertEqual(set(DATA['all_vector_ids']),set(DATA['common_set_ids'])|bad)
 def test_same_source_digest_across_candidates(self):
  for vid in DATA['all_vector_ids']:
   digest={x['source_vector_SHA256'] for key,x in DATA['all_run_metrics'].items() if key.startswith(vid+'|')}
   self.assertEqual(len(digest),1)
   self.assertEqual(len(digest.pop()),64)
 def test_matched_profile_and_stage_metrics(self):
  for key,x in DATA['all_run_metrics'].items():
   self.assertEqual(x['reference_CUT_count'],2782)
   self.assertEqual(len(x['stage_error']),7)
   self.assertAlmostEqual(x['FFT_bin_error']['RMS'],x['stage_error']['FFT5']['RMS'],places=11)
   self.assertAlmostEqual(x['FFT_bin_error']['MAX'],x['stage_error']['FFT5']['MAX'],places=11)
   for stage,st in x['stage_error'].items():
    self.assertGreaterEqual(st['MAX']+1e-12,st['RMS'])
   self.assertEqual(x['cut_direction_0_to_1']+x['cut_direction_1_to_0'],x['cut_changed_count'])
 def test_strict_cfar_margin_and_alpha_consistency(self):
  for key,x in DATA['all_run_metrics'].items():
   a,f=x['alpha_candidate_rational']
   self.assertAlmostEqual(x['alpha_abs_difference'],abs(a/(1<<f)-A.ALPHA_REF))
   for m in x['cut_mismatches_all']:
    self.assertNotEqual(m['float_alarm'],m['integer_alarm'])
    signed=int(m['integer_raw_comparator_margin'])
    self.assertEqual(signed>0,m['integer_alarm'])
    self.assertEqual(m['float_threshold_margin_original_power']>0,m['float_alarm'])
 def test_no_false_native_cluster_claim(self):
  self.assertEqual(DATA['native_integer_clustering'],'OPEN_NOT_IMPLEMENTED')
  for x in DATA['all_run_metrics'].values():
   self.assertEqual(x['integer_native_clustering_status'],'OPEN_NOT_IMPLEMENTED')
   self.assertEqual(x['full_cluster_bittrue_match'],'OPEN')
 def test_pairwise_stage_delta_independent_recalculation(self):
  cases=DATA['all_run_metrics']
  for pair,rows in DATA['pairwise_per_vector'].items():
   a,b=pair.split('__VS__')
   for r in rows:
    sa=cases[r['vector_id']+'|'+a]
    sb=cases[r['vector_id']+'|'+b]
    for stage in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5'):
     val=r['stagewise_paired_deltas_original_float_amplitude'][stage]
     self.assertAlmostEqual(val['MAX_error_A_minus_B'],sa['stage_error'][stage]['MAX']-sb['stage_error'][stage]['MAX'])
     self.assertAlmostEqual(val['RMS_error_A_minus_B'],sa['stage_error'][stage]['RMS']-sb['stage_error'][stage]['RMS'])
    z=r['FFT5_per_bin_paired_error_A_minus_B']
    self.assertEqual(z['A_smaller_count']+z['B_smaller_count']+z['equal_count'],4096)
 def test_C_distributed_vs_A_exact_on_common(self):
  k='A:DISTRIBUTED_3__VS__C_hypothetical:DISTRIBUTED_3'
  rows=DATA['pairwise_per_vector'][k]
  common=[x for x in rows if x['common_no_saturation']]
  self.assertEqual(len(common),14)
  for x in common:
   self.assertEqual(x['FFT5_per_bin_paired_error_A_minus_B']['A_smaller_count'],0)
   self.assertEqual(x['FFT5_per_bin_paired_error_A_minus_B']['B_smaller_count'],0)
   self.assertEqual(x['FFT5_per_bin_paired_error_A_minus_B']['equal_count'],4096)
 def test_C_distributed_not_worse_than_B_on_all_bins_is_false(self):
  k='B:DISTRIBUTED_3__VS__C_hypothetical:DISTRIBUTED_3'
  rows=[x for x in DATA['pairwise_per_vector'][k] if x['common_no_saturation']]
  self.assertGreater(sum(x['FFT5_per_bin_paired_error_A_minus_B']['A_smaller_count'] for x in rows),0)
  self.assertGreater(sum(x['FFT5_per_bin_paired_error_A_minus_B']['B_smaller_count'] for x in rows),0)
 def test_power_full_map_float_and_cfar_array_shape(self):
  src,iq,tel=M.source_vector('phase_interference',1)
  r=M.run_one(src,iq,tel,'C_hypothetical',[0,1,0,1,1],1,capture_maps=True)
  p,fft,mask,raw=A.fixed_map(r,'C_hypothetical','DISTRIBUTED_3',1)
  self.assertEqual(p.shape,(128,32));self.assertEqual(mask.shape,(128,32))
  self.assertEqual(fft.shape,(128,32))
  self.assertEqual(int(mask.sum()),r['cfar_alarm_count'])
  self.assertEqual(len(r['captured']['cut_records']),2782)
  self.assertEqual(int(mask[:3,:].sum()),0)
 def test_hypothesis_not_approval(self):
  self.assertIn('UNAPPROVED',DATA['status'])
  self.assertEqual(DATA['C02'],'OPEN')
  self.assertEqual(set(DATA['hypothesis_C_distributed_3']),{'A:DISTRIBUTED_3','B:DISTRIBUTED_3'})
 def test_reference_uses_approved_frozen_alpha_not_s03_default(self):
  import json
  approved=json.loads((ROOT/'decisions/S02-C-CFAR-02-v1.2-approved-amendment.json').read_text())['alpha_frozen']
  self.assertEqual(A.ALPHA_REF,approved)
  self.assertEqual(approved,7.476912055027923)
  x=DATA['all_run_metrics']['g1:phase_interference|A:DISTRIBUTED_3']
  self.assertEqual(x['alpha_real_reference'],approved)
  code=(ROOT/'engineering/s04_numeric/s04_c02_paired_analysis_v06.py').read_text()
  self.assertIn('S03.cfar_2d(p,alpha=ALPHA_REF)',code)
 def test_same_cfar_mask_does_not_imply_same_host_peak(self):
  diag=json.loads((ROOT/'engineering/s04_numeric/S04-C02-paired-decision-summary-v0.6.json').read_text())
  for a in ('A','C_hypothetical'):
   row=diag['per_architecture'][a+':DISTRIBUTED_3']
   self.assertEqual(sum(x['cfar_cut_change_full'] for x in row['profiles']),0)
   self.assertGreater(row['host_first20_peak_signature_differing_cases'],0)
   self.assertEqual(row['integer_native_cluster_status'],'OPEN')
 def test_alpha_quantization_observed_effect_is_zero_not_assumed_universal(self):
  summary=json.loads((ROOT/'engineering/s04_numeric/S04-C02-paired-decision-summary-v0.6.json').read_text())
  for row in summary['per_architecture'].values():
   self.assertEqual(row['alpha_only_reference_cut_changes'],0)
   self.assertEqual(row['alpha_only_fixed_power_cut_changes'],0)
 def test_no_stochastic_seed_calls(self):
  code=(ROOT/'engineering/s04_numeric/s04_c02_paired_analysis_v06.py').read_text()
  for t in ('noise_only_cpi(', 'generate_cpi(', 'default_rng(', 'np.random', 'SeedSequence('):
   self.assertNotIn(t,code)
if __name__=='__main__':unittest.main()

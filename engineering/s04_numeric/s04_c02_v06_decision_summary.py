"""Audit digest and decision matrix grounded in full paired JSON, no ranking."""
from pathlib import Path
import json,hashlib,math,collections
ROOT=Path(__file__).resolve().parents[2]
J=json.load(open(ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json'))
P=json.load(open(ROOT/'engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json'))
R=json.load(open(ROOT/'engineering/s04_numeric/S04-C02-range-bitgrowth-v0.2.json'))
A=json.load(open(ROOT/'engineering/s04_numeric/S04-C02-cfar-width-arithmetic-audit-v0.3.1.json'))
out={'project':'AX309-RDSP-001','version':'v0.6','decision':'HOLD_NO_ARCH_APPROVED',
 'common_count':len(J['common_set_ids']),'all_count':len(J['all_vector_ids']),
 'per_architecture':{},'hypothesis_C_distributed':{},
 'statistical_generalization':'NOT_ALLOWED','native_integer_clustering':'OPEN'}
for opt in ('A','B','C_hypothetical'):
 for shift in ('ZERO','EARLY_3','DISTRIBUTED_3','ALL_5'):
  k=f'{opt}:{shift}'
  x=[v for name,v in J['all_run_metrics'].items() if name.endswith('|'+k)]
  entries=[]
  directions=collections.Counter(m['direction'] for r in x for m in r['cut_mismatches_all'])
  margins=[abs(m['float_threshold_margin_original_power']) for r in x for m in r['cut_mismatches_all']]
  int_margins=[abs(m['fixed_threshold_margin_original_power']) for r in x for m in r['cut_mismatches_all']]
  host_cluster_count_disagreement=sum(r['Float_S03_reference_clusters_count']!=r['Float_host_clusters_on_fixed_mask_count'] for r in x)
  def key_peaks(records):
   return [(int(r['range_bin']),int(r['doppler_bin']),int(r['cluster_cells'])) for r in records]
  host_peak_disagreement=sum(key_peaks(r['Float_S03_reference_clusters_count'] and r['Float_host_cluster_peak_records_reference'] or [])
                        !=key_peaks(r['Float_host_cluster_peak_records_on_fixed']) for r in x)
  for g in ('1','5'):
   summary=J['paired_summary'][k][g]
   common=summary['common_cases']
   entries.append({'g':int(g),
      'common_n':len(summary['common_vector_ids']),'full_n':len(summary['all_vector_ids']),
      'common_stages':common,'full_stages':summary['all_cases'],
      'common_FFT5_MAX':common['FFT5']['MAX'],'common_FFT5_RMS':common['FFT5']['RMS'],
      'full_FFT5_MAX':summary['all_cases']['FFT5']['MAX'],
      'full_FFT5_RMS':summary['all_cases']['FFT5']['RMS'],
      'cfar_cut_change_common':summary['total_CFAR_cut_changes_common_cases'],
      'cfar_cut_change_full':summary['total_CFAR_cut_changes_all_cases'],
      'input_sat_event_count_full':summary['total_input_saturations_all_cases'],
      'internal_event_count_full':summary['total_internal_events_all_cases']})
  fmt=R['candidate_formats_not_approved'][opt]
  out['per_architecture'][k]={'option':opt,'schedule':shift,'profiles':entries,
   'cfar_direction_full':dict(directions),
   'cfar_float_reference_abs_margin_min':min(margins) if margins else None,
   'cfar_float_reference_abs_margin_max':max(margins) if margins else None,
   'cfar_fixed_abs_margin_min':min(int_margins) if int_margins else None,
   'cfar_fixed_abs_margin_max':max(int_margins) if int_margins else None,
   'alpha_only_reference_cut_changes':sum(r['reference_alpha_only_changed_CUT'] for r in x),
   'alpha_only_fixed_power_cut_changes':sum(r['fixed_power_alpha_only_changed_CUT'] for r in x),
   'host_cluster_count_differing_cases':host_cluster_count_disagreement,
   'host_first20_peak_signature_differing_cases':host_peak_disagreement,
   'integer_native_cluster_status':'OPEN',
   'FFT_complex_buffer_bits_proxy':fmt['resource_storage_proxies']['RD_complex_FFT_buffer_bits_128x32'],
   'RD_power_buffer_bits_proxy':fmt['resource_storage_proxies']['RD_power_buffer_bits_128x32'],
   'MF_raw_accumulator_signed_width':fmt['resource_storage_proxies']['raw_16tap_accumulator_bits_conservative'],
   'candidate_full_width_CFAR_comparator_bits':[
    A['calculations'][opt]['full_precision_pre_narrowing_path']['left_conservative_bits'],
    A['calculations'][opt]['full_precision_pre_narrowing_path']['right_conservative_bits']],
   'logic/control_complexity':'OPEN: five FFT shifts, RNE sites, pipeline and saturation flag placement not approved',
   'req_scr_01':'BINDING_OPEN','req_rng_03':'BINDING_OPEN'}
pair_common=J['pairwise_per_vector']['A:DISTRIBUTED_3__VS__C_hypothetical:DISTRIBUTED_3']
pair_cb=J['pairwise_per_vector']['B:DISTRIBUTED_3__VS__C_hypothetical:DISTRIBUTED_3']
for g in (1,5):
 rows_ac=[r for r in pair_common if r['vector_id'].startswith(f'g{g}:') and r['common_no_saturation']]
 rows_bc=[r for r in pair_cb if r['vector_id'].startswith(f'g{g}:') and r['common_no_saturation']]
 out['hypothesis_C_distributed'][str(g)]={
  'common_vectors':len(rows_ac),
  'A_vs_C_paired_MAX_differences':sorted(set(r['stagewise_paired_deltas_original_float_amplitude']['FFT5']['MAX_error_A_minus_B'] for r in rows_ac)),
  'A_vs_C_equal_bin_errors':sum(r['FFT5_per_bin_paired_error_A_minus_B']['equal_count'] for r in rows_ac),
  'B_vs_C_B_smaller_bin_errors':sum(r['FFT5_per_bin_paired_error_A_minus_B']['A_smaller_count'] for r in rows_bc),
  'B_vs_C_C_smaller_bin_errors':sum(r['FFT5_per_bin_paired_error_A_minus_B']['B_smaller_count'] for r in rows_bc),
  'B_vs_C_equal_bin_errors':sum(r['FFT5_per_bin_paired_error_A_minus_B']['equal_count'] for r in rows_bc),
  'rank_or_approval':'NONE',
  'conditional_cost_note':'C uses narrower FFT buffer than A and wider than B; not a synthesized utilization estimate'}
target=ROOT/'engineering/s04_numeric/S04-C02-paired-decision-summary-v0.6.json'
target.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('SHA256',hashlib.sha256(target.read_bytes()).hexdigest())
for k,r in out['per_architecture'].items():
 print(k,'directions',r['cfar_direction_full'],'host peak diff cases',r['host_first20_peak_signature_differing_cases'],
       'cluster count',r['host_cluster_count_differing_cases'],'margins',r['cfar_float_reference_abs_margin_min'],r['cfar_fixed_abs_margin_min'])
print('C hypothesis',out['hypothesis_C_distributed'])

"""S04-C05 independently self-checking integer power/CFAR/grouping tests.

Independent expected values from math/Fraction, original C03 oracle,
and separate union-find component algorithm; not native function re-use.
"""
import unittest,sys,json,hashlib
from pathlib import Path
from fractions import Fraction
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c05_native_integer_v1 as N
import s04_c05_integrated_qualification_v1 as I
import s04_c03_independent_oracle_v1 as O
E=json.loads((ROOT/'engineering/s04_numeric/S04-C05-integrated-power-cfar-grouping-v1.0.json').read_text())
BY={x['vector_id']:x for x in E['all_cases']}
def blank():
    return [[False]*32 for _ in range(128)],[[0]*32 for _ in range(128)]
class C05IndependentQualification(unittest.TestCase):
 def test_01_frozen_architecture_and_selected_alpha(self):
    import json
    c=json.loads((ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json').read_text())
    self.assertEqual(c['architecture'],'C')
    self.assertEqual(c['schedule'],[0,1,0,1,1])
    self.assertEqual(c['CFAR']['strict_comparison'],'40*Pcut*65536 > 490007*SUM40')
    self.assertEqual((N.ALPHA_N,N.ALPHA_DEN),(490007,65536))
 def test_02_power_zero_signed_boundaries_and_saturation(self):
    for iq in ((0,0),(1,-1),(-1,0),(1<<24-1,0),(-(1<<24),0)):
        q,clip,t=N.checked_sqpower(iq)
        gold,cl=O.oracle_power(*iq)
        self.assertEqual((q,clip),(gold,cl))
        self.assertEqual(t['raw'],iq[0]**2+iq[1]**2)
    vmax=(1<<24)-1
    q,clip,_=N.checked_sqpower((vmax,vmax))
    self.assertEqual((q,clip),((1<<46)-1,True))
    q,clip,_=N.checked_sqpower((0,0))
    self.assertEqual((q,clip),(0,False))
 def test_03_power_full_4096_map_no_silent_wrap(self):
    rd=[[(0,0)]*32 for _ in range(128)]
    rd[3][4]=(-(1<<24),-(1<<24))
    power,events=N.native_power_map(rd)
    self.assertEqual(power[3][4],(1<<46)-1)
    self.assertEqual(len(events),1)
    self.assertEqual(events[0]['integer_pre_narrow'],str(1<<49))
    self.assertEqual(events[0]['range'],3)
    self.assertEqual(sum(sum(x>0 for x in row) for row in power),1)
 def test_04_exact_40_training_geometry(self):
    self.assertEqual(len(N.GEO),40)
    self.assertEqual(set(N.GEO),set((dr,dd) for dr in range(-3,4) for dd in range(-3,4) if abs(dr)>1 or abs(dd)>1))
    p=[[0]*32 for _ in range(128)]
    for dr,db in N.GEO:p[25+dr][10+db]=100+dr*10+db
    p[25][10]=9999
    val,_=N.checked_train(p,25,10)
    self.assertEqual(val,sum(100+dr*10+db for dr,db in N.GEO))
    self.assertEqual(val,40*100)
 def test_05_sum40_uint52_corner(self):
    p=[[(1<<46)-1]*32 for _ in range(128)]
    val,_=N.checked_train(p,3,3)
    self.assertEqual(val,40*((1<<46)-1))
    self.assertEqual((val,False),O.oracle_sum40([(1<<46)-1]*40))
    self.assertLess(val,1<<52)
 def test_06_strict_threshold_exact_tie_and_adjacent_integer(self):
    # choose training=40*65536, then cut=490007 is exactly equal
    t=40*65536
    for cut,expect in ((490006,False),(490007,False),(490008,True)):
        got,margin=N.compare(cut,t)
        self.assertEqual(got,expect)
        self.assertEqual(got,O.oracle_cfar(cut,t))
        self.assertEqual((margin>0),expect)
    self.assertEqual(N.compare(490007,t)[1],0)
 def test_07_strict_CFAR_wide_products_independent_Fraction(self):
    for cut,total in ((0,0),(1,0),(0,(1<<52)-1),((1<<46)-1,(1<<52)-1)):
        hit,margin=N.compare(cut,total)
        self.assertEqual(hit,Fraction(cut)>Fraction(490007,65536)*Fraction(total,40))
        self.assertEqual(margin,40*cut*65536-490007*total)
 def test_08_VALID_2782_CUT_boundary_zero_nonwrap(self):
    p=[[0]*32 for _ in range(128)]
    mask,recs=N.native_cfar(p)
    self.assertEqual(len(recs),2782)
    self.assertEqual(sum(x['alarm'] for x in recs),0)
    self.assertEqual(sum(sum(row) for row in mask),0)
    self.assertEqual((recs[0]['range'],recs[0]['doppler_bin']),(3,3))
    self.assertEqual((recs[-1]['range'],recs[-1]['doppler_bin']),(109,28))
 def test_09_clustering_diagonal_touch_is_one_cluster(self):
    a,p=blank()
    for pos,val in (((10,10),20),((11,11),10),((12,12),5)):
        a[pos[0]][pos[1]]=True;p[pos[0]][pos[1]]=val
    got=N.native_clusters(a,p)
    self.assertEqual(len(got),1)
    self.assertEqual(got[0]['cluster_cells'],3)
    self.assertEqual((got[0]['range_bin'],got[0]['doppler_bin']),(10,10))
 def test_10_no_Doppler_wrap_and_signed_bin_tie(self):
    a,p=blank()
    a[10][0]=True;a[10][31]=True;p[10][0]=p[10][31]=15
    records=N.native_clusters(a,p)
    self.assertEqual(len(records),2) # first and last bin do NOT wrap
    self.assertEqual([(x['range_bin'],x['doppler_bin']) for x in records],[(10,31),(10,0)])
    a,p=blank()
    for r,d in ((15,15),(15,16),(16,16)):
        a[r][d]=True;p[r][d]=5
    rec=N.native_clusters(a,p)
    self.assertEqual((rec[0]['range_bin'],rec[0]['doppler_bin']),(15,16))
    self.assertTrue(rec[0]['tie_flag'])
    self.assertEqual(rec[0]['max_equal_power_cells'],3)
 def test_11_exact_tie_uses_lower_range_after_doppler(self):
    a,p=blank()
    for r,d in ((5,20),(4,20),(5,21)):
        a[r][d]=True;p[r][d]=111
    got=N.native_clusters(a,p)
    self.assertEqual((got[0]['range_bin'],got[0]['doppler_bin']),(4,20))
    self.assertEqual(got[0]['max_equal_power_cells'],3)
 def test_12_target_records_integer_and_rational_fields(self):
    a,p=blank();a[4][20]=True;p[4][20]=7
    rec=N.native_clusters(a,p)[0]
    self.assertEqual(rec['record_id'],0)
    self.assertEqual(rec['signed_doppler_bin'],-12)
    self.assertEqual(rec['range_m_exact_rational'],[4*299792458,2000000])
    self.assertEqual(Fraction(*rec['velocity_m_s_nominal_rational']),Fraction(-12*300000000,2*10000000000*32//1000))
 def test_13_independent_union_find_vs_native_all_cases(self):
    self.assertEqual(E['vector_count'],18)
    self.assertEqual(len(BY),18)
    self.assertTrue(all(x['cluster_match_independent_union_find'] for x in BY.values()))
    self.assertTrue(all(x['oracle_complete_power_CUT_grouping']=='PASS' for x in BY.values()))
 def test_14_every_full_MAP_cell_and_CUT_independent(self):
    self.assertEqual(E['power_bins_compared'],18*4096)
    self.assertEqual(E['CFAR_CUTs_compared'],18*2782)
    self.assertTrue(all(x['power_bin_count']==4096 and x['cut_count']==2782 for x in BY.values()))
    self.assertTrue(all(x['power_overflow_events']==0 for x in BY.values()))
 def test_15_all_C05_DUT_fixed_masks_v06_replayed(self):
    old=json.loads((ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json').read_text())
    for vid,cur in BY.items():
        key=vid+'|C_hypothetical:DISTRIBUTED_3'
        historical=old['all_run_metrics'][key]
        self.assertEqual(cur['changed_CFAR_CUT_vs_S03_Float'],historical['cut_changed_count'])
        self.assertEqual(cur['native_alarm_count'],historical['integer_CFAR_alarms'])
        self.assertEqual(cur['native_cluster_count'],historical['Float_host_clusters_on_fixed_mask_count'])
 def test_16_reproduce_two_specific_peak_signature_differences(self):
    self.assertEqual(len(E['v06_discrepancies']),2)
    self.assertEqual(set(x['v06_vector_id'] for x in E['v06_discrepancies']),{'g1:phase_interference','g5:phase_interference'})
    for x in E['v06_discrepancies']:
        self.assertEqual(x['reference_peaks'][0],[3,20])
        self.assertEqual(x['native_peaks'][0],[4,20])
        self.assertTrue(x['reference_exact_peak_competitors']['float_reference_exact_tie'])
        self.assertEqual(x['integer_peak_competitors']['delta_r4_minus_r3'],54948)
        self.assertTrue(x['same_CFAR_alarm_mask'])
        self.assertTrue(x['independent_grouping_matches_S03_host_on_fixed'])
 def test_17_peak_changes_NOT_waived_by_C05(self):
    for x in E['v06_discrepancies']:
        self.assertIn('retain as open',x['decision'])
        self.assertIn('C06',x['decision'])
    self.assertTrue(E['Float_vs_fixed_mismatch_is_not_automatically_waived'])
 def test_18_zero_and_saturation_masks_separate(self):
    for g in (1,5):
        c=BY[f'g{g}:zero'];self.assertEqual(c['native_alarm_count'],0)
        self.assertEqual(c['native_cluster_count'],0)
        stress=BY[f'g{g}:overrange_stress']
        self.assertEqual(stress['input_saturation_events'],8448)
        self.assertEqual(stress['internal_overflow_events_from_DUT'],0)
 def test_19_no_architecture_change_or_statistical_CPI(self):
    s=json.loads((ROOT/'engineering/S04-progress.json').read_text())
    self.assertEqual(s['completed_count'],4)
    self.assertTrue(s['criteria'][3]['completed'])
    self.assertFalse(s['criteria'][4]['completed'])
    self.assertEqual(s['stage_percent'],50.0)
    self.assertEqual(s['project_percent'],29.166666666666668)
    self.assertEqual(s['gate'],'open')
    self.assertEqual(E['fft_shifts'],[0,1,0,1,1])
    self.assertEqual(E['statistics'],'NOT_EXECUTED')
if __name__=='__main__':unittest.main(verbosity=2)

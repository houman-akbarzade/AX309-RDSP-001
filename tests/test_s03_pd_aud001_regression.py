"""Only deterministic scorer cases; NEVER generate target CPI or touch reserved seed."""
import itertools
import json
import unittest
from pathlib import Path
import numpy as np
from s03_reference import pd_acceptance_candidate as pd
from s03_reference import model as model

FIXTURE=Path(__file__).parent/'fixtures/s03_pd_v02_pre_fix_nonV_baseline.json'

def rec(k,b,idx=0):
    return {'record_id':idx,'range_bin':k,'doppler_bin':b,
            'velocity_m_s_nominal':float(model.bin_velocity(b))}

def power(b=4,mode='valid'):
    p=np.zeros(32,dtype=float)
    p[b]=15
    if mode=='tie':p[(b+1)%32]=15
    if mode=='allzero':p[:]=0
    if mode=='global_elsewhere':p[(b+3)%32]=20
    return p

class TestVContractTruthTable(unittest.TestCase):
    def test_exhaustive_D_E_and_error_boundary(self):
        border=pd.DOPPLER_ACCURACY_M_S
        for matched,eligible,error,expected in itertools.product((False,True),(False,True),
                (border-1e-6,border,border+1e-6,0.,.46875),(False,True)):
            rule=bool(matched and eligible and error<=border)
            if rule!=expected:continue
            with self.subTest(matched=matched,eligible=eligible,error=error):
                self.assertEqual(pd.doppler_accuracy_event(matched,eligible,error),expected)

    def test_just_inside_exactly_at_and_outside_boundary(self):
        half=pd.DOPPLER_ACCURACY_M_S
        for e,want in [(0,True),(half-1e-9,True),(half,True),(half+1e-9,False),(.46875,False)]:
            with self.subTest(error=e):
                self.assertEqual(pd.doppler_accuracy_event(True,True,e),want)

    def test_independent_false_cases_and_invalid_error(self):
        for d,e in itertools.product((False,True),repeat=2):
            if not(d and e):
                self.assertFalse(pd.doppler_accuracy_event(d,e,None))
        for value in (float('nan'),float('inf'),float('-inf'),-0.01,None):
            with self.subTest(value=value):
                with self.assertRaises((ValueError,TypeError)):
                    pd.doppler_accuracy_event(True,True,value)

class TestScorerAndNonVRegression(unittest.TestCase):
    def test_full_pre_fix_nonV_baseline_invariance(self):
        data=json.loads(FIXTURE.read_text())
        self.assertEqual(len(data),10)
        for tag,s in data.items():
            with self.subTest(case=tag):
                z=pd.score_detection_records(s['detections'],matched_range_power_bins=s['power_row'])
                for key,source in [('status','status'),('detection_and_one_to_one_association','D'),
                      ('range_accuracy_conditional','R'),('joint_detection_and_both_accuracies','J'),
                      ('extra_unmatched_cluster_count','extra'),('matched_record_id','match')]:
                    self.assertEqual(z.get(key),s[source],msg=key)
                if z['status']=='VALID':
                    self.assertEqual(z['doppler_halfbin_accuracy_conditional'],
                       bool(z['detection_and_one_to_one_association'] and z['doppler_peak_eligible']
                           and (z['velocity_error_m_s_nominal'] is not None)
                           and z['velocity_error_m_s_nominal']<=pd.DOPPLER_ACCURACY_M_S))
                    if tag=='tie':
                        self.assertTrue(s['V_legacy'])
                        self.assertFalse(z['doppler_halfbin_accuracy_conditional'])

    def test_actual_scorer_all_four_D_E_validity_combinations(self):
        cases=[
            ('D0 E0', [rec(47,4)],None,False,False),
            ('D1 E1', [rec(40,4)],power(4),True,True),
            ('D1 E0 tied', [rec(40,4)],power(4,'tie'),True,False),
            ('D1 E0 no positive peak', [rec(40,4)],power(4,'allzero'),True,False),
            ('D1 E0 wrong strongest', [rec(40,4)],power(4,'global_elsewhere'),True,False),
        ]
        for tag,records,prow,D,E in cases:
            with self.subTest(case=tag):
                r=pd.score_detection_records(records,matched_range_power_bins=prow)
                self.assertEqual(r['status'],'VALID')
                self.assertEqual(r['detection_and_one_to_one_association'],D)
                self.assertEqual(r['doppler_peak_eligible'],E)
                self.assertEqual(r['doppler_halfbin_accuracy_conditional'],bool(D and E))

    def test_error_outside_half_bin_even_if_peak_eligible(self):
        s=pd.score_detection_records([rec(40,5)],matched_range_power_bins=power(5))
        self.assertTrue(s['detection_and_one_to_one_association'])
        self.assertTrue(s['doppler_peak_eligible'])
        self.assertFalse(s['doppler_halfbin_accuracy_conditional'])
        self.assertEqual(s['velocity_error_m_s_nominal'],.46875)

    def test_invalid_records_and_missing_power_row(self):
        self.assertEqual(pd.score_detection_records([],valid_input=False)['status'],'INCONCLUSIVE')
        self.assertEqual(pd.score_detection_records([rec(40,4)])['status'],'INCONCLUSIVE')
        self.assertEqual(pd.score_detection_records([rec(40,4)],matched_range_power_bins=[np.nan]*32)['status'],'INCONCLUSIVE')
        self.assertEqual(pd.score_detection_records([rec(40,4),rec(41,4)])['status'],'INCONCLUSIVE')
        self.assertEqual(pd.score_detection_records([rec(40,4,0),rec(40,4,0)])['status'],'INCONCLUSIVE')

    def test_association_does_not_require_doppler_eligibility(self):
        z=pd.score_detection_records([rec(40,4),rec(60,5,1)],matched_range_power_bins=power(4,'tie'))
        self.assertTrue(z['detection_and_one_to_one_association'])
        self.assertTrue(z['range_accuracy_conditional'])
        self.assertFalse(z['doppler_halfbin_accuracy_conditional'])
        self.assertFalse(z['joint_detection_and_both_accuracies'])
        self.assertEqual(z['extra_unmatched_cluster_count'],1)

if __name__=='__main__':
    unittest.main()

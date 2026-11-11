"""No stochastic radar/Pd trial: hand-authored cluster records and exact CI identities only."""
import unittest,math
import numpy as np
from scipy.stats import beta,binom
from s03_reference import pd_acceptance_candidate as a
from s03_reference import model as m

def peak(b):
    x=np.zeros(32,dtype=float)
    x[b]=15
    return x

def record(k,b,idx=0):
    return {'record_id':idx,'range_bin':k,'doppler_bin':b,
            'velocity_m_s_nominal':float(m.bin_velocity(b))}

class TestPdProtocol(unittest.TestCase):
    def test_frozen_values(self):
        self.assertTrue(a.verify_fixed_parameters())
        self.assertEqual((a.N,a.MASTER_SEED_RESERVED),(1000,411091704))
        self.assertAlmostEqual(a.NOISE_VARIANCE,.18**2/100)
        self.assertAlmostEqual(a.TRUE_VELOCITY,4*.46875)
    def test_independent_binomial_duality(self):
        self.assertLess(a.exact_one_sided_lower(915),.9)
        self.assertGreaterEqual(a.exact_one_sided_lower(916),.9)
        self.assertGreater(binom.sf(914,1000,.9),.05)
        self.assertLessEqual(binom.sf(915,1000,.9),.05)
        self.assertAlmostEqual(a.exact_one_sided_lower(916),float(beta.ppf(.05,916,85)),places=14)
        self.assertEqual(a.min_success_count(),916)
    def test_no_detection_is_valid_failure(self):
        z=a.score_detection_records([])
        self.assertEqual(z['status'],'VALID')
        self.assertFalse(z['detection_and_one_to_one_association'])
        self.assertFalse(z['joint_detection_and_both_accuracies'])
    def test_correctly_matched_and_accurate(self):
        z=a.score_detection_records([record(40,4,0),record(53,4,1)],matched_range_power_bins=peak(4))
        self.assertTrue(z['detection_and_one_to_one_association'])
        self.assertTrue(z['range_accuracy_conditional'])
        self.assertTrue(z['doppler_halfbin_accuracy_conditional'])
        self.assertTrue(z['joint_detection_and_both_accuracies'])
        self.assertEqual(z['extra_unmatched_cluster_count'],1)
    def test_matched_but_bad_range_accuracy(self):
        z=a.score_detection_records([record(42,4)],matched_range_power_bins=peak(4))
        self.assertTrue(z['detection_and_one_to_one_association'])
        self.assertFalse(z['range_accuracy_conditional'])
        self.assertTrue(z['doppler_halfbin_accuracy_conditional'])
        self.assertFalse(z['joint_detection_and_both_accuracies'])
    def test_matched_but_bad_doppler_accuracy(self):
        z=a.score_detection_records([record(40,5)],matched_range_power_bins=peak(5))
        self.assertTrue(z['detection_and_one_to_one_association'])
        self.assertTrue(z['range_accuracy_conditional'])
        self.assertFalse(z['doppler_halfbin_accuracy_conditional'])
        self.assertFalse(z['joint_detection_and_both_accuracies'])
    def test_outside_matching_gate(self):
        z=a.score_detection_records([record(43,4)],matched_range_power_bins=peak(4))
        self.assertFalse(z['detection_and_one_to_one_association'])
    def test_invalid_not_silent_failure(self):
        self.assertEqual(a.score_detection_records([],valid_input=False)['status'],'INCONCLUSIVE')
        self.assertEqual(a.score_detection_records([record(40,4,7),record(41,4,7)])['status'],'INCONCLUSIVE')
    def test_matched_missing_power_row_inconclusive(self):
        z=a.score_detection_records([record(40,4)])
        self.assertEqual(z['status'],'INCONCLUSIVE')
    def test_matched_power_tie_joint_fails(self):
        x=peak(4);x[5]=15
        z=a.score_detection_records([record(40,4)],matched_range_power_bins=x)
        self.assertTrue(z['detection_and_one_to_one_association'])
        self.assertFalse(z['doppler_peak_eligible'])
        self.assertFalse(z['doppler_halfbin_accuracy_conditional'])
        self.assertFalse(z['joint_detection_and_both_accuracies'])
    def test_doppler_eligibility(self):
        import numpy as np
        power=np.zeros(32)
        power[4]=15
        z=a.doppler_peak_eligibility(power,4)
        self.assertTrue(z['eligible'])
        power[5]=15
        z=a.doppler_peak_eligibility(power,4)
        self.assertFalse(z['eligible'])
        z=a.doppler_peak_eligibility(np.zeros(32),4)
        self.assertFalse(z['eligible'])

    def test_true_velocity_accuracy_and_nominal(self):
        self.assertEqual(float(m.bin_velocity(4)),1.875)
        self.assertEqual(a.fixed_target_truth()['range_m_nominal'],6000.)
        self.assertEqual(a.fixed_target_truth()['velocity_m_s'],1.875)
if __name__=='__main__':unittest.main()

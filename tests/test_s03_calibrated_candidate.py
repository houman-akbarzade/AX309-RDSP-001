import unittest
import numpy as np
from scipy.stats import binom
from s03_reference import calibrated_critical_candidate as c
class TestProspectiveCriticalRule(unittest.TestCase):
    def test_critical_rank_family_control(self):
        self.assertEqual(c.familywise_order_stat_rank(5000),4792)
        r=c.familywise_order_stat_rank(5000)
        self.assertGreaterEqual(binom.cdf(r-1,5000,.95),1-.05/15)
        self.assertLess(binom.cdf(r-2,5000,.95),1-.05/15)
    def test_seed_domains_are_disjoint(self):
        v=[c.CAL_MASTER_SEED,c.QUAL_MASTER_SEED,c.SPATIAL_MASTER_SEED,c.ALPHA_MASTER_SEED,c.MAIN_MASTER_SEED]
        self.assertEqual(len(v),len(set(v)))
        self.assertNotIn(20261109,v)
        self.assertNotIn(370091001,v)
    def test_positive_calibration_delta_non_decreases_bound(self):
        a=np.zeros(c.G,int)
        a[::3]=1
        a[1::23]=16
        u1=c.candidate_upper(a,0)
        u2=c.candidate_upper(a,1)
        self.assertIsNotNone(u1)
        self.assertGreater(u2,u1)
    def test_invalid_observations_never_get_interval(self):
        self.assertIsNone(c.candidate_upper(np.zeros(c.G),0))
        with self.assertRaises(ValueError):c.candidate_upper(np.ones(c.G),-1)
    def test_calibration_requires_all_cases(self):
        with self.assertRaises(ValueError):c.prospective_delta_star([np.ones(5000)])
    def test_rank_protection_under_missing_values(self):
        with self.assertRaises(ValueError):c.prospective_delta_star([np.full(5000,np.nan) for _ in range(15)])
if __name__=='__main__':unittest.main()

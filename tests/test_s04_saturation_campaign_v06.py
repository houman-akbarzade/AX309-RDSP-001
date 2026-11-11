"""Pure analytical campaign-risk regression; no stochastic data or S03 imports."""
import importlib.util
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'engineering/s04_numeric/saturation_campaign_review_v06.py'
spec=importlib.util.spec_from_file_location('s04_campaign_v06',SRC)
camp=importlib.util.module_from_spec(spec)
spec.loader.exec_module(camp)

class CampaignRiskTests(unittest.TestCase):
    def test_identity_and_monotone_campaign_n(self):
        for g in (1,2,3,4,5,6,8):
            q=camp.v05.independent_unit_gaussian(g)['prob_at_least_one']
            for N in (1000,20000):
                ans=camp.campaign_risk_for_unit(g,N)
                expected=1.0 if q>=1 else -math.expm1(N*math.log1p(-q))
                self.assertAlmostEqual(ans,expected,
                                       delta=max(1e-30,ans*1e-10))
            self.assertGreaterEqual(camp.campaign_risk_for_unit(g,20000),
                                    camp.campaign_risk_for_unit(g,1000))

    def test_extreme_rare_event_stable_log(self):
        r=camp.campaign_from_logq(-1000*math.log(10),20000)
        self.assertEqual(r['probability'],0.0)
        self.assertAlmostEqual(r['log10_probability'],-1000+math.log10(20000),places=9)

    def test_risk_tier_inversions(self):
        for N in (1000,20000):
            prev=0.
            for target in (.1,.01,.001):
                g=camp.inverse_scale_noise_only(N,target)
                self.assertGreater(g,prev)
                self.assertAlmostEqual(camp.campaign_risk_for_unit(g,N),target,delta=2e-10)
                prev=g

    def test_zero_probability_and_unity_probability(self):
        self.assertEqual(camp.campaign_from_logq(0,1000)['probability'],1)
        self.assertEqual(camp.campaign_from_logq(float('-inf'),1000)['probability'],0)
        self.assertEqual(camp.campaign_from_logq(math.log(.01),1000)['probability'],
                         -math.expm1(1000*math.log1p(-.01)))

    def test_quantization_tradeoff(self):
        for g in (1,2,3,4,5,6,8):
            q=camp.v05.quantization(g)
            self.assertEqual(q['component_max_abs_original_units'],g/65536)
            self.assertAlmostEqual(q['component_rms_uniform_roundoff_hypothesis'],
                                   g/(32768*math.sqrt(12)))

    def test_heterogeneous_independent_and_correlated_bounds(self):
        qs=(.01,.02,.03)
        independent=1-math.prod(1-q for q in qs)
        self.assertGreaterEqual(independent,max(qs))
        self.assertLessEqual(independent,sum(qs))
        # No independence: union lower max(q_i), upper min(1,sum q_i).
        self.assertEqual(max(qs),.03)
        self.assertEqual(min(1,sum(qs)),.06)

if __name__=='__main__':
    unittest.main()

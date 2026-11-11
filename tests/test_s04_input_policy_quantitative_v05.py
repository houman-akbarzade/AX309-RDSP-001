"""Deterministic quantitative policy audit: no random samples or S03 import."""
import importlib.util
import math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT/'engineering/s04_numeric/input_policy_quant_review_v05.py'
spec=importlib.util.spec_from_file_location('s04_policy_v05_readonly',SRC)
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class QuantitativePolicyTests(unittest.TestCase):
    def test_individual_component_tail_risk_is_ordered_and_finite(self):
        mu,var,_=v.model('PD_REFERENCE_LIKE')
        g=1
        sigma=math.sqrt(var/2)
        from scipy.special import log_ndtr
        import numpy as np
        z=np.logaddexp(log_ndtr((mu-float(v.v03.UPPER)*g)/sigma),
                       log_ndtr((float(v.v03.LOWER)*g-mu)/sigma))
        self.assertEqual(len(z),8448)
        self.assertTrue(np.isfinite(z).all())
        self.assertLessEqual(float(z.min()),float(z.max()))
        self.assertTrue(float(z.max())<0)

    def test_noise_only_independent_tail_formula(self):
        for g in (1,2,3,4,5,6,8):
            m,variance,_=v.model('NOISE_ONLY_UNIT')
            a=v.v03.gaussian_saturation(m,variance,g)
            b=v.independent_unit_gaussian(g)
            self.assertAlmostEqual(a['expected_saturated_components'],b['expected_components'],delta=max(1e-23,b['expected_components']*1e-11))
            self.assertAlmostEqual(a['prob_at_least_one_saturation'],b['prob_at_least_one'],delta=max(1e-23,b['prob_at_least_one']*1e-11))

    def test_clipping_monotonicity_in_noiseless_mean_class(self):
        mu,var,_=v.model('NOISE_ONLY_UNIT')
        vals=[v.v03.gaussian_saturation(mu,var,g)['prob_at_least_one_saturation'] for g in [1,2,3,4,5,6,8]]
        self.assertEqual(vals,sorted(vals,reverse=True))

    def test_g_four_not_below_risk_one_in_ten_thousand(self):
        mu,var,_=v.model('NOISE_ONLY_UNIT')
        risk=v.v03.gaussian_saturation(mu,var,4)['prob_at_least_one_saturation']
        self.assertGreater(risk,.0001)
        self.assertLess(risk,.001)

    def test_uniform_quantization_resolution_scales_with_g(self):
        for g in (1,2,3,4,5,6,8):
            z=v.quantization(g)
            self.assertEqual(z['component_max_abs_original_units'],g/65536)
            self.assertAlmostEqual(z['component_rms_uniform_roundoff_hypothesis'],g/(32768*math.sqrt(12)))

    def test_unidentified_class_unapproved_limits_no_profile(self):
        self.assertRaises(ValueError,v.model,'UNSPECIFIED')

    def test_real_pd_mean_analytical_without_draws(self):
        mu,var,_=v.model('PD_REFERENCE_LIKE')
        self.assertEqual(len(mu),8448)
        self.assertEqual(var,.000324)
        self.assertEqual(sum(abs(x)>1e-12 for x in mu),33*16*2)

    def test_exact_thresholds_existing_v03(self):
        self.assertEqual(v.v03.test_exact_endpoints(),20)
        self.assertEqual(v.v03.test_all_boundary_scales(),120)
        self.assertEqual(v.v03.test_stored_reconstructed(),36)

if __name__=='__main__':
    unittest.main()

"""S04-C01 exact deterministic design checks; no model/PRNG or CPI generation."""
import importlib.util
import math
from pathlib import Path
from fractions import Fraction
import unittest

SRC=Path(__file__).resolve().parent.parent/'engineering/s04_numeric/input_scaling_analysis_v03.py'
spec=importlib.util.spec_from_file_location('s04_scale_v03_readonly',SRC)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestS04ScalingDeterministic(unittest.TestCase):
    def test_exact_q15_thresholds_and_ties(self):
        self.assertEqual(mod.test_exact_endpoints(),20)

    def test_all_boundaries_and_options(self):
        self.assertEqual(mod.test_all_boundary_scales(),120)

    def test_fft_and_power_reconstruction(self):
        self.assertEqual(mod.test_stored_reconstructed(),36)

    def test_independent_noise_formula(self):
        g=4
        s=math.sqrt(.5)
        upper=float(mod.UPPER)*g
        lower=float(mod.LOWER)*g
        pcomp=.5*math.erfc(upper/(s*math.sqrt(2)))+.5*math.erfc(-lower/(s*math.sqrt(2)))
        z=mod.gaussian_saturation(mod.np.zeros(8448),1.,g)
        self.assertAlmostEqual(z['expected_saturated_components'],8448*pcomp,places=13)
        self.assertAlmostEqual(z['prob_at_least_one_saturation'],-math.expm1(8448*math.log1p(-pcomp)),places=14)

    def test_pd_analytic_mean_only_not_sampled(self):
        v=mod.cpi_component_means_pd()
        self.assertEqual(v.shape,(33,128))
        self.assertEqual(int(mod.np.count_nonzero(v)),33*16)
        self.assertAlmostEqual(abs(v[0,40]),.18)
        self.assertTrue(mod.np.all(v[:,0]==0))

    def test_noise_and_pd_are_different_admission_classes(self):
        z=mod.np.zeros(8448)
        noise=mod.gaussian_saturation(z,1.,1)
        pd=mod.gaussian_saturation(mod.to_component_means(mod.cpi_component_means_pd()),.000324,1)
        self.assertGreater(noise['expected_saturated_components'],1000)
        self.assertLess(pd['log10_expected_saturated_components'],-800)

    def test_reconstruction_units_and_alpha_no_gain(self):
        for option in ('A','B'):
            for g in (1,2,4,8):
                m=mod.boundary_scale_map(option,g)
                self.assertEqual(m['B06_RD_power'],m['B05_FFT']**2)
                self.assertEqual(m['B08_training_mean'],m['B06_RD_power'])
                self.assertEqual(m['B11_range_m'],1)
                self.assertEqual(m['B11_velocity_m_s'],1)
                self.assertIsNone(m['B09_alarm_flag'])
                self.assertEqual(mod.decode_component(1024,Fraction(g)),Fraction(g,32))

    def test_scale_nonpositive_is_rejected(self):
        for g in (0,-1):
            with self.assertRaises(ValueError):mod.boundary_scale_map('A',g)
            with self.assertRaises(ValueError):mod.encode_component(Fraction(0),g)

if __name__=='__main__':
    unittest.main()

import unittest,hashlib
import numpy as np
from pathlib import Path
from s03_reference import skew_ci_candidate as sc
from s03_reference import model as m
from s03_reference.skew_formula_audit import moment_skew

class TestSkewTheoryAndProvenance(unittest.TestCase):
    def test_skewness_and_positive_upper_correction(self):
        a=np.zeros(sc.G_PROPOSED,dtype=np.int32)
        a[::10]=5
        a[1]=100
        up,info=sc.upper_and_diagnostics(a)
        self.assertIsNotNone(up)
        self.assertGreater(info['sample_skew_m3_over_m2pow1_5'],0)
        self.assertGreater(info['positive_skew_correction'],0)
        self.assertGreaterEqual(up,info['base_t_upper'])
    def test_invalid_zero_and_bad_counts(self):
        v,d=sc.upper_and_diagnostics(np.zeros(sc.G_PROPOSED,dtype=np.int32))
        self.assertIsNone(v)
        with self.assertRaises(ValueError):
            sc.upper_and_diagnostics(np.ones(4096,dtype=int))
        arr=np.zeros(sc.G_PROPOSED)
        arr[0]=2783
        with self.assertRaises(ValueError):
            sc.upper_and_diagnostics(arr)
    def test_formula_central_moments(self):
        x=np.array([0.,0.,0.,1.,4.,5.])
        d=x-x.mean()
        g=float(np.mean(d**3)/np.mean(d*d)**1.5)
        self.assertAlmostEqual(g,moment_skew(x),places=14)
    def test_preserve_gate_s02_original_sha(self):
        import json
        root=Path(__file__).resolve().parents[1]
        baseline=json.loads((root/'decisions/GATE-S02-approved-baseline.json').read_text())
        for r,h in baseline['approved_artifacts_sha256'].items():
            self.assertEqual(hashlib.sha256((root/r).read_bytes()).hexdigest(),h)
    def test_no_mutation_of_reference_mf_outputs(self):
        x=m.generate_cpi([m.Target(0,1.5,.18),m.Target(112,-3,.18)])
        z=m.pulse_compress(x)
        self.assertEqual(z.shape,(33,128))
        self.assertTrue(np.all(np.isfinite(z)))
    def test_doppler_signed_tie_selection(self):
        power=np.zeros(32)
        power[3]=10
        power[31]=10
        peak,state=m.select_peak(power)
        self.assertEqual((peak,state),(31,'PEAK_TIE'))

if __name__=='__main__':unittest.main()

"""Pure deterministic proof-parameter tests, no new CPI or main Pfa samples."""
import json,math,unittest
from pathlib import Path
from s03_reference.c04_cpi_bounded_protocol_analysis import (
    eb,kl,kl_bound,kl_threshold,ALPHA,LIMIT,TARGET,N_PROPOSED,MCUT)
class TestC04CpiBoundedDesign(unittest.TestCase):
    def test_fixed_per_CPI_bounded_unit_not_per_CUT_iid(self):
        self.assertEqual(MCUT,2782)
        self.assertEqual(N_PROPOSED,20000)
        self.assertEqual(ALPHA,.05)
        self.assertEqual((TARGET,LIMIT),(.001,.0015))
    def test_empirical_Bernstein_formula(self):
        n=20000;mu=.001;v=3.9913375090621184/2782**2
        expect=mu+math.sqrt(2*v*math.log(40)/n)+7*math.log(40)/(3*(n-1))
        self.assertAlmostEqual(eb(n,mu,v),expect,places=15)
        self.assertLess(expect,LIMIT)
    def test_eb_at_4096_too_conservative(self):
        v=3.9913375090621184/2782**2
        self.assertGreater(eb(4096,TARGET,v),LIMIT)
    def test_kl_inversion_and_deterministic_bound(self):
        n=32768
        up=kl_bound(n,TARGET)
        self.assertAlmostEqual(n*kl(TARGET,up),math.log(20),places=8)
        x=kl_threshold(n)
        self.assertLess(TARGET,x)
        self.assertAlmostEqual(n*kl(x,LIMIT),math.log(20),places=8)
    def test_no_fabricated_performance_results(self):
        root=Path(__file__).resolve().parents[1]
        x=json.loads((root/'engineering/S03-C04-CPI-bounded-analytical-cost-and-power-v0.1.json').read_text())
        self.assertTrue(x['no_simulation_new_samples'])
        self.assertTrue(x['normal_power_model_is_only_approximation_not_guarantee'])
        self.assertEqual(x['source_diagnostic_file'],'engineering/S03-C04-post-alpha-spatial-diagnostic-v0.1.json')
    def test_preserve_current_gate_and_spatial_fail(self):
        root=Path(__file__).resolve().parents[1]
        p=json.loads((root/'engineering/S03-progress.json').read_text())
        x=json.loads((root/'engineering/S03-C04-post-alpha-spatial-diagnostic-v0.1.json').read_text())
        self.assertEqual(p['gate'],'open')
        self.assertEqual((p['stage_percent'],p['completed_count']),(75.,6))
        self.assertEqual(x['status'],'FAIL_SPATIAL_TRANSFER_GATE')
if __name__=='__main__':unittest.main()

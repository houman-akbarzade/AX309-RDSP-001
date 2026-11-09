import unittest
import json
import numpy as np
from pathlib import Path
from s03_reference import c04_alpha_frozen as a
from s03_reference import model as m

class TestAlphaPredeclared(unittest.TestCase):
    def test_frozen_policy_and_seeds(self):
        p=a.fixed_policy()
        self.assertEqual(p['alpha_calibration']['CPI'],4096)
        self.assertEqual(p['post_alpha_real_chain_diagnostic']['CPI'],4096)
        self.assertEqual(p['CI_delta_star_fixed'],.28734133322686817)
        self.assertEqual(len(set(p['independent_seed_streams'].values())),5)
    def test_seed_replay_and_isolation(self):
        x=a.generate(a.SEED_CAL,1)
        self.assertTrue(np.array_equal(x,a.generate(a.SEED_CAL,1)))
        self.assertFalse(np.array_equal(x,a.generate(a.SEED_SPATIAL,1)))
    def test_train_exact_40_reference(self):
        r=np.random.default_rng(338)
        power=r.uniform(.1,10,size=(128,32))
        z=a.training_mean(power)
        self.assertEqual(z.shape,(107,26))
        test=sum(power[21+dr,10+db] for dr,db in m.TRAIN_OFFSETS)/40
        self.assertAlmostEqual(z[21-3,10-3],test,places=13)
    def test_calibration_quantile_rank_algebra(self):
        n=1_000_000;p=.001;k=round(n*p)
        values=np.arange(n,dtype=float)
        alpha=np.partition(values,n-k-1)[n-k-1]
        self.assertEqual((values>alpha).sum(),k)
        self.assertLessEqual(abs((values>alpha).mean()-p),1e-5)
    def test_wilson99_exact_span(self):
        lo,hi=a.wilson99(100,4096)
        self.assertTrue(0<lo<100/4096<hi<1)
        self.assertEqual(a.wilson99(0,0),(0.,1.))
    def test_unchanged_original_stat_approval(self):
        root=Path(__file__).resolve().parents[1]
        q=json.loads((root/'engineering/S03_C04_v11_independent_15x3000_qualification.json').read_text())
        self.assertEqual((q['passed_conditions'],q['failed_conditions']),(15,0))
if __name__=='__main__':unittest.main()

"""Pre-run deterministic arithmetic tests only (NO new radar CPI)."""
import unittest,math,json
import numpy as np
from pathlib import Path
from s03_reference import c04_eb_independent_preflight as f
from s03_reference import model as m
class TestNewEBPreflightBeforeGeneration(unittest.TestCase):
    def test_policy_and_baselines(self):
        x=f.frozen_state()
        self.assertEqual(x['status'],'PRE-FROZEN_BEFORE_NEW_REFERENCE_OR_IMPLEMENTATION_CPI')
        self.assertEqual(x['n_final_reserved_not_generated'],20000)
    def test_independent_integral_sum_mask_with_integer_grid(self):
        pw=np.arange(128*32).reshape((128,32)).astype(float)+1
        count,mean,mask=f.independent_training_and_count(pw)
        a,valid,ref=m.cfar_2d(pw,alpha=f.ALPHA)
        self.assertEqual(int(valid.sum()),2782)
        self.assertTrue(np.allclose(mean,ref[3:110,3:29],atol=1e-8,rtol=1e-10))
        self.assertEqual(int(a.sum()),count)
        self.assertTrue(np.array_equal(a[3:110,3:29],mask))
    def test_stable_nonuniform_power(self):
        # deterministic mathematical construction; no PRNG / CPI used
        k=np.arange(128)[:,None]
        b=np.arange(32)[None,:]
        pw=(1+np.mod(k*k+7*b*b+11*k*b,101)).astype(float)
        count,mean,mask=f.independent_training_and_count(pw)
        aa,_,train=m.cfar_2d(pw,alpha=f.ALPHA)
        self.assertEqual(count,int(aa.sum()))
        self.assertTrue(np.allclose(mean,train[3:110,3:29],atol=1e-8))
        self.assertTrue(np.array_equal(mask,aa[3:110,3:29]))
    def test_independent_EB_arithmetic(self):
        counts=np.array([0,1,12,100,2782,1,0,5,75,8,0,2,3],dtype=np.int64)
        a,am,av=f.eb_numpy(counts)
        b,bm,bv=f.eb_welford(counts)
        self.assertAlmostEqual(am,bm,places=13)
        self.assertAlmostEqual(av,bv,places=13)
        self.assertAlmostEqual(a,b,places=13)
    def test_reject_final_action(self):
        self.assertEqual(f.MASTERS,(411091701,411091702))
        self.assertNotIn(411091703,f.MASTERS)
        self.assertNotIn(411091704,f.MASTERS)
        self.assertEqual(f.N,4096)
if __name__=='__main__':unittest.main()

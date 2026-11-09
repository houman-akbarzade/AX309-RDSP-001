import unittest
import numpy as np
from s03_reference import model as m
from s03_reference import cfar_qualification as q

class TestC04Contract(unittest.TestCase):
    def test_qualification_frozen_dimensions(self):
        self.assertEqual(q.NOUT,3000)
        self.assertEqual(q.NCPI,4096)
        self.assertEqual(q.NCUT,2782)
        self.assertEqual(len(q.RHO_VALUES)*len(q.P_VALUES),15)

    def test_invalid_coverage_is_not_counted(self):
        arr=np.zeros((2,4096),dtype=np.int32)
        valid,covered=q.classify_count_array(arr,.001)
        self.assertEqual(valid.tolist(),[False,False])
        self.assertEqual(covered.tolist(),[False,False])

    def test_wilson(self):
        lo,hi=q.wilson_bounds(2850,3000)
        self.assertGreater(lo,.93)
        self.assertLess(hi,1)
        lo,hi=q.wilson_bounds(130,3000)
        self.assertLessEqual(hi,.05)
        lo,hi=q.wilson_bounds(131,3000)
        self.assertGreater(hi,.05)

    def test_scr_power_definition_before_quantization(self):
        t=m.Target(20,-3,.18)
        target_amp_power=abs(t.amplitude)**2
        for scr in (10.,-10.):
            cl_amp=abs(t.amplitude)/np.sqrt(10**(scr/10))
            cl=np.full(128,cl_amp,dtype=np.complex128)
            Pcl=np.mean(abs(cl[20:36])**2)
            measured=10*np.log10(target_amp_power/Pcl)
            self.assertAlmostEqual(measured,scr,places=12)

    def test_stationary_clutter_exactly_cancels_in_float_chain(self):
        t=m.Target(20,0,.15)
        cl=np.full(128,.18+.07j)
        y=m.mti(m.pulse_compress(m.generate_cpi([t],clutter=cl)))
        self.assertEqual(np.max(abs(y)),0)

if __name__=='__main__':unittest.main()

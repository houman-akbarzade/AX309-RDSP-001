import unittest
import numpy as np
from s03_reference import model as m
from s03_reference.extended_scenarios import CASES

class TestExtendedS03(unittest.TestCase):
    def test_boundary_mf_all_113_delays(self):
        s=m.chirp();h=m.matched_filter()
        for k in range(113):
            x=np.zeros((33,128),dtype=np.complex128)
            x[0,k:k+16]=.2*s
            z=np.convolve(x[0],h,mode='full')[15:143]
            self.assertEqual(int(np.argmax(abs(z)**2)),k)
            self.assertAlmostEqual(float(abs(z[k])),3.2,places=12)
    def test_cfar_CUT_edges(self):
        p=np.zeros((128,32))
        for k,b in [(2,4),(110,4),(3,3),(109,28),(3,29),(109,2)]:
            p[:]=0;p[k,b]=10
            a,v,noise=m.cfar_2d(p)
            self.assertEqual(bool(v[k,b]),3<=k<=109 and 3<=b<=28)
            self.assertEqual(bool(a[k,b]),3<=k<=109 and 3<=b<=28)
    def test_mti_nyquist_and_dc(self):
        x=m.generate_cpi([m.Target(20,-16*.46875,.15)])
        y=m.rd_power(m.doppler(m.mti(m.pulse_compress(x))))
        b,_=m.select_peak(y[20])
        self.assertEqual(b,16)
        dc=m.generate_cpi([m.Target(20,0,.15)])
        self.assertEqual(np.max(abs(m.mti(m.pulse_compress(dc)))),0)
    def test_noisy_replay_diversity(self):
        ts=[m.Target(20,-3),m.Target(40,1.5),m.Target(60,5)]
        a=m.generate_cpi(ts,snr_db=10,seed=1732)
        b=m.generate_cpi(ts,snr_db=10,seed=1732)
        c=m.generate_cpi(ts,snr_db=10,seed=1733)
        self.assertTrue(np.array_equal(a,b))
        self.assertFalse(np.array_equal(a,c))
    def test_multitarget_independent_same_range(self):
        ts=[m.Target(20,-3,.18),m.Target(20,5,.18)]
        iq=m.generate_cpi(ts)
        rd=m.rd_power(m.doppler(m.mti(m.pulse_compress(iq))))
        self.assertEqual(rd.shape,(128,32))
        for t in ts:
            b=int(round(t.velocity/.46875))%32
            self.assertGreater(rd[20,b],0)
    def test_all_case_names_unique_and_seeds_separate(self):
        self.assertEqual(len(CASES),len(set(x[0] for x in CASES)))
        self.assertEqual(len(CASES),19)

if __name__=='__main__':unittest.main()

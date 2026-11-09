import unittest
import numpy as np
from s03_reference import model as m

class TestS03Model(unittest.TestCase):
    def test_chirp_support_and_phase(self):
        s=m.chirp()
        self.assertEqual(s.shape,(16,))
        np.testing.assert_allclose(abs(s),1,atol=1e-15)
        t=(np.arange(16)+.5)/m.FS
        phase=2*np.pi*((-m.B/2)*t + m.B/(2*(16/m.FS))*t*t)
        np.testing.assert_allclose(s,np.exp(1j*phase),atol=1e-15)

    def test_grid_validity_and_mf_peak(self):
        for k in [0,1,3,20,40,60,109,112]:
            x=m.generate_cpi([m.Target(k,0,0.25)])
            z=m.pulse_compress(x)
            self.assertEqual(int(np.argmax(abs(z[0])**2)),k)
            self.assertAlmostEqual(abs(z[0,k]),4,places=12)
        with self.assertRaises(ValueError):
            m.generate_cpi([m.Target(113,0,.2)])

    def test_manual_mf_direct_inner_product(self):
        x=np.zeros((33,128),complex)
        x[0,7:23]=m.chirp()*.2
        p=m.pulse_compress(x)
        self.assertAlmostEqual(p[0,7].real,3.2,places=12)
        self.assertAlmostEqual(p[0,7].imag,0,places=12)

    def test_integer_quantization_and_byte_order(self):
        x=np.zeros((33,128),complex)
        x[0,0]=.5-.25j
        blob,clips=m.quantize_iq(x)
        self.assertEqual(len(blob),16896)
        self.assertEqual(clips,0)
        self.assertEqual(blob[:4],bytes.fromhex('004000e0'))
        blob2,clips2=m.quantize_iq(x)
        self.assertEqual(blob,blob2)
        bad=np.ones((33,128),complex)*1.5
        self.assertGreater(m.quantize_iq(bad)[1],0)

    def test_noise_replay_and_real_imag_variance(self):
        a=m.noise_only_cpi(2.0,17)
        b=m.noise_only_cpi(2.0,17)
        self.assertTrue(np.array_equal(a,b))
        self.assertFalse(np.array_equal(a,m.noise_only_cpi(2.0,18)))
        # Moments of large independent ensemble, not precise finite-record SNR
        rng=np.random.default_rng(10)
        x=np.sqrt(2.0/2)*(rng.normal(size=100000)+1j*rng.normal(size=100000))
        self.assertLess(abs(np.mean(abs(x)**2)-2),.025)

    def test_snr_definition(self):
        t=m.Target(20,3,.2)
        self.assertAlmostEqual(m.noise_variance(t,20),.0004)
        self.assertAlmostEqual(m.noise_variance(t,0),.04)

    def test_mti_dc_cancel(self):
        x=m.generate_cpi([m.Target(20,0,.2)],clutter=np.ones(128)*(.03+.01j))
        y=m.mti(m.pulse_compress(x))
        self.assertEqual(float(np.max(np.abs(y))),0.0)

    def test_doppler_center_bin_and_sign(self):
        for signed in [-12,-6,-1,1,3,11,15]:
            v=signed*.46875
            x=m.generate_cpi([m.Target(20,v,.15)])
            spectrum=m.doppler(m.mti(m.pulse_compress(x)))
            peak,_=m.select_peak(abs(spectrum[20])**2)
            expect=signed%32
            self.assertEqual(peak,expect)

    def test_off_bin_three_target_velocities_isolated(self):
        for vel in [-3.,1.5,5.]:
            x=m.generate_cpi([m.Target(20,vel,.15)])
            power=abs(m.doppler(m.mti(m.pulse_compress(x)))[20])**2
            chosen,status=m.select_peak(power)
            self.assertEqual(status,'OK')
            estimate=float(m.bin_velocity(chosen))
            self.assertLessEqual(abs(estimate-vel),.234375+1e-12)

    def test_doppler_zero_and_tie(self):
        b,status=m.select_peak(np.zeros(32))
        self.assertEqual(status,'NO_VALID_PEAK')
        self.assertEqual(b,16)  # -16 is smallest signed bin
        p=np.zeros(32)
        p[31]=2
        p[2]=2
        b,status=m.select_peak(p)
        self.assertEqual((b,status),(31,'PEAK_TIE'))

    def test_cfar_geometry_and_strict_threshold(self):
        power=np.zeros((128,32),float)
        alarm,valid,noise=m.cfar_2d(power)
        self.assertEqual(int(valid.sum()),2782)
        self.assertEqual(int(alarm.sum()),0)
        self.assertEqual(len(m.TRAIN_OFFSETS),40)
        power[20,10]=1
        alarm,valid,noise=m.cfar_2d(power)
        self.assertTrue(alarm[20,10])
        self.assertFalse(alarm[0,0])
        self.assertFalse(alarm[112,10])

    def test_cfar_reference_40_manual_sum(self):
        p=np.arange(128*32,dtype=float).reshape(128,32)
        alarm,valid,noise=m.cfar_2d(p)
        direct=sum(p[20+dr,10+db] for dr,db in m.TRAIN_OFFSETS)/40
        self.assertAlmostEqual(noise[20,10],direct)

    def test_clusters_and_ties(self):
        a=np.zeros((128,32),bool)
        p=np.zeros((128,32))
        a[20,10:12]=True
        p[20,10]=4
        p[20,11]=4
        records=m.clusters_8(a,p)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['doppler_bin'],10)
        self.assertEqual(records[0]['cluster_cells'],2)

    def test_truth_assignment_is_one_to_one(self):
        det=[{'record_id':0,'range_bin':20,'velocity_m_s_nominal':1.5},
             {'record_id':1,'range_bin':21,'velocity_m_s_nominal':1.5},
             {'record_id':2,'range_bin':40,'velocity_m_s_nominal':-3.0}]
        truth=[{'id':0,'range_m_nominal':3000,'velocity_m_s':1.5},
               {'id':1,'range_m_nominal':6000,'velocity_m_s':-3},
               {'id':2,'range_m_nominal':3000,'velocity_m_s':1.5}]
        pairs=m.truth_match(det,truth)
        self.assertEqual(len(pairs),3)
        self.assertEqual(len(set(x[0] for x in pairs)),3)
        self.assertEqual(len(set(x[1] for x in pairs)),3)

    def test_end_to_end_shapes_and_replay(self):
        t=[m.Target(20,-3),m.Target(40,1.5),m.Target(60,5)]
        a=m.generate_cpi(t,snr_db=20,seed=20261109)
        b=m.generate_cpi(t,snr_db=20,seed=20261109)
        self.assertTrue(np.array_equal(a,b))
        out=m.pipeline(a)
        self.assertEqual(out['pc'].shape,(33,128))
        self.assertEqual(out['mti'].shape,(32,128))
        self.assertEqual(out['doppler'].shape,(128,32))
        self.assertEqual(out['power'].shape,(128,32))
        self.assertEqual(int(out['valid'].sum()),2782)
        self.assertTrue(all(r['range_bin'] in range(3,110) for r in out['targets']))

if __name__=='__main__':unittest.main()

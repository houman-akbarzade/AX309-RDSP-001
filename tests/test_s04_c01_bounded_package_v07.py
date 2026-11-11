"""Pure analytical regression of bounded C01 input contract; no RNG or CPI generation."""
import importlib.util
import math
from fractions import Fraction
from pathlib import Path
import unittest

SRC=Path(__file__).resolve().parent.parent/'engineering/s04_numeric/s04_c01_bounded_precision_v07.py'
class TestBoundedC01(unittest.TestCase):
    def test_script_source_has_no_stochastic_generator(self):
        s=SRC.read_text()
        for forbidden in ['generate_cpi(', 'noise_only_cpi(', 'SeedSequence(', 'default_rng(']:
            self.assertNotIn(forbidden,s)

    def test_exact_candidate_quantization(self):
        for g in [1,2,4,5]:
            # Independent exact rational round-nearest for positive 0.18.
            x=Fraction(9,50)*Fraction(32768,g)
            q=int(x+Fraction(1,2))
            e=abs(Fraction(g*q,32768)-Fraction(9,50))
            self.assertLessEqual(e,Fraction(g,65536))

    def test_precision_g1_better_than_g5(self):
        assert math.sqrt(2)/(65536*.18)<5*math.sqrt(2)/(65536*.18)

    def test_risk_from_existing_noisetail(self):
        sig=math.sqrt(.5)
        def p(g):
            return .5*math.erfc((g*65535/65536)/(sig*math.sqrt(2)))+\
                   .5*math.erfc((g*65537/65536)/(sig*math.sqrt(2)))
        a=-math.expm1(20000*8448*math.log1p(-p(5)))
        b=-math.expm1(20000*8448*math.log1p(-p(4)))
        self.assertLess(a,.001)
        self.assertGreater(b,.001)

    def test_s02_clutter_multi_target_not_waived(self):
        text=(SRC.parent.parent/'S04-C01-BOUNDED-BASELINE-CONTRACT-APPROVAL-PACKAGE-v0.7.md').read_text()
        for term in ['REQ-SCR-01','REQ-RNG-03','CONFLICT/OPEN','S04-C01 HOLD','S04 0%']:
            self.assertIn(term,text)

if __name__=='__main__':unittest.main()

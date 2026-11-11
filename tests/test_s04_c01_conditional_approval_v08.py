"""Source-only C01 conditional contract checks; no CPI generation."""
import json,math,unittest
from pathlib import Path
from fractions import Fraction
root=Path(__file__).resolve().parent.parent
report=root/'engineering/S04-C01-FINAL-CONDITIONAL-APPROVAL-PACKAGE-v0.8.md'
matrix=root/'engineering/S02-C-CFAR-02-requirements-matrix-APPROVED-v1.2.json'

class ConditionalC01Tests(unittest.TestCase):
 def test_source_binding_conflict_preserved(self):
  m=json.loads(matrix.read_text())['rows']
  a={r['id']:r for r in m}
  self.assertEqual(a['REQ-SCR-01']['classification'],'binding')
  self.assertEqual(a['REQ-RNG-03']['classification'],'binding_test')
  self.assertEqual(a['REQ-SCR-01']['dependency_stage_owners'],['S03'])
  self.assertEqual(a['REQ-RNG-03']['dependency_stage_owners'],['S03'])
  t=report.read_text()
  for x in ('BLOCKER-SCR','BLOCKER-RNG','C02','C06','Gate-S04','HOLD'):
   self.assertIn(x,t)
 def test_exact_q15_input_precision(self):
  a=Fraction(9,50)
  delta=Fraction(1,32768)
  emax=Fraction(1,65536)
  self.assertLessEqual(delta/a,Fraction(17,100000))
  self.assertLessEqual(math.sqrt(2)*float(emax/a),.00012)
 def test_noise_campaign_risk_and_lock(self):
  g=5
  sigma=math.sqrt(.5)
  p=.5*math.erfc((g*65535/65536)/(sigma*math.sqrt(2)))+.5*math.erfc((g*65537/65536)/(sigma*math.sqrt(2)))
  stop=-math.expm1(20000*8448*math.log1p(-p))
  self.assertLess(stop,.001)
  self.assertGreater(stop,.0002)
 def test_no_approval_or_execution_claim(self):
  s=report.read_text()
  for x in ('UNAPPROVED','PENDING','C01-V01','C01-V06','0%','25%','unknown operational'):
   if x=='unknown operational':
    self.assertIn('operational UNKNOWN',s)
   else:
    self.assertIn(x,s)
 def test_source_is_not_reused_for_tuning(self):
  s=report.read_text()
  self.assertIn('No CPI',s)
  self.assertIn('accepted Pd/Pfa seed',s)
 def test_declared_lab_is_not_operational_target_detection(self):
  t=report.read_text()
  self.assertIn('SELECT(declared_test_manifest,approved_profile_registry)',t)
  self.assertIn('no IQ samples',t)

if __name__=='__main__':unittest.main()

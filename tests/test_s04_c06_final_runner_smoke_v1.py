"""Deterministic C06 runner-only smoke and fail-closed tests.
Only existing C04 overrange stress fixture; no C06 acceptance CPI/seed.
"""
import json, tempfile, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c04_selected_C_stage_capture_v1 as ENGINE
import s04_c06_final_runner_v1 as RUNNER
class C06RunnerSmoke(unittest.TestCase):
 def test_existing_diagnostic_fulltrace_native_oracle_and_disposition(self):
  with tempfile.TemporaryDirectory() as folder:
   res=RUNNER.execute(input_tel_factory=lambda:ENGINE.source_vector('overrange_stress',1),
         profile_id='DIAGNOSTIC_ONLY',g=1,vector_id='C04-EXISTING-OVERRANGE',
         cpi_id='PF08-RUNNER-TEST-EXISTING',output_dir=folder,mode='DIAGNOSTIC_ONLY')
   self.assertEqual(res['trace']['status'],'COMPLETE_READBACK_VERIFIED')
   self.assertEqual(res['disposition'],'STRESS_ONLY')
   self.assertFalse(res['performance_eligible'])
   self.assertEqual(res['trace']['total_event_count'],8448)
   self.assertEqual(res['trace']['per_scope'][0]['event_count'],8448)
   self.assertEqual(res['trace']['per_scope'][1]['event_count'],0)
   self.assertEqual(res['processing']['cut_count'],2782)
   self.assertEqual(res['expected_denominators']['MF'],4224)
   self.assertEqual(res['expected_denominators']['FFT5'],4096)
   self.assertEqual(len(list(Path(folder).glob('*.manifest.json'))),1)
 def test_acceptance_interlock_prevents_any_factory_call(self):
  with tempfile.TemporaryDirectory() as folder:
   called=[]
   def forbidden():
    called.append(True)
    raise AssertionError('should never be called')
   with self.assertRaisesRegex(PermissionError,'interlock OFF'):
    RUNNER.execute(input_tel_factory=forbidden,profile_id='NOISE_ONLY_UNIT',g=5,
         vector_id='FORBIDDEN',cpi_id='PF08-FORBIDDEN',output_dir=folder,
         mode='C06_ACCEPTANCE',meta={'authorization_status':'INDEPENDENTLY_APPROVED'})
   self.assertEqual(called,[])
   self.assertEqual(list(Path(folder).iterdir()),[])
 def test_missing_second_telemetry_scope_keeps_partial_and_fails_closed(self):
  with tempfile.TemporaryDirectory() as folder:
   def abort():
    ENGINE.source_vector('overrange_stress',1)
    raise RuntimeError('INJECTED_INTERRUPTION_AFTER_INPUT')
   with self.assertRaisesRegex(RuntimeError,'INJECTED_INTERRUPTION'):
    RUNNER.execute(input_tel_factory=abort,profile_id='DIAGNOSTIC_ONLY',g=1,
         vector_id='C04-EXISTING-OVERRANGE',cpi_id='PF08-ABORT',output_dir=folder,
         mode='DIAGNOSTIC_ONLY')
   p=Path(folder)/'PF08-ABORT.incomplete.json'
   self.assertEqual(json.loads(p.read_text())['status'],
                   'INCOMPLETE_CAPTURE_NOT_VALID_FOR_PREFLIGHT')
   self.assertFalse((Path(folder)/'PF08-ABORT.manifest.json').exists())
   self.assertEqual(len((Path(folder)/'PF08-ABORT.input.jsonl.partial').read_bytes().splitlines()),8448)
if __name__=='__main__':unittest.main(verbosity=2)

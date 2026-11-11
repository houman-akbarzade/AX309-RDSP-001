"""No CPI generation: verify launch imports and preflight's absence of side effects."""
import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest import mock

BASE = Path(__file__).resolve().parent.parent
RUNNER = BASE / 'engineering' / 'run_s03_pd_main_once_v1.py'
MAIN_OUTPUT = BASE / 'engineering' / 'S03-Pd-MAIN-1000CPI-v1'

class TestRunnerZeroCpiPreflight(unittest.TestCase):
    def test_import_runner_from_repository_root_without_running_main(self):
        self.assertFalse(MAIN_OUTPUT.exists())
        spec=importlib.util.spec_from_file_location('pd_runner_preflight_test',RUNNER)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.BASE,BASE)
        self.assertEqual(Path(module.m.__file__).resolve(),BASE/'s03_reference'/'model.py')
        self.assertEqual(Path(module.pd.__file__).resolve(),BASE/'s03_reference'/'pd_acceptance_candidate.py')
        self.assertFalse(MAIN_OUTPUT.exists())

    def test_preflight_blocks_all_stochastic_and_main_calls(self):
        spec=importlib.util.spec_from_file_location('pd_runner_preflight_test2',RUNNER)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(module,'main',side_effect=AssertionError('main() forbidden')) as main, \
             mock.patch.object(module.np.random,'SeedSequence',side_effect=AssertionError('seed forbidden')) as rng, \
             mock.patch.object(module.m,'generate_cpi',side_effect=AssertionError('CPI forbidden')) as cpi, \
             mock.patch.object(Path,'mkdir',side_effect=AssertionError('any mkdir forbidden')) as folder:
            with redirect_stdout(io.StringIO()) as s:
                self.assertEqual(module.preflight(),0)
            self.assertIn('PREFLIGHT PASS',s.getvalue())
            main.assert_not_called()
            rng.assert_not_called()
            cpi.assert_not_called()
            folder.assert_not_called()
        self.assertFalse(MAIN_OUTPUT.exists())
        self.assertFalse((MAIN_OUTPUT/'STARTED.json').exists())

    def test_contract_and_pre_sample_sources_historically_unchanged(self):
        import hashlib
        def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(sha(BASE/'s03_reference'/'model.py'),
                         '2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b')
        self.assertEqual(sha(BASE/'s03_reference'/'pd_acceptance_candidate.py'),
                         'aa0661b52aa56a1da3b3b41332f0927eba58f4fcddace12a391c2488404784ea')
        self.assertEqual(sha(BASE/'engineering'/'S03-Pd-independent-fixed-execution-contract-v0.3.json'),
                         '602e4fe6132c4d8521b33c61a1c2cd413c3e75cc4325fe8b9bca6dea966bed5f')
        result=json.loads((BASE/'engineering'/'S03-Pd-MAIN-FIRST-ATTEMPT-INCONCLUSIVE-v1'/'RESULT.json').read_text())
        self.assertEqual(result['result'],'INCONCLUSIVE')
        self.assertEqual(result['attempted_CPI'],0)
        self.assertFalse(MAIN_OUTPUT.exists())

if __name__=='__main__':
    unittest.main()

"""Focused C06 pow/CFAR uncertainty dimensional regression.

Uses deterministic synthetic arrays only. No CPI input, generator, seed,
pipeline, acceptance runner, or statistical procedure is invoked.
"""
from fractions import Fraction
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engineering" / "s04_numeric"))
import s04_c06_16cpi_authorized_runner_v1 as RUNNER


class C06PowCfarUncertaintyRepairTests(unittest.TestCase):
    @staticmethod
    def offsets():
        # Independently restated C05 7x7 outer ring, excluding central 3x3.
        return tuple(
            (dr, db)
            for dr in range(-3, 4)
            for db in range(-3, 4)
            if abs(dr) > 1 or abs(db) > 1
        )

    def test_exact_c05_geometry_and_all_2782_cut_uncertainties(self):
        offsets = self.offsets()
        self.assertEqual(len(offsets), 40)
        self.assertEqual(len(set(offsets)), 40)

        cuts = [(r, d) for r in range(3, 110) for d in range(3, 29)]
        self.assertEqual(len(cuts), 2782)
        for r, d in cuts:
            cells = [(r + dr, d + db) for dr, db in offsets]
            self.assertEqual(len(cells), 40)
            self.assertTrue(all(0 <= rr < 128 and 0 <= dd < 32
                                for rr, dd in cells))
            self.assertNotIn((r, d), cells)
            self.assertTrue(all(abs(rr-r) <= 3 and abs(dd-d) <= 3
                                for rr, dd in cells))

        # Distinct, nonuniform diagnostic fields make accidental broadcasting
        # or use of the full 128x32 epow map observable.
        epow = (np.arange(128 * 32, dtype=np.float64).reshape(128, 32)
                / 8192.0 + 0.125)
        train_avg = (np.arange(128 * 32, dtype=np.float64).reshape(128, 32)
                     / 4096.0 + 0.5)
        alpha_fixed = Fraction(490007, 65536)
        alpha_float = 7.476912055027923

        got = RUNNER.cfar_uncertainty_terms(
            epow, train_avg, offsets, alpha_fixed, alpha_float
        )
        for name in ("cut_power_error", "training_power_error_sum",
                     "alpha_quantization_error", "total"):
            self.assertEqual(got[name].shape, (107, 26))

        # Independent scalar oracle: explicit per-CUT list and Python sum.
        for r, d in cuts:
            training_sum = sum(epow[r + dr, d + db] for dr, db in offsets)
            expected_cut = epow[r, d]
            expected_alpha = (abs(float(alpha_fixed) - alpha_float)
                              * train_avg[r, d])
            expected_total = (expected_cut
                              + float(alpha_fixed) * training_sum / 40.0
                              + expected_alpha)
            ir, idop = r - 3, d - 3
            self.assertAlmostEqual(
                got["cut_power_error"][ir, idop], expected_cut, places=13
            )
            self.assertAlmostEqual(
                got["training_power_error_sum"][ir, idop],
                training_sum, places=11
            )
            self.assertAlmostEqual(
                got["alpha_quantization_error"][ir, idop],
                expected_alpha, places=13
            )
            self.assertAlmostEqual(
                got["total"][ir, idop], expected_total, places=11
            )

    def test_pow_and_cfar_integration_on_synthetic_zero_map(self):
        import json
        import tempfile

        rd = [[(0, 0) for _ in range(32)] for _ in range(128)]
        original = {"FFT5": np.zeros((128, 32), dtype=np.complex128)}
        with tempfile.TemporaryDirectory(
                dir=ROOT / "engineering" / "s04_numeric") as tmp:
            detail = Path(tmp) / "synthetic-cfar-details.json"
            result = RUNNER.pow_and_cfar(
                {"rd": rd}, original, 1, detail
            )
            self.assertEqual(result["integer_oracle"]["power_cell_count"], 4096)
            self.assertEqual(result["integer_oracle"]["power_mismatches"], 0)
            self.assertEqual(result["integer_oracle"]["CUT_training_comparisons"], 2782)
            self.assertEqual(result["integer_oracle"]["training_mismatches"], 0)
            self.assertEqual(result["integer_oracle"]["CUT_alarm_comparisons"], 2782)
            self.assertEqual(result["integer_oracle"]["alarm_mismatches"], 0)
            self.assertEqual(result["integer_oracle"]["CUT_margin_comparisons"], 2782)
            self.assertEqual(result["integer_oracle"]["margin_mismatches"], 0)
            evidence = json.loads(detail.read_text())
            self.assertEqual(len(evidence["CUTs"]), 2782)
            self.assertEqual(evidence["changed"], [])
            self.assertTrue(all(cut["SUM40_Fixed_stored"] == 0
                                for cut in evidence["CUTs"]))
            self.assertEqual(result["Float_fixed_CFAR"]["total_CUT_denominator"],
                             2782)

    def test_rejects_wrong_map_shape_and_non_c05_training_geometry(self):
        epow = np.ones((128, 32), dtype=np.float64)
        train_avg = np.ones((128, 32), dtype=np.float64)
        offsets = self.offsets()
        with self.assertRaisesRegex(ValueError, "128x32"):
            RUNNER.cfar_uncertainty_terms(
                np.ones((107, 26)), train_avg, offsets,
                Fraction(490007, 65536), 7.476912055027923
            )
        with self.assertRaisesRegex(ValueError, "40-cell"):
            RUNNER.cfar_uncertainty_terms(
                epow, train_avg, offsets[:-1],
                Fraction(490007, 65536), 7.476912055027923
            )
        with self.assertRaisesRegex(ValueError, "40-cell"):
            RUNNER.cfar_uncertainty_terms(
                epow, train_avg, offsets + (offsets[0],),
                Fraction(490007, 65536), 7.476912055027923
            )

    def test_frozen_numeric_decisions_are_unchanged(self):
        self.assertEqual(RUNNER.ALPHA_FIXED, Fraction(490007, 65536))
        self.assertEqual(RUNNER.ALPHA_FLOAT, 7.476912055027923)
        self.assertEqual(RUNNER.SIDES, {
            "NOISE_ONLY_UNIT": 5,
            "SINGLE_TARGET_REFERENCE_LIKE_LAB": 1,
        })
        source = (ROOT / "engineering/s04_numeric/"
                  "s04_c06_16cpi_authorized_runner_v1.py").read_text()
        self.assertIn("ENG.run_one(src,iq,inputtel,'C_hypothetical',(0,1,0,1,1),g",
                      source)
        self.assertIn("pack['architecture']!='C'", source)
        self.assertIn("pack['fft_shifts']!=[0,1,0,1,1]", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)

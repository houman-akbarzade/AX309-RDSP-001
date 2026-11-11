"""Focused unit tests for C06 trace persistence only.

No radar pipeline, IQ generation, CPI, C06 acceptance vector, seed or
statistical procedure is executed here.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engineering" / "s04_numeric"))
import s04_c02_integer_bittrue_v05 as DUT
import s04_c04_selected_C_stage_capture_v1 as C04
import s04_c06_fulltrace_capture_v1 as TRACE


class C06FullTracePersistenceUnitTests(unittest.TestCase):
    def test_more_than_24_events_are_streamed_and_read_back_in_both_scopes(self):
        with tempfile.TemporaryDirectory() as tmp:
            def executor():
                input_tel = DUT.Telemetry()
                for i in range(40):
                    input_tel.record("IQ", (0, i), "I", 32768 + i, 16)
                processing_tel = DUT.Telemetry()
                for i in range(35):
                    processing_tel.record("FFT5", (i % 32, i), "Q",
                                          (1 << 24) + i, 25)
                return "fixture-only"

            captured = TRACE.capture_with_executor(
                executor=executor, cpi_id="UNIT-TRACE-0001",
                profile_id="DIAGNOSTIC_ONLY", gain=1,
                vector_id="SYNTHETIC-LOGGER-FIXTURE", output_dir=tmp
            )
            manifest = captured["manifest"]
            self.assertEqual(manifest["status"], "COMPLETE_READBACK_VERIFIED")
            self.assertEqual(manifest["total_event_count"], 75)
            scopes = {x["source_scope"]: x for x in manifest["per_scope"]}
            combined = hashlib.sha256()
            for scope in ("input", "processing"):
                combined.update((Path(tmp) / scopes[scope]["file"]).read_bytes())
            self.assertEqual(manifest["complete_ordered_stream_sha256"],
                             combined.hexdigest())
            self.assertEqual(scopes["input"]["event_count"], 40)
            self.assertEqual(scopes["processing"]["event_count"], 35)
            self.assertTrue(scopes["input"]["legacy_preview_truncated"])
            self.assertTrue(scopes["processing"]["legacy_preview_truncated"])
            self.assertEqual(scopes["input"]["legacy_preview_count"], 24)
            all_ids = []
            for scope, item in scopes.items():
                path = Path(tmp) / item["file"]
                raw = path.read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
                records = [json.loads(line) for line in raw.splitlines()]
                self.assertEqual(len(records), item["event_count"])
                self.assertEqual(
                    [x["ordinal_in_stream"] for x in records],
                    list(range(item["event_count"]))
                )
                self.assertTrue(all(x["cpi_id"] == "UNIT-TRACE-0001" for x in records))
                self.assertTrue(all(x["source_scope"] == scope for x in records))
                self.assertTrue(all(x["pre_narrow_integer"] is not None for x in records))
                self.assertTrue(all(x["event_id"] and x["sticky"] for x in records))
                for event in records:
                    before = int(event["pre_narrow_integer"])
                    self.assertTrue(before < int(event["min_integer"]) or
                                    before > int(event["max_integer"]))
                    self.assertEqual(event["direction"],
                                     "negative" if before < 0 else "positive")
                all_ids.extend(x["event_id"] for x in records)
            self.assertEqual(len(all_ids), len(set(all_ids)))
            self.assertEqual(captured["result"], "fixture-only")

    def test_adapter_can_wrap_the_pinned_C04_capture_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            original_telemetry = C04.Telemetry
            def executor():
                input_tel = C04.Telemetry()
                input_tel.record("IQ", (0, 0), "I", 40000, 16)
                processing_tel = C04.Telemetry()
                processing_tel.record("FFT5", (0, 0), "Q", 1 << 25, 25)
                return "C04-interface-fixture-only"

            captured = TRACE.capture_with_executor(
                executor=executor, cpi_id="UNIT-TRACE-C04",
                profile_id="DIAGNOSTIC_ONLY", gain=1,
                vector_id="C04-INTERFACE-FIXTURE", output_dir=tmp,
                engine_module=C04
            )
            self.assertEqual(captured["manifest"]["status"],
                             "COMPLETE_READBACK_VERIFIED")
            self.assertEqual(captured["manifest"]["total_event_count"], 2)
            self.assertIs(C04.Telemetry, original_telemetry)

    def test_unsigned_power_and_cfar_intermediate_guards_are_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            def executor():
                DUT.Telemetry()
                processing_tel = DUT.Telemetry()
                DUT.unsigned_intermediate_guard(
                    1 << 51, 51, processing_tel, "POWER_RAW", (12, 7)
                )
                DUT.unsigned_intermediate_guard(
                    1 << 68, 68, processing_tel, "CFAR_LEFT_PRODUCT", (12, 7)
                )
                DUT.unsigned_intermediate_guard(
                    1 << 72, 72, processing_tel, "CFAR_RIGHT_PRODUCT", (12, 7)
                )
                return processing_tel.summary()["total"]

            captured = TRACE.capture_with_executor(
                executor=executor, cpi_id="UNIT-TRACE-UNSIGNED-GUARDS",
                profile_id="DIAGNOSTIC_ONLY", gain=1,
                vector_id="UNSIGNED-GUARD-FIXTURE", output_dir=tmp
            )
            self.assertEqual(captured["result"], 3)
            processing = next(x for x in captured["manifest"]["per_scope"]
                              if x["source_scope"] == "processing")
            records = [json.loads(line) for line in
                       (Path(tmp) / processing["file"]).read_bytes().splitlines()]
            self.assertEqual([x["stage"] for x in records],
                             ["POWER", "CFAR", "CFAR"])
            self.assertEqual([x["site"] for x in records],
                             ["POWER_RAW", "CFAR_LEFT_PRODUCT", "CFAR_RIGHT_PRODUCT"])
            self.assertTrue(all(x["signedness"] == "unsigned" for x in records))
            self.assertTrue(all(x["kind"] == "intermediate_width_exceeded" for x in records))
            self.assertEqual([x["cumulative_count"] for x in records], [1, 1, 1])

    def test_zero_event_cpi_still_gets_two_complete_empty_trace_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            def executor():
                DUT.Telemetry()
                DUT.Telemetry()
                return None

            captured = TRACE.capture_with_executor(
                executor=executor, cpi_id="UNIT-TRACE-ZERO",
                profile_id="DIAGNOSTIC_ONLY", gain=5,
                vector_id="EMPTY-LOGGER-FIXTURE", output_dir=tmp
            )
            self.assertEqual(captured["manifest"]["total_event_count"], 0)
            for item in captured["manifest"]["per_scope"]:
                raw = (Path(tmp) / item["file"]).read_bytes()
                self.assertEqual(raw, b"")
                self.assertEqual(item["sha256"], hashlib.sha256(b"").hexdigest())
                self.assertEqual(item["readback"], "PASS")

    def test_executor_failure_preserves_partial_trace_and_marks_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            def executor():
                tel = DUT.Telemetry()
                tel.record("IQ", (0, 0), "I", 40000, 16)
                raise RuntimeError("synthetic logger interruption")

            with self.assertRaisesRegex(RuntimeError, "synthetic logger interruption"):
                TRACE.capture_with_executor(
                    executor=executor, cpi_id="UNIT-TRACE-INTERRUPT",
                    profile_id="DIAGNOSTIC_ONLY", gain=1,
                    vector_id="INTERRUPTED-LOGGER-FIXTURE", output_dir=tmp
                )
            incomplete = json.loads(
                (Path(tmp) / "UNIT-TRACE-INTERRUPT.incomplete.json").read_text()
            )
            self.assertEqual(incomplete["status"],
                             "INCOMPLETE_CAPTURE_NOT_VALID_FOR_PREFLIGHT")
            self.assertEqual(len(incomplete["partial_scopes"]), 1)
            partial = Path(tmp) / incomplete["partial_scopes"][0]["partial_file"]
            self.assertTrue(partial.exists())
            self.assertEqual(len(partial.read_bytes().splitlines()), 1)
            self.assertFalse((Path(tmp) / "UNIT-TRACE-INTERRUPT.manifest.json").exists())

    def test_c01_profile_gain_pair_is_enforced_before_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "g=5"):
                TRACE.capture_with_executor(
                    executor=lambda: None, cpi_id="UNIT-TRACE-BAD-G",
                    profile_id="NOISE_ONLY_UNIT", gain=1,
                    vector_id="INVALID-PROFILE-FIXTURE", output_dir=tmp
                )
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_existing_cpi_trace_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            def executor():
                DUT.Telemetry()
                DUT.Telemetry()

            kwargs = dict(cpi_id="UNIT-TRACE-IMMUTABLE",
                          profile_id="DIAGNOSTIC_ONLY", gain=1,
                          vector_id="NO-OVERWRITE-FIXTURE", output_dir=tmp)
            TRACE.capture_with_executor(executor=executor, **kwargs)
            with self.assertRaises(FileExistsError):
                TRACE.capture_with_executor(executor=executor, **kwargs)


if __name__ == "__main__":
    unittest.main(verbosity=2)

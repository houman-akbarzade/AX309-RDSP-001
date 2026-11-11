"""S04-C06 durable full overflow-trace adapter.

Wraps the frozen v0.5 Telemetry call sites without changing any integer
arithmetic, rounding, coefficients, formats, saturation or narrowing.
The executor must create exactly two Telemetry instances in order:
input quantization, then processing. This module is capture infrastructure,
not a CPI generator or C06 acceptance runner.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT / "engineering" / "s04_numeric"))
import s04_c02_integer_bittrue_v05 as DUT

_NAMESPACE = uuid.UUID("f039d62a-b7fa-4bad-9c69-2c11ca52e80d")
_CPI_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _canonical_line(record: dict) -> bytes:
    return json.dumps(record, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8") + b"\n"


class C06FullTraceRecorder(DUT.Telemetry):
    """Drop-in Telemetry replacement that streams every event to JSONL."""

    instances = []
    cpi_id = None
    profile_id = None
    gain = None
    vector_id = None
    output_dir = None
    input_payload_sha256 = None
    engine_source_sha256 = None
    arithmetic_contract_sha256 = None
    _configured = False

    def __init__(self):
        if not type(self)._configured:
            raise RuntimeError("C06 trace recorder has not been configured")
        super().__init__()
        index = len(type(self).instances)
        if index > 1:
            raise RuntimeError("unexpected third Telemetry instance; scope order is ambiguous")
        self.source_scope = ("input", "processing")[index]
        self.events_written = 0
        self.event_ids = set()
        self.first_event = None
        self.last_event = None
        self.stream_hash = hashlib.sha256()
        stem = type(self).cpi_id
        self.partial_path = type(self).output_dir / f"{stem}.{self.source_scope}.jsonl.partial"
        self.final_path = type(self).output_dir / f"{stem}.{self.source_scope}.jsonl"
        if self.partial_path.exists() or self.final_path.exists():
            raise FileExistsError(f"trace output already exists for {stem}/{self.source_scope}")
        self._file = self.partial_path.open("xb")
        type(self).instances.append(self)

    def record(self, site, indices, component, before, W, under=False):
        # Keep the original v0.5 counters, 24-event preview and digest unchanged.
        super().record(site, indices, component, before, W, under=under)
        ordinal = self.events_written
        kind = "intermediate_width_exceeded" if under else "output_saturation"
        signed = component != "unsigned"
        index_list = list(indices)
        event_key = json.dumps(index_list, separators=(",", ":"))
        event_name = (
            f"{type(self).cpi_id}|{self.source_scope}|{ordinal}|{site}|"
            f"{event_key}|{component}|{kind}"
        )
        event_id = str(uuid.uuid5(_NAMESPACE, event_name))
        if event_id in self.event_ids:
            raise RuntimeError(f"duplicate event id {event_id}")
        site_name = str(site)
        pulse_index = None
        range_index = None
        bin_or_tap = None
        if site_name == "IQ":
            stage = "INPUT"
            pulse_index, range_index = index_list[0], index_list[1]
        elif site_name.startswith("MF"):
            stage = "MF"
            pulse_index = index_list[0]
            range_index = index_list[1]
            bin_or_tap = index_list[2] if len(index_list) > 2 else None
        elif site_name.startswith("MTI"):
            stage = "MTI"
            pulse_index = index_list[0]
            range_index = index_list[1]
        elif site_name.startswith("FFT"):
            stage = site_name.split("_")[0]
            range_index = index_list[0]
            bin_or_tap = index_list[1:] if len(index_list) > 1 else None
        elif site_name.startswith("POWER"):
            stage = "POWER"
            range_index = index_list[0]
            bin_or_tap = index_list[1] if len(index_list) > 1 else None
        elif site_name.startswith("SUM40"):
            stage = "SUM40"
            range_index = index_list[0]
            bin_or_tap = index_list[1] if len(index_list) > 1 else None
        elif site_name.startswith("CFAR"):
            stage = "CFAR"
            range_index = index_list[0]
            bin_or_tap = index_list[1] if len(index_list) > 1 else None
        else:
            stage = site_name
        min_value = -(1 << (W - 1)) if signed else 0
        max_value = (1 << (W - 1)) - 1 if signed else (1 << W) - 1
        cumulative_count = self.counts[site_name + ":" + kind]
        event = {
            "event_id": event_id,
            "cpi_id": type(self).cpi_id,
            "profile_id": type(self).profile_id,
            "g": type(self).gain,
            "vector_id": type(self).vector_id,
            "source_scope": self.source_scope,
            "ordinal_in_stream": ordinal,
            "site": site_name,
            "stage": stage,
            "indices": index_list,
            "pulse": pulse_index,
            "range": range_index,
            "bin_or_tap": bin_or_tap,
            "component": str(component),
            "I_or_Q": str(component),
            "signed": signed,
            "signedness": "signed" if signed else "unsigned",
            "word_width": int(W),
            "fractional_bits": 0 if site_name == "IQ" else None,
            "pre_narrow_integer": str(int(before)),
            "full_integer_before_narrowing": str(int(before)),
            "min_integer": str(min_value),
            "max_integer": str(max_value),
            "signed_min": str(min_value) if signed else None,
            "signed_max": str(max_value) if signed else None,
            "direction": "negative" if before < 0 else "positive",
            "kind": kind,
            "cumulative_count": cumulative_count,
            "sticky": True,
        }
        raw = _canonical_line(event)
        self._file.write(raw)
        self._file.flush()
        self.stream_hash.update(raw)
        self.event_ids.add(event_id)
        self.events_written += 1
        if self.first_event is None:
            self.first_event = event
        self.last_event = event

    def close_durable(self):
        if not self._file.closed:
            self._file.flush()
            os.fsync(self._file.fileno())
            self._file.close()

    def close_incomplete(self):
        self.close_durable()

    def finalize_file(self):
        self.close_durable()
        if self.final_path.exists():
            raise FileExistsError(self.final_path)
        self.partial_path.replace(self.final_path)
        raw = self.final_path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != self.stream_hash.hexdigest():
            raise IOError(f"trace hash mismatch after readback: {self.final_path}")
        lines = raw.splitlines()
        if len(lines) != self.events_written:
            raise IOError(f"trace count mismatch after readback: {self.final_path}")
        decoded = [json.loads(line) for line in lines]
        if len({e["event_id"] for e in decoded}) != len(decoded):
            raise IOError(f"duplicate event IDs after readback: {self.final_path}")
        if [e["ordinal_in_stream"] for e in decoded] != list(range(len(decoded))):
            raise IOError(f"non-contiguous event order after readback: {self.final_path}")
        if any(e["cpi_id"] != type(self).cpi_id for e in decoded):
            raise IOError(f"CPI identity mismatch after readback: {self.final_path}")
        if any(e["source_scope"] != self.source_scope for e in decoded):
            raise IOError(f"scope mismatch after readback: {self.final_path}")
        seen_counts = Counter()
        for event in decoded:
            width = event["word_width"]
            signed = event["signed"]
            expected_min = -(1 << (width - 1)) if signed else 0
            expected_max = (1 << (width - 1)) - 1 if signed else (1 << width) - 1
            before = int(event["pre_narrow_integer"])
            if (event["min_integer"], event["max_integer"]) != (str(expected_min), str(expected_max)):
                raise IOError(f"stored numeric limits mismatch: {event['event_id']}")
            if expected_min <= before <= expected_max:
                raise IOError(f"event does not exceed its declared numeric limits: {event['event_id']}")
            if event["direction"] != ("negative" if before < 0 else "positive"):
                raise IOError(f"event sign mismatch: {event['event_id']}")
            if event["sticky"] is not True:
                raise IOError(f"sticky event flag missing: {event['event_id']}")
            if event["full_integer_before_narrowing"] != event["pre_narrow_integer"]:
                raise IOError(f"pre-narrow integer alias mismatch: {event['event_id']}")
            if event["I_or_Q"] != event["component"]:
                raise IOError(f"component alias mismatch: {event['event_id']}")
            if event["signedness"] != ("signed" if signed else "unsigned"):
                raise IOError(f"signedness mismatch: {event['event_id']}")
            count_key = (event["site"], event["kind"])
            seen_counts[count_key] += 1
            if event["cumulative_count"] != seen_counts[count_key]:
                raise IOError(f"cumulative event count mismatch: {event['event_id']}")
        if decoded and (decoded[0] != self.first_event or decoded[-1] != self.last_event):
            raise IOError(f"first/last event mismatch after readback: {self.final_path}")
        legacy_hash = hashlib.sha256()
        for event in decoded:
            legacy = {k: event[k] for k in (
                "site", "indices", "component", "pre_narrow_integer",
                "direction", "kind"
            )}
            legacy["signed_W"] = event["word_width"]
            legacy_hash.update((json.dumps(
                legacy, sort_keys=True, separators=(",", ":")
            ) + "\n").encode("utf-8"))
            expected_name = (
                f"{type(self).cpi_id}|{self.source_scope}|"
                f"{event['ordinal_in_stream']}|{event['site']}|"
                f"{json.dumps(event['indices'], separators=(',', ':'))}|"
                f"{event['component']}|{event['kind']}"
            )
            if event["event_id"] != str(uuid.uuid5(_NAMESPACE, expected_name)):
                raise IOError(f"event ID derivation mismatch: {event['event_id']}")
        if legacy_hash.hexdigest() != self.summary()["all_event_order_sha256"]:
            raise IOError(f"legacy event-order digest mismatch: {self.final_path}")
        return {
            "source_scope": self.source_scope,
            "file": self.final_path.name,
            "sha256": digest,
            "event_count": len(decoded),
            "first_event": decoded[0] if decoded else None,
            "last_event": decoded[-1] if decoded else None,
            "legacy_preview_count": len(self.summary()["first_24"]),
            "legacy_preview_truncated": self.summary()["events_truncated_in_record"],
            "legacy_order_sha256": self.summary()["all_event_order_sha256"],
            "cumulative_counts_by_site_kind": {
                f"{site}:{kind}": count
                for (site, kind), count in sorted(seen_counts.items())
            },
            "sticky_flags_by_site": {
                site: True for site in sorted({event["site"] for event in decoded})
            },
            "readback": "PASS",
            "unique_ids": "PASS",
            "ordered_sequence": "PASS",
            "no_truncation": True,
        }

    @classmethod
    def configure(cls, *, cpi_id, profile_id, gain, vector_id, output_dir,
                  input_payload_sha256=None, engine_source_sha256=None,
                  arithmetic_contract_sha256=None):
        if not isinstance(cpi_id, str) or not _CPI_RE.fullmatch(cpi_id):
            raise ValueError("cpi_id must be a safe, non-empty stable identifier")
        if type(gain) is not int or gain not in (1, 5):
            raise ValueError("gain must be the frozen C01 integer value 1 or 5")
        if profile_id == "NOISE_ONLY_UNIT" and gain != 5:
            raise ValueError("NOISE_ONLY_UNIT is authorized only with g=5")
        if profile_id == "SINGLE_TARGET_REFERENCE_LIKE_LAB" and gain != 1:
            raise ValueError("SINGLE_TARGET_REFERENCE_LIKE_LAB is authorized only with g=1")
        if profile_id not in ("NOISE_ONLY_UNIT", "SINGLE_TARGET_REFERENCE_LIKE_LAB", "DIAGNOSTIC_ONLY"):
            raise ValueError("profile_id is not an approved C01 profile or DIAGNOSTIC_ONLY fixture")
        cls.instances = []
        cls.cpi_id = cpi_id
        cls.profile_id = str(profile_id)
        cls.gain = int(gain)
        cls.vector_id = str(vector_id)
        for label, digest in (("input_payload_sha256", input_payload_sha256),
                              ("engine_source_sha256", engine_source_sha256),
                              ("arithmetic_contract_sha256", arithmetic_contract_sha256)):
            if digest is not None and not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"{label} must be a lowercase SHA-256 hex digest")
        cls.input_payload_sha256 = input_payload_sha256
        cls.engine_source_sha256 = engine_source_sha256
        cls.arithmetic_contract_sha256 = arithmetic_contract_sha256
        cls.output_dir = Path(output_dir)
        cls.output_dir.mkdir(parents=True, exist_ok=True)
        for suffix in (".input.jsonl.partial", ".processing.jsonl.partial",
                       ".input.jsonl", ".processing.jsonl", ".manifest.json",
                       ".incomplete.json"):
            if (cls.output_dir / f"{cpi_id}{suffix}").exists():
                raise FileExistsError(f"capture already exists for CPI {cpi_id}")
        cls._configured = True

    @classmethod
    def finalize_complete(cls):
        if [x.source_scope for x in cls.instances] != ["input", "processing"]:
            raise RuntimeError(
                "complete capture requires exactly input and processing telemetry scopes"
            )
        scopes = [rec.finalize_file() for rec in cls.instances]
        combined_order_hash = hashlib.sha256()
        for scope in scopes:  # canonical order: input, then processing
            combined_order_hash.update((cls.output_dir / scope["file"]).read_bytes())
        all_ids = set()
        for rec in cls.instances:
            if all_ids.intersection(rec.event_ids):
                raise RuntimeError("event ID collision across telemetry scopes")
            all_ids.update(rec.event_ids)
        manifest = {
            "schema": "AX309-S04-C06-FULL-OVERFLOW-TRACE-v1.0",
            "status": "COMPLETE_READBACK_VERIFIED",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "cpi_id": cls.cpi_id,
            "profile_id": cls.profile_id,
            "g": cls.gain,
            "vector_id": cls.vector_id,
            "input_payload_sha256": cls.input_payload_sha256,
            "engine_source_sha256": cls.engine_source_sha256,
            "arithmetic_contract_sha256": cls.arithmetic_contract_sha256,
            "scope_order": ["input", "processing"],
            "event_order_semantics": "input JSONL order followed by processing JSONL order; each scope has contiguous zero-based ordinal_in_stream",
            "complete_ordered_stream_sha256": combined_order_hash.hexdigest(),
            "total_event_count": sum(x["event_count"] for x in scopes),
            "per_scope": scopes,
            "unique_event_ids": len(all_ids),
            "no_truncation": True,
            "streaming_write": True,
            "durable_fsync": True,
            "bittrue_arithmetic_modified": False,
            "acceptance_test": False,
            "CPI_generated_by_recorder": False,
        }
        path = cls.output_dir / f"{cls.cpi_id}.manifest.json"
        temp = path.with_suffix(path.suffix + ".partial")
        with temp.open("xb") as f:
            f.write(json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                               indent=2).encode("utf-8") + b"\n")
            f.flush()
            os.fsync(f.fileno())
        temp.replace(path)
        # Verify the manifest itself after durable write.
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if loaded != manifest:
            raise IOError("trace manifest readback mismatch")
        manifest["manifest_file"] = path.name
        manifest["manifest_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        return manifest

    @classmethod
    def finalize_incomplete(cls, error):
        partials = []
        for rec in cls.instances:
            rec.close_incomplete()
            if rec.partial_path.exists():
                raw = rec.partial_path.read_bytes()
                partials.append({
                    "source_scope": rec.source_scope,
                    "partial_file": rec.partial_path.name,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "bytes": len(raw),
                    "events_written": rec.events_written,
                })
        manifest = {
            "schema": "AX309-S04-C06-FULL-OVERFLOW-TRACE-v1.0",
            "status": "INCOMPLETE_CAPTURE_NOT_VALID_FOR_PREFLIGHT",
            "cpi_id": cls.cpi_id,
            "profile_id": cls.profile_id,
            "g": cls.gain,
            "vector_id": cls.vector_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "partial_scopes": partials,
            "no_truncation_claim": False,
        }
        path = cls.output_dir / f"{cls.cpi_id}.incomplete.json"
        with path.open("x", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, sort_keys=True, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        return manifest


def capture_with_executor(*, executor, cpi_id, profile_id, gain, vector_id,
                          output_dir, engine_module=DUT,
                          input_payload_sha256=None, engine_source_sha256=None,
                          arithmetic_contract_sha256=None):
    """Capture two Telemetry scopes from a pinned engine module; never runs a CPI itself.

    engine_module must expose the unchanged Telemetry interface used by v0.5.
    It may be the v0.5 datapath module or the C04 stage-capture wrapper.
    """
    C06FullTraceRecorder.configure(
        cpi_id=cpi_id, profile_id=profile_id, gain=gain,
        vector_id=vector_id, output_dir=output_dir,
        input_payload_sha256=input_payload_sha256,
        engine_source_sha256=engine_source_sha256,
        arithmetic_contract_sha256=arithmetic_contract_sha256
    )
    previous = engine_module.Telemetry
    engine_module.Telemetry = C06FullTraceRecorder
    try:
        result = executor()
        manifest = C06FullTraceRecorder.finalize_complete()
        return {"result": result, "manifest": manifest}
    except Exception as exc:
        C06FullTraceRecorder.finalize_incomplete(exc)
        raise
    finally:
        engine_module.Telemetry = previous
        C06FullTraceRecorder._configured = False

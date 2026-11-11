"""Engineer-authorized REQ-RNG-03 Float-first / Fixed-Point qualification.

Twelve deterministic two-target cases: delta-range 3/4/5 samples x
relative phases 0/90/180/270 degrees. The Float phase is completed and
archived first. The Fixed phase reads the exact archived complex IQ arrays.
No noise, no clutter, no architecture/contract/threshold changes.
"""
import sys, json, math, hashlib, platform, datetime
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engineering/s04_numeric"))
from s03_reference import model as S03

ALPHA = 7.476912055027923
G = 1
TARGET_RANGE_1 = 40
TARGET_DOPPLER_BIN = 4
TARGET_VELOCITY = float(S03.bin_velocity(TARGET_DOPPLER_BIN))
TARGET_AMPLITUDE = 0.18
SEPARATIONS = (3, 4, 5)
PHASES_DEG = (0, 90, 180, 270)
RANGE_ERROR_LIMIT_BINS = 1
REQUIRED_SEPARATIONS = (4, 5)

EVIDENCE = ROOT / "engineering/s04_numeric/req_rng03_v1"
INPUTS = EVIDENCE / "REQ-RNG-03-INPUTS-v1.0.npz"
FLOAT_OUTPUTS = EVIDENCE / "REQ-RNG-03-FLOAT-OUTPUTS-v1.0.npz"
FLOAT_RESULTS = EVIDENCE / "REQ-RNG-03-FLOAT-RESULTS-v1.0.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def case_id(delta, phase):
    return f"RNG_D{delta}_PHASE_{phase:03d}"


def strict_pair_association(detections, truth_ranges):
    """One-to-one matching, exact required Doppler bin, +/-1 range bin."""
    candidates = []
    for truth in truth_ranges:
        eligible = []
        for index, det in enumerate(detections):
            error = int(det["range_bin"]) - int(truth)
            if int(det["doppler_bin"]) == TARGET_DOPPLER_BIN and abs(error) <= RANGE_ERROR_LIMIT_BINS:
                eligible.append((index, error))
        candidates.append(eligible)

    full = []
    for i, e1 in candidates[0]:
        for j, e2 in candidates[1]:
            if i != j:
                full.append((abs(e1) + abs(e2), i, j, e1, e2))
    if full:
        _, i, j, e1, e2 = min(full)
        return {
            "matched_count": 2, "missed_count": 0,
            "pairs": [
                {"truth_range_bin": int(truth_ranges[0]), "detection_index": i,
                 "detection_range_bin": int(detections[i]["range_bin"]),
                 "detection_doppler_bin": int(detections[i]["doppler_bin"]),
                 "range_error_bins": int(e1)},
                {"truth_range_bin": int(truth_ranges[1]), "detection_index": j,
                 "detection_range_bin": int(detections[j]["range_bin"]),
                 "detection_doppler_bin": int(detections[j]["doppler_bin"]),
                 "range_error_bins": int(e2)}
            ],
            "distinct_detection_records": True
        }

    # Retain the maximum-cardinality partial association for diagnosis.
    partial = []
    for i, e1 in candidates[0]:
        partial.append((1, abs(e1), i, None, e1, None))
    for j, e2 in candidates[1]:
        partial.append((1, abs(e2), None, j, None, e2))
    if partial:
        _, _, i, j, e1, e2 = min(partial, key=lambda z: ( -z[0], z[1], z[2] if z[2] is not None else 9999,
                                                          z[3] if z[3] is not None else 9999))
        pairs = []
        if i is not None:
            pairs.append({"truth_range_bin": int(truth_ranges[0]), "detection_index": i,
                          "detection_range_bin": int(detections[i]["range_bin"]),
                          "detection_doppler_bin": int(detections[i]["doppler_bin"]),
                          "range_error_bins": int(e1)})
        if j is not None:
            pairs.append({"truth_range_bin": int(truth_ranges[1]), "detection_index": j,
                          "detection_range_bin": int(detections[j]["range_bin"]),
                          "detection_doppler_bin": int(detections[j]["doppler_bin"]),
                          "range_error_bins": int(e2)})
    else:
        pairs = []
    return {
        "matched_count": len(pairs), "missed_count": 2 - len(pairs),
        "pairs": pairs, "distinct_detection_records": len({p["detection_index"] for p in pairs}) == len(pairs)
    }


def run_float_phase():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    cases = [(d, p) for d in SEPARATIONS for p in PHASES_DEG]
    inputs = {}
    arrays = {}
    results = {
        "project": "AX309-RDSP-001", "requirement": "REQ-RNG-03",
        "engineer_approval": {
            "title": "Engineer system approval", "date": "2026-11-12",
            "approved": {
                "target_amplitude_each": TARGET_AMPLITUDE, "gain_g": G,
                "common_doppler_bin": TARGET_DOPPLER_BIN,
                "noise": "none", "clutter": "none",
                "range_separation_samples": list(SEPARATIONS),
                "relative_phase_deg": list(PHASES_DEG),
                "maximum_range_error_bins": RANGE_ERROR_LIMIT_BINS,
                "mandatory_pass_separations": list(REQUIRED_SEPARATIONS),
                "mandatory_success_count": 8,
                "separation_3_sample_disposition": "characterization_only; failure alone does not fail REQ-RNG-03",
                "merged_targets_one_cluster": "FAIL at 4- and 5-sample separations"
            },
            "execution_authorization": "Explicitly granted by project system engineer on 2026-11-12"
        },
        "source_model": "s03_reference.model.generate_cpi / Target",
        "architecture": "C", "fft_shifts": [0, 1, 0, 1, 1],
        "alpha": ALPHA, "gain_g": G,
        "target_1": {"range_bin": TARGET_RANGE_1, "doppler_bin": TARGET_DOPPLER_BIN,
                     "velocity_m_s_nominal": TARGET_VELOCITY, "amplitude": TARGET_AMPLITUDE,
                     "phase_deg": 0},
        "cases": [], "float_phase_status": "RUNNING"
    }

    # FLOAT FIRST: generate and process all 12 scenarios before any Fixed run.
    for delta, phase in cases:
        cid = case_id(delta, phase)
        truth = [TARGET_RANGE_1, TARGET_RANGE_1 + delta]
        targets = [
            S03.Target(TARGET_RANGE_1, TARGET_VELOCITY, TARGET_AMPLITUDE, 0.0),
            S03.Target(TARGET_RANGE_1 + delta, TARGET_VELOCITY, TARGET_AMPLITUDE,
                       math.radians(phase))
        ]
        src = S03.generate_cpi(targets, snr_db=None)
        out = S03.pipeline(src, alpha=ALPHA)
        assoc = strict_pair_association(out["targets"], truth)
        passed = assoc["matched_count"] == 2 and assoc["distinct_detection_records"]
        status = ("PASS" if passed else "FAIL") if delta in REQUIRED_SEPARATIONS else "CHARACTERIZATION_ONLY"

        inputs[f"float_iq_{cid}"] = np.asarray(src, dtype=np.complex128)
        arrays[f"float_mf_{cid}"] = np.asarray(out["pc"], dtype=np.complex128)
        arrays[f"float_mti_{cid}"] = np.asarray(out["mti"], dtype=np.complex128)
        arrays[f"float_doppler_{cid}"] = np.asarray(out["doppler"], dtype=np.complex128)
        arrays[f"float_power_{cid}"] = np.asarray(out["power"], dtype=np.float64)
        arrays[f"float_cfar_{cid}"] = np.asarray(out["cfar"], dtype=np.uint8)

        component_energy = 33 * 16 * TARGET_AMPLITUDE**2
        results["cases"].append({
            "case_id": cid, "delta_range_bins": delta,
            "separation_m_exact": float(delta * S03.C / (2 * S03.FS)),
            "relative_phase_deg": phase,
            "source": {
                "shape": list(src.shape), "dtype": str(src.dtype),
                "sha256_float_iq_little_endian": sha(np.asarray(src, dtype="<c16").tobytes()),
                "target_component_energy_each_before_superposition": component_energy,
                "target_component_energy_equal": True,
                "noise": "none", "clutter": "none",
                "input_gain_g": G
            },
            "float": {
                "status": status, "cfar_alarm_count": int(np.count_nonzero(out["cfar"])),
                "cluster_count": len(out["targets"]), "clusters": out["targets"],
                "association": assoc
            },
            "fixed": {"status": "NOT_RUN_YET"}
        })
        print("FLOAT", cid, "clusters", len(out["targets"]),
              "matched", assoc["matched_count"], "status", status, flush=True)

    np.savez_compressed(INPUTS, **inputs)
    np.savez_compressed(FLOAT_OUTPUTS, **arrays)
    results["input_archive"] = {
        "path": str(INPUTS.relative_to(ROOT)), "sha256": sha(INPUTS.read_bytes()),
        "arrays": len(inputs), "format": "compressed NPZ; exact complex128 CPI arrays"
    }
    results["float_output_archive"] = {
        "path": str(FLOAT_OUTPUTS.relative_to(ROOT)), "sha256": sha(FLOAT_OUTPUTS.read_bytes()),
        "arrays": len(arrays)
    }
    results["float_phase_status"] = "COMPLETE_12_OF_12"
    results["environment"] = {
        "python": platform.python_version(), "numpy": np.__version__,
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    FLOAT_RESULTS.write_text(json.dumps(results, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print("FLOAT_PHASE_COMPLETE", FLOAT_RESULTS.relative_to(ROOT), flush=True)
    return results


if __name__ == "__main__":
    run_float_phase()

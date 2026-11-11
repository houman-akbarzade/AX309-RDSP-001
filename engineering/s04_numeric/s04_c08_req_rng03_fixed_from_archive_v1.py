"""REQ-RNG-03 Fixed-Point qualification using the exact archived Float IQ inputs.

Float is completed and archived by s04_c08_req_rng03_float_first_v1.py first.
This script NEVER regenerates CPI inputs and NEVER reruns the Float pipeline.
It reads the archived complex128 IQ arrays, packs those exact samples to Q1.15,
runs the frozen architecture-C Fixed-Point path, and compares independent
C03 Fraction and C05 union-find oracles.
"""
import sys, json, math, hashlib, platform, datetime
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engineering/s04_numeric"))
from s03_reference import model as S03
import s04_c03_independent_oracle_v1 as OR
import s04_c04_selected_C_stage_capture_v1 as DUT
import s04_c05_native_integer_v1 as NAT
import s04_c05_integrated_qualification_v1 as C05
import s04_c08_req_scr01_qualification_v1 as SCR
import s04_c08_req_rng03_float_first_v1 as RNG

G = 1
SHIFTS = (0, 1, 0, 1, 1)
INPUTS = ROOT / "engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-INPUTS-v1.0.npz"
FLOAT_OUTPUTS = ROOT / "engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-FLOAT-OUTPUTS-v1.0.npz"
FLOAT_RESULTS = ROOT / "engineering/s04_numeric/req_rng03_v1/REQ-RNG-03-FLOAT-RESULTS-v1.0.json"
EVIDENCE = ROOT / "engineering/s04_numeric/req_rng03_v1"
Q15_INPUTS = EVIDENCE / "REQ-RNG-03-Q15-INPUTS-v1.0.npz"
FIXED_OUTPUTS = EVIDENCE / "REQ-RNG-03-FIXED-OUTPUTS-v1.0.npz"
FINAL_RESULTS = EVIDENCE / "REQ-RNG-03-RESULTS-v1.0.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def max_rms(a, b):
    d = np.abs(np.asarray(a) - np.asarray(b))
    return {"MAX": float(np.max(d)), "RMS": float(np.sqrt(np.mean(d*d))), "count": int(d.size)}


def pack_exact_float_iq(src):
    iq, sat = SCR.pack_source(src)
    arr = np.asarray(iq, dtype=np.int16)
    return iq, arr, sat


def main():
    if not INPUTS.exists() or not FLOAT_OUTPUTS.exists() or not FLOAT_RESULTS.exists():
        raise FileNotFoundError("Float phase must complete and archive all 12 scenarios before Fixed execution.")

    float_results = json.loads(FLOAT_RESULTS.read_text())
    if float_results.get("float_phase_status") != "COMPLETE_12_OF_12" or len(float_results.get("cases", [])) != 12:
        raise AssertionError("Float phase evidence is incomplete; Fixed phase not authorized to start.")

    input_sha = sha(INPUTS.read_bytes())
    with np.load(INPUTS, allow_pickle=False) as z:
        input_arrays = {k: z[k] for k in z.files}
    with np.load(FLOAT_OUTPUTS, allow_pickle=False) as z:
        float_arrays = {k: z[k] for k in z.files}
    if len(input_arrays) != 12 or len(float_arrays) != 60:
        raise AssertionError(f"Unexpected Float archive shape: IQ={len(input_arrays)} outputs={len(float_arrays)}")

    result_by_id = {r["case_id"]: r for r in float_results["cases"]}
    q15_archive = {}
    fixed_archive = {}
    fixed_cases = []

    # FIXED SECOND: only read the immutable Float IQ archive. No input regeneration.
    for delta in RNG.SEPARATIONS:
        for phase in RNG.PHASES_DEG:
            cid = RNG.case_id(delta, phase)
            key = f"float_iq_{cid}"
            if key not in input_arrays:
                raise KeyError(f"Missing archived exact Float IQ array: {key}")
            src = input_arrays[key]
            source_hash = sha(np.asarray(src, dtype="<c16").tobytes())
            expected_hash = result_by_id[cid]["source"]["sha256_float_iq_little_endian"]
            if source_hash != expected_hash:
                raise AssertionError(f"Archived Float IQ hash mismatch for {cid}")

            iq, q15_array, input_sat = pack_exact_float_iq(src)
            q15_archive[f"q15_iq_{cid}"] = q15_array
            tel = DUT.Telemetry()
            fixed = DUT.run_one(src, iq, tel, "C_hypothetical", SHIFTS, G, capture_stages=True)
            cap = fixed["captured"]

            # Independent C03 stage arithmetic and C03/C05 map checks.
            oracle_errors = []
            stage_oracle = None
            mapped = None
            try:
                stage_oracle, _, _, _ = SCR.compare_integer_stages(iq, cap)
            except Exception as exc:
                oracle_errors.append({"oracle": "C03_stage", "error": repr(exc)})
            try:
                mapped = SCR.independent_map_check(cap["rd"])
            except Exception as exc:
                oracle_errors.append({"oracle": "C03_power_Cfar_C05_grouping", "error": repr(exc)})
                # Retain diagnostic native map outputs even if the independent check failed.
                try:
                    mapped = NAT.complete_map(cap["rd"])
                except Exception as map_exc:
                    oracle_errors.append({"oracle": "native_map", "error": repr(map_exc)})

            if mapped is None:
                fixed_cases.append({
                    "case_id": cid, "delta_range_bins": delta, "relative_phase_deg": phase,
                    "status": "INCONCLUSIVE_MAP_FAILURE",
                    "input_sha256": source_hash, "oracle_errors": oracle_errors
                })
                print("FIXED", cid, "INCONCLUSIVE_MAP_FAILURE", flush=True)
                continue

            float_case = result_by_id[cid]["float"]
            float_targets = float_case["clusters"]
            fixed_targets = mapped["clusters"]
            truth = [RNG.TARGET_RANGE_1, RNG.TARGET_RANGE_1 + delta]
            fixed_assoc = RNG.strict_pair_association(fixed_targets, truth)
            float_assoc = float_case["association"]

            float_mask = np.asarray(float_arrays[f"float_cfar_{cid}"], dtype=bool)
            fixed_mask = np.asarray(mapped["mask"], dtype=bool)
            valid = np.zeros((128, 32), dtype=bool)
            valid[3:110, 3:29] = True
            changed_cuts = int(np.logical_xor(float_mask, fixed_mask)[valid].sum())

            fixed_mf_codes = np.asarray(cap["mf"], dtype=np.float64)
            fixed_mf = (fixed_mf_codes[:, :, 0] + 1j * fixed_mf_codes[:, :, 1]) * (G / 32768.0)
            fixed_mti_codes = np.asarray(cap["mti"], dtype=np.float64)
            fixed_mti = (fixed_mti_codes[:, :, 0] + 1j * fixed_mti_codes[:, :, 1]) * (G / 32768.0)
            fixed_fft_codes = np.asarray(cap["rd"], dtype=np.float64)
            fixed_fft = (fixed_fft_codes[:, :, 0] + 1j * fixed_fft_codes[:, :, 1]) * (G * 8 / 32768.0)
            float_mf = float_arrays[f"float_mf_{cid}"]
            float_mti = float_arrays[f"float_mti_{cid}"]
            float_fft = float_arrays[f"float_doppler_{cid}"]
            float_power = float_arrays[f"float_power_{cid}"]
            fixed_power = np.asarray(mapped["power"], dtype=np.float64) * (G * 8 / 32768.0)**2

            fixed_archive[f"fixed_mf_{cid}"] = fixed_mf
            fixed_archive[f"fixed_mti_{cid}"] = fixed_mti
            fixed_archive[f"fixed_fft_original_amplitude_{cid}"] = fixed_fft
            fixed_archive[f"fixed_power_original_units_{cid}"] = fixed_power
            fixed_archive[f"fixed_cfar_{cid}"] = fixed_mask.astype(np.uint8)

            overflow = fixed["overflow"]
            power_overflow = len(mapped["power_events"])
            oracle_pass = not oracle_errors
            association_pass = fixed_assoc["matched_count"] == 2 and fixed_assoc["distinct_detection_records"]
            float_association_pass = float_assoc["matched_count"] == 2 and float_assoc["distinct_detection_records"]
            mandatory = delta in RNG.REQUIRED_SEPARATIONS
            case_pass = (association_pass and float_association_pass and oracle_pass
                         and len(input_sat) == 0 and overflow["total"] == 0 and power_overflow == 0)
            status = ("PASS" if case_pass else "FAIL") if mandatory else "CHARACTERIZATION_ONLY"

            fixed_cases.append({
                "case_id": cid, "delta_range_bins": delta,
                "separation_m_exact": float(delta * S03.C / (2 * S03.FS)),
                "relative_phase_deg": phase, "input_sha256_reused_from_Float": source_hash,
                "same_exact_archived_float_iq_used": True,
                "input_q15_saturation_count": len(input_sat),
                "fixed": {
                    "status": status, "cfar_alarm_count": int(np.count_nonzero(fixed_mask)),
                    "cluster_count": len(fixed_targets), "clusters": fixed_targets,
                    "association": fixed_assoc,
                    "internal_overflow_count": overflow["total"],
                    "internal_overflow_by_site": overflow["counts"],
                    "power_overflow_count": power_overflow,
                    "C03_stage_oracle": stage_oracle,
                    "C03_power_Cfar_C05_grouping_oracle": "PASS" if oracle_pass else "FAIL",
                    "oracle_errors": oracle_errors
                },
                "float": {
                    "status": float_case["status"], "cluster_count": len(float_targets),
                    "association": float_assoc
                },
                "Float_vs_Fixed": {
                    "changed_valid_CUT_count": changed_cuts,
                    "cluster_count_delta_fixed_minus_float": len(fixed_targets) - len(float_targets),
                    "Float_peak_coordinates": [[x["range_bin"], x["doppler_bin"]] for x in float_targets],
                    "Fixed_peak_coordinates": [[x["range_bin"], x["doppler_bin"]] for x in fixed_targets],
                    "MF_original_amplitude": max_rms(float_mf, fixed_mf),
                    "MTI_original_amplitude": max_rms(float_mti, fixed_mti),
                    "FFT_original_amplitude": max_rms(float_fft, fixed_fft),
                    "power_original_units": max_rms(float_power, fixed_power)
                },
                "mandatory_acceptance_case": mandatory,
                "acceptance_pass": case_pass if mandatory else None
            })
            print("FIXED", cid, "clusters", len(fixed_targets),
                  "matched", fixed_assoc["matched_count"], "oracle", "PASS" if oracle_pass else "FAIL",
                  "status", status, flush=True)

    np.savez_compressed(Q15_INPUTS, **q15_archive)
    np.savez_compressed(FIXED_OUTPUTS, **fixed_archive)
    by_id = {x["case_id"]: x for x in fixed_cases}
    combined = []
    for fcase in float_results["cases"]:
        cid = fcase["case_id"]
        combined.append({
            "case_id": cid, "delta_range_bins": fcase["delta_range_bins"],
            "separation_m_exact": fcase["separation_m_exact"],
            "relative_phase_deg": fcase["relative_phase_deg"],
            "source": fcase["source"], "float": fcase["float"],
            "fixed": by_id[cid]["fixed"] if "fixed" in by_id[cid] else {"status": by_id[cid]["status"]},
            "Float_vs_Fixed": by_id[cid].get("Float_vs_Fixed"),
            "acceptance_pass": by_id[cid].get("acceptance_pass")
        })

    mandatory = [x for x in combined if x["delta_range_bins"] in RNG.REQUIRED_SEPARATIONS]
    float_passes = sum(x["float"]["association"]["matched_count"] == 2 and
                       x["float"]["association"]["distinct_detection_records"] for x in mandatory)
    fixed_passes = sum(x["fixed"].get("association", {}).get("matched_count") == 2 and
                       x["fixed"].get("association", {}).get("distinct_detection_records") for x in mandatory)
    both_passes = sum(bool(x["acceptance_pass"]) for x in mandatory)
    all_oracles = all(
        x["fixed"].get("C03_power_Cfar_C05_grouping_oracle") == "PASS" and
        not x["fixed"].get("oracle_errors")
        for x in combined
    )
    no_overflow = all(
        x["fixed"].get("internal_overflow_count") == 0 and
        x["fixed"].get("power_overflow_count") == 0 and
        x["fixed"].get("input_q15_saturation_count") == 0
        for x in combined
    )
    result = {
        "project": "AX309-RDSP-001", "requirement": "REQ-RNG-03",
        "decision_basis": "Engineer-system approval 2026-11-12; mandatory resolution criteria apply at 4- and 5-sample separation; 3-sample cases are characterization only.",
        "execution_order": [
            "All 12 Float CPI generated and processed first; exact complex128 arrays archived.",
            "Fixed-Point phase then read those archived arrays; no CPI regeneration and no Float pipeline rerun."
        ],
        "engineer_approval": float_results["engineer_approval"],
        "architecture": "C", "fft_shifts": list(SHIFTS), "gain_g": G,
        "alpha": float_results["alpha"],
        "input_archive": {
            "path": str(INPUTS.relative_to(ROOT)), "sha256": input_sha,
            "arrays": len(input_arrays), "exact_complex128_CPI": True
        },
        "float_output_archive": float_results["float_output_archive"],
        "q15_input_archive": {
            "path": str(Q15_INPUTS.relative_to(ROOT)), "sha256": sha(Q15_INPUTS.read_bytes()),
            "arrays": len(q15_archive)
        },
        "fixed_output_archive": {
            "path": str(FIXED_OUTPUTS.relative_to(ROOT)), "sha256": sha(FIXED_OUTPUTS.read_bytes()),
            "arrays": len(fixed_archive)
        },
        "cases": combined,
        "acceptance_summary": {
            "all_12_scenarios_float_executed": len(float_results["cases"]) == 12,
            "all_12_fixed_executed": len(fixed_cases) == 12,
            "float_mandatory_pass_count": float_passes,
            "fixed_mandatory_pass_count": fixed_passes,
            "both_float_and_fixed_mandatory_pass_count": both_passes,
            "mandatory_case_count": 8,
            "float_8_of_8_pass": float_passes == 8,
            "fixed_8_of_8_pass": fixed_passes == 8,
            "combined_8_of_8_pass": both_passes == 8,
            "all_12_independent_C03_C05_oracles_pass": all_oracles,
            "all_12_no_input_or_internal_or_power_overflow": no_overflow,
            "three_sample_cases_are_characterization_only": True
        },
        "overall": "PASS" if both_passes == 8 and all_oracles and no_overflow else "FAIL",
        "fixed_phase_status": "COMPLETE_12_OF_12" if len(fixed_cases) == 12 else "INCOMPLETE",
        "environment": {
            "python": platform.python_version(), "numpy": np.__version__,
            "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    }
    FINAL_RESULTS.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    print("OVERALL", result["overall"], json.dumps(result["acceptance_summary"], sort_keys=True), flush=True)
    print("RESULT", FINAL_RESULTS.relative_to(ROOT),
          "SHA256", sha(FINAL_RESULTS.read_bytes()), flush=True)


if __name__ == "__main__":
    main()

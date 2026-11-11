"""Authorized 11-case REQ-SCR-01 qualification for AX309-RDSP-001.

The source definition is measured at the single target range cell k=40 over
33 pulses, before noise and Q1.15. Range [40,56) is diagnostic output support
only. Fixed stages are checked against the separate C03 Fraction oracle;
power/CFAR/grouping are checked against C03 and the independent C05 union-find.
"""
import sys, json, math, hashlib, platform, datetime
from pathlib import Path
from fractions import Fraction as Q
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engineering/s04_numeric"))
from s03_reference import model as S03
import s04_c03_independent_oracle_v1 as OR
import s04_c04_selected_C_stage_capture_v1 as DUT
import s04_c05_native_integer_v1 as NAT
import s04_c05_integrated_qualification_v1 as C05

G = 1
SHIFTS = (0, 1, 0, 1, 1)
ALPHA = 7.476912055027923
SEED = 20261112
TARGET_RANGE = 40
TARGET_DOPPLER_BIN = 4
TARGET_AMPLITUDE = 0.18
TARGET_SNR_DB = 20.0
PHASES = (0, 90, 180, 270)
SCRS = (10.0, -10.0)
OUTPUT_SUPPORT = (40, 56)  # diagnostic range bins [40, 56), not SCR support
SCR_MEASUREMENT_CELL = 40  # one range cell, power averaged across 33 pulses

def sha(b):
    return hashlib.sha256(b).hexdigest()

def max_rms(a, b):
    d = np.abs(np.asarray(a) - np.asarray(b))
    return {"MAX": float(np.max(d)), "RMS": float(np.sqrt(np.mean(d*d))), "count": int(d.size)}

def pack_source(src):
    iq = []
    input_sat = []
    for p in range(src.shape[0]):
        row = []
        for r in range(src.shape[1]):
            pair = []
            for ci, val in enumerate((src[p, r].real, src[p, r].imag)):
                q, sat = OR.input_pack(Q.from_float(float(val)), G)
                pair.append(q)
                if sat:
                    input_sat.append({"pulse": p, "range": r, "component": "IQ"[ci], "code": q})
            row.append(tuple(pair))
        iq.append(row)
    return iq, input_sat

def compare_integer_stages(iq, captured):
    taps = OR.independent_mf_taps()
    tw = OR.independent_twiddles()
    mf = [[OR.mf_at(iq, p, r, taps) for r in range(128)] for p in range(33)]
    mti = [[OR.mti(mf[p][r], mf[p+1][r]) for r in range(128)] for p in range(32)]
    fft = [[] for _ in range(5)]
    for r in range(128):
        stages = OR.fft32_oracle([mti[p][r] for p in range(32)], tw)
        for j in range(5):
            fft[j].append(stages[j])
    refs = [("MF", mf, captured["mf"]), ("MTI", mti, captured["mti"])]
    refs += [(f"FFT{j+1}", fft[j], captured["fft_stages_range_major"][j]) for j in range(5)]
    summary = {}
    for name, expected, actual in refs:
        e = np.asarray(expected, dtype=np.int64)
        a = np.asarray(actual, dtype=np.int64)
        mismatches = np.argwhere(e != a)
        summary[name] = {
            "mismatch_count": int(len(mismatches)),
            "integer_component_count": int(e.size),
            "first_mismatch_index": mismatches[0].tolist() if len(mismatches) else None
        }
        if len(mismatches):
            raise AssertionError(f"{name} independent C03 oracle mismatch at {mismatches[0].tolist()}")
    return summary, mf, mti, fft

def independent_map_check(rd_codes):
    mapped = NAT.complete_map(rd_codes)
    # C03 Fraction oracle: every stored power and each valid CUT decision.
    for r in range(128):
        for b in range(32):
            expected, saturated = OR.oracle_power(*rd_codes[r][b])
            if saturated or expected != mapped["power"][r][b]:
                raise AssertionError(f"power oracle mismatch at {(r,b)}")
    for rec in mapped["cut_records"]:
        if rec["alarm"] != OR.oracle_cfar(rec["Pcut"], rec["SUM40"]):
            raise AssertionError(f"CFAR Fraction oracle mismatch at {(rec['range'],rec['doppler_bin'])}")
    union = C05.independent_components(mapped["mask"], mapped["power"])
    native = mapped["clusters"]
    if len(union) != len(native):
        raise AssertionError("independent union-find component count mismatch")
    keys = ("range_bin", "doppler_bin", "cluster_cells", "power_stored_integer", "tie_flag", "max_equal_power_cells")
    for i, (a, b) in enumerate(zip(union, native)):
        for k in keys:
            if a[k] != b[k]:
                raise AssertionError(f"independent grouping mismatch cluster={i} field={k}")
    return mapped

def run_case(case_id, kind, scr_db=None, phase_deg=None):
    target = S03.Target(TARGET_RANGE, float(S03.bin_velocity(TARGET_DOPPLER_BIN)), TARGET_AMPLITUDE, 0.0)
    clutter = None
    clutter_amp = None
    if scr_db is not None:
        clutter_amp = TARGET_AMPLITUDE / math.sqrt(10.0 ** (scr_db / 10.0))
        # Define the clutter phasor relative to the target's first sample at
        # k=40, pulse 0; the moving target's phase then evolves at Doppler +4.
        phi0 = float(np.angle(S03.chirp()[0])) + math.radians(float(phase_deg or 0.0))
        clutter = np.full(128, clutter_amp * np.exp(1j * phi0), dtype=np.complex128)
    elif kind.startswith("clutter_only"):
        raise AssertionError("clutter-only cases require explicit SCR")
    if kind == "target_no_clutter":
        src = S03.generate_cpi([target], snr_db=TARGET_SNR_DB, seed=SEED)
    elif kind == "target_plus_clutter":
        src = S03.generate_cpi([target], snr_db=TARGET_SNR_DB, seed=SEED, clutter=clutter)
    elif kind == "clutter_only":
        src = S03.generate_cpi([], clutter=clutter)
    else:
        raise ValueError(kind)

    # Independently reconstruct the source components for SCR metrology.
    target_component = S03.generate_cpi([target], snr_db=None) if kind != "clutter_only" else np.zeros((33,128), dtype=np.complex128)
    clutter_component = np.zeros((33,128), dtype=np.complex128) if clutter is None else np.broadcast_to(clutter, (33,128)).copy()
    p_target = float(np.mean(np.abs(target_component[:, SCR_MEASUREMENT_CELL])**2))
    p_clutter = float(np.mean(np.abs(clutter_component[:, SCR_MEASUREMENT_CELL])**2))
    measured_scr = None if scr_db is None or kind == "clutter_only" else 10.0 * math.log10(p_target / p_clutter)

    iq, input_sat = pack_source(src)
    tel = DUT.Telemetry()
    fixed = DUT.run_one(src, iq, tel, "C_hypothetical", SHIFTS, G, capture_stages=True)
    cap = fixed["captured"]
    stage_oracle, oracle_mf, oracle_mti, oracle_fft = compare_integer_stages(iq, cap)
    rd_codes = cap["rd"]
    mapped = independent_map_check(rd_codes)

    float_out = S03.pipeline(src, alpha=ALPHA)
    float_mf = S03.pulse_compress(src)
    float_mti = S03.mti(float_mf)
    float_fft = S03.doppler(float_mti)  # compare in original-amplitude units; Fixed is reconstructed with g*8/32768

    fixed_mf = np.asarray(cap["mf"], dtype=np.float64)
    fixed_mf = (fixed_mf[:,:,0] + 1j*fixed_mf[:,:,1]) * (G / 32768.0)
    fixed_mti = np.asarray(cap["mti"], dtype=np.float64)
    fixed_mti = (fixed_mti[:,:,0] + 1j*fixed_mti[:,:,1]) * (G / 32768.0)
    fixed_fft_iq = np.asarray(rd_codes, dtype=np.float64)
    fixed_fft = (fixed_fft_iq[:,:,0] + 1j*fixed_fft_iq[:,:,1]) * (G*8 / 32768.0)

    float_mask = np.asarray(float_out["cfar"], dtype=bool)
    fixed_mask = np.asarray(mapped["mask"], dtype=bool)
    valid = np.zeros((128,32), dtype=bool)
    valid[3:110,3:29] = True
    changed_cuts = int(np.logical_xor(float_mask, fixed_mask)[valid].sum())
    float_target = any(t["range_bin"] == TARGET_RANGE and t["doppler_bin"] == TARGET_DOPPLER_BIN for t in float_out["targets"])
    fixed_target = any(t["range_bin"] == TARGET_RANGE and t["doppler_bin"] == TARGET_DOPPLER_BIN for t in mapped["clusters"])
    float_peak_coordinates = [(t["range_bin"], t["doppler_bin"]) for t in float_out["targets"]]
    fixed_peak_coordinates = [(t["range_bin"], t["doppler_bin"]) for t in mapped["clusters"]]
    cluster_peak_coordinates_identical = float_peak_coordinates == fixed_peak_coordinates
    if not cluster_peak_coordinates_identical:
        raise AssertionError(f"Float/Fixed cluster peak-coordinate mismatch in {case_id}")

    if kind == "clutter_only":
        mti_exact_zero = bool(np.count_nonzero(cap["mti"]) == 0)
        float_mti_exact_zero = bool(np.count_nonzero(float_mti) == 0)
        if not mti_exact_zero or not float_mti_exact_zero:
            raise AssertionError("stationary clutter-only MTI output is not exactly zero")
        if mapped["clusters"] or float_out["targets"]:
            raise AssertionError("clutter-only zero MTI unexpectedly produced detections")
    else:
        mti_exact_zero = None
        float_mti_exact_zero = None
        if not float_target:
            raise AssertionError(f"Float reference failed target association in {case_id}")
        if not fixed_target:
            raise AssertionError(f"Fixed-Point target association failed in {case_id}")

    overflow = fixed["overflow"]
    power_overflow = len(mapped["power_events"])
    if input_sat or overflow["total"] or power_overflow:
        raise AssertionError(f"clipping/overflow in {case_id}: input={len(input_sat)} internal={overflow['total']} power={power_overflow}")

    return {
        "case_id": case_id, "kind": kind, "SCR_requested_dB": scr_db, "SCR_measured_dB": measured_scr,
        "SCR_phase_offset_deg_at_target_cell_pulse0": phase_deg,
        "SCR_measurement": {
            "target_range_cell": SCR_MEASUREMENT_CELL, "pulse_indices": [0,32],
            "target_power_mean_before_noise_quantization": p_target,
            "clutter_power_mean_before_noise_quantization": p_clutter,
            "output_diagnostic_range_support": list(OUTPUT_SUPPORT),
            "note": "SCR uses only the single target range cell k=40, averaged over 33 pulses; [40,56) is output diagnostics only."
        },
        "source": {
            "shape": list(src.shape), "dtype": str(src.dtype), "seed_for_target_noise": SEED if kind != "clutter_only" else None,
            "gain_g": G, "input_saturation_count": len(input_sat),
            "input_sha256_float_c128_little_endian": sha(np.asarray(src, dtype="<c16").tobytes())
        },
        "fixed": {
            "internal_overflow_count": overflow["total"], "internal_overflow_by_site": overflow["counts"],
            "power_overflow_count": power_overflow, "fixed_target_associated": fixed_target,
            "cfar_alarm_count": sum(sum(bool(v) for v in row) for row in mapped["mask"]),
            "cluster_count": len(mapped["clusters"]), "clusters": mapped["clusters"],
            "changed_CUT_count_vs_Float": changed_cuts,
            "Float_Fixed_cluster_peak_coordinates_identical": cluster_peak_coordinates_identical,
            "Float_cluster_peak_coordinates": float_peak_coordinates,
            "Fixed_cluster_peak_coordinates": fixed_peak_coordinates,
            "bittrue_independent_C03_oracle": stage_oracle,
            "C03_power_Cfar_oracle": "PASS_ALL_4096_POWER_AND_2782_CUTS",
            "C05_independent_union_find_grouping": "PASS"
        },
        "float": {
            "target_associated": float_target, "cfar_alarm_count": int(np.count_nonzero(float_mask)),
            "cluster_count": len(float_out["targets"]), "targets": float_out["targets"]
        },
        "Float_vs_Fixed_original_amplitude_error": {
            "MF": max_rms(float_mf, fixed_mf), "MTI": max_rms(float_mti, fixed_mti),
            "FFT_final_original_amplitude": max_rms(float_fft, fixed_fft),
            "power_final_original_units": max_rms(np.abs(float_fft)**2, np.asarray(mapped["power"], dtype=np.float64) * (G*8/32768.0)**2)
        },
        "clutter_only_MTI_exact_zero": mti_exact_zero,
        "float_clutter_only_MTI_exact_zero": float_mti_exact_zero,
        "status": "PASS"
    }, src, fixed_mf, fixed_mti, fixed_fft, float_mf, float_mti, float_fft

def run():
    cases = [("SCR00_TARGET_NO_CLUTTER", "target_no_clutter", None, None)]
    for scr in SCRS:
        for phase in PHASES:
            cases.append((f"SCR_{'PLUS10' if scr>0 else 'MINUS10'}_PHASE_{phase:03d}", "target_plus_clutter", scr, phase))
    for scr in SCRS:
        amp = TARGET_AMPLITUDE / math.sqrt(10.0 ** (scr / 10.0))
        phi0 = float(np.angle(S03.chirp()[0]))
        cl = np.full(128, amp * np.exp(1j*phi0), dtype=np.complex128)
        cases.append((f"CLUTTER_ONLY_{'PLUS10' if scr>0 else 'MINUS10'}", "clutter_only", scr, 0))
    assert len(cases) == 11
    results = {
        "project": "AX309-RDSP-001", "requirement": "REQ-SCR-01",
        "decision_basis": "Engineer-system approval 2026-11-12; SCR measured at target range cell 40 over 33 pulses before noise and Q1.15; range [40,56) is diagnostic output support only.",
        "engineer_approval": {"title":"Engineer system approval","date":"2026-11-12","authority":"Project system engineer","approved_parameters":{"SCR_conditions_dB":[10,-10,"no_clutter"],"generator_tolerance_dB":0.1,"clutter_model":"stationary coherent complex clutter","relative_phase_offsets_deg":[0,90,180,270],"isolated_stationary_clutter_MTI_output":"exactly_zero","SCR_measurement":"single target range cell k=40; mean power over 33 pulses; before noise and Q1.15","output_monitoring_range_cells":[40,55]},"execution_authorization":"Explicitly granted in the engineer instruction on 2026-11-12"},
        "fixed_reconstruction_note": "FFT Fixed-Point is reconstructed as g*8*code/32768 and compared against the unscaled S03 DFT output; archived Float and Fixed FFT arrays are both in original-amplitude units.",
        "architecture": "C", "fft_shifts": list(SHIFTS), "gain_g": G,
        "source_model": "s03_reference.model.generate_cpi; no Float model changes",
        "seed": SEED, "seed_reused_across_target_cases_for_paired_noise": True,
        "cases": [], "overall": "RUNNING"
    }
    input_archive = {}
    output_archive = {}
    for case_id, kind, scr, phase in cases:
        row, src, fixed_mf, fixed_mti, fixed_fft, float_mf, float_mti, float_fft = run_case(case_id, kind, scr, phase)
        results["cases"].append(row)
        input_archive[f"float_iq_{case_id}"] = np.asarray(src, dtype=np.complex128)
        q15_iq, q15_saturation = pack_source(src)
        if q15_saturation:
            raise AssertionError(f"Q1.15 input saturation during archive for {case_id}")
        input_archive[f"q15_iq_{case_id}"] = np.asarray(q15_iq, dtype=np.int16)
        output_archive[f"float_mf_{case_id}"] = np.asarray(float_mf, dtype=np.complex128)
        output_archive[f"float_mti_{case_id}"] = np.asarray(float_mti, dtype=np.complex128)
        output_archive[f"float_fft_original_amplitude_{case_id}"] = np.asarray(float_fft, dtype=np.complex128)
        output_archive[f"fixed_mf_{case_id}"] = np.asarray(fixed_mf, dtype=np.complex128)
        output_archive[f"fixed_mti_{case_id}"] = np.asarray(fixed_mti, dtype=np.complex128)
        output_archive[f"fixed_fft_original_amplitude_{case_id}"] = np.asarray(fixed_fft, dtype=np.complex128)
        print("PASS", case_id, "SCR", row["SCR_measured_dB"], "clusters", row["fixed"]["cluster_count"],
              "changedCUT", row["fixed"]["changed_CUT_count_vs_Float"], flush=True)
    results["overall"] = "PASS_11_OF_11"
    results["acceptance_summary"] = {
        "all_11_scenarios_executed": True,
        "all_11_Float_Fixed_cluster_peak_coordinates_identical": all(x["fixed"]["Float_Fixed_cluster_peak_coordinates_identical"] for x in results["cases"]),
        "all_11_input_sets_no_saturation": all(x["source"]["input_saturation_count"] == 0 for x in results["cases"]),
        "all_11_fixed_no_internal_or_power_overflow": all(x["fixed"]["internal_overflow_count"] == 0 and x["fixed"]["power_overflow_count"] == 0 for x in results["cases"]),
        "all_9_target_scenarios_associated_in_float_and_fixed": all(x["fixed"]["fixed_target_associated"] and x["float"]["target_associated"] for x in results["cases"] if x["kind"] != "clutter_only"),
        "both_clutter_only_scenarios_exact_zero_after_MTI_float_and_fixed": all(x["clutter_only_MTI_exact_zero"] and x["float_clutter_only_MTI_exact_zero"] for x in results["cases"] if x["kind"] == "clutter_only"),
        "all_fixed_arithmetic_stages_match_independent_C03_oracle": all(all(v["mismatch_count"] == 0 for v in x["fixed"]["bittrue_independent_C03_oracle"].values()) for x in results["cases"]),
        "all_fixed_power_cfar_match_independent_C03_oracle": all(x["fixed"]["C03_power_Cfar_oracle"].startswith("PASS") for x in results["cases"]),
        "all_fixed_grouping_matches_independent_C05_union_find": all(x["fixed"]["C05_independent_union_find_grouping"] == "PASS" for x in results["cases"])
    }
    if not all(results["acceptance_summary"].values()):
        raise AssertionError("one or more REQ-SCR-01 acceptance checks failed")
    evidence_dir = ROOT / "engineering/s04_numeric/req_scr01_v1"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    inputs_path = evidence_dir / "REQ-SCR-01-INPUTS-v1.0.npz"
    outputs_path = evidence_dir / "REQ-SCR-01-OUTPUTS-v1.0.npz"
    np.savez_compressed(inputs_path, **input_archive)
    np.savez_compressed(outputs_path, **output_archive)
    results["archives"] = {
        "inputs": {"path": str(inputs_path.relative_to(ROOT)), "sha256": sha(inputs_path.read_bytes()), "arrays": len(input_archive)},
        "outputs": {"path": str(outputs_path.relative_to(ROOT)), "sha256": sha(outputs_path.read_bytes()), "arrays": len(output_archive)}
    }
    results["environment"] = {"python": platform.python_version(), "numpy": np.__version__, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    out = evidence_dir / "REQ-SCR-01-RESULTS-v1.0.json"
    out.write_text(json.dumps(results, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    results["result_sha256"] = sha(out.read_bytes())
    print("OVERALL", results["overall"], json.dumps(results["acceptance_summary"], sort_keys=True), flush=True)
    print("RESULT", out.relative_to(ROOT), "SHA256", results["result_sha256"], flush=True)
if __name__ == "__main__":
    run()

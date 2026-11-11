"""Post-run evidence assembly for REQ-RNG-03.

The Float and Fixed signal chains have already completed. This utility reads
only their archived arrays, reconstructs Fixed target records from archived
Fixed FFT integer codes, and assembles the final report. It does not regenerate
IQ, rerun MF/MTI/FFT, or rerun C03/C05 oracle qualification.
"""
import sys, json, hashlib, platform, datetime
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engineering/s04_numeric"))
from s03_reference import model as S03
import s04_c05_native_integer_v1 as NAT
import s04_c08_req_rng03_float_first_v1 as RNG
import s04_c08_req_scr01_qualification_v1 as SCR

EVIDENCE = ROOT / "engineering/s04_numeric/req_rng03_v1"
INPUTS = EVIDENCE / "REQ-RNG-03-INPUTS-v1.0.npz"
FLOAT_OUTPUTS = EVIDENCE / "REQ-RNG-03-FLOAT-OUTPUTS-v1.0.npz"
FLOAT_RESULTS = EVIDENCE / "REQ-RNG-03-FLOAT-RESULTS-v1.0.json"
Q15_INPUTS = EVIDENCE / "REQ-RNG-03-Q15-INPUTS-v1.0.npz"
FIXED_OUTPUTS = EVIDENCE / "REQ-RNG-03-FIXED-OUTPUTS-v1.0.npz"
FINAL = EVIDENCE / "REQ-RNG-03-RESULTS-v1.0.json"
G = 1


def sha(b):
    return hashlib.sha256(b).hexdigest()


def max_rms(a, b):
    d = np.abs(np.asarray(a) - np.asarray(b))
    return {"MAX": float(np.max(d)), "RMS": float(np.sqrt(np.mean(d*d))), "count": int(d.size)}


def main():
    for p in (INPUTS, FLOAT_OUTPUTS, FLOAT_RESULTS, Q15_INPUTS, FIXED_OUTPUTS):
        if not p.exists():
            raise FileNotFoundError(p)
    fr = json.loads(FLOAT_RESULTS.read_text())
    with np.load(INPUTS, allow_pickle=False) as z: inputs = {k:z[k] for k in z.files}
    with np.load(FLOAT_OUTPUTS, allow_pickle=False) as z: floats = {k:z[k] for k in z.files}
    with np.load(Q15_INPUTS, allow_pickle=False) as z: q15 = {k:z[k] for k in z.files}
    with np.load(FIXED_OUTPUTS, allow_pickle=False) as z: fixed = {k:z[k] for k in z.files}
    if not (len(inputs)==12 and len(floats)==60 and len(q15)==12 and len(fixed)==60):
        raise AssertionError("Archive inventory does not match the completed 12-case execution.")

    # Status lines captured from the completed Fixed process output. PASS was
    # emitted only after both associations, all C03/C05 oracles, zero input
    # saturation and zero internal/power overflow for that mandatory case.
    fixed_log_status = {
        "RNG_D3_PHASE_000":"CHARACTERIZATION_ONLY",
        "RNG_D3_PHASE_090":"CHARACTERIZATION_ONLY",
        "RNG_D3_PHASE_180":"CHARACTERIZATION_ONLY",
        "RNG_D3_PHASE_270":"CHARACTERIZATION_ONLY",
        "RNG_D4_PHASE_000":"FAIL",
        "RNG_D4_PHASE_090":"FAIL",
        "RNG_D4_PHASE_180":"PASS",
        "RNG_D4_PHASE_270":"FAIL",
        "RNG_D5_PHASE_000":"FAIL",
        "RNG_D5_PHASE_090":"PASS",
        "RNG_D5_PHASE_180":"PASS",
        "RNG_D5_PHASE_270":"PASS"
    }
    float_by_id = {x["case_id"]:x for x in fr["cases"]}
    rows = []
    q15_sat_total = 0
    all_fft_roundtrip_exact = True
    all_cfar_roundtrip_exact = True
    all_power_roundtrip_exact = True

    for delta in RNG.SEPARATIONS:
        for phase in RNG.PHASES_DEG:
            cid = RNG.case_id(delta, phase)
            src = inputs[f"float_iq_{cid}"]
            source_hash = sha(np.asarray(src, dtype="<c16").tobytes())
            if source_hash != float_by_id[cid]["source"]["sha256_float_iq_little_endian"]:
                raise AssertionError(f"Source hash mismatch: {cid}")

            packed, sat = SCR.pack_source(src)
            q15_arr = np.asarray(packed, dtype=np.int16)
            if not np.array_equal(q15_arr, q15[f"q15_iq_{cid}"]):
                raise AssertionError(f"Q1.15 input archive differs from exact Float source: {cid}")
            q15_sat_total += len(sat)

            # Reconstruct final integer FFT words from archived original-amplitude
            # Fixed FFT samples. No MF/MTI/FFT operation is rerun.
            fixed_fft = fixed[f"fixed_fft_original_amplitude_{cid}"]
            scaled = fixed_fft * (32768.0 / (G * 8))
            rd = np.rint(np.stack((scaled.real, scaled.imag), axis=-1)).astype(np.int64)
            roundtrip = (rd[:, :, 0] + 1j*rd[:, :, 1]) * (G*8/32768.0)
            fft_exact = bool(np.array_equal(roundtrip, fixed_fft))
            all_fft_roundtrip_exact &= fft_exact
            rd_codes = [[(int(rd[r,b,0]), int(rd[r,b,1])) for b in range(32)] for r in range(128)]
            mapped = NAT.complete_map(rd_codes)

            saved_mask = np.asarray(fixed[f"fixed_cfar_{cid}"], dtype=bool)
            map_mask = np.asarray(mapped["mask"], dtype=bool)
            cfar_exact = bool(np.array_equal(saved_mask, map_mask))
            all_cfar_roundtrip_exact &= cfar_exact

            saved_power = np.asarray(fixed[f"fixed_power_original_units_{cid}"], dtype=np.float64)
            map_power = np.asarray(mapped["power"], dtype=np.float64) * (G*8/32768.0)**2
            power_exact = bool(np.array_equal(saved_power, map_power))
            all_power_roundtrip_exact &= power_exact

            fcase = float_by_id[cid]
            float_clusters = fcase["float"]["clusters"]
            fixed_clusters = mapped["clusters"]
            truth = [RNG.TARGET_RANGE_1, RNG.TARGET_RANGE_1 + delta]
            fixed_assoc = RNG.strict_pair_association(fixed_clusters, truth)
            float_assoc = fcase["float"]["association"]
            float_pass = float_assoc["matched_count"] == 2 and float_assoc["distinct_detection_records"]
            fixed_pass = fixed_assoc["matched_count"] == 2 and fixed_assoc["distinct_detection_records"]
            mandatory = delta in RNG.REQUIRED_SEPARATIONS
            execution_status = fixed_log_status[cid]

            float_mask = np.asarray(floats[f"float_cfar_{cid}"], dtype=bool)
            valid = np.zeros((128,32), dtype=bool)
            valid[3:110,3:29] = True
            changed_cuts = int(np.logical_xor(float_mask, saved_mask)[valid].sum())

            float_mf = floats[f"float_mf_{cid}"]
            float_mti = floats[f"float_mti_{cid}"]
            float_fft = floats[f"float_doppler_{cid}"]
            float_power = floats[f"float_power_{cid}"]
            fixed_mf = fixed[f"fixed_mf_{cid}"]
            fixed_mti = fixed[f"fixed_mti_{cid}"]
            fixed_power = saved_power

            # Overflow detail was evaluated by the original fixed run. It is not
            # present in the archived NPZ; do not invent counts. For cases whose
            # runner printed PASS, its explicit PASS predicate included zero
            # input/internal/power overflow.
            overflow_evidence = (
                {"status":"ZERO_BY_ORIGINAL_RUNNER_PASS_PREDICATE",
                 "internal_count":0,"power_count":0,"input_saturation_count":0}
                if execution_status == "PASS" else
                {"status":"NOT_PERSISTED_FOR_FAILED_OR_CHARACTERIZATION_CASE",
                 "internal_count":None,"power_count":len(mapped["power_events"]),
                 "input_saturation_count":len(sat)}
            )

            rows.append({
                "case_id":cid, "delta_range_bins":delta,
                "separation_m_exact":float(delta*S03.C/(2*S03.FS)),
                "relative_phase_deg":phase,
                "source_sha256":source_hash,
                "same_archived_float_iq_used_for_fixed":True,
                "float":{
                    "status":fcase["float"]["status"],
                    "cluster_count":len(float_clusters),
                    "clusters":float_clusters,
                    "association":float_assoc
                },
                "fixed":{
                    "status":execution_status,
                    "cluster_count":len(fixed_clusters),
                    "clusters":fixed_clusters,
                    "association":fixed_assoc,
                    "input_q15_saturation_count":len(sat),
                    "power_overflow_count_reconstructed":len(mapped["power_events"]),
                    "overflow_evidence":overflow_evidence,
                    "independent_oracle_execution_log":"PASS_C03_STAGE_C03_POWER_CFAR_C05_GROUPING",
                    "archive_roundtrip":{
                        "fixed_fft_integer_reconstruction_exact":fft_exact,
                        "fixed_cfar_mask_reconstruction_exact":cfar_exact,
                        "fixed_power_reconstruction_exact":power_exact
                    }
                },
                "Float_vs_Fixed":{
                    "changed_valid_CUT_count":changed_cuts,
                    "cluster_count_delta_fixed_minus_float":len(fixed_clusters)-len(float_clusters),
                    "Float_peak_coordinates":[[x["range_bin"],x["doppler_bin"]] for x in float_clusters],
                    "Fixed_peak_coordinates":[[x["range_bin"],x["doppler_bin"]] for x in fixed_clusters],
                    "MF_original_amplitude":max_rms(float_mf,fixed_mf),
                    "MTI_original_amplitude":max_rms(float_mti,fixed_mti),
                    "FFT_original_amplitude":max_rms(float_fft,fixed_fft),
                    "power_original_units":max_rms(float_power,fixed_power)
                },
                "mandatory_acceptance_case":mandatory,
                "mandatory_case_pass":(float_pass and fixed_pass and execution_status=="PASS") if mandatory else None
            })

    mandatory_rows=[x for x in rows if x["mandatory_acceptance_case"]]
    float_pass_count=sum(x["float"]["association"]["matched_count"]==2 and
                         x["float"]["association"]["distinct_detection_records"] for x in mandatory_rows)
    fixed_pass_count=sum(x["fixed"]["association"]["matched_count"]==2 and
                         x["fixed"]["association"]["distinct_detection_records"] for x in mandatory_rows)
    both_pass_count=sum(bool(x["mandatory_case_pass"]) for x in mandatory_rows)
    oracle_pass_all=True  # all 12 per-case outputs explicitly printed "oracle PASS" by the completed run
    result={
        "project":"AX309-RDSP-001","requirement":"REQ-RNG-03",
        "decision_basis":"Engineer-system approval 2026-11-12. Mandatory separability at 4 and 5 samples; 3-sample cases characterization only.",
        "execution_order":[
            "Float processed all 12 scenarios first; exact complex128 CPI inputs and Float outputs archived.",
            "Fixed-Point processed all 12 scenarios second by reading those exact archived complex128 CPI inputs.",
            "Post-run report assembly reconstructed final detection records from archived Fixed FFT integer words; no Float/Fixed MF/MTI/FFT rerun."
        ],
        "engineer_approval":fr["engineer_approval"],
        "architecture":"C","fft_shifts":[0,1,0,1,1],"gain_g":G,"alpha":RNG.ALPHA,
        "input_archive":{"path":str(INPUTS.relative_to(ROOT)),"sha256":sha(INPUTS.read_bytes()),"arrays":len(inputs)},
        "float_output_archive":{"path":str(FLOAT_OUTPUTS.relative_to(ROOT)),"sha256":sha(FLOAT_OUTPUTS.read_bytes()),"arrays":len(floats)},
        "q15_input_archive":{"path":str(Q15_INPUTS.relative_to(ROOT)),"sha256":sha(Q15_INPUTS.read_bytes()),"arrays":len(q15)},
        "fixed_output_archive":{"path":str(FIXED_OUTPUTS.relative_to(ROOT)),"sha256":sha(FIXED_OUTPUTS.read_bytes()),"arrays":len(fixed)},
        "cases":rows,
        "acceptance_summary":{
            "float_mandatory_pass_count":float_pass_count,
            "fixed_mandatory_pass_count":fixed_pass_count,
            "combined_float_fixed_mandatory_pass_count":both_pass_count,
            "mandatory_case_count":8,
            "float_8_of_8_pass":float_pass_count==8,
            "fixed_8_of_8_pass":fixed_pass_count==8,
            "combined_8_of_8_pass":both_pass_count==8,
            "all_12_fixed_C03_C05_oracles_pass":oracle_pass_all,
            "all_12_q15_inputs_match_archived_float_sources":q15_sat_total==0,
            "all_12_fixed_fft_archive_reconstruction_exact":all_fft_roundtrip_exact,
            "all_12_fixed_power_archive_reconstruction_exact":all_power_roundtrip_exact,
            "all_12_fixed_cfar_archive_reconstruction_exact":all_cfar_roundtrip_exact,
            "three_sample_cases_characterization_only":True
        },
        "overall":"PASS" if both_pass_count==8 and oracle_pass_all and q15_sat_total==0 else "FAIL",
        "execution_log_status":"ALL_12_FIXED_COMPLETED; REPORT_ASSEMBLY_FAILED_AFTER_ARCHIVES_WRITTEN; FINAL_RESULT_RECOVERED_FROM_ARCHIVES",
        "report_recovery_note":"The first Fixed runner completed all 12 Fixed cases and printed per-case association counts and C03/C05 oracle PASS. It then encountered a Python report-assembly KeyError after both NPZ archives had been written. This recovery utility only reconstructs final detection records and metrics from those archived arrays; it does not rerun the signal chain or repeat C03/C05 oracle tests.",
        "unpersisted_telemetry_note":"The first runner did not persist per-case internal overflow telemetry in its NPZ. For the four mandatory cases printed PASS, the runner's PASS predicate itself required zero input saturation, internal overflow and power overflow. Failed cases already fail the approved association rule; no internal-overflow count is inferred for those cases.",
        "environment":{"python":platform.python_version(),"numpy":np.__version__,
                       "utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
    }
    FINAL.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("OVERALL",result["overall"],json.dumps(result["acceptance_summary"],sort_keys=True),flush=True)
    print("RESULT",FINAL.relative_to(ROOT),"SHA256",sha(FINAL.read_bytes()),flush=True)


if __name__=="__main__":
    main()

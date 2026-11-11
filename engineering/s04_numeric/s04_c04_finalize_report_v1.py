"""One evidence-backed final C04 report; no additional simulation."""
from pathlib import Path
import json,hashlib,datetime,platform,subprocess
R=Path(__file__).resolve().parents[2]
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
P=json.loads((R/'engineering/s04_numeric/S04-C04-integrated-fullchain-v1.0.json').read_text())
G=json.loads((R/'engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json').read_text())
u=(R/'engineering/S04-C04-INTEGRATED-v1.0-INDEPENDENT-TESTS.log').read_text()
assert 'Ran 18 tests' in u and '\nOK\n' in u
assert len(P['vectors'])==18 and len(G['records'])==18
assert all(all(z['mismatch_count']==0 for z in item['bittrue_stage_agreement'].values()) for item in P['vectors'])
assert all(item['internal_overflow_count']==0 for item in P['vectors'])
st=json.loads((R/'engineering/S04-progress.json').read_text())
pr=json.loads((R/'project.yaml').read_text())
assert st['completed_count']==3 and not st['criteria'][3]['completed']
assert st['stage_percent']==37.5 and pr['progress']['overall_percent']==28.125
ob='engineering/S04-C02-SELECTED-C-OPEN-OBLIGATIONS-v1.0.json'
assert sha(R/ob)=='ba845f306186beba2d1ae085ae417ec63a9b083044241115e3751f6857c3b7ac'
original='engineering/s04_numeric/s04_c02_integer_bittrue_v05.py'
assert not subprocess.check_output(['git','diff','--',original,ob,'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json'],cwd=R,text=True).strip()
report=R/'engineering/S04-C04-INTEGRATED-BITTRUE-MF-MTI-DOPPLER-QUALIFICATION-v1.0.md'
lines=['# AX309-RDSP-001 | S04-C04 Integrated Bit-True MF/MTI/Doppler Qualification v1.0','',
 '**EXECUTED; READY FOR INDEPENDENT SIGN-OFF — NOT C04 PASS.** The approved C01 bounded input scaling and C02 selected architecture C with five FFT shifts [0,1,0,1,1] were not altered. C03 has an independent engineer PASS. C04 remains OPEN pending its own independent engineer signature.',
 '',
 '## Exact execution and expected-value independence','',
 'One executable integrated C04 package evaluates **18 deterministic complete 33×128 input records**: nine physical/rational stimulus types at **g=1 and g=5**, including zero, DC stationary, pulse-alternating DC, extrema of signed Q16.15, positive/negative half-LSB, signed alternating phase, a noiseless on-bin target at Doppler bin 5, a noiseless off-bin target at 5.37 bins, and intentional input overrange. These are **test vectors**, not statistical noise-only CPI samples; g5 is used only as a deterministic arithmetic scaling test and does not expand approved C01 statistical populations.',
 '',
 'Independent expected outputs were computed with the C03 standalone **Integer/Fraction Oracle**, not the selected-C implementation arithmetic helpers. Full integer MF outputs (33×128), MTI outputs (32×128) and *each* of five FFT stages (128×32 complex) were checked against the v0.5 exact-integer engine using a derived stage-capture adapter. In all **18×(8448+8192+5×8192)=1,036,800** individual stored real/imag stage comparisons, **zero bit-true mismatch** occurred. Source digest, exact golden MF/MTI point samples and FFT-stage bins in every input profile are separately frozen in §engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json§, derived only from the independent Oracle.',
 '',
 'Reference Float samples are deterministic S03 LFM echoes with a known fixed amplitude (0.18) and an explicitly chosen deterministic slow-time Doppler; source generation does not use a statistical CPI or accepted seeds. Comparison to frozen S03 pulse compression, MTI and unnormalized forward FFT is performed **in original physical Float amplitude units**, reconstructing each fixed stage with cumulative g×2^(sum stage shifts). Natural (not fftshifted) Doppler bins are retained. This work validates the selected stage output order and scaling, not target detection probability.',
 '',
 '## Complete self-checking results','',
 '| Test category | Independent checks | Result |','|---|---|---|',
 '| Full MF16, MTI two-pulse and five FFT stages | Exact 1,036,800 component comparisons from 18 × 7 stage arrays | **PASS; zero integer mismatch** |',
 '| Zero/constant DC | Zero chain; exact stationary DC cancellation after MTI, retained zero FFT | **PASS** |',
 '| On-bin / off-bin | Float on-bin target k=5 and off-bin k=5.37; fixed reconstructed peaks at natural FFT index 5; off-bin leakage independently verified | **PASS** |',
 '| Signed and half-LSB | Q16.15 signed endpoints, RNE negative ties, alternating sequences | **PASS** |',
 '| Saturation | Two overrange vectors, **8448 input component clips each** and no internal processing overflow; clipped vectors retained | **PASS** |',
 '| Float/Fixed numerical effects | For each stage, separate source-input quantization and fixed coefficient/twiddle/rounding effects; observed MAX/RMS and triangle consistency | **PASS** |',
 '| Reproduction and state | Exact independent golden outputs/digests, frozen C, seed and RTL restrictions, unchanged C04 state/progress | **PASS** |',
 '','**New C04 independent self-checking unit tests: 18/18 PASS, 0 FAIL.** Previous C03/C02 tests remain historical and do not constitute this C04 result.',
 '',
 '## Numeric error: implementation versus quantization (not the same thing)','',
 'For all 18 vectors every stored integer output of all seven processing stages matches the independent C03 Oracle **exactly**, so tested **integer implementation mismatch = 0**. Deviations from the ideal Float S03 reference can be nonzero due to quantized input, MF coefficients, FFT twiddles, selected RNE/shifts and deliberate saturation. This is *not* evidence of an incorrect bit-true implementation.',
 '',
 'Source-only component: §S03(Float output from independently packed/reconstructed IQ) − S03(Float output from original analog source)§. Processing component: §fixed integer stage reconstructed in original units − S03(Float output from packed/reconstructed IQ)§. Total reference deviation is their *sum as complex vectors*, NOT the sum of MAX/RMS scalar budgets. Separate observed MAX/RMS are saved for each vector and each stage, and the triangle upper bound was independently checked. These observed values do not approve numerical error limits or Pfa/Pd.',
 '',
 '| Stimulus | g | FFT final total MAX | FFT final total RMS | FFT source-only MAX | FFT fixed-processing MAX | input clipping |',
 '|---|---:|---:|---:|---:|---:|---:|']
for g in (1,5):
 for kind in ('onbin_k5','offbin_k5p37','signed_extreme','overrange'):
  z=next(v for v in P['vectors'] if v['g']==g and v['kind']==kind)
  total=z['float_reference_stage_error_original_amplitude']['FFT5']
  a=z['source_quantization_effect_stage_original_amplitude']['FFT5']
  b=z['fixed_coefficient_twiddle_arithmetic_effect_stage_original_amplitude']['FFT5']
  lines.append(f"| {kind} | {g} | {total['MAX']:.8g} | {total['RMS']:.8g} | {a['MAX']:.8g} | {b['MAX']:.8g} | {z['input_saturation_count']} |")
lines+=['',
 'The overrange cases are **STRESS_ONLY-style deterministic numerical tests** and their much larger Float reference deviations originate predominantly from deliberate input clipping; they are not eligible for claims of accepted normal-source performance. The source, stage, overflow and MAX/RMS evidence remains available for **all** vectors without deletion. No retrospectively chosen performance threshold is claimed.',
 '',
 '## One concrete diagnostic capture defect, disposition',
 '',
 'The untouched historical v0.5 diagnostic code reinitialized its FFT stage capture list **inside the first range loop**. As a result, diagnostic **FFT1–FFT4** per-stage metrics omitted range 0, while FFT5 had all 128 ranges and the actual returned integer FFT outputs were still correct. The initial C04 all-range comparison exposed the shape mismatch (127 versus 128 ranges). The **derived C04 stage-capture adapter only** moves the list initialization outside the range loop. It does not change any MF, MTI, FFT butterfly, coefficient, arithmetic, narrowing, RNE, overflow or numerical contract. **All 128 range rows ×32 bins of all five stages** were independently checked after the adjustment. Historical v0.5/v0.6 values and accepted engineer decisions have not been edited; any historical stage-1..4 population-wide statistic must be interpreted with that documented range-0 omission.',
 '',
 '## Reproduction and frozen evidence',
 '',
 'From repository root with §/usr/bin/python3§ (Python '+platform.python_version()+'):',
 '§§§bash',
 '/usr/bin/python3 -B engineering/s04_numeric/s04_c04_independent_golden_v1.py',
 '/usr/bin/python3 -B engineering/s04_numeric/s04_c04_fullchain_qualification_v1.py',
 "/usr/bin/python3 -B -m unittest discover -s tests -p 'test_s04_c04_fullchain_qualification_v1.py' -v",
 '§§§',
 'Primary code: §engineering/s04_numeric/s04_c04_fullchain_qualification_v1.py§ and §engineering/s04_numeric/s04_c04_selected_C_stage_capture_v1.py§. Expected values from independent Oracle: §engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json§. All per-vector exact-stage mismatch counts, Float source/fixed-process error MAX/RMS and bin checks: §engineering/s04_numeric/S04-C04-integrated-fullchain-v1.0.json§. Complete test and command stdout/stderr logs and SHA-256 manifest accompany this report.',
 '',
 '## Acceptance boundary',
 '',
 '**C04=OPEN, READY FOR INDEPENDENT SIGN-OFF.** The present qualification covers deterministic full-chain exact integer MF/MTI/FFT behaviour on the declared vectors; it does not constitute independent stochastic Pfa/Pd qualification, full clustering/CFAR target-list certification, hardware resource validation, statistical input profile expansion, or RTL/FPGA proof. The historical binding **REQ-SCR-01, REQ-RNG-03**, native clustering, peak discrepancies, numeric error budget and hardware overflow event retention remain OPEN with original owners. No accepted S03 seeds, main statistical CPI, RTL, synthesis, FPGA or architecture reselection was used. **C01=PASS BOUNDED; C02=PASS; C03=PASS; C04=OPEN READY FOR SIGN-OFF; S04=37.5%; overall=28.125%; Gate-S04 OPEN.**']
report.write_text('\n'.join(lines).replace('§',chr(96))+'\n')
evidence={
 'project':'AX309-RDSP-001','criterion':'S04-C04',
 'version':'integrated-fullchain-v1.0','readiness':'READY_FOR_INDEPENDENT_SIGN_OFF',
 'official_pass':False,'completed':False,'frozen_architecture':'C',
 'FFT_shift_schedule':[0,1,0,1,1],
 'new_unit_tests_pass':18,'unit_tests_failed':0,
 'deterministic_vector_count':18,'source_g_values':[1,5],
 'total_integer_component_compared':1036800,
 'all_integer_stage_mismatches':0,
 'MF_output_components_per_vector':8448,'MTI_output_components_per_vector':8192,
 'five_FFT_stage_components_per_vector':40960,
 'independent_oracle':'S04-C03 Independent Integer/Fraction golden',
 'original_S03_Float_source_and_reference':True,
 'deterministic_no_noise_onbin':5.0,'deterministic_no_noise_offbin':5.37,
 'Doppler_peaks_natural_bin':5,
 'input_clipping_stress_components_total':16896,
 'internal_processing_overflow_events_on_18_vectors':0,
 'legacy_v05_FFT1_to_FFT4_range0_missing_from_diagnostic_metrics':True,
 'derived_C04_stage_capture_fixes_range0_without_changing_arithmetic':True,
 'source_quantization_and_fixed_processing_errors_separate':True,
 'float_error_thresholds_approved':False,
 'C03':'PASS','C04':'OPEN','S04_percent':37.5,'overall_percent':28.125,'gate_S04':'OPEN',
 'req_scr_01':'BINDING_OPEN','req_rng_03':'BINDING_OPEN',
 'no_main_statistical_CPI':True,'no_accepted_S03_seeds':True,
 'no_RTL':True,'no_synthesis':True,'no_FPGA':True,
 'original_obligations_SHA256':sha(R/ob),
 'source_files_sha256':{str(x.relative_to(R)):sha(x) for x in [
 R/'engineering/s04_numeric/s04_c04_selected_C_stage_capture_v1.py',
 R/'engineering/s04_numeric/s04_c04_fullchain_qualification_v1.py',
 R/'engineering/s04_numeric/s04_c04_independent_golden_v1.py',
 R/'tests/test_s04_c04_fullchain_qualification_v1.py',
 R/'engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json',
 R/'engineering/s04_numeric/S04-C04-integrated-fullchain-v1.0.json',
 R/'engineering/S04-C04-INTEGRATED-v1.0-INDEPENDENT-TESTS.log',
 R/'engineering/S04-C04-INTEGRATED-v1.0-FULLCHAIN-RUN.log',
 R/'engineering/S04-C04-INTEGRATED-v1.0-GOLDEN-RUN.log']},
 'report_SHA256':sha(report),'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
out=R/'engineering/s04_numeric/S04-C04-integrated-qualification-evidence-v1.0.json'
out.write_text(json.dumps(evidence,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('REPORT_SHA256',sha(report))
print('EVIDENCE_SHA256',sha(out))
print('FULLCHAIN_SHA256',sha(R/'engineering/s04_numeric/S04-C04-integrated-fullchain-v1.0.json'))
print('GOLDEN_SHA256',sha(R/'engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json'))
print('LOCKED_OBLIGATIONS_UNCHANGED',sha(R/ob))

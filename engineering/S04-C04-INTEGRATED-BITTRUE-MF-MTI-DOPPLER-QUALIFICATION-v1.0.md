# AX309-RDSP-001 | S04-C04 Integrated Bit-True MF/MTI/Doppler Qualification v1.0

**EXECUTED; READY FOR INDEPENDENT SIGN-OFF — NOT C04 PASS.** The approved C01 bounded input scaling and C02 selected architecture C with five FFT shifts [0,1,0,1,1] were not altered. C03 has an independent engineer PASS. C04 remains OPEN pending its own independent engineer signature.

## Exact execution and expected-value independence

One executable integrated C04 package evaluates **18 deterministic complete 33×128 input records**: nine physical/rational stimulus types at **g=1 and g=5**, including zero, DC stationary, pulse-alternating DC, extrema of signed Q16.15, positive/negative half-LSB, signed alternating phase, a noiseless on-bin target at Doppler bin 5, a noiseless off-bin target at 5.37 bins, and intentional input overrange. These are **test vectors**, not statistical noise-only CPI samples; g5 is used only as a deterministic arithmetic scaling test and does not expand approved C01 statistical populations.

Independent expected outputs were computed with the C03 standalone **Integer/Fraction Oracle**, not the selected-C implementation arithmetic helpers. Full integer MF outputs (33×128), MTI outputs (32×128) and *each* of five FFT stages (128×32 complex) were checked against the v0.5 exact-integer engine using a derived stage-capture adapter. In all **18×(8448+8192+5×8192)=1,036,800** individual stored real/imag stage comparisons, **zero bit-true mismatch** occurred. Source digest, exact golden MF/MTI point samples and FFT-stage bins in every input profile are separately frozen in `engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json`, derived only from the independent Oracle.

Reference Float samples are deterministic S03 LFM echoes with a known fixed amplitude (0.18) and an explicitly chosen deterministic slow-time Doppler; source generation does not use a statistical CPI or accepted seeds. Comparison to frozen S03 pulse compression, MTI and unnormalized forward FFT is performed **in original physical Float amplitude units**, reconstructing each fixed stage with cumulative g×2^(sum stage shifts). Natural (not fftshifted) Doppler bins are retained. This work validates the selected stage output order and scaling, not target detection probability.

## Complete self-checking results

| Test category | Independent checks | Result |
|---|---|---|
| Full MF16, MTI two-pulse and five FFT stages | Exact 1,036,800 component comparisons from 18 × 7 stage arrays | **PASS; zero integer mismatch** |
| Zero/constant DC | Zero chain; exact stationary DC cancellation after MTI, retained zero FFT | **PASS** |
| On-bin / off-bin | Float on-bin target k=5 and off-bin k=5.37; fixed reconstructed peaks at natural FFT index 5; off-bin leakage independently verified | **PASS** |
| Signed and half-LSB | Q16.15 signed endpoints, RNE negative ties, alternating sequences | **PASS** |
| Saturation | Two overrange vectors, **8448 input component clips each** and no internal processing overflow; clipped vectors retained | **PASS** |
| Float/Fixed numerical effects | For each stage, separate source-input quantization and fixed coefficient/twiddle/rounding effects; observed MAX/RMS and triangle consistency | **PASS** |
| Reproduction and state | Exact independent golden outputs/digests, frozen C, seed and RTL restrictions, unchanged C04 state/progress | **PASS** |

**New C04 independent self-checking unit tests: 18/18 PASS, 0 FAIL.** Previous C03/C02 tests remain historical and do not constitute this C04 result.

## Numeric error: implementation versus quantization (not the same thing)

For all 18 vectors every stored integer output of all seven processing stages matches the independent C03 Oracle **exactly**, so tested **integer implementation mismatch = 0**. Deviations from the ideal Float S03 reference can be nonzero due to quantized input, MF coefficients, FFT twiddles, selected RNE/shifts and deliberate saturation. This is *not* evidence of an incorrect bit-true implementation.

Source-only component: `S03(Float output from independently packed/reconstructed IQ) − S03(Float output from original analog source)`. Processing component: `fixed integer stage reconstructed in original units − S03(Float output from packed/reconstructed IQ)`. Total reference deviation is their *sum as complex vectors*, NOT the sum of MAX/RMS scalar budgets. Separate observed MAX/RMS are saved for each vector and each stage, and the triangle upper bound was independently checked. These observed values do not approve numerical error limits or Pfa/Pd.

| Stimulus | g | FFT final total MAX | FFT final total RMS | FFT source-only MAX | FFT fixed-processing MAX | input clipping |
|---|---:|---:|---:|---:|---:|---:|
| onbin_k5 | 1 | 0.0018593196 | 0.00017719726 | 0.0018971043 | 0.0016718979 | 0 |
| offbin_k5p37 | 1 | 0.0023257815 | 0.00020832441 | 0.0013398892 | 0.002095694 | 0 |
| signed_extreme | 1 | 0.057617019 | 0.009418618 | 0 | 0.057617019 | 0 |
| overrange | 1 | 95.42513 | 13.795946 | 95.367523 | 0.057617019 | 8448 |
| onbin_k5 | 5 | 0.0090008355 | 0.00073504685 | 0.0081488614 | 0.0034963387 | 0 |
| offbin_k5p37 | 5 | 0.0070799307 | 0.00086673428 | 0.0065904257 | 0.0025022977 | 0 |
| signed_extreme | 5 | 0.28808509 | 0.04709309 | 0 | 0.28808509 | 0 |
| overrange | 5 | 477.12565 | 68.97973 | 476.83761 | 0.28808509 | 8448 |

The overrange cases are **STRESS_ONLY-style deterministic numerical tests** and their much larger Float reference deviations originate predominantly from deliberate input clipping; they are not eligible for claims of accepted normal-source performance. The source, stage, overflow and MAX/RMS evidence remains available for **all** vectors without deletion. No retrospectively chosen performance threshold is claimed.

## One concrete diagnostic capture defect, disposition

The untouched historical v0.5 diagnostic code reinitialized its FFT stage capture list **inside the first range loop**. As a result, diagnostic **FFT1–FFT4** per-stage metrics omitted range 0, while FFT5 had all 128 ranges and the actual returned integer FFT outputs were still correct. The initial C04 all-range comparison exposed the shape mismatch (127 versus 128 ranges). The **derived C04 stage-capture adapter only** moves the list initialization outside the range loop. It does not change any MF, MTI, FFT butterfly, coefficient, arithmetic, narrowing, RNE, overflow or numerical contract. **All 128 range rows ×32 bins of all five stages** were independently checked after the adjustment. Historical v0.5/v0.6 values and accepted engineer decisions have not been edited; any historical stage-1..4 population-wide statistic must be interpreted with that documented range-0 omission.

## Reproduction and frozen evidence

From repository root with `/usr/bin/python3` (Python 3.14.4):
```bash
/usr/bin/python3 -B engineering/s04_numeric/s04_c04_independent_golden_v1.py
/usr/bin/python3 -B engineering/s04_numeric/s04_c04_fullchain_qualification_v1.py
/usr/bin/python3 -B -m unittest discover -s tests -p 'test_s04_c04_fullchain_qualification_v1.py' -v
```
Primary code: `engineering/s04_numeric/s04_c04_fullchain_qualification_v1.py` and `engineering/s04_numeric/s04_c04_selected_C_stage_capture_v1.py`. Expected values from independent Oracle: `engineering/s04_numeric/S04-C04-independent-golden-expected-v1.0.json`. All per-vector exact-stage mismatch counts, Float source/fixed-process error MAX/RMS and bin checks: `engineering/s04_numeric/S04-C04-integrated-fullchain-v1.0.json`. Complete test and command stdout/stderr logs and SHA-256 manifest accompany this report.

## Acceptance boundary

**C04=OPEN, READY FOR INDEPENDENT SIGN-OFF.** The present qualification covers deterministic full-chain exact integer MF/MTI/FFT behaviour on the declared vectors; it does not constitute independent stochastic Pfa/Pd qualification, full clustering/CFAR target-list certification, hardware resource validation, statistical input profile expansion, or RTL/FPGA proof. The historical binding **REQ-SCR-01, REQ-RNG-03**, native clustering, peak discrepancies, numeric error budget and hardware overflow event retention remain OPEN with original owners. No accepted S03 seeds, main statistical CPI, RTL, synthesis, FPGA or architecture reselection was used. **C01=PASS BOUNDED; C02=PASS; C03=PASS; C04=OPEN READY FOR SIGN-OFF; S04=37.5%; overall=28.125%; Gate-S04 OPEN.**

"""Render auditable Markdown tables from deterministic numerical evidence."""
import json,hashlib,math
from pathlib import Path
root=Path(__file__).resolve().parents[2]
a=json.load(open(root/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json'))
old=json.load(open(root/'engineering/s04_numeric/S04-C02-range-bitgrowth-v0.2.json'))
p=root/'engineering/S04-C02-COEFFICIENT-FFT-SHIFT-REVIEW-v0.3.md'
out=[]
def add(s=''):out.append(s)
def f(x):return f"{x:.8g}"
add('# AX309-RDSP-001 | S04-C02 Coefficient Precision and FFT Shift-Schedule Review v0.3')
add()
add('**DESIGN ANALYSIS / NO APPROVAL.** C01 PASS BOUNDED, C02 OPEN, Gate-S04 OPEN; S04 12.5%, overall 26.04%. No CPI, accepted S03 seed, RTL, synthesis or FPGA operation.')
add()
add('## 1. Exact signed/unsigned width correction')
add('Signed Q(W,F) range: [-2^(W-F-1), 2^(W-F-1)-2^-F]. Unsigned U(W,F): [0,2^(W-F)-2^-F]. To cover a continuous symmetric real magnitude M>=0, set K=ceil(M*2^F) with exact rational arithmetic. Minimum positive-symmetric signed width W=max(2,1+bit_length(K)); unsigned nonnegative W=max(1,bit_length(K)). This is a conservative enclosure for continuous real signals; an already quantized integer set can require fewer bits if its extrema are known exactly.')
add('Signed minimum -2^(W-1) is representable, +2^(W-1) is not; at power-of-two endpoints signed width needs one more bit than an unsigned integer of that magnitude. Previous v0.2 floating log2 formulas were numerically fragile near powers-of-two. Exact Fraction/integer tests validate boundary endpoints, negative/positive asymmetry and F=0,1,2,7,13,15,26,30. **No listed v0.2 ideal-stage minimum widths changed** after exact arithmetic verification: MF21/F15, MTI22/F15, FFT27/F15 unshifted or FFT22/F13 shifted8, power U52/F30, training sum U57/F30, shifted8 power U42/F26 and sum U47/F26. The v0.2 source/report is preserved unchanged.')
add()
add('## 2. Frozen S03 coefficient conventions')
add('MF: 16 midpoint chirp samples, Fs=1 MHz, B=250 kHz; h=conjugate(reverse(chirp)), as frozen s03_reference/model.py. FFT: unnormalized forward 32-point negative-exponential FFT. Radix2 DIT stages m=2,4,8,16,32 use w=exp(-i*2*pi*j/m), j=0..m/2-1, with bit-reversed input ordering for natural output order. These reproduce the mathematical Float reference, not a prescribed RTL butterfly realization. 16 MF and 31 radix2 stage-twiddle occurrences are serialized in numerical JSON, including decoded coefficient integer pairs, component errors, phase errors and magnitude errors.')
add('Candidate coefficient encoding: signed RNE separately per real/imag part with endpoint saturation. This rounding is proposed, NOT approved for coefficient/twiddle or internal arithmetic.')
add()
add('| Variant | MF coeff W/F | Twiddle W/F, candidate | MF max complex error | MF max phase error rad | max |MF coeff| | Twiddle max complex error | Twiddle max phase error rad | max |Twiddle| |')
add('|---|---|---|---:|---:|---:|---:|---:|---:|')
for name,v in a['formats'].items():
 mc=max(abs(x['phase_error_rad'] or 0) for x in v['mf16'])
 tc=max(abs(x['phase_error_rad'] or 0) for z in v['twiddle32_by_stage'].values() for x in z)
 w=v['metadata']
 add(f"| {name} | {w['mf_coeff'][0]}/{w['mf_coeff'][1]} | {w['twiddle_candidate'][0]}/{w['twiddle_candidate'][1]} | {f(v['mf_coefficient_complex_abs_error_max'])} | {f(mc)} | {f(v['mf_magnitude_max'])} | {f(v['twiddle_max_abs_error'])} | {f(tc)} | {f(v['twiddle_max_magnitude'])} |")
add('Quantized Twiddle maximum modulus A/C ~1.00001157, B ~1.00006582; unit-modulus assumptions from v0.2 are not certified for these actual rounded coefficients. The signed +1 coefficient becomes the positive maximum representable value, not exact +1.')
add()
add('## 3. Quantized MF16 and MTI2 bounds, separate errors')
add('For |IQstored|<=sqrt2 after approved input SATQ15 and candidate rounded taps hhat[k], triangle inequality gives |MF|<=sqrt2*SUM|hhat| and |MTI|<=2*sqrt2*SUM|hhat|, on an exact-complex-operations assumption. Coefficient-only MF error relative to ideal h is bounded by sqrt2*SUM|hhat-h|, distinct from internal multiply/accumulator rounding. The full raw real product of signed Q16.15 input and coefficient signed W/F uses 16+W bits (fraction 15+F), complex pair 17+W bits, exact 16-term pair accumulator 21+W bits before narrowing.')
add('| Variant | sum |hhat| | MF magnitude bound | MTI magnitude bound | coefficient-only MF error | raw product bits | raw complex pair bits | raw 16-tap acc bits |')
add('|---|---:|---:|---:|---:|---:|---:|---:|')
for name,v in a['formats'].items():
 add(f"| {name} | {f(v['mf_coeff_sum_abs'])} | {f(v['mf_magnitude_growth_upper'])} | {f(v['mti_magnitude_growth_upper'])} | {f(v['mf_coefficient_error_bound_at_complex_input_magnitude_sqrt2'])} | {v['raw_mf_component_product_bits']} | {v['raw_mf_real_pair_bits']} | {v['raw_mf_accum16_bits']} |")
add('Input Q1.15 error has a separate C01 budget. To claim bounded real MF/MTI implementation error, the exact product narrowing, rounding, saturation, post-accumulator and MTI-output bit widths must be independently fixed.')
add()
add('## 4. FFT five-stage shift schedules and conditional bounds')
add('For stage j with quantized beta_j=max|what_j|, delta_j=max|what_j-w_j|, shift s_j=0/1: M_j<=M_(j-1)*(1+beta_j)/2^s_j, given exact complex multiplication/addition. At each stage the JSON records M_j, integer-exact minimum signed W for the proposal F, candidate W/F, remaining signed positive capacity, shift, twiddle error and the candidate one-output-RNE rounding bound. This uses the SAME candidate final FFT W/F at every stage as a sensitivity proxy; actual internal stage-specific widths are OPEN.')
add()
add('| Schedule | divide factor | FFT reconstructed amplitude at g5 / g1 | reconstructed power at g5 / g1 |')
add('|---|---:|---:|---:|')
for key,s in a['schedules'].items():
 r=s['reconstruction']
 add(f"| {key} {s['shifts']} | {s['FFT_normalization']} | {r['NOISE_ONLY_UNIT']['FFT_amplitude_scale']}/{r['SINGLE_TARGET_REFERENCE_LIKE_LAB']['FFT_amplitude_scale']} | {r['NOISE_ONLY_UNIT']['power_scale']}/{r['SINGLE_TARGET_REFERENCE_LIKE_LAB']['power_scale']} |")
add()
for key,s in a['schedules'].items():
 add(f"### {key}, stages 1–5, shifts {s['shifts']}")
 add('| Variant | stage | shift | complex magnitude upper | required signed W | candidate W/F | positive capacity minus bound | post-stage RNE max component error |')
 add('|---|---:|---:|---:|---:|---|---:|---:|')
 for name,v in s['per_architecture'].items():
  for t in v['stage']:
   add(f"| {name} | {t['stage']} | {t['shift']} | {f(t['complex_magnitude_upper_if_exact_ops'])} | {t['minimum_signed_W_at_Foutput']} | {t['candidate_stage_out_W']}/{t['candidate_stage_out_F']} | {f(t['candidate_stage_output_margin'])} | {f(t['candidate_post_stage_RNE_max_component_error'])} |")
add('Zero-shift B/C final-width-at-every-stage proxies fail at later stages (negative margins); A fits conditional twiddle growth. Other schedules fit these particular stage-output proxies but do not prove full intermediate-product overflow freedom.')
add()
add('### Separation of twiddle quantization and rounding errors')
add('Under the explicitly hypothetical exact-products/one RNE per stage and exact MF/MTI arithmetic before output narrowing, complex error recursion is E_j<=((1+beta_j)E_(j-1)+delta_j*Mideal_(j-1))/2^s_j+sqrt2*2^(-F-1). Initial E_0 includes actual MF coefficient-only error, one MF output RNE and one MTI output RNE. Twiddle-only errors omit MF/MTI coefficient and operation rounding. Both are **conditional analytical envelopes**, not formally certified worst-case Float-to-fixed bounds or empirical RMS; additional internal butterfly product rounding, shifts, twiddle ordering or saturation invalidates this simplification.')
add('| Schedule | A conditional error | B conditional error | C conditional error | twiddle-only A/B/C |')
add('|---|---:|---:|---:|---|')
for key,s in a['schedules'].items():
 vals=[s['per_architecture'][x] for x in ('A','B','C_hypothetical')]
 add(f"| {key} | {f(vals[0]['conditional_MF_MTI_quantization_plus_FFT_one_RNE_each_stage_error_bound'])} | {f(vals[1]['conditional_MF_MTI_quantization_plus_FFT_one_RNE_each_stage_error_bound'])} | {f(vals[2]['conditional_MF_MTI_quantization_plus_FFT_one_RNE_each_stage_error_bound'])} | {' / '.join(f(v['twiddle_only_error_bound_from_mti_input']) for v in vals)} |")
add('Schedules with equal net 3 shifts have identical physical reconstruction factor but different intermediate headroom and conditional rounding-error propagation; no FFT shift schedule selected.')
add()
add('## 5. Power and strict CA-CFAR full-width integer arithmetic')
add('For W-bit signed FFT I/Q, full signed products need 2W bits; I²+Q² conservatively needs 2W+1 before narrowing. Exact sum of 40 nonnegative power words needs power W+ceil(log2 40) bits before narrowing. Strict candidate decision with alpha=A/2^Fa and same stored power scale on CUT and 40-cell SUM is 40*Pcut*2^Fa > A*SUM40. Equality gives NO alarm. Exact integer examples with SUM40=40*2^Fa and CUT=A-1,A,A+1 return FALSE,FALSE,TRUE. This does NOT qualify Pd/Pfa or near-threshold decision match against Float.')
add('| Variant | 2W real square | 2W+1 I²+Q² | power W/F | sum40 W/F | comparison left/right conservative bits | alpha numerator / 2^Fa |')
add('|---|---:|---:|---|---|---|---|')
for name,v in a['CFAR'].items():
 add(f"| {name} | {v['raw_exact_real_square_product_bits']} | {v['raw_exact_I2_plus_Q2_bits']} | {v['power_stored_width']}/{v['power_frac']} | {v['sum40_stored_width']}/{v['sum40_frac']} | {v['integer_compare_left_width_conservative']}/{v['integer_compare_right_width_conservative']} | {v['alpha_numerator']}/2^{v['alpha_frac']} |")
add()
add('## 6. Cost and comparative numerical risks (pre-synthesis proxies only)')
add('| Option | MF coeff bits | raw MF accumulator bits | full FFT buffer bits | full power buffer bits | FFT zero-shift proxy fits? | numeric risk and controller complexity |')
add('|---|---:|---:|---:|---:|---|---|')
for name,v in a['formats'].items():
 prior=old['candidate_formats_not_approved'][name]['resource_storage_proxies']
 fit=a['schedules']['ZERO']['per_architecture'][name]['all_stages_fit_candidate_output_format']
 add(f"| {name} | {prior['coefficient_rom_bits_16_complex']} | {v['raw_mf_accum16_bits']} | {prior['RD_complex_FFT_buffer_bits_128x32']} | {prior['RD_power_buffer_bits_128x32']} | {fit} | {'wide F15 with no FFT shift' if name=='A' else ('narrow F13 and larger coefficient errors' if name=='B' else 'retains F15 with three shifts')} |")
add('A 32-point radix2 FFT has 5x16=80 complex butterfly computations per transform; MF has 16 complex products per output, each optionally four real products; sum40 can be computed with 39 additions without reuse. These are operation counts, NOT instantiated multipliers, LUT/FF/DSP48/BRAM usage, measured timing, throughput or synthesis area. Real memory packing, pipeline control and multiplier sharing remain OPEN. Near CFAR threshold, finite precision and different FFT shift sites can flip alarms; no acceptable margin threshold selected.')
add()
add('## 7. Outstanding S02 binding requirements and limits')
add('| Obligation | Additional approved C02 owner | C06 independent verifier | Unavailable source conditions | Gate-S04 |')
add('|---|---|---|---|---|')
add('| REQ-SCR-01, SCR +10/-10 dB and no clutter | design numeric target+clutter dynamic-range and gain profile | independent S02-prescribed scenario coverage | absolute target/clutter amplitudes, joint distribution/crest, phase, source mask and admitted g | BINDING OPEN, close before gate |')
add('| REQ-RNG-03 two equal-power targets around nominal 600m | design coherent superposition, MF sidelobes, list/cluster headroom | independent frozen resolved-pair oracle and Float/Fixed coverage | absolute target envelope, relative phase, overlaps and denominator | BINDING OPEN, close before gate |')
add('S02 historical S03 ownership remains unchanged; newer C02/C06 responsibilities derive from explicit engineer C01 signoff. No new clutter source law or target envelope adopted.')
add()
add('## 8. Evidence and held decision')
add('Source: engineering/s04_numeric/s04_c02_coeff_shift_v03.py. Data: engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json, with complete 16-tap and 31 twiddle coefficient vectors and detailed five-stage errors. Unit tests: tests/test_s04_c02_coeff_shift_v03.py; exact rational/integer independent boundary-width tests, negative half-LSB RNE, MF reverse conjugate, FFT sign/twiddles, multi-stage margins and strict CFAR comparator. An early unit test rejected the substring ISE appearing in NOISE, then was corrected; no source numerical model change or statistical trial resulted.')
add('The highest-risk OPEN decisions are real internal FFT stage widths and product rounding, coefficient/twiddle rounding policy, five shift schedule, downstream saturation handling, certified numerical MAX/RMS bounds and independent threshold-decision acceptance. No A/B/C selected, no bit-true Pd or Pfa inference, no RTL or synthesis. **C01 PASS BOUNDED; C02 OPEN; Gate-S04 OPEN; S04 12.5%; overall 26.04%.**')
p.write_text('\n'.join(out)+'\n')
print('REPORT_LINES',len(out),'SHA',hashlib.sha256(p.read_bytes()).hexdigest())

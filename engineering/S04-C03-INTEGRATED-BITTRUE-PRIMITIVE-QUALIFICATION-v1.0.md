# AX309-RDSP-001 | S04-C03 Integrated Bit-True Arithmetic Primitive Qualification v1.0

**READY FOR INDEPENDENT SIGN-OFF; C03 remains OPEN (NOT PASS).** The full P01–P08 entry-package work was performed in one executable deterministic qualification suite. Architecture C and FFT shift [0,1,0,1,1] remain frozen. S04=25%, overall=27.08%, Gate-S04 OPEN.

## Independent oracle versus the C02 implementation

The new independent Oracle, `engineering/s04_numeric/s04_c03_independent_oracle_v1.py`, implements Gaussian-integer/Fraction formulas and Python Fraction ties-to-even without calling the C02 model rounding, overflow or coefficient helpers. It re-derives S03 LFM phase and FFT Twiddles, checks frozen integer tables, and compares independent MF/MTI/FFT outputs at selected range bins. It also verifies the entire 4096-cell candidate power map and every one of the 2782 valid CFAR CUT via its own 7x7/3x3 training geometry and exact rational comparator.

## P01–P08 final test outcomes

| Item | Independently qualified operations | New tests | Status |
|---|---|---:|---|
| C03-P01 | IQ packing g1/g5, signed saturation edges, interleaving, reconstruction | 2 | **PASS** |
| C03-P02 | Independent S03 MF16 coeff and FFT32 Twiddle integers, sign/order | 2 | **PASS** |
| C03-P03 | Four exact real products, Gaussian complex multiplication, 16-tap MF accumulator | 3 | **PASS** |
| C03-P04 | MTI, five FFT Butterflies, full intermediate widths and shift schedule | 3 | **PASS** |
| C03-P05 | Independent Fraction nearest-even, both signed ties, signed extrema | 3 | **PASS** |
| C03-P06 | Unsigned power, SUM40, strict CFAR; 4096 powers and 2782 CUT independently verified | 4 | **PASS** |
| C03-P07 | All overflow/saturation events, stable UUID/order/full int and SHA readback | 4 | **PASS** |
| C03-P08 | Independent golden values, deterministic provenance, immutable C and scope | 3 | **PASS** |

**NEW C03 tests: 24/24 PASS; all eight P01–P08 subsections PASS.** Three separate *C02 regressions* were rerun: selected-C 10/10, v0.5 14/14, v0.6 15/15, all PASS. These 39 historical tests are not counted as C03 independent evidence.

**Observed test-oracle repair:** The first diagnostic run reported two failing *expected constants*: the positive exact input tie x/g=65535/65536 clips under RNE, and an extreme signed complex product has zero real part, not one. These were corrected against independently computed rational identities before final frozen tests. The approved C02 contract and DUT code were not changed. Initial diagnostic failures are disclosed here and were seen in command output; a standalone initial-failure log was overwritten during rerun and therefore is **not claimed to be archived**. Neither failure is counted as PASS.

## Complete overflow and saturation event traces

The selected-C fulltrace adapter records the entire ordered event stream **without modifying the historic v0.5 integer datapath**. It records event UUIDv5, vector ID, ordinal, input/processing scope, arithmetic site/location/component, sign, full prelimit integer and allowed bounds, and sticky event status. Event SHA-256 and unique IDs are verified after byte-level readback.
- **16,896** events in the two g1/g5 overrange input-stress vectors, all retained. Four normal/near-clip traces have zero events (as expected). No internal overflow arose for these selected-C test input vectors; this is not a stochastic risk claim.
- **159** deliberately forced internal events: 77 signed FFT5, 41 unsigned power and 41 unsigned SUM40, with independent integer saturation expectations, all written to complete trace JSONL.
- **17,055 total events** retained across seven trace files, including all events beyond the old 24-event preview. The previous historical model and obligations file were not altered. Complete event capture in later RTL/hardware remains an OPEN downstream implementation/verification obligation.

## Exact reproducibility

Run from repository root with `/usr/bin/python3` 3.14.4:
```bash
/usr/bin/python3 -B engineering/s04_numeric/s04_c03_fulltrace_v1.py
/usr/bin/python3 -B engineering/s04_numeric/s04_c03_internal_overflow_evidence_v1.py
/usr/bin/python3 -B -m unittest discover -s tests -p 'test_s04_c03_integrated_qualification_v1.py' -v
```
Actual log names: `engineering/S04-C03-INTEGRATED-v1.0-FULLTRACE.log`, `engineering/S04-C03-INTEGRATED-v1.0-FORCED-OVERFLOW.log`, `engineering/S04-C03-INTEGRATED-v1.0-INDEPENDENT-TESTS.log`. Machine-readable manifests enumerate **all** JSONL files and hashes: `engineering/s04_numeric/S04-C03-complete-overflow-replay-v1.0.json` and `engineering/s04_numeric/S04-C03-forced-internal-overflow-evidence-v1.0.json`.

## Sign-off disposition and exclusions

**The executed C03 P01–P08 package is READY FOR INDEPENDENT SIGN-OFF.** The user/engineer has not yet issued the separate C03 PASS decision. Neither 24 unit tests nor full Python telemetry constitute authorization for a statistical CPI, accepted S03 seed reuse, RTL, synthesis or FPGA test. The original open **REQ-SCR-01, REQ-RNG-03**, native clustering, two host-peak differences, statistical validation and hardware event/protocol checks remain explicitly OPEN; no implicit waiver. **C01=PASS BOUNDED; C02=PASS; C03=OPEN; Gate-S04=OPEN; S04=25%; overall=27.08%.**

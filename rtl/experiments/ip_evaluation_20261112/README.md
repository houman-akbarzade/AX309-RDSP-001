# Float comparison and complete-chain resource probes

Laboratory evaluation only. Production RTL, the active UART/IQ bitstream,
approved C02 baseline, acceptance and progress were not modified.

## Numeric comparison

Run build_numeric_vectors.py to reproduce the 11 finite deterministic cases.
It retains the exact pre-quantizer source without changing quantization,
checks the three old source reconstructions bytewise, captures common MTI,
and builds three Float64 references:

1. Original source -> Float MF/MTI/FFT, divided by 8.
2. The same quantized ADC IQ -> Float MF/MTI/FFT, divided by 8.
3. Identical fixed MTI -> NumPy FFT, divided by 8 (isolated FFT accuracy).

Eight new structural-IP CPI simulations plus the prior three immutable
structural traces give 45056 complex outputs. No archived statistical CPI,
main Pfa seed, alpha tuning or REQ-RNG-03 acceptance campaign is used.
Low-SNR development case uses noise RMS .06; others use .002. Cases are
correlated deterministic development examples, not independent statistical
trials. Metrics use complex RMSE and energy-normalized NRMSE, never gain/phase
fitting. Exact component membership, peaks, equal maxima and truth association
are compared after complete Power/CFAR/Grouping, using the same C05 integer
postprocessor for both fixed FFT paths and S03 Float postprocessing.

    bash rtl/experiments/ip_evaluation_20261112/run_numeric.sh

The runner needs the existing generated Lite-BRAM FFT v7.1 simulation model.
The numerical analysis and all underlying commands were executed. The
packaged runner was syntax checked, not redundantly rerun as one batch.

## Resource probes

    bash rtl/experiments/ip_evaluation_20261112/run_resources.sh

prepare_resource_probes.py regenerates all six measured integration sources.
The regenerated PRJ/XST/top/core files were hash-compared to the files
actually measured: identical. Expected failing intermediate variants are
retained. Reported LUTs are MAP values, not sums of standalone estimates.

The resource top contains actual UART/R1 input/readback and actual full IQ
RAM shared with DSP. A diagnostic START pin is qualified by complete upload
and readback ACK coverage. Host traffic must remain quiet during DSP.
Results use diagnostic buses and external ready, **not UART RESULT packets**.
This is NOT a deployable board top. No bitgen or new board programming ran.

Final all-stage probe: grouping_ram_globalclock:
4722 LUT / 3504 FF / 14 DSP48A1 / 25 RAMB16BWER + 5 RAMB8BWER.
PAR and internal 20ns timing PASS, minimum 19.260ns, setup/hold errors 0.
External delays and actual diagnostic-output board pins are unqualified.

Changes retain the MF arithmetic and Grouping semantics:
- MF final RNE occurs one cycle after the complete full-precision sum.
- IQ bank select is registered with the synchronous data.
- emitted/row tables have unified single-write ports and infer LUTRAM.
- one explicit top BUFG clocks both opaque IP and soft logic.

Without the last change, mixed XST/NGC integration left the IP on a local
fabric-routed raw IBUF clock: 18 DSP cascade hold errors. The fixed PAR clock
report has only the common global clk_g. No false path/multicycle relaxation
or slower requested period was used.

## Verification

Recorded ISim passes:
- Grouping: all 11 existing cases, 30602 CUTs, 887 exact oracle records;
  capacity 702, late merges, ties, stalls, overflow and malformed input.
- Grouping + 8-entry FIFO: 702/702 exact records under forced full stalls.
- MF pipeline: 64 complete complex 16-tap vectors and prelimit/tags matched
  the frozen integer oracle, plus the existing MF/MTI/RNE smoke.
- Registered IQ bank: full 16896B upload/readback, 35 packets, CRC/retry.
- IP adapter: 15 frames / 480 exact outputs, sparse inputs, uninterrupted
  frame reuse, output backpressure and stability.

No complete UART-to-DSP-to-UART hardware run is claimed. Board top, result
packetization, RUN/COMMIT/ABORT, final I/O timing and physical tests remain.
The IP is still not strictly bit-identical to C02 and has different overflow
and internal telemetry behavior. Selection/adoption awaits the engineer.

Canonical evidence and report:
engineering/evidence/s05/ip_evaluation_20261112/manifest.json
engineering/IP-FLOAT-AND-FULL-CHAIN-EVALUATION-20261112.md

## v0.2.1 operator interface update

Dimensioned axes, independent PRI/bin/range-cell selection, input/output range–PRI or range–Doppler/velocity maps, FPGA/software/difference views, full data tables, readable error metrics, threshold plots, individual target velocities, arbitrary fractional complex-noise RMS, dynamic SVG diagrams and Persian B Nazanin help. See `engineering/STAGE-LAB-v0.2.1-GUI-REPORT.md`. The stable v0.1 and lab v0.2.0 tags are retained. No RTL or bitstream changes.

# AX309 Stage Lab v0.2.0

A separate development application and separate FPGA test images. The stable full pipeline, original GUI and its shortcut are preserved.

- Stable code/firmware tag: stable/full-ip-uart-gui-v0.1 (a5ae0cd).
- Development branch: feature/stage-lab-v0.2.
- Stable workspace: /home/houman/AX309-RDSP-001.
- Stage Lab workspace: /home/houman/AX309-RDSP-001-stage-lab.
- New shortcut: AX309 Stage Lab v0.2; old AX309 Radar Lab remains.
- Run from this workspace: python3 -m stage_lab.
- Full Persian guide: GUIDE_FA.html and the GUI's Persian help tab.

## Stage choices
MF: 1..33 raw PRIs, including one independent PRI.
MTI: 2..33 MF PRIs, giving one fewer MTI row.
FFT: 32 MTI rows.
Power: 32 rows of software FFT input.
CFAR: independent software Power input; optional software FFT input to combined hardware Power+CFAR.
Grouping: software CFAR mask AND Power. All valid CUTs are replayed in their fixed raster order.

Raw PRI/CPI mode executes successive hardware images with UART roundtrips between stages. There is no software DSP substitution between those stages; integer stored codes are transferred losslessly. It is intentionally slower than the original full normal pipeline and is not a real-time acquisition mode.

Software input engine is independently selectable as Python Float or MATLAB Float. Neither input generator uses the IP bit-accurate FFT model for downstream tests. Reference engine can be Python, MATLAB or both, with Float, Fixed or both. Independent-stage references receive exactly the echoed, quantized hardware input. Input quantization RMSE is separately recorded. Raw-chain comparisons are separately identified from isolated final-stage comparisons.

Fixed FFT references in BOTH languages use the installed official Xilinx FFT v7.1 C model, through separate Python ctypes/MATLAB MEX adapters. They share this vendor arithmetic model; they are not claimed to be two independently reimplemented fixed FFT algorithms. Float FFT uses NumPy/MATLAB FFT. MF/MTI/Power/CFAR/Grouping reference implementations are separately executed in Python and MATLAB. MATLAB Fixed CFAR uses exact 72-bit fi comparisons.

## Formats
All matrices have 128 range columns. Rows represent PRI/slow time, or natural FFT bin. Numeric comparison never uses fftshift; only map drawing does.

UART uses 64-bit little-endian canonical words:
- Raw IQ: signed 16-bit stored components, sign extended to two signed32 lanes (I low, Q high), F=15.
- MF: signed22 components, F=15, sign extended to the same lanes.
- MTI: signed23 components, F=15.
- FFT: signed25 components, F=15; total FFT scale is 1/8.
- Power: low46 unsigned bits, F=30.
- CFAR: Power low46, alarm bit63; returned valid-CUT marker bit62.
- Grouping: each existing 99-bit record in two 64-bit words, with zero upper padding.

NPY, NPZ and MATLAB MAT v7 files can be loaded. Complex data use data or codes; Power may use power; Grouping requires power and mask. Choose Normalized float or Stored codes explicitly. A one-dimensional PRI can be reshaped into 128 range columns. Nonfinite, clipping, invalid width/shape or out-of-ROI CFAR masks are rejected. MAT v7.3/HDF5 and serialized MATLAB fi objects are not directly imported: save ordinary arrays with save(...,'-v7').

File raw PRI/CPI mode accepts external raw arrays. File FFT -> hardware Power + CFAR accepts external software FFT arrays for the combined test. File mode without a prefix selects the immediate previous-stage input. Self-describing saved NPZ input_words/entry or initial_words/initial_entry may be replayed in the matching mode.

Results save JSON plus NPZ, including actual input echo, hardware output, all selected matrix references, hashes, firmware identity and numerical metrics. Grouping JSON also contains all hardware/reference records; no Top-K or truth filtering is applied.

## UART and execution
This is a distinct laboratory request/response protocol layered on the unchanged S02 CRC/8N1 parser, NOT a replacement for the stable R1 firmware. One request is outstanding at a time. A nonzero random session nonce, case ID, sequence and CRC bind data to each run. Upload coverage and exact input readback are required before VERIFY/RUN. Read replies are replayable; duplicate RUN does not start a second computation. Programming is SRAM-only. A new configuration intentionally replaces an idle laboratory case; it is not the retained-terminal-state production recovery contract.

Low status flags: bit0 MF saturation, bit1 FFT overflow, bit2 Power saturation. Upper error bits reject a comparison. Results are read only after hardware reports complete. Keep Program selected when changing stages; it may be disabled for repeated cases on the same image.

Restore stable FPGA v0.1 decompresses and verifies the committed stable bitstream archive before SRAM programming. Its SHA-256 is fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb. Stable rollback was physically tested using the original full UART/GUI pipeline (9 records and COMMIT). Flash and original source files were not changed.

## Verification actually executed
- All 7 test images mapped, routed and met 20 ns, with zero setup/hold errors.
- ISim tested all six isolated engines, Power saturation, CFAR high powers, and 702 grouping records.
- Full serial ISim tested corrupt CRC, duplicate CONFIG/upload/read/RUN, premature RUN rejection, exact echoed input and all 4096 Power outputs (75627 checked UART bytes).
- Actual board tests passed for every stage, plus Power saturation, CFAR large powers, 702 groups, signed-bin equal-peak tie priority, late merging, the edge CUT, empty output, a single independent MF PRI and a two-PRI MTI pair.
- Raw CPI passed through all six hardware stages with exact fixed comparison; combined software FFT -> hardware Power+CFAR passed against all four references.
- 12 actual MATLAB/Python stage reference comparisons passed; fixed outputs were exact, Float differences were normal floating arithmetic differences.
- Exact 72-bit CFAR below/equal/above-threshold decisions were [false,false,true] in MATLAB, Python and FPGA.
- Official FFT C-model matched 45056 independent previously captured structural ISim complex outputs on 11 CPIs.
- GUI rendering used actual recorded data for all six stages/four components, including the 702-record table. The visible GUI also executed a real Power test with MATLAB Float FFT input and all four references.
- MAT FFT file, empty Grouping MAT and single-PRI NPY injection were physically tested. Repeated fresh cases without reprogramming passed.
- 57 inherited PC link regressions passed.

A 64-threshold exploration view is available for FFT/Power. Noise-only cells and target scenario fractions are labelled exploratory one-CPI measurements. Correlated CUTs are not independent trials. This is NOT a statistical Pd/Pfa/ROC qualification, and does not close existing radar acceptance gates. Grouping comparison covers complete final record fields and peak geometry; no new per-cell hardware label trace is claimed.

## Reproduce
From this workspace:
    python3 rtl/stage_lab/build.py
    python3 -m stage_lab.verify sim 1 2 3 4 4:edge 5 5:edge 6 6:edge
    python3 -m stage_lab.verify_uart
    python3 -m stage_lab.verify_references
    QT_QPA_PLATFORM=offscreen python3 -m stage_lab.smoke

The following programs the connected FPGA with each selected TEST image:
    python3 -m stage_lab.verify board 1 2 3 4 4:edge 5 5:edge 6 6:edge

Interactive GUI and four-reference physical Power demonstration:
    python3 -m stage_lab.gui --show-power --matlab-input

Dependencies already used on the host: Python/NumPy/SciPy/PySide6/pyserial, ISE 14.7, MATLAB R2024a with Fixed-Point Designer, and the installed FFT v7.1 C-model library. Missing vendor generated FFT products can be rebuilt from the committed XCO. CoreGen/MEX products remain in ignored caches; canonical source and evidence are versioned.

"""MATLAB binary I/O bridge to the *actual* Xilinx FFT v7.1 bit-accurate C model.

Input: 32x128x2 signed int64, C row-major (pulse,range,component).
Output: 128x32x2 signed int64, C row-major (range,bin,component).
No floating FFT approximation or reimplemented butterfly.
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engineering'/'s04_numeric'))
from fft_ip_fullchain_v1 import vendor_fft,assert_vendor
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--overflow',required=True)
    args=ap.parse_args()
    assert_vendor()
    inp=np.fromfile(args.input,dtype='<i8')
    if inp.size!=32*128*2:
        raise ValueError(f'Bad input word count: {inp.size}')
    mt=inp.reshape((32,128,2))
    assert np.max(np.abs(mt))<2**23, 'MTI is not signed 23-bit'
    rd,overflow=vendor_fft(mt)
    if rd.shape!=(128,32,2):raise RuntimeError('Bad Xilinx FFT dimensions')
    Path(args.output).write_bytes(np.asarray(rd,dtype='<i8').tobytes())
    Path(args.overflow).write_text(str(int(overflow))+'\n')
    print(f'XILINX_FFT_OK ranges=128 bins=32 overflow={overflow}')
if __name__=='__main__':main()

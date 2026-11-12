"""Vendor v7.1 bit-accurate C-model through its documented v7.1-compatible C ABI.
No use of this model when generating software-FFT inputs for downstream tests."""
import ctypes as C
from pathlib import Path
import numpy as np
LIB=Path('/opt/Xilinx/14.7/ISE_DS/ISE/sysgen/lib/lin64')
class Generics(C.Structure):
 _fields_=[(n,C.c_int) for n in ['nfft','arch','variable','floating','width','twiddle','scaling','bfp','rounding']]
class Inputs(C.Structure):
 _fields_=[('nfft',C.c_int),('re',C.POINTER(C.c_double)),('nr',C.c_int),('im',C.POINTER(C.c_double)),('ni',C.c_int),('shifts',C.POINTER(C.c_int)),('ns',C.c_int),('forward',C.c_int)]
class Outputs(C.Structure):
 _fields_=[('re',C.POINTER(C.c_double)),('nr',C.c_int),('im',C.POINTER(C.c_double)),('ni',C.c_int),('exponent',C.c_int),('overflow',C.c_int)]
def fft_codes(a):
 a=np.asarray(a)
 if a.shape!=(32,128):raise ValueError('FFT requires 32x128, slow-time major')
 for name in ['libstlport.so.5.1','libstlport.so']:
  if (LIB/name).exists():C.CDLL(str(LIB/name),mode=C.RTLD_GLOBAL);break
 lib=C.CDLL(str(LIB/'libIp_xfft_v7_1_bitacc_cmodel.so'),mode=C.RTLD_GLOBAL)
 create=lib.xilinx_ip_xfft_v7_1_create_state;create.argtypes=[Generics];create.restype=C.c_void_p
 sim=lib.xilinx_ip_xfft_v7_1_bitacc_simulate;sim.argtypes=[C.c_void_p,Inputs,C.POINTER(Outputs)];sim.restype=C.c_int
 destroy=lib.xilinx_ip_xfft_v7_1_destroy_state;destroy.argtypes=[C.c_void_p]
 state=create(Generics(5,4,0,0,25,16,1,0,1))
 if not state:raise RuntimeError('FFT C-model state creation failed')
 shifts=(C.c_int*5)(0,1,0,1,1);out=np.empty((32,128),complex);overflow=0
 try:
  for r in range(128):
   re=np.ascontiguousarray(a[:,r].real/(1<<24),dtype=np.float64)
   im=np.ascontiguousarray(a[:,r].imag/(1<<24),dtype=np.float64)
   yr=np.zeros(32);yi=np.zeros(32)
   ptr=lambda x:x.ctypes.data_as(C.POINTER(C.c_double))
   inp=Inputs(5,ptr(re),32,ptr(im),32,shifts,5,1);res=Outputs(ptr(yr),32,ptr(yi),32,0,0)
   code=sim(state,inp,C.byref(res))
   if code or res.nr!=32 or res.ni!=32:raise RuntimeError('FFT C-model simulation failed')
   out[:,r]=np.rint(yr*(1<<24))+1j*np.rint(yi*(1<<24));overflow|=res.overflow
 finally:destroy(state)
 return out,overflow

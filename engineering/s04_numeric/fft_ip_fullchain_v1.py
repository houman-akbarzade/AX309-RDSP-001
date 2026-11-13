"""Full raw-IQ -> fixed MF -> MTI -> Xilinx v7.1 bit accurate FFT -> U46 Power -> CA-CFAR -> grouping.
Independent software candidate. Xilinx IP FFT is executed by vendor library; no FFT input stage injection.
"""
from __future__ import annotations
import ctypes as ct
import hashlib
from pathlib import Path
import numpy as np
import s04_c04_selected_C_stage_capture_v1 as C04
import s04_c05_native_integer_v1 as C05
LIB=Path('/opt/Xilinx/14.7/ISE_DS/ISE/sysgen/lib/lin64')
VENDOR=LIB/'libIp_xfft_v7_1_bitacc_cmodel.so'
EXPECTED_LIB_SHA='4a8f02f24f269bc947d5f0d3e89a73916f763b8491c7a0f4e68b4bee88a994a9'
class Generics(ct.Structure):
 _fields_=[(n,ct.c_int) for n in ('nfft','arch','variable','floating','width','twiddle','scaling','bfp','rounding')]
class Inputs(ct.Structure):
 _fields_=[('nfft',ct.c_int),('re',ct.POINTER(ct.c_double)),('nr',ct.c_int),('im',ct.POINTER(ct.c_double)),('ni',ct.c_int),('shifts',ct.POINTER(ct.c_int)),('ns',ct.c_int),('forward',ct.c_int)]
class Outputs(ct.Structure):
 _fields_=[('re',ct.POINTER(ct.c_double)),('nr',ct.c_int),('im',ct.POINTER(ct.c_double)),('ni',ct.c_int),('exponent',ct.c_int),('overflow',ct.c_int)]
def library_sha256():
 return hashlib.sha256(VENDOR.read_bytes()).hexdigest()
def assert_vendor():
 if not VENDOR.is_file():raise FileNotFoundError(VENDOR)
 digest=library_sha256()
 if digest!=EXPECTED_LIB_SHA:raise RuntimeError('Vendor library identity changed: '+digest)
def fixed_frontend(iq):
 """Match S04 selected C MF/MTI: single RNE after 16 exact integer tap products."""
 iq=np.asarray(iq,dtype=np.int64)
 assert iq.shape==(33,128,2) and np.all((iq>=-32768)&(iq<=32767))
 taps,_=C04.coefficients('C_hypothetical')
 mf=np.zeros((33,128,2),dtype=np.int64)
 mfclip=0;mticlip=0
 lim_mf=2**21;lim_mti=2**22
 for p in range(33):
  for r in range(128):
   re=im=0
   for k,(hr,hi) in enumerate(taps):
    idx=r+15-k
    if idx>=128:continue
    ir=int(iq[p,idx,0]);ii=int(iq[p,idx,1])
    re+=ir*hr-ii*hi;im+=ir*hi+ii*hr
   a=C04.rne(re,32768);b=C04.rne(im,32768)
   mfclip+=int(not -lim_mf<=a<lim_mf)+int(not -lim_mf<=b<lim_mf)
   mf[p,r,0]=max(-lim_mf,min(lim_mf-1,a))
   mf[p,r,1]=max(-lim_mf,min(lim_mf-1,b))
 mt=np.diff(mf,axis=0)
 mticlip=int(np.count_nonzero((mt < -lim_mti)|(mt >= lim_mti)))
 mt=np.clip(mt,-lim_mti,lim_mti-1)
 return mt,mfclip,mticlip

def vendor_fft(mt):
 """32 slow-time samples by 128 range cells, vendor ABI documented v7.1."""
 assert_vendor()
 assert mt.shape==(32,128,2)
 for dep in ('libstlport.so.5.1','libstlport.so'):
  if (LIB/dep).exists():ct.CDLL(str(LIB/dep),mode=ct.RTLD_GLOBAL);break
 lib=ct.CDLL(str(VENDOR),mode=ct.RTLD_GLOBAL)
 create=lib.xilinx_ip_xfft_v7_1_create_state
 create.argtypes=[Generics];create.restype=ct.c_void_p
 simulate=lib.xilinx_ip_xfft_v7_1_bitacc_simulate
 simulate.argtypes=[ct.c_void_p,Inputs,ct.POINTER(Outputs)];simulate.restype=ct.c_int
 destroy=lib.xilinx_ip_xfft_v7_1_destroy_state;destroy.argtypes=[ct.c_void_p]
 state=create(Generics(5,4,0,0,25,16,1,0,1))
 if not state:raise RuntimeError('Cannot create Xilinx FFT v7.1 state')
 schedule=(ct.c_int*5)(0,1,0,1,1)
 result=np.empty((128,32,2),dtype=np.int64);overflow_count=0
 ptr=lambda x:x.ctypes.data_as(ct.POINTER(ct.c_double))
 try:
  for r in range(128):
   # 25-bit signed input Q24 as required by vendor reference model.
   re=np.ascontiguousarray(mt[:,r,0]/(1<<24),dtype=np.float64)
   im=np.ascontiguousarray(mt[:,r,1]/(1<<24),dtype=np.float64)
   yr=np.zeros(32,dtype=np.float64);yi=np.zeros(32,dtype=np.float64)
   inp=Inputs(5,ptr(re),32,ptr(im),32,schedule,5,1)
   out=Outputs(ptr(yr),32,ptr(yi),32,0,0)
   rc=simulate(state,inp,ct.byref(out))
   if rc!=0 or out.nr!=32 or out.ni!=32:raise RuntimeError(f'Xilinx FFT failed r={r} rc={rc}')
   result[r,:,0]=np.rint(yr*(1<<24)).astype(np.int64)
   result[r,:,1]=np.rint(yi*(1<<24)).astype(np.int64)
   overflow_count+=int(bool(out.overflow))
 finally:destroy(state)
 return result,overflow_count

def full_chain(iq):
 mt,mfc,mtic=fixed_frontend(iq)
 fft,fftov=vendor_fft(mt)
 rd=[[tuple(map(int,fft[r,b])) for b in range(32)] for r in range(128)]
 native=C05.complete_map(rd)
 assert len(native['cut_records'])==2782
 alarms=sum(int(x['alarm']) for x in native['cut_records'])
 return dict(mt=mt,fft=fft,native=native,alarms=alarms,
             mf_clip=mfc,mti_clip=mtic,fft_overflow=fftov,
             power_clip=len(native['power_events']))

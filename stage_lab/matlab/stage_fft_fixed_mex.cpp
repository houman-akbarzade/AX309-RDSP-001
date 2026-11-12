// Thin MATLAB adapter for the installed Xilinx FFT v7.1 C model.
// Structures follow Xilinx's documented v7.1-compatible bit-accurate C API.
// The adapter is validated against independent structural ISim traces.
#include "mex.h"
#include <dlfcn.h>
#include <cmath>
struct G { int nfft,arch,variable,floating,width,twiddle,scaling,bfp,rounding; };
struct I { int nfft;double* re;int nr;double* im;int ni;int* shifts;int ns;int forward; };
struct O { double* re;int nr;double* im;int ni;int exponent;int overflow; };
void mexFunction(int nl,mxArray** out,int nr,const mxArray** in){
 if(nr!=1 || mxGetM(in[0])!=32 || mxGetN(in[0])!=128 || !mxIsDouble(in[0]))mexErrMsgIdAndTxt("stage:shape","32x128 complex codes required");
 dlopen("/opt/Xilinx/14.7/ISE_DS/ISE/sysgen/lib/lin64/libstlport.so.5.1",RTLD_NOW|RTLD_GLOBAL);
 void* h=dlopen("/opt/Xilinx/14.7/ISE_DS/ISE/sysgen/lib/lin64/libIp_xfft_v7_1_bitacc_cmodel.so",RTLD_NOW|RTLD_GLOBAL);
 if(!h)mexErrMsgIdAndTxt("stage:library","%s",dlerror());
 auto create=(void*(*)(G))dlsym(h,"xilinx_ip_xfft_v7_1_create_state");
 auto simulate=(int(*)(void*,I,O*))dlsym(h,"xilinx_ip_xfft_v7_1_bitacc_simulate");
 auto destroy=(void(*)(void*))dlsym(h,"xilinx_ip_xfft_v7_1_destroy_state");
 if(!create||!simulate||!destroy)mexErrMsgIdAndTxt("stage:api","Missing FFT C model API");
 void* state=create(G{5,4,0,0,25,16,1,0,1});
 if(!state)mexErrMsgIdAndTxt("stage:state","FFT state failed");
 out[0]=mxCreateDoubleMatrix(32,128,mxCOMPLEX);
 double* ar=mxGetPr(in[0]);double* ai=mxGetPi(in[0]);double* br=mxGetPr(out[0]);double* bi=mxGetPi(out[0]);
 int shifts[5]={0,1,0,1,1};double re[32],im[32],yr[32],yi[32];
 for(int r=0;r<128;r++){
  for(int p=0;p<32;p++){re[p]=ar[r*32+p]/16777216.;im[p]=ai?ai[r*32+p]/16777216.:0;}
  I input{5,re,32,im,32,shifts,5,1};O output{yr,32,yi,32,0,0};
  if(simulate(state,input,&output)){destroy(state);mexErrMsgIdAndTxt("stage:simulate","FFT model failed");}
  for(int p=0;p<32;p++){br[r*32+p]=std::nearbyint(yr[p]*16777216.);bi[r*32+p]=std::nearbyint(yi[p]*16777216.);}
 }
 destroy(state);
}

"""Prospective analytical stage error bounds, no acceptance tests or seeds."""
from pathlib import Path
import json,math,cmath,hashlib
R=Path(__file__).resolve().parents[2]
C=json.loads((R/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json').read_text())
assert C['architecture']=='C' and C['schedule']==[0,1,0,1,1]
sqrt2=math.sqrt(2)
e0=sqrt2/65536
M0=sqrt2*(1+2**-15)
tap=C['MF']['mf16_stored_pairs']
h=[complex(i/32768,j/32768) for i,j in tap]
ref=[]
for k in range(16):
 n=15-k;t=(n+.5)/1e6
 phi=2*math.pi*(-125000*t+.5*(250000/(16/1e6))*t*t)
 ref.append(cmath.exp(-1j*phi))
delta_h=sum(abs(a-b) for a,b in zip(h,ref))
norm_h=sum(map(abs,h))
error={'input':e0*norm_h,'mf_coeff':M0*delta_h,'mf_RNE':e0,'fft_twiddle':0.,'fft_RNE':0.}
M=16*M0
stages=[]
def add(name,cum,M,error,beta=None,delta=None):
 B=sum(error.values())*cum
 E={'stage':name,'cumulative_scale':cum,'max_ideal_original_per_g':M*cum,
 'components_original_per_g':{k:v*cum for k,v in error.items()},
 'analytic_MAX_bound_original_per_g':B,
 'analytic_RMS_upper_via_MAX_per_g':B,
 'PROPOSED_MAX_cap_g1':math.ceil(B*1.25*1e5)/1e5,
 'PROPOSED_MAX_cap_g5':math.ceil(5*B*1.25*1e5)/1e5,
 'PROPOSED_RMS_cap_g1':math.ceil(B*1.25*1e5)/1e5,
 'PROPOSED_RMS_cap_g5':math.ceil(5*B*1.25*1e5)/1e5}
 if beta is not None:E['beta']=beta;E['delta_twiddle']=delta
 stages.append(E)
add('MF',1,M,error)
error={k:2*v for k,v in error.items()};M=2*M
add('MTI',1,M,error)
cum=1
for j,st in enumerate(C['FFT']['stages'],1):
 div=2**st['shift']
 tw=[complex(i/32768,q/32768) for i,q in st['twiddle_stage_stored_pairs']]
 ideal=[cmath.exp(-2j*math.pi*k/(1<<j)) for k in range(len(tw))]
 beta=max(map(abs,tw));delta=max(abs(a-b) for a,b in zip(tw,ideal))
 gain=(1+beta)/div
 error={k:v*gain for k,v in error.items()}
 error['fft_twiddle']+=delta*M/div
 error['fft_RNE']+=e0
 M=2*M/div;cum*=div
 add('FFT'+str(j),cum,M,error,beta,delta)
out={'project':'AX309-RDSP-001','criterion':'S04-C06',
'status':'PROPOSED_NOT_APPROVED','no_empirical_results_used':True,
'no_main_CPI_or_historical_seeds':True,
'conditional_assumptions':['no input clip','no internal overflow or saturation','abs(re(x/g)) and abs(im(x/g)) <=1+2^-15','frozen selected C exact RNE and widths'],
'input_component_error_per_g':1/65536,'input_complex_error_per_g':e0,
'MF_coefficient_L1_error':delta_h,'MF_quantized_coefficient_L1_norm':norm_h,
'proposed_design_factor_NOT_APPROVED':1.25,
'stagewise':stages,'RMS_note':'RMS upper bound equals MAX analytical bound; not a measured or calibrated RMS performance tolerance',
'final_power_error_formula':'abs(Pbittrue-Pfloat)<=2*abs(Zfloat)*Efft+Efft**2 before clipping',
'CFAR_prospective_margin_formula':'abs(float_margin)> (Ecutpower + alpha*sum(Etrainpower)/40 + abs(delta_alpha)*mean(FloatPtrain)); else margin ambiguous; never drop CPI or CUT'}
f=R/'engineering/s04_numeric/S04-C06-proposed-analytic-stage-bounds-v0.1.json'
f.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
for x in stages:print(x['stage'],'B_per_g',x['analytic_MAX_bound_original_per_g'],'CAP_g1',x['PROPOSED_MAX_cap_g1'],'CAP_g5',x['PROPOSED_MAX_cap_g5'])
print('SHA256',hashlib.sha256(f.read_bytes()).hexdigest())

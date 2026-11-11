"""S04-C04 integrated MF16/MTI2/FFT32 bit-true full-chain qualification.

Independent C03 Fraction oracle, no shared candidate arithmetic helpers. All
vectors deterministic. S03 Float is only used for signal creation/reference.
No accepted Pfa/Pd seeds and no statistical CPI or hardware operations.
"""
import sys,json,hashlib,math,cmath,platform,datetime
from pathlib import Path
from fractions import Fraction as Q
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c03_independent_oracle_v1 as O
import s04_c04_selected_C_stage_capture_v1 as D
from s03_reference import model as S03

G=(1,5)
SHIFT=(0,1,0,1,1)
TAPS=O.independent_mf_taps()
TW=O.independent_twiddles()
KINDS=('zero','dc_stationary','dc_pulsed','signed_extreme','half_lsb','negative_alternating','onbin_k5','offbin_k5p37','overrange')
assert [list(x) for x in TAPS]==O.CONTRACT['MF']['mf16_stored_pairs']
def source(kind,g):
    # Rational values in source units. g normalization is fixed before source.
    real=[]
    for p in range(33):
        row=[]
        for r in range(128):
            if kind=='zero': v=(Q(0),Q(0))
            elif kind=='dc_stationary':v=(Q(g,8),-Q(g,16))
            elif kind=='dc_pulsed':v=(Q(g*(1 if p%2==0 else -1),4),Q(g,16))
            elif kind=='signed_extreme':
                v=(Q(g*(32767 if (p+r)%2 else -32768),32768),
                   Q(g*(-32768 if p%2==0 else 32767),32768))
            elif kind=='half_lsb':
                v=(Q(g*(1 if (p+r)%2 else -1),65536),Q(g*(-3 if p%2 else 3),65536))
            elif kind=='negative_alternating':
                v=(Q(g*(-7 if (p+r)%2 else 7),16),
                   Q(g*(-5 if (p+2*r)%2 else 5),16))
            elif kind=='overrange':
                v=(Q(g*(6 if (p+r)%2 else -6),5),Q(g*(9 if p%2 else -9),8))
            elif kind in ('onbin_k5','offbin_k5p37'):
                if 40<=r<56:
                    chirp=S03.chirp()[r-40]
                    dopbin=5.0 if kind=='onbin_k5' else 5.37
                    # Deterministic sampled echo without random noise.
                    z=(.18*chirp)*cmath.exp(2j*math.pi*dopbin*p/32)
                    v=(Q.from_float(float(z.real)),Q.from_float(float(z.imag)))
                else:v=(Q(0),Q(0))
            else:raise ValueError(kind)
            row.append(v)
        real.append(row)
    src=np.array([[complex(float(x),float(y)) for x,y in row] for row in real],dtype=np.complex128)
    q=[];input_events=[]
    h=hashlib.sha256()
    for p,row in enumerate(real):
        vals=[]
        for r,xy in enumerate(row):
            code=[]
            for ci,val in enumerate(xy):
                n,sat=O.input_pack(val,g)
                code.append(n)
                h.update(f'{p}:{r}:{ci}:{val.numerator}/{val.denominator}:{n}\n'.encode())
                if sat:
                    raw=round(val*Q(32768,g))
                    input_events.append({'pulse':p,'range':r,'component':'IQ'[ci],
                      'raw':str(raw),'limited':n,'status':'SAT'})
            vals.append(tuple(code))
        q.append(vals)
    return src,q,input_events,h.hexdigest()

def max_rms(a,b):
    diff=np.abs(np.asarray(a)-np.asarray(b))
    return {'MAX':float(np.max(diff)),'RMS':float(np.sqrt(np.mean(np.square(diff))))}

def as_float(a,g,shift=0):
    a=np.asarray(a,dtype=np.int64)
    # a[...,0],a[...,1] exact integers within int64
    return (a[...,0].astype(np.float64)+1j*a[...,1].astype(np.float64))*((g*(1<<shift))/32768)

def s03_fft_stage_reference(mt):
    # Independent complex Float S03 chain, staged DIT only for diagnostic
    results=[[] for _ in range(5)]
    for r in range(128):
        a=[complex(mt[int(f'{i:05b}'[::-1],2),r]) for i in range(32)]
        for j,shift in enumerate(SHIFT):
            span=1<<(j+1)
            b=a.copy()
            for ix in range(0,32,span):
                for k in range(span//2):
                    x=ix+k;y=x+span//2
                    tw=cmath.exp(-2j*math.pi*k/span)
                    product=tw*a[y]
                    b[x]=(a[x]+product)/(1<<shift)
                    b[y]=(a[x]-product)/(1<<shift)
            a=b
            results[j].append(a.copy())
    return [np.asarray(v,dtype=np.complex128) for v in results]

def run_case(kind,g):
    src,iq,input_events,srcdigest=source(kind,g)
    tel=D.Telemetry()
    cand=D.run_one(src,iq,tel,'C_hypothetical',SHIFT,g,capture_stages=True)
    captured=cand['captured']
    ref_mf=S03.pulse_compress(src)
    ref_mt=S03.mti(ref_mf)
    ref_fft_stages=s03_fft_stage_reference(ref_mt)
    assert np.max(abs(ref_fft_stages[-1]*8-S03.doppler(ref_mt)))<1e-8
    ora_mf=[]
    for p in range(33):
        ora_mf.append([O.mf_at(iq,p,r,TAPS) for r in range(128)])
    ora_mt=[[O.mti(ora_mf[p][r],ora_mf[p+1][r]) for r in range(128)] for p in range(32)]
    ora_fft_stage=[[] for _ in range(5)]
    for r in range(128):
        stages=O.fft32_oracle([ora_mt[p][r] for p in range(32)],TW)
        for j in range(5):ora_fft_stage[j].append(stages[j])
    equality={}
    for name,a,b in [('MF',ora_mf,captured['mf']),('MTI',ora_mt,captured['mti'])]+[
     (f'FFT{j+1}',ora_fft_stage[j],captured['fft_stages_range_major'][j]) for j in range(5)]:
        arr1=np.asarray(a,dtype=np.int64);arr2=np.asarray(b,dtype=np.int64)
        assert arr1.shape==arr2.shape, (kind,g,name,arr1.shape,arr2.shape)
        mismatch=np.argwhere(arr1!=arr2)
        equality[name]={'matched_integer_components':int(arr1.size-len(mismatch)),
          'total_integer_components':int(arr1.size),
          'mismatch_count':int(len(mismatch)),
          'first_mismatch':mismatch[0].tolist() if len(mismatch) else None}
        assert len(mismatch)==0,(kind,g,name,mismatch[0])
    # Decompose numerical differences without conflating source quantization
    # with coefficients/twiddles and operation rounding. Same original units.
    quant_float=as_float(iq,g)
    quant_ref_mf=S03.pulse_compress(quant_float)
    quant_ref_mt=S03.mti(quant_ref_mf)
    quant_ref_fft=s03_fft_stage_reference(quant_ref_mt)
    source_only={}
    processing_only={}
    signed_error={}
    for key,actual,ref,shift in [('MF',ora_mf,ref_mf,0),('MTI',ora_mt,ref_mt,0)]+[
        (f'FFT{j+1}',ora_fft_stage[j],ref_fft_stages[j],sum(SHIFT[:j+1])) for j in range(5)]:
        if key in ('MF','MTI'):
            expected=ref
        else: expected=ref*(1<<shift)
        measured=as_float(actual,g,shift)
        signed_error[key]=max_rms(measured,expected)
        if key=='MF': stage_quant=quant_ref_mf
        elif key=='MTI': stage_quant=quant_ref_mt
        else: stage_quant=quant_ref_fft[int(key[-1])-1]*(1<<shift)
        source_only[key]=max_rms(stage_quant,expected)
        processing_only[key]=max_rms(measured,stage_quant)
    # FFT final natural bin order, not fftshift; on-bin assertion uses S03 oracle.
    ord_coded=np.asarray(ora_fft_stage[-1])
    original_rd=as_float(ora_fft_stage[-1],g,3)
    fft_float=S03.doppler(ref_mt)
    ref_bin=int(np.argmax(np.abs(fft_float[40]))) if kind in ('onbin_k5','offbin_k5p37') else None
    actual_bin=int(np.argmax(np.abs(original_rd[40]))) if ref_bin is not None else None
    # On-bin: distinguish largest raw Doppler bin from all other bins.
    if kind=='onbin_k5':
        assert ref_bin==actual_bin==5,(g,ref_bin,actual_bin)
    if kind=='offbin_k5p37':
        assert ref_bin==actual_bin==5,(g,ref_bin,actual_bin)
    if kind=='zero':
        assert np.count_nonzero(ord_coded)==0
        assert all(x['MAX']==0 for x in signed_error.values())
    if kind=='dc_stationary':
        assert np.count_nonzero(np.asarray(ora_mt))==0
        assert np.count_nonzero(ord_coded)==0
    # Source-reconstruction error must be separated from MF coeff/ops.
    original=np.asarray(src)
    input_float=as_float(iq,g)
    input_error=max_rms(input_float,original)
    return {'vector_id':f'g{g}:{kind}','g':g,'kind':kind,
      'source_sha256':srcdigest,'source_sample_count':33*128,
      'input_saturation_count':len(input_events),
      'first_input_saturation':input_events[:2],
      'internal_overflow_count':cand['overflow']['total'],
      'internal_overflow_by_site':cand['overflow']['counts'],
      'internal_overflow_first_24':cand['overflow']['first_24'],
      'input_float_max_rms':input_error,
      'bittrue_stage_agreement':equality,
      'float_reference_stage_error_original_amplitude':signed_error,
      'source_quantization_effect_stage_original_amplitude':source_only,
      'fixed_coefficient_twiddle_arithmetic_effect_stage_original_amplitude':processing_only,
      'error_budget_disposition':'observed MAX/RMS are not algebraically additive and not approved numeric acceptance limits',
      'reference_bin_at_range40':ref_bin,'fixed_bin_at_range40':actual_bin,
      'reconstruction_final_amplitude_factor':g*8,
      'scaling_contract':'g*8*code/32768; original power uses (g*8)^2 on normalized stored power',
      'numeric_deviation_includes_quantization_input_coeff_twiddle_rounding_and_sat':True,
      'implementation_error_from_independent_oracle':0,
      'not_stochastic_CPI':True}

def run_all():
    res={'project':'AX309-RDSP-001','criterion':'S04-C04',
     'version':'integrated-full-chain-v1.0','decision':'UNAPPROVED_C04_READY_FOR_REVIEW',
     'frozen_arch':'C','fft_shifts':list(SHIFT),
     'vectors':[],'g1':{},'g5':{},
     'error_interpretation':'zero integer oracle mismatch is proof for tested deterministic vectors only; float deviations reflect input and coefficient quantization, rounding, and clipping; no Pd/Pfa conclusion',
     'no_main_statistical_CPI':True,'no_historic_accepted_seeds':True}
    for g in G:
        for k in KINDS:
            v=run_case(k,g)
            res['vectors'].append(v)
            print('PASS',v['vector_id'],'input_sat',v['input_saturation_count'],
             'internal',v['internal_overflow_count'],
             'FFT5_max',v['float_reference_stage_error_original_amplitude']['FFT5']['MAX'],
             'bin',v['fixed_bin_at_range40'],flush=True)
    assert len(res['vectors'])==len(G)*len(KINDS)
    out=ROOT/'engineering/s04_numeric/S04-C04-integrated-fullchain-v1.0.json'
    out.write_text(json.dumps(res,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('SAVED',out,'SHA256',hashlib.sha256(out.read_bytes()).hexdigest())
if __name__=='__main__':run_all()

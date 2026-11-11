"""AX309 S04-C04 v1: derived stage-capture adapter, preserving v0.5 integer arithmetic.

Fixed path uses Python int and rational nearest-even; NO Float/NumPy in
MF/MTI/FFT/power/SUM40/CFAR. Float is used only for reference and metrics.
No random generator, original acceptance seeds, stochastic CPI, RTL or hardware.
"""
import json, math, cmath, hashlib, sys, platform, time
from fractions import Fraction
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from s03_reference import model as S03
import numpy as np
DATA=json.loads((ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json').read_text())
V04=json.loads((ROOT/'engineering/s04_numeric/S04-C02-internal-arithmetic-error-propagation-v0.4.json').read_text())
CFAR=json.loads((ROOT/'engineering/s04_numeric/S04-C02-cfar-width-arithmetic-audit-v0.3.1.json').read_text())
N=128;P=33;L=16;NF=32
PAIR=tuple[int,int]
def rne(n,d=1):
    assert type(n) is int and type(d) is int and d>0
    sign=-1 if n<0 else 1
    q,r=divmod(abs(n),d)
    return sign*(q+(2*r>d or (2*r==d and q%2==1)))
def shifted_round(n,shift):
    if shift>=0:return n<<shift
    return rne(n,1<<(-shift))
def required_width_signed(n):
    if n>=0:return max(2,n.bit_length()+1)
    return max(2,(-n-1).bit_length()+1)
def realformat(W,F):
    return {'signed':True,'W':W,'F':F,
            'stored_min':-(1<<(W-1)),'stored_max':(1<<(W-1))-1}
class Telemetry:
 def __init__(self):
    self.counts=Counter();self.first=[];self.digest=hashlib.sha256()
 def record(self,site,indices,component,before,W,under=False):
    r={'site':site,'indices':list(indices),'component':component,
       'pre_narrow_integer':str(before),'signed_W':W,
       'direction':'negative' if before<0 else 'positive',
       'kind':'intermediate_width_exceeded' if under else 'output_saturation'}
    self.counts[site+':'+r['kind']]+=1
    line=json.dumps(r,sort_keys=True,separators=(',',':'))
    self.digest.update((line+'\n').encode())
    if len(self.first)<24:self.first.append(r)
 def summary(self):
    return {'counts':dict(sorted(self.counts.items())),
       'total':sum(self.counts.values()),'first_24':self.first,
       'all_event_order_sha256':self.digest.hexdigest(),
       'events_truncated_in_record':sum(self.counts.values())>24}
def bounded(x,W,tel,site,index,component):
    lo=-(1<<(W-1));hi=(1<<(W-1))-1
    if not(lo<=x<=hi):
       tel.record(site,index,component,x,W)
       return max(lo,min(hi,x))
    return x
def intermediate_guard(x,W,tel,site,index,component):
    lo=-(1<<(W-1));hi=(1<<(W-1))-1
    if not lo<=x<=hi: tel.record(site,index,component,x,W,under=True)

def unsigned_intermediate_guard(x,W,tel,site,index):
    if not 0<=x<(1<<W):
        tel.record(site,index,'unsigned',x,W,under=True)

def ubounded(x,W,tel,site,index):
    if x<0:
        tel.record(site,index,'unsigned',x,W,under=True)
    assert x>=0
    hi=(1<<W)-1
    if x>hi:
       tel.record(site,index,'unsigned',x,W)
       return hi
    return x

# Accepted C01 profiles. Deterministic vectors: rational in normalized *stored* amplitude.
# Convert to original reference Float x=g*y only when constructing source.
def vector_value(kind,p,r):
    if kind=='zero':return (Fraction(0),Fraction(0))
    if kind=='impulse':return (Fraction(1,2),Fraction(-1,4)) if (p,r)==(8,40) else (Fraction(0),Fraction(0))
    if kind=='positive_max':return (Fraction(32767,32768),Fraction(32767,32768))
    if kind=='negative_min':return (Fraction(-32768,32768),Fraction(-32768,32768))
    if kind=='near_clip':return ((Fraction(65535,65536)-Fraction(1,1<<18)) if (r%2==0) else -Fraction(65537,65536)+Fraction(1,1<<18),
                                Fraction(-32767,32768) if p%2 else Fraction(32767,32768))
    if kind=='half_lsb_pos_neg':return ((Fraction(1,65536) if (p+r)%2 else -Fraction(1,65536)),
                                       (Fraction(-3,65536) if p%3 else Fraction(3,65536)))
    if kind=='alternating':return (Fraction(7*(-1)**(p+r),16),Fraction(5*(-1)**(p+2*r),16))
    if kind=='phase_interference':
       t=(p+3*r)%8
       return ((Fraction(9,16) if t in (0,1) else -Fraction(9,16) if t in (4,5) else Fraction(0)),
               (Fraction(9,16) if t in (2,3) else -Fraction(9,16) if t in (6,7) else Fraction(0)))
    if kind=='overrange_stress':
       return (Fraction(6,5) if r%2 else Fraction(-6,5),Fraction(9,8) if p%2 else Fraction(-9,8))
    raise ValueError(kind)
KINDS=('zero','impulse','positive_max','negative_min','near_clip','half_lsb_pos_neg','alternating','phase_interference','overrange_stress')
def source_vector(kind,g):
    logical=[[vector_value(kind,p,r) for r in range(N)] for p in range(P)]
    # Before the quantizer ONLY: original normalized Float reference for S03.
    src=np.array([[complex(float(re*g),float(im*g)) for re,im in row] for row in logical],dtype=np.complex128)
    iq=[]
    tel=Telemetry()
    for p,row in enumerate(logical):
       out=[]
       for r,(re,im) in enumerate(row):
          components=[]
          for component,v in zip('IQ',(re,im)):
             q=rne((v*32768).numerator,(v*32768).denominator)
             components.append(bounded(q,16,tel,'IQ',(p,r),component))
          out.append(tuple(components))
       iq.append(out)
    return src,iq,tel
def bitreverse(n,bits=5):
    return int(f'{n:0{bits}b}'[::-1],2)
def coefficients(name):
    v=DATA['formats'][name]
    taps=[tuple(x['stored_integer']) for x in v['mf16']]
    stages=[[tuple(x['stored_integer']) for x in v['twiddle32_by_stage'][str(i)]] for i in range(1,6)]
    return taps,stages
def metrics():
    return {'count':0,'sum_squared':0.,'max_abs':0.}
def accumulate(stat,actual,ideal):
    a=np.asarray(actual,dtype=np.complex128)
    err=np.abs(a-ideal)
    stat['count']+=int(err.size)
    stat['sum_squared']+=float(np.sum(np.square(err)))
    stat['max_abs']=max(stat['max_abs'],float(np.max(err)))
def stage_metric(stats):
    return {'samples':stats['count'],'MAX':stats['max_abs'],
       'RMS':math.sqrt(stats['sum_squared']/stats['count']) if stats['count'] else None}
def complex_float_matrix(mat,F,scale=1):
    return np.array([[complex(i*scale/(1<<F),q*scale/(1<<F)) for i,q in row] for row in mat],dtype=np.complex128)
def run_one(src,iq,initial_tel,opt,shifts,g,capture_stages=False):
    fmt=V04['summaries'][opt]['candidate_formats']
    tap,tw=coefficients(opt)
    fcoef=DATA['formats'][opt]['metadata']['mf_coeff'][1]
    fmf=fmt['mf'][1];fmti=fmt['mti'][1];ffft=fmt['fft'][1];ftw=fmt['twiddle'][1]
    wmf=fmt['mf'][0];wmti=fmt['mti'][0];wfft=fmt['fft'][0];wtw=fmt['twiddle'][0]
    tel=Telemetry()
    # Capture input clips in the current operation-specific audit without mutable reuse.
    for e in initial_tel.first:pass
    # Realized MF q[k] corresponds to full convolution output index k+15.
    mf=[]
    for p in range(P):
       row=[]
       for r in range(N):
          acc_re=acc_im=0
          for k,(hr,hi) in enumerate(tap):
             idx=r+15-k
             ir,ii=iq[p][idx] if 0<=idx<N else (0,0)
             r1=ir*hr;r2=ii*hi;r3=ir*hi;r4=ii*hr
             wprod=16+DATA['formats'][opt]['metadata']['mf_coeff'][0]
             for ci,value in enumerate((r1,r2,r3,r4)):
                 intermediate_guard(value,wprod,tel,'MF_PRODUCT',(p,r,k),str(ci))
             pr=r1-r2;pi=r3+r4
             intermediate_guard(pr,wprod+1,tel,'MF_PAIR',(p,r,k),'I')
             intermediate_guard(pi,wprod+1,tel,'MF_PAIR',(p,r,k),'Q')
             acc_re+=pr;acc_im+=pi
             intermediate_guard(acc_re,wprod+5,tel,'MF_ACC',(p,r,k),'I')
             intermediate_guard(acc_im,wprod+5,tel,'MF_ACC',(p,r,k),'Q')
          out=[]
          for component,x in zip('IQ',(acc_re,acc_im)):
             y=shifted_round(x,fmf-15-fcoef)
             out.append(bounded(y,wmf,tel,'MF',(p,r),component))
          row.append(tuple(out))
       mf.append(row)
    mt=[]
    for p in range(32):
       row=[]
       for r in range(N):
          value=[]
          for i,c in enumerate('IQ'):
             diff=mf[p+1][r][i]-mf[p][r][i]
             value.append(bounded(diff,wmti,tel,'MTI',(p,r),c))
          row.append(tuple(value))
       mt.append(row)
    # Float stage reference, non-stochastic, S03 MF/MTI and radix-2 DIT stage.
    mf_float=S03.pulse_compress(src)
    mt_float=S03.mti(mf_float)
    fm=complex_float_matrix(mf,fmf,g)
    tm=complex_float_matrix(mt,fmti,g)
    stats={'MF':metrics(),'MTI':metrics()}
    accumulate(stats['MF'],fm,mf_float)
    accumulate(stats['MTI'],tm,mt_float)
    fft_stages=[[] for _ in range(5)];ref_stages=[[] for _ in range(5)]
    stage_ref=[np.asarray(mt_float[:,r],dtype=np.complex128)[[bitreverse(k) for k in range(32)]].copy()
               for r in range(N)]
    rd_codes=[]
    for r in range(N):
       a=[mt[bitreverse(k)][r] for k in range(32)]
       for j,shift in enumerate(shifts):
          span=2**(j+1);half=span//2
          out=a.copy()
          twj=tw[j]
          Finput=fmti if j==0 else ffft
          Winput=wmti if j==0 else wfft
          for block in range(0,32,span):
             for k in range(half):
                i=block+k;h=i+half
                ur,ui=a[i];vr,vi=a[h]
                wr,wi=twj[k]
                v1=vr*wr;v2=vi*wi;v3=vr*wi;v4=vi*wr
                prodW=Winput+wtw
                for ci,value in enumerate((v1,v2,v3,v4)):
                    intermediate_guard(value,prodW,tel,f'FFT{j+1}_PRODUCT',(r,i,h),str(ci))
                tr=v1-v2;ti=v3+v4
                intermediate_guard(tr,prodW+1,tel,f'FFT{j+1}_TW_PAIR',(r,i,h),'I')
                intermediate_guard(ti,prodW+1,tel,f'FFT{j+1}_TW_PAIR',(r,i,h),'Q')
                # Integer fixed arithmetic: align u to the twiddle product F.
                uar=u_r=ur<<ftw;uai=ui<<ftw
                for dest,sign in ((i,1),(h,-1)):
                   zre=uar+sign*tr;zim=uai+sign*ti
                   bfW=max(Winput+ftw,prodW+1)+1
                   intermediate_guard(zre,bfW,tel,f'FFT{j+1}_BUTTERFLY',(r,dest),'I')
                   intermediate_guard(zim,bfW,tel,f'FFT{j+1}_BUTTERFLY',(r,dest),'Q')
                   denshift=Finput+ftw+shift-ffft
                   qr=shifted_round(zre,-denshift)
                   qi=shifted_round(zim,-denshift)
                   out[dest]=(bounded(qr,wfft,tel,f'FFT{j+1}',(r,dest),'I'),
                              bounded(qi,wfft,tel,f'FFT{j+1}',(r,dest),'Q'))
          a=out
          # Ideal S03 stage reference uses mathematically negative exponent (Float permitted).
          refprev=stage_ref[r].copy()
          refout=refprev.copy()
          for block in range(0,32,span):
             for k in range(half):
                ix=block+k;iy=ix+half
                w=cmath.exp(-2j*math.pi*k/span)
                t=w*refprev[iy]
                refout[ix]=(refprev[ix]+t)/(1<<shift)
                refout[iy]=(refprev[ix]-t)/(1<<shift)
          stage_ref[r]=refout
          # Accumulate per-stage after all 128 range bins below, store 128 stage references
          fft_stages[j].append(a.copy())
          ref_stages[j].append(refout.copy())
       rd_codes.append(a)
    shift_sum=sum(shifts)
    for j in range(5):
       # stage refs in range-major [range][doppler], same as stored codes.
       saved=complex_float_matrix(fft_stages[j],ffft,g*(1<<sum(shifts[:j+1])))
       expected=np.asarray(ref_stages[j],dtype=np.complex128)*(1<<sum(shifts[:j+1]))
       stats[f'FFT{j+1}']=metrics()
       accumulate(stats[f'FFT{j+1}'],saved,expected)
    final_s03=S03.doppler(mt_float)/(1<<shift_sum)
    final_stage=np.asarray(ref_stages[4])
    fft_consistency=float(np.max(np.abs(final_stage-final_s03)))
    # S03 unnormalized FFT scaled by schedule for validation.
    if fft_consistency>1e-9*max(1,float(np.max(np.abs(final_s03)))):
       raise AssertionError(('FFT convention',opt,shifts,fft_consistency))
    # Integer-only power: exact I²+Q², unsigned store, sum40, strict compare
    config=CFAR['calculations'][opt]['config']
    wp=config['powerW'];ws=config['sumW'];fa=config['alphaF'];a_coef=config['alphaNum']
    pw=[]
    for r,row in enumerate(rd_codes):
       prow=[]
       for b,(i,q) in enumerate(row):
          raw=i*i+q*q
          unsigned_intermediate_guard(raw,2*wfft+1,tel,'POWER_RAW',(r,b))
          assert raw <(1<<(2*wfft+1))
          prow.append(ubounded(raw,wp,tel,'POWER',(r,b)))
       pw.append(prow)
    alarms=0;valid=0;decisions=[]
    for r in range(3,110):
       for b in range(3,29):
          sm=0
          for dr,db in S03.TRAIN_OFFSETS:
             sm+=pw[r+dr][b+db]
          sm=ubounded(sm,ws,tel,'SUM40',(r,b))
          cut=pw[r][b]
          left=40*cut*(1<<fa);right=a_coef*sm
          left_width=CFAR['calculations'][opt]['post_narrowing_candidate_operands']['left_conservative_bits']
          right_width=CFAR['calculations'][opt]['post_narrowing_candidate_operands']['right_conservative_bits']
          unsigned_intermediate_guard(left,left_width,tel,'CFAR_LEFT_PRODUCT',(r,b))
          unsigned_intermediate_guard(right,right_width,tel,'CFAR_RIGHT_PRODUCT',(r,b))
          assert left <(1<<left_width)
          assert right<(1<<right_width)
          hit=left>right
          valid+=1;alarms+=hit
          if hit and len(decisions)<20:decisions.append((r,b))
    assert valid==2782
    captured={'mf':mf,'mti':mt,'fft_stages_range_major':fft_stages,'rd':rd_codes} if capture_stages else {}
    return {'captured':captured,'metrics':{k:stage_metric(v) for k,v in stats.items()},
       'max_power_stored_integer':max(max(x) for x in pw),
       'cfar_valid_cut_count':valid,'cfar_alarm_count':alarms,'first_20_alarms':decisions,
       'fft_float_reference_max_abs_diff':fft_consistency,
       'overflow':tel.summary()}
def all_trials():
    results={'project':'AX309-RDSP-001','version':'v0.5','status':'DETERMINISTIC_INTEGER_BITTRUE_PROTOTYPE_NO_ARCH_APPROVAL',
      'implementation':'All fixed path uses Python int; float confined to original reference, coefficient preparation (v0.3) and observed metrics',
      'reference':'s03_reference/model.py pulse_compress, mti, doppler, CFAR geometry',
      'C01_g':{'NOISE_ONLY_UNIT':5,'SINGLE_TARGET_REFERENCE_LIKE_LAB':1},
      'vector_kinds':KINDS,'per_profile':{},'per_option_schedule':{},
      'warnings':['These vectors are arbitrary deterministic stress samples; not statistical CPI/no Pfa or Pd',
      'Saturation observed in stress vectors; v0.4 bounds valid ONLY for nonsaturating input and internal stages',
      'Stagewise analytic comparison conditional on same exact-intermediate once-RNE arithmetic candidate',
      'No newly approved clutter/unknown-target model; g1 lab and g5 noise-only used only as scales'],
      'resource_proxies':{k:DATA['formats'][k]['metadata'] for k in DATA['formats']}}
    cases={}
    for g,profile in ((1,'SINGLE_TARGET_REFERENCE_LIKE_LAB'),(5,'NOISE_ONLY_UNIT')):
       for kind in KINDS:
          src,iq,tel=source_vector(kind,g)
          cases[(g,kind)]=(src,iq,tel)
          results['per_profile'][f'{profile}:{kind}']={'g':g,'input_saturations':tel.summary(),'sample_count':P*N}
    for opt in ('A','B','C_hypothetical'):
       for schedule,shifts in (('ZERO',(0,0,0,0,0)),('EARLY_3',(1,1,1,0,0)),
            ('DISTRIBUTED_3',(0,1,0,1,1)),('ALL_5',(1,1,1,1,1))):
          aggregate={x:metrics() for x in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5')}
          eligible={x:metrics() for x in aggregate}
          stress={x:metrics() for x in aggregate}
          sat=Counter();sample_results=[]
          cap=V04['summaries'][opt]['FFT']['schedules'][schedule]
          for g,profile in ((1,'SINGLE_TARGET_REFERENCE_LIKE_LAB'),(5,'NOISE_ONLY_UNIT')):
             for kind in KINDS:
                src,iq,inputtel=cases[g,kind]
                out=run_one(src,iq,inputtel,opt,shifts,g)
                for stage,meas in out['metrics'].items():
                   stat=aggregate[stage]
                   stat['count']+=meas['samples']
                   stat['sum_squared']+=meas['RMS']**2*meas['samples']
                   stat['max_abs']=max(stat['max_abs'],meas['MAX'])
                for site,count in out['overflow']['counts'].items():sat[site]+=count
                accepted=inputtel.summary()['total']==0 and out['overflow']['total']==0
                metric_target=eligible if accepted else stress
                for stage,meas in out['metrics'].items():
                   target=metric_target[stage]
                   target['count']+=meas['samples']
                   target['sum_squared']+=meas['RMS']**2*meas['samples']
                   target['max_abs']=max(target['max_abs'],meas['MAX'])
                v04_bound=cap['reconstructed_original_Float_error_amplitude'][str(g)]
                measured=out['metrics']['FFT5']['MAX']
                within=measured<=v04_bound+1e-9 if accepted else None
                sample_results.append({'input_profile':profile,'kind':kind,
                  'admissible_for_v04_bound':accepted,'v04_bound':v04_bound,
                  'FFT_max':measured,'FFT_RMS':out['metrics']['FFT5']['RMS'],
                  'v04_bound_verified_if_admissible':within,
                  'full_stage_metrics':out['metrics'],
                  'CFAR_valid_cut_count':out['cfar_valid_cut_count'],
                  'CFAR_alarm_count':out['cfar_alarm_count'],
                  'saturation':out['overflow']})
          key=f'{opt}:{schedule}'
          results['per_option_schedule'][key]={'option':opt,'schedule':schedule,'shifts':shifts,
            'case_count':len(sample_results),
            'aggregated_stage_metrics':{k:stage_metric(x) for k,x in aggregate.items()},
            'eligible_no_saturation_stage_metrics':{k:stage_metric(x) for k,x in eligible.items()},
            'stress_or_saturation_stage_metrics':{k:stage_metric(x) for k,x in stress.items()},
            'total_output_saturation_count':sum(sat.values()),
            'saturation_by_site':dict(sat),
            'conditional_v04_bounds_satisfied_on_all_admissible':all(
                x['v04_bound_verified_if_admissible'] is not False for x in sample_results),
            'admissible_case_count':sum(x['admissible_for_v04_bound'] for x in sample_results),
            'cases':sample_results}
          print('DONE',key,'FFT_MAX',results['per_option_schedule'][key]['aggregated_stage_metrics']['FFT5']['MAX'],
             'SAT',sum(sat.values()),'ADMISS',results['per_option_schedule'][key]['admissible_case_count'],flush=True)
    return results
if __name__=='__main__':
    t=time.perf_counter()
    data=all_trials()
    data['elapsed_seconds_environment_only']=time.perf_counter()-t
    p=ROOT/'engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json'
    p.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('SHA256',hashlib.sha256(p.read_bytes()).hexdigest(),'elapsed_s',data['elapsed_seconds_environment_only'])

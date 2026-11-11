"""AX309 S04-C03 independent integer/rational primitive oracle v1.

Independent from v0.5 model's rne, shifted_round, bounded, arithmetic helpers.
Fraction.__round__ is Python's independently implemented ties-to-even oracle.
All post-source fixed-point calculations are exact integer/Fraction. Trig floats
are used *only* for independent reference coefficient construction.
"""
from fractions import Fraction as Q
from pathlib import Path
import json,math,struct,hashlib

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=json.loads((ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json').read_text())
SCHED=(0,1,0,1,1)
def ref_round(q):
    assert isinstance(q,Q)
    return round(q)

def limits(w,signed=True):
    assert w>0
    return ((-(1<<(w-1)),(1<<(w-1))-1) if signed else (0,(1<<w)-1))

def checked(x,w,signed=True):
    assert isinstance(x,int)
    lo,hi=limits(w,signed)
    return (min(hi,max(lo,x)), not lo<=x<=hi)

def input_pack(x,g):
    assert isinstance(x,Q) and g in (1,5)
    original_code=ref_round(x*Q(32768,g))
    return checked(original_code,16,True)

def unpack_input(q,g):
    return Q(q*g,32768)

def interleaved_iq_bytes(items):
    return b''.join(struct.pack('<hh',i,j) for i,j in items)

def integer_complex(a,b):
    assert len(a)==len(b)==2
    ar,ai=a;br,bi=b
    # Independent algebra in Gaussian integers: no shared candidate helpers.
    return (ar*br-ai*bi, ar*bi+ai*br)

def mf_full_accumulator(packed,taps):
    assert len(packed)==len(taps)==16
    contributions=[integer_complex(x,h) for x,h in zip(packed,taps)]
    return (sum(p[0] for p in contributions),sum(p[1] for p in contributions))

def mf_at(q,p,r,taps):
    items=[]
    for k in range(16):
        idx=r+15-k
        items.append(q[p][idx] if 0<=idx<128 else (0,0))
    a,b=mf_full_accumulator(items,taps)
    return tuple(checked(ref_round(Q(v,32768)),22)[0] for v in (a,b))

def mti(a,b):
    assert len(a)==len(b)==2
    return tuple(checked(b[i]-a[i],23)[0] for i in (0,1))

def butterfly(u,v,w,stage):
    # Fraction-oracle independent of candidate shift helper.
    assert stage in range(5)
    z=integer_complex(v,w)
    sh=15+SCHED[stage]
    exact=[(u[0]*(1<<15)+z[0],u[1]*(1<<15)+z[1]),
           (u[0]*(1<<15)-z[0],u[1]*(1<<15)-z[1])]
    return tuple(tuple(checked(ref_round(Q(c,1<<sh)),25)[0] for c in pair) for pair in exact)

def fft32_oracle(mt_column,stage_twiddles):
    assert len(mt_column)==32 and [len(v) for v in stage_twiddles]==[1,2,4,8,16]
    perm=[int(format(i,'05b')[::-1],2) for i in range(32)]
    x=[mt_column[i] for i in perm]
    intermediates=[]
    for j in range(5):
        step=1<<(j+1)
        y=x.copy()
        for start in range(0,32,step):
            for k in range(step//2):
                i=start+k
                t=i+step//2
                y[i],y[t]=butterfly(x[i],x[t],stage_twiddles[j][k],j)
        x=y
        intermediates.append(x.copy())
    return intermediates

def independent_mf_taps():
    # S03 chirp phase re-derived independently using t=(n+0.5)/Fs.
    taps=[]
    for k in range(16):
        n=15-k
        t=(n+0.5)/1_000_000.0
        phi=2*math.pi*(-125000.0*t+0.5*(250000.0/(16.0/1_000_000.0))*t*t)
        ref=(math.cos(phi),-math.sin(phi))
        taps.append(tuple(checked(ref_round(Q.from_float(y)*32768),16)[0] for y in ref))
    return taps

def independent_twiddles():
    stages=[]
    for stage in range(5):
        span=1<<(stage+1)
        entries=[]
        for k in range(span//2):
            phase=-2*math.pi*k/span
            entries.append(tuple(checked(ref_round(Q.from_float(y)*32768),16)[0] for y in (math.cos(phase),math.sin(phase))))
        stages.append(entries)
    return stages

def oracle_power(i,q):
    return checked(i*i+q*q,46,signed=False)

def oracle_sum40(values):
    assert len(values)==40
    assert all(0<=x<1<<46 for x in values)
    return checked(sum(values),52,signed=False)

def oracle_cfar(cut,training):
    assert 0<=cut<(1<<46) and 0<=training<(1<<52)
    return Q(cut,1)>Q(490007,65536)*Q(training,40)

def immutable_fingerprint(obj):
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

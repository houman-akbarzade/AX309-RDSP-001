"""Pure NumPy floating-point signal-chain reference for AX309 S03.

Contracts: engineering/S02-engineering-contracts-FINAL-PROPOSED-v1.0.md
No claims about RTL, bit-true rounding, hardware, or measured radar performance.
"""
from dataclasses import dataclass
import numpy as np

C = 299792458.0
C_NOMINAL = 300000000.0
FS = 1_000_000.0
FC = 10_000_000_000.0
PRI = .001
L = 16
N = 128
PULSES = 33
FFT_N = 32
B = 250_000.0
TRAIN_OFFSETS = [(dr,db) for dr in range(-3,4) for db in range(-3,4)
                 if abs(dr)>1 or abs(db)>1]
VALID_R = slice(3,110)
VALID_D = slice(3,29)

@dataclass(frozen=True)
class Target:
    delay: int
    velocity: float
    amplitude: complex = 0.18+0j
    phase: float = 0.0

def chirp():
    """16 complex midpoint samples with continuous edge frequencies ±125 kHz."""
    t=(np.arange(L,dtype=float)+.5)/FS
    phase=2*np.pi*((-B/2)*t+(.5*B/(L/FS))*t*t)
    return np.exp(1j*phase)

def matched_filter():
    return np.conjugate(chirp()[::-1])

def noise_variance(target: Target, snr_db: float):
    """SNR based on active echo power, E|w|²=sigma²."""
    return abs(target.amplitude)**2 / (10**(snr_db/10))

def generate_cpi(targets=(),snr_db=None,seed=12345,clutter=None):
    """Deterministic 33x128 float64-complex input. Seed and config must be retained.

    clutter is a complex length-128 stationary range profile, identical across
    pulses. More sophisticated clutter is a separately identified S03 task.
    """
    x=np.zeros((PULSES,N),dtype=np.complex128)
    s=chirp()
    slow=np.arange(PULSES)
    for target in targets:
        k=int(target.delay)
        if not (0<=k<=N-L):raise ValueError("full-echo grid delay required 0..112")
        fd=2*target.velocity*FC/C_NOMINAL
        factor=target.amplitude*np.exp(1j*(2*np.pi*fd*PRI*slow+target.phase))
        x[:,k:k+L]+=factor[:,None]*s[None,:]
    if clutter is not None:
        cl=np.asarray(clutter,dtype=np.complex128)
        if cl.shape!=(N,):raise ValueError("clutter must be stationary 128-complex profile")
        x+=cl[None,:]
    if snr_db is not None:
        if not targets:raise ValueError("SNR requires an echo; use noise_only_cpi()")
        variances=np.array([noise_variance(t,snr_db) for t in targets])
        if not np.allclose(variances,variances[0],rtol=1e-12):
            raise ValueError("target amplitudes must match for common SNR")
        sigma2=float(variances[0])
        rng=np.random.Generator(np.random.PCG64(seed))
        w=np.sqrt(sigma2/2)*(rng.standard_normal(x.shape)+1j*rng.standard_normal(x.shape))
        x=x+w
    return x

def noise_only_cpi(sigma2=1.0,seed=12345):
    rng=np.random.Generator(np.random.PCG64(seed))
    return np.sqrt(sigma2/2)*(rng.standard_normal((PULSES,N))+1j*rng.standard_normal((PULSES,N)))

def quantize_iq(x):
    """Candidate host signed Q1.15 input packing, not FPGA arithmetic model."""
    arr=np.asarray(x)
    xy=np.stack([arr.real,arr.imag],axis=-1)
    rounded=np.rint(xy*32768.0)
    clipped=np.clip(rounded,-32768,32767)
    saturated=int(np.count_nonzero(rounded!=clipped))
    return clipped.astype('<i2').tobytes(order='C'),saturated

def pulse_compress(x):
    """Full linear 143-output MF; extract delay-aligned k=0..127 from q=k+15."""
    a=np.asarray(x,dtype=np.complex128)
    if a.shape!=(PULSES,N):raise ValueError("expected 33 x 128")
    h=matched_filter()
    z=np.array([np.convolve(p,h,mode='full') for p in a])
    assert z.shape==(PULSES,N+L-1)
    return z[:,L-1:L-1+N]

def mti(pc):
    """First difference, 33 pulses to 32 (fixed sign convention)."""
    pc=np.asarray(pc)
    if pc.shape!=(PULSES,N):raise ValueError("MTI expects 33x128")
    return pc[1:]-pc[:-1]

def doppler(mt):
    if np.shape(mt)!=(FFT_N,N):raise ValueError("Doppler expects 32x128")
    return np.fft.fft(mt,n=FFT_N,axis=0).T

def rd_power(dft):
    return np.square(np.abs(dft))

def signed_bins():
    b=np.arange(FFT_N)
    return np.where(b<=15,b,b-32)

def bin_velocity(b, nominal_c=True):
    signed=np.where(np.asarray(b)<=15,np.asarray(b),np.asarray(b)-32)
    return signed*(C_NOMINAL if nominal_c else C)*1/PRI/(2*FC*FFT_N)

def select_peak(power_bins):
    """Deterministic output: max power, signed-bin minimum on exact tie."""
    vals=np.asarray(power_bins)
    if vals.shape!=(FFT_N,):raise ValueError("32 power bins required")
    if not np.all(np.isfinite(vals)) or np.any(vals<0):raise ValueError("nonnegative finite power required")
    maximum=float(np.max(vals))
    ties=np.flatnonzero(vals==maximum)
    chosen=min(ties,key=lambda b:(int(signed_bins()[b]),int(b)))
    if maximum==0:return int(chosen),'NO_VALID_PEAK'
    return int(chosen),'PEAK_TIE' if len(ties)>1 else 'OK'

def cfar_2d(power, alpha=None):
    """Strict 7x7/3x3 CA-CFAR; 2782 valid cells, zero-padded edges NOT used."""
    p=np.asarray(power,dtype=float)
    if p.shape!=(N,FFT_N):raise ValueError("CFAR expects 128x32")
    if np.any(p<0) or not np.all(np.isfinite(p)):raise ValueError("linear finite powers")
    if alpha is None:alpha=40*(.001**(-1/40)-1) # design initializer, NOT calibrated
    valid=np.zeros_like(p,dtype=bool)
    valid[VALID_R,VALID_D]=True
    training=np.zeros_like(p)
    for dr,db in TRAIN_OFFSETS:
        training[3:110,3:29]+=p[3+dr:110+dr,3+db:29+db]
    average=training/len(TRAIN_OFFSETS)
    alarm=valid&(p>float(alpha)*average)
    return alarm,valid,average

def clusters_8(alarm,power):
    """S03 baseline 8-connected clusters, no Doppler wrap; not a mandated RTL partition."""
    a=np.asarray(alarm,bool)
    p=np.asarray(power,float)
    if a.shape!=(N,FFT_N) or p.shape!=a.shape:raise ValueError("cluster shape")
    seen=np.zeros_like(a,bool)
    out=[]
    sb=signed_bins()
    for k,b in np.argwhere(a):
        if seen[k,b]:continue
        stack=[(int(k),int(b))]
        seen[k,b]=True
        cells=[]
        while stack:
            r,d=stack.pop()
            cells.append((r,d))
            for rr in range(max(0,r-1),min(N,r+2)):
                for dd in range(max(0,d-1),min(FFT_N,d+2)):
                    if a[rr,dd] and not seen[rr,dd]:
                        seen[rr,dd]=True
                        stack.append((rr,dd))
        peak=min(cells,key=lambda pair:(-float(p[pair]),int(sb[pair[1]]),pair[0],pair[1]))
        out.append({'range_bin':peak[0],'doppler_bin':peak[1],
                    'velocity_m_s_nominal':float(bin_velocity(peak[1])),
                    'range_m_exact':float(peak[0]*C/(2*FS)),
                    'power_linear':float(p[peak]),'cluster_cells':len(cells)})
    out.sort(key=lambda v:(v['range_bin'],int(signed_bins()[v['doppler_bin']])))
    for i,r in enumerate(out):r['record_id']=i
    return out

def pipeline(iq,alpha=None):
    pc=pulse_compress(iq)
    delta=mti(pc)
    rd=doppler(delta)
    power=rd_power(rd)
    alarm,valid,noise=cfar_2d(power,alpha)
    targets=clusters_8(alarm,power)
    return {'pc':pc,'mti':delta,'doppler':rd,'power':power,
            'cfar':alarm,'valid':valid,'noise_estimate':noise,'targets':targets}

def truth_match(detections,truth):
    """Exhaustive globally optimal matching for small truth sets (S03 reference scorer).

    Optimize cardinality, then sum normalized squared errors, then ID lexicographic.
    Handles three-target baseline; do not use combinatorial implementation for
    arbitrary large truth lists.
    """
    truth=sorted(truth,key=lambda r:r['id'])
    detections=sorted(detections,key=lambda r:r['record_id'])
    dr_gate=2*C_NOMINAL/(2*FS)
    dv_gate=C_NOMINAL/(2*FC*FFT_N*PRI)
    candidates=[]
    for t in truth:
        edges=[]
        for d in detections:
            dr=abs(float(t['range_m_nominal'])-d['range_bin']*C_NOMINAL/(2*FS))
            dv=abs(float(t['velocity_m_s'])-d['velocity_m_s_nominal'])
            if dr<=dr_gate and dv<=dv_gate:
                edges.append((d['record_id'],(dr/dr_gate)**2+(dv/dv_gate)**2))
        candidates.append(edges)
    best=None
    def rec(i,chosen,used,cost):
        nonlocal best
        if i==len(truth):
            rank=(-len(chosen),round(cost,12),tuple(chosen))
            if best is None or rank<best[0]:best=(rank,list(chosen))
            return
        rec(i+1,chosen,used,cost)
        for did,c in candidates[i]:
            if did not in used:
                rec(i+1,chosen+[(truth[i]['id'],did)],used|{did},cost+c)
    rec(0,[],set(),0.)
    return best[1]

def separation_metrics(detections,truth):
    pairs=truth_match(detections,truth)
    return {'matched':len(pairs),'missed':len(truth)-len(pairs),
            'false':len(detections)-len(pairs),'pairs':pairs}

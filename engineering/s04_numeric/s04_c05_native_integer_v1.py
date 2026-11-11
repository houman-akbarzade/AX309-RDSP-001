"""AX309 S04-C05 native exact integer power, CFAR and 8-connected grouping.

No numpy, Float, C02 model helpers, stochastic CPI or architecture selection.
Signed-bin tie rules copied as a *contract* from frozen S03, implemented natively.
Output engineering physical units are rational (Fraction), not floating-point.
"""
from fractions import Fraction
from collections import deque
from hashlib import sha256
import json

NR=128
ND=32
CUT_R=range(3,110)
CUT_D=range(3,29)
ALPHA_N=490007
ALPHA_DEN=65536
GEO=tuple((dr,dd) for dr in range(-3,4) for dd in range(-3,4) if abs(dr)>1 or abs(dd)>1)
assert len(GEO)==40
def limit(x,w):
    if not isinstance(x,int) or x<0:raise ValueError('unsigned nonnegative integer required')
    hi=(1<<w)-1
    return (min(hi,x),x>hi)

def checked_sqpower(pair):
    i,q=pair
    if not isinstance(i,int) or not isinstance(q,int):raise TypeError('integer IQ')
    lo=-(1<<24);hi=(1<<24)-1
    if not lo<=i<=hi or not lo<=q<=hi:raise ValueError('signed 25-bit FFT IQ out of contract')
    total=i*i+q*q
    assert 0<=total<(1<<51)
    stored,clip=limit(total,46)
    return stored,clip,{'raw':total,'i_square':i*i,'q_square':q*q,
          'raw_width':51,'word_width':46,'input_I':i,'input_Q':q}

def native_power_map(rd):
    if len(rd)!=NR or any(len(row)!=ND for row in rd):raise ValueError('128x32 required')
    power=[];events=[]
    for r,row in enumerate(rd):
        dst=[]
        for b,pair in enumerate(row):
            stored,clip,trace=checked_sqpower(pair)
            if clip:events.append({'site':'POWER','range':r,'doppler_bin':b,
                'integer_pre_narrow':str(trace['raw']),'limited':stored,'word_bits':46})
            dst.append(stored)
        power.append(dst)
    return power,events

def checked_train(power,r,d):
    if not (r in CUT_R and d in CUT_D):raise ValueError('invalid CUT')
    vals=[power[r+dr][d+dd] for dr,dd in GEO]
    assert len(vals)==40
    if any((not isinstance(v,int) or not 0<=v<(1<<46)) for v in vals):
        raise ValueError('bad stored U46.30 power')
    total=sum(vals)
    assert total <(1<<52) # full sum of 40 U46 cannot overflow U52
    return total,{'training_cell_count':40,'raw_integer':str(total),'word_bits':52}

def compare(cut,training):
    if not 0<=cut<(1<<46) or not 0<=training<(1<<52):raise ValueError('bad U power')
    left=40*cut*ALPHA_DEN
    right=ALPHA_N*training
    assert left<(1<<68) and right<(1<<72)
    return left>right,left-right

def native_cfar(power):
    if len(power)!=NR or any(len(x)!=ND for x in power):raise ValueError('128x32')
    mask=[[False]*ND for _ in range(NR)]
    detail=[]
    for r in CUT_R:
        for d in CUT_D:
            train,trace=checked_train(power,r,d)
            hit,delta=compare(power[r][d],train)
            mask[r][d]=hit
            detail.append({'range':r,'doppler_bin':d,'Pcut':power[r][d],
              'SUM40':train,'signed_unbounded_margin':str(delta),'alarm':hit})
    assert len(detail)==2782
    return mask,detail

def signed_bin(d):
    return d if d<=15 else d-32

def _neighbors8(r,d):
    # Range/Doppler nonwrapped. Unique neighbors ascending r then d.
    for rr in range(max(0,r-1),min(NR-1,r+1)+1):
        for dd in range(max(0,d-1),min(ND-1,d+1)+1):
            if (rr,dd)!=(r,d):yield (rr,dd)

def native_clusters(mask,power):
    if len(mask)!=NR or len(power)!=NR or any(len(a)!=ND or len(b)!=ND for a,b in zip(mask,power)):
        raise ValueError('128x32')
    seen=set()
    records=[]
    for r in range(NR):
        for d in range(ND):
            if not mask[r][d] or (r,d) in seen:continue
            todo=deque([(r,d)]);seen.add((r,d));members=[]
            while todo:
                point=todo.popleft();members.append(point)
                for rr,dd in _neighbors8(*point):
                    if mask[rr][dd] and (rr,dd) not in seen:
                        seen.add((rr,dd));todo.append((rr,dd))
            # Exact priority contract: maximum *stored integer* power;
            # minimum signed-Doppler on equal power; then min range/bin.
            peak=min(members,key=lambda cell:(-power[cell[0]][cell[1]],
                signed_bin(cell[1]),cell[0],cell[1]))
            rpeak,dpeak=peak
            tied=sum(power[rr][dd]==power[rpeak][dpeak] for rr,dd in members)
            records.append({'range_bin':rpeak,'doppler_bin':dpeak,
                'signed_doppler_bin':signed_bin(dpeak),
                'power_stored_integer':power[rpeak][dpeak],
                'cluster_cells':len(members),
                'tie_flag':tied>1,'max_equal_power_cells':tied,
                'record_id':-1,
                'range_m_exact_rational':[rpeak*299792458,2*1000000],
                'velocity_m_s_nominal_rational':[signed_bin(dpeak)*300000000,
                  2*10000000000*32//1000]})
    records.sort(key=lambda a:(a['range_bin'],a['signed_doppler_bin']))
    for idx,record in enumerate(records):record['record_id']=idx
    return records

def complete_map(rd):
    power,power_events=native_power_map(rd)
    mask,cut_records=native_cfar(power)
    clusters=native_clusters(mask,power)
    return {'power':power,'power_events':power_events,'mask':mask,
            'cut_records':cut_records,'clusters':clusters}

"""S04 C05 selected-C native power/CFAR/grouping deterministic qualification.

Independent C03 exact arithmetic power/CFAR oracle; independent component
reference uses separate union-find, never calls native clustering helpers.
S03 Float only for independent historic mismatch diagnosis.
"""
import sys,json,math,hashlib
from pathlib import Path
from fractions import Fraction as F
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
from s03_reference import model as S03
import s04_c05_native_integer_v1 as NAT
import s04_c03_independent_oracle_v1 as OR
import s04_c02_integer_maps_v06 as DUT
PRE=json.loads((ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json').read_text())
TYPES=DUT.KINDS
assert len(TYPES)==9
SHIFTS=(0,1,0,1,1)

def independent_components(mask,powers):
    # Independent union-find connected-component oracle, distinct from native BFS.
    points=[(r,b) for r in range(128) for b in range(32) if mask[r][b]]
    parent={point:point for point in points}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]
            x=parent[x]
        return x
    def unite(a,b):
        a=find(a);b=find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    P=set(points)
    for r,b in points:
        for dr,dd in ((-1,-1),(-1,0),(-1,1),(0,-1)):
            node=(r+dr,b+dd)
            if node in P:unite((r,b),node)
    groups={}
    for cell in points:groups.setdefault(find(cell),[]).append(cell)
    # Sorting by tuple gives a separately implemented tie rule.
    ans=[]
    for members in groups.values():
        vmax=max(powers[r][b] for r,b in members)
        tied=[(r,b) for r,b in members if powers[r][b]==vmax]
        p=min(tied,key=lambda z:(z[1] if z[1]<=15 else z[1]-32,z[0],z[1]))
        ans.append({'range_bin':p[0],'doppler_bin':p[1],'cluster_cells':len(members),
                    'power_stored_integer':vmax,'tie_flag':len(tied)>1,
                    'max_equal_power_cells':len(tied)})
    ans.sort(key=lambda x:(x['range_bin'],x['doppler_bin'] if x['doppler_bin']<=15 else x['doppler_bin']-32))
    return ans

def fingerprint(p):
    return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def one(g,kind):
    src,iq,tel=DUT.source_vector(kind,g)
    ref=S03.pipeline(src,alpha=7.476912055027923)
    result=DUT.run_one(src,iq,tel,'C_hypothetical',SHIFTS,g,capture_maps=True)
    old=result['captured']
    out=NAT.complete_map(old['rd_iq_integer'])
    power,mask=out['power'],out['mask']
    assert power==old['power_integer'],('power mismatch',g,kind)
    golden_cut={(r,b):(bool(hit),int(delta),int(cut),int(train))
                for r,b,hit,delta,cut,train in old['cut_records']}
    assert len(golden_cut)==2782
    assert len(out['cut_records'])==2782
    for c in out['cut_records']:
        k=(c['range'],c['doppler_bin'])
        t=golden_cut[k]
        assert (c['alarm'],int(c['signed_unbounded_margin']),c['Pcut'],c['SUM40'])==t,(g,kind,k)
        # independent Fraction oracle from S04-C03:
        assert c['alarm']==OR.oracle_cfar(c['Pcut'],c['SUM40'])
    assert all(mask[r][d]==golden_cut[(r,d)][0] for r in range(3,110) for d in range(3,29))
    parent=independent_components(mask,power)
    native=out['clusters']
    assert len(parent)==len(native),(g,kind,'clusters',len(parent),len(native))
    for k,(a,b) in enumerate(zip(parent,native)):
        for key in ('range_bin','doppler_bin','cluster_cells','power_stored_integer','tie_flag','max_equal_power_cells'):
            assert a[key]==b[key],(g,kind,k,key,a[key],b[key])
        assert b['record_id']==k
    oldkey=f'g{g}:{kind}|C_hypothetical:DISTRIBUTED_3'
    oldv=PRE['all_run_metrics'][oldkey]
    original_P=np.abs(S03.doppler(S03.mti(S03.pulse_compress(src))))**2
    ref_alarm,valid,_=S03.cfar_2d(original_P,alpha=7.476912055027923)
    change=int(np.logical_xor(ref_alarm,np.asarray(mask,dtype=bool))[valid].sum())
    assert change==oldv['cut_changed_count'],(g,kind,'cut mismatch',change,oldv['cut_changed_count'])
    reference_peaks=[(x['range_bin'],x['doppler_bin']) for x in oldv['Float_host_cluster_peak_records_reference']]
    fixed_peaks=[(x['range_bin'],x['doppler_bin']) for x in oldv['Float_host_cluster_peak_records_on_fixed']]
    fixed_native_peaks=[(x['range_bin'],x['doppler_bin']) for x in native[:20]]
    assert fixed_native_peaks==fixed_peaks,(g,kind,'native vs host',fixed_native_peaks,fixed_peaks)
    issue=None
    if reference_peaks!=fixed_native_peaks:
        assert kind=='phase_interference' and g in (1,5)
        assert change==0
        # Investigate exact integer winner on Doppler 20 at range 3 vs range 4.
        winner=(native[0]['range_bin'],native[0]['doppler_bin'])
        p3=power[3][20];p4=power[4][20]
        f3=float(original_P[3,20]);f4=float(original_P[4,20])
        assert winner==(4,20) and p4>p3 and f3==f4,(g,p3,p4,f3,f4)
        issue={'v06_vector_id':f'g{g}:phase_interference','reference_peaks':reference_peaks,
            'native_peaks':fixed_native_peaks,
            'reference_exact_peak_competitors':{'r3_b20':f3,'r4_b20':f4,'float_delta_r3_minus_r4':f3-f4,'float_reference_exact_tie':f3==f4},
            'integer_peak_competitors':{'r3_b20':p3,'r4_b20':p4,'delta_r4_minus_r3':p4-p3},
            'same_CFAR_alarm_mask':True,'independent_grouping_matches_S03_host_on_fixed':True,
            'cause':'rounded/quantized FFT power reverses ordering of two exactly tied Float-reference maxima (S03 tie picks lower range), while 8-neighbor grouping, mask, and tie rule agree; not an equal-integer-power tie',
            'decision':'Native integer peak must use maximum STORED U46.30 power and signed-Doppler then range tie order. Difference relative to S03 Float original-input power is a numerical quantization change, not bit-true implementation mismatch; retain as open end-to-end Float/Fixed numeric acceptance for C06; no threshold or waiver approved.'}
    return {'vector_id':f'g{g}:{kind}','g':g,'kind':kind,
        'power_bin_count':4096,'cut_count':2782,'power_overflow_events':len(out['power_events']),
        'internal_overflow_events_from_DUT':result['overflow']['total'],
        'input_saturation_events':tel.summary()['total'],
        'native_alarm_count':sum(x['alarm'] for x in out['cut_records']),
        'changed_CFAR_CUT_vs_S03_Float':change,
        'native_cluster_count':len(native),
        'reference_cluster_count':len(ref['targets']),
        'cluster_match_independent_union_find':True,
        'native_target_records':native[:20],
        'native_vs_Float_reference_peak_difference':bool(issue),
        'reproduced_peak_issue':issue,
        'power_raw_SHA256':fingerprint(power),
        'mask_SHA256':fingerprint(mask),
        'native_target_record_SHA256':fingerprint(native),
        'oracle_complete_power_CUT_grouping':'PASS'}
def run():
    rows=[one(g,k) for g in (1,5) for k in TYPES]
    issues=[r['reproduced_peak_issue'] for r in rows if r['reproduced_peak_issue']]
    assert len(rows)==18 and len(issues)==2
    assert [x['v06_vector_id'] for x in issues]==['g1:phase_interference','g5:phase_interference']
    out={'project':'AX309-RDSP-001','version':'S04-C05-integrated-v1.0',
        'status':'INDEPENDENT_NESTED_ORACLE_DETERMINISTIC_NO_STAT_CPI',
        'architecture':'C','fft_shifts':list(SHIFTS),
        'vector_count':18,'power_bins_compared':18*4096,
        'CFAR_CUTs_compared':18*2782,'all_cases':rows,
        'v06_discrepancies':issues,'v06_discrepancies_count':len(issues),
        'native_grouping':'NATIVE_INTEGER_IMPLEMENTED_AND_COMPARED_TO_INDEPENDENT_UNION_FIND',
        'Float_vs_fixed_mismatch_is_not_automatically_waived':True,
        'REQ_SCR_01':'OPEN','REQ_RNG_03':'OPEN','statistics':'NOT_EXECUTED',
        'no_accepted_seeds':True,'no_RTL_or_FPGA':True}
    f=ROOT/'engineering/s04_numeric/S04-C05-integrated-power-cfar-grouping-v1.0.json'
    f.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('C05',len(rows),'CASES','POWER',out['power_bins_compared'],'CUTS',out['CFAR_CUTs_compared'],
        'DISCREPANCIES',len(issues),'SHA',hashlib.sha256(f.read_bytes()).hexdigest(),flush=True)
    for issue in issues:print(json.dumps(issue,sort_keys=True),flush=True)
if __name__=='__main__':run()

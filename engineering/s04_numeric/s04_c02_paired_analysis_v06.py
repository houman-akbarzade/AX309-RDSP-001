"""S04 C02 v0.6 paired deterministic architecture and full RD/CFAR audit.

Reuses exact integer datapath in derived s04_c02_integer_maps_v06.py. No
statistical CPI, no accepted S03 seeds, no new target/clutter model, no RTL.
"""
import json,sys,hashlib,math,datetime,itertools
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c02_integer_maps_v06 as I
from s03_reference import model as S03
PREVIOUS=json.loads((ROOT/'engineering/s04_numeric/S04-C02-deterministic-integer-prototype-v0.5.json').read_text())
VECTORS=json.loads((ROOT/'engineering/s04_numeric/S04-C02-deterministic-test-vectors-v0.5.json').read_text())
BUCKET={'A':'A','B':'B','C_hypothetical':'C'}
ARCHS=('A','B','C_hypothetical')
SCHEDULES=('ZERO','EARLY_3','DISTRIBUTED_3','ALL_5')
ALPHA_REF=float(json.loads((ROOT/'decisions/S02-C-CFAR-02-v1.2-approved-amendment.json').read_text())['alpha_frozen'])
FALPHA={'A':(490007,16),'B':(30625,12),'C_hypothetical':(490007,16)}
GEOM=[(r,b) for r in range(3,110) for b in range(3,29)]
assert len(GEOM)==2782
def digest_array(a):
    arr=np.ascontiguousarray(a)
    return hashlib.sha256(arr.tobytes()).hexdigest()
def rms_error(a,b):
    diff=np.asarray(a)-np.asarray(b)
    return {'MAX':float(np.max(np.abs(diff))),
            'RMS':float(np.sqrt(np.mean(np.abs(diff)**2)))}
def error_stats(values):
    a=np.asarray(values,dtype=np.float64)
    return {'MAX':float(np.max(a)),'RMS':float(np.sqrt(np.mean(a*a))),
            'COUNT':int(a.size)}
def cfar_float_at_alpha(p,alpha):
    valid=np.zeros((128,32),bool)
    valid[3:110,3:29]=True
    alarm=np.zeros_like(valid)
    for r,b in GEOM:
        training=sum(float(p[r+dr,b+db]) for dr,db in S03.TRAIN_OFFSETS)
        alarm[r,b]=float(p[r,b])>alpha*training/40
    return alarm
def reference_cfar(p):
    alarm,valid,avg=S03.cfar_2d(p,alpha=ALPHA_REF)
    assert valid.sum()==2782
    return alarm,valid,avg
def fixed_map(run,arch,schedule,g):
    raw=np.asarray(run['captured']['power_integer'],dtype=np.int64)
    # raw value fits within int64 under tested stimulus; avoid overflow in casting
    assert max(max(row) for row in run['captured']['power_integer']) < 2**62
    W,F=I.V04['summaries'][arch]['candidate_formats']['fft']
    S=1<<sum(I.DATA['schedules'][schedule]['shifts'])
    power=raw.astype(np.float64)*(float(g*S)/(1<<F))**2
    iq=I.complex_float_matrix(run['captured']['rd_iq_integer'],F,g*S)
    mask=np.zeros((128,32),bool)
    positions=[]
    for r,b,decision,margin,CUT,SUM in run['captured']['cut_records']:
        assert 3<=r<110 and 3<=b<29
        mask[r,b]=bool(decision)
        positions.append((r,b))
    assert positions==GEOM
    return power,iq,mask,raw
def check_same_vector(profile,kind,g):
    key=f'g{g}:{kind}'
    assert key in VECTORS['patterns']
    # vector digest computed by v05 evidence includes g scaling only in key, rational stored pattern same.
    import hashlib
    h=hashlib.sha256()
    for p in range(33):
        for r in range(128):
            a,b=I.vector_value(kind,p,r)
            h.update(f'{p},{r},{a.numerator}/{a.denominator},{b.numerator}/{b.denominator}\n'.encode())
    assert h.hexdigest()==VECTORS['patterns'][key]['rational_source_vector_sha256']
    return h.hexdigest()
def one_case(g,profile,kind):
    source,iq,inp=I.source_vector(kind,g)
    ref_MF=S03.pulse_compress(source)
    ref_MT=S03.mti(ref_MF)
    ref_RD=S03.doppler(ref_MT)
    ref_P=np.abs(ref_RD)**2
    ref_alarm,valid,ref_mean=reference_cfar(ref_P)
    ref_clusters=S03.clusters_8(ref_alarm,ref_P)
    valid_indices=np.where(valid)
    vid=check_same_vector(profile,kind,g)
    runs={}
    for arch in ARCHS:
        for sched in SCHEDULES:
            full_key=f'{arch}:{sched}'
            run=I.run_one(source,iq,inp,arch,I.DATA['schedules'][sched]['shifts'],g,capture_maps=True)
            assert run['cfar_valid_cut_count']==2782
            prev_case=next(x for x in PREVIOUS['per_option_schedule'][full_key]['cases']
                           if x['kind']==kind and x['input_profile']==profile)
            assert run['overflow']['counts']==prev_case['saturation']['counts'],(full_key,g,kind)
            power,fft,mask,raw=fixed_map(run,arch,sched,g)
            # Note clusters_8 is S03 Float *host postprocessor* only, NOT integer-native cluster bittrue.
            host_clusters=S03.clusters_8(mask,power)
            fixed_training_margin={}
            alpha_n,fa=FALPHA[arch]
            alpha_q=alpha_n/(1<<fa)
            ref_aq=cfar_float_at_alpha(ref_P,alpha_q)
            fixed_a_float=cfar_float_at_alpha(power,ALPHA_REF)
            fixed_a_q_float=cfar_float_at_alpha(power,alpha_q)
            # S03 Float CFAR may have order-of-operation last-bit discrepancies in ties.
            mismatch=np.logical_xor(mask,ref_alarm)&valid
            rising=np.logical_and(mask,~ref_alarm)&valid
            falling=np.logical_and(~mask,ref_alarm)&valid
            diff_points=np.argwhere(mismatch)
            details=[]
            for r,b in diff_points:
                r=int(r);b=int(b)
                j=GEOM.index((r,b))
                rec=run['captured']['cut_records'][j]
                tr=sum(float(ref_P[r+dr,b+db]) for dr,db in S03.TRAIN_OFFSETS)
                ref_margin=float(ref_P[r,b]-ALPHA_REF*tr/40)
                fp_tr=sum(float(power[r+dr,b+db]) for dr,db in S03.TRAIN_OFFSETS)
                fixed_margin=float(power[r,b]-alpha_q*fp_tr/40)
                # margin in original source power units; exact integer arithmetic margin stored also kept.
                details.append({'range':r,'doppler':b,
                    'float_alarm':bool(ref_alarm[r,b]),'integer_alarm':bool(mask[r,b]),
                    'direction':'0_to_1' if rising[r,b] else '1_to_0',
                    'float_threshold_margin_original_power':ref_margin,
                    'fixed_threshold_margin_original_power':fixed_margin,
                    'integer_raw_comparator_margin':str(rec[3]),
                    'fixed_CUT_stored':str(rec[4]),'fixed_SUM40_stored':str(rec[5])})
            stats={
                'profile':profile,'g':g,'kind':kind,'vector_id':f'g{g}:{kind}',
                'source_vector_SHA256':vid,
                'has_input_saturation':inp.summary()['total']>0,
                'input_component_saturations':inp.summary()['total'],
                'internal_event_count':run['overflow']['total'],
                'internal_event_by_site':run['overflow']['counts'],
                'first_internal_overflow':run['overflow']['first_24'][0] if run['overflow']['first_24'] else None,
                'first_input_overflow':inp.summary()['first_24'][0] if inp.summary()['first_24'] else None,
                'overflow_digest':run['overflow']['all_event_order_sha256'],
                'conditional_bound_eligible':inp.summary()['total']==0 and run['overflow']['total']==0,
                'stage_error':run['metrics'],
                'FFT_bin_error':rms_error(fft,ref_RD),
                'power_map_error':rms_error(power,ref_P),
                'power_map_sha256_float64':digest_array(power.astype('<f8')),
                'power_raw_integer_map_sha256':hashlib.sha256(
                    b''.join(f'{x}\n'.encode() for row in run['captured']['power_integer'] for x in row)).hexdigest(),
                'cfar_full_mask_sha256':digest_array(mask.astype(np.uint8)),
                'cut_changed_count':int(mismatch.sum()),
                'cut_direction_0_to_1':int(rising.sum()),
                'cut_direction_1_to_0':int(falling.sum()),
                'cut_mismatches_all':details,
                'reference_CUT_count':2782,
                'integer_CFAR_alarms':int(mask.sum()),
                'Float_S03_CFAR_alarms':int(ref_alarm.sum()),
                'alpha_real_reference':ALPHA_REF,
                'alpha_candidate_rational':[alpha_n,fa],
                'alpha_abs_difference':abs(alpha_q-ALPHA_REF),
                'reference_alpha_only_changed_CUT':int(np.logical_xor(ref_aq,ref_alarm)[valid].sum()),
                'fixed_power_alpha_only_changed_CUT':int(np.logical_xor(fixed_a_q_float,fixed_a_float)[valid].sum()),
                'integer_vs_same_power_float_qalpha_changed_CUT':int(np.logical_xor(mask,fixed_a_q_float)[valid].sum()),
                'Float_S03_reference_clusters_count':len(ref_clusters),
                'Float_host_clusters_on_fixed_mask_count':len(host_clusters),
                'Float_host_cluster_peak_records_reference':ref_clusters[:20],
                'Float_host_cluster_peak_records_on_fixed':host_clusters[:20],
                'integer_native_clustering_status':'OPEN_NOT_IMPLEMENTED',
                'full_cluster_bittrue_match':'OPEN',
                'no_stochastic_CPI':True}
            runs[full_key]={'stats':stats,'fft_bin_abs_error':np.abs(fft-ref_RD)}
    assert len(runs)==12
    return runs
def aggregate_metrics(cases,mask_key):
    # each case has same sample count for given stage. Pool RMS properly.
    import math
    if not cases:return {'cases':0,'MAX':None,'RMS':None,'samples':0}
    maxi=max(c['stage_error'][mask_key]['MAX'] for c in cases)
    n=sum(c['stage_error'][mask_key]['samples'] for c in cases)
    s=sum(c['stage_error'][mask_key]['RMS']**2*c['stage_error'][mask_key]['samples'] for c in cases)
    return {'cases':len(cases),'MAX':maxi,'RMS':math.sqrt(s/n),'samples':n}
def build():
    report={'project':'AX309-RDSP-001','version':'v0.6',
     'status':'PAIRED_DETERMINISTIC_COMPARISON_UNAPPROVED',
     'common_scope':'All 12 candidate/schedule combinations use exactly same named rational source vector in each approved g scalar',
     'profiles':{'g1':'lab-reference scaling only','g5':'noise-only scaling only; deterministic patterns not noise population draws'},
     'all_vector_ids':[f'g{g}:{kind}' for g in (1,5) for kind in I.KINDS],
     'sample_count_each':{'complex_source':33*128,'complex_RD':128*32,'CUT_valid':2782},
     'all_run_metrics':{},'pairwise_per_vector':{},'paired_summary':{},
     'common_set_ids':[],'excluded_from_common_detailed':[],
     'native_integer_clustering':'OPEN_NOT_IMPLEMENTED',
     'Float_host_clustering':'S03.clusters_8 used only as diagnostic, no native bittrue claim',
     'C01':'PASS_BOUNDED','C02':'OPEN','Gate_S04':'OPEN',
     'REQ_SCR_01':'BINDING_OPEN','REQ_RNG_03':'BINDING_OPEN',
     'forbidden_actions_not_performed':['statistical main CPI','S03 accepted seeds','RTL','synthesis','FPGA']}
    grouped={f'{arch}:{sc}':[] for arch in ARCHS for sc in SCHEDULES}
    per_vector_runs={}
    for g,profile in ((1,'SINGLE_TARGET_REFERENCE_LIKE_LAB'),(5,'NOISE_ONLY_UNIT')):
       for kind in I.KINDS:
          vid=f'g{g}:{kind}'
          d=one_case(g,profile,kind)
          per_vector_runs[vid]=d
          for k,x in d.items():
             stat=x['stats']
             grouped[k].append(stat)
             report['all_run_metrics'][f'{vid}|{k}']=stat
          print('VECTOR',vid,'total runs',len(d),'CFAR mismatches',sum(x['stats']['cut_changed_count'] for x in d.values()),flush=True)
    # Common no-saturation intersection, not architecture-specific denominator.
    for vid,d in per_vector_runs.items():
        reasons=[]
        for k,v in d.items():
            st=v['stats']
            if st['has_input_saturation']: reasons.append({'candidate':k,'reason':'INPUT_SATURATION','count':st['input_component_saturations']})
            if st['internal_event_count']: reasons.append({'candidate':k,'reason':'INTERNAL_OVERFLOW_OR_SATURATION','count':st['internal_event_count']})
        if reasons: report['excluded_from_common_detailed'].append({'vector_id':vid,'reasons':reasons})
        else:report['common_set_ids'].append(vid)
    common=set(report['common_set_ids'])
    assert len(common)==14,(len(common),report['excluded_from_common_detailed'])
    report['denominators']={'all_vectors_per_architecture':18,'common_no_saturation_per_architecture':14,
       'g1_all':9,'g1_common':7,'g5_all':9,'g5_common':7,
       'source_complex_per_vector':4224,'RD_complex_per_vector':4096}
    for k,cases in grouped.items():
       per_g={}
       for g in (1,5):
          rows=[x for x in cases if x['g']==g]
          accepted=[x for x in rows if x['vector_id'] in common]
          per_g[str(g)]={'all_vector_ids':[x['vector_id'] for x in rows],
            'common_vector_ids':[x['vector_id'] for x in accepted],
            'all_cases':{stage:aggregate_metrics(rows,stage) for stage in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5')},
            'common_cases':{stage:aggregate_metrics(accepted,stage) for stage in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5')},
            'total_input_saturations_all_cases':sum(x['input_component_saturations'] for x in rows),
            'total_internal_events_all_cases':sum(x['internal_event_count'] for x in rows),
            'total_CFAR_cut_changes_all_cases':sum(x['cut_changed_count'] for x in rows),
            'total_CFAR_cut_changes_common_cases':sum(x['cut_changed_count'] for x in accepted),
            'total_alpha_only_reference_changes_all_cases':sum(x['reference_alpha_only_changed_CUT'] for x in rows),
            'total_native_cluster_matches':None}
       report['paired_summary'][k]=per_g
    # per-cell paired error difference; full 66 pairs, all 18 vector IDs
    keys=sorted(grouped)
    for key_a,key_b in itertools.combinations(keys,2):
      pair=f'{key_a}__VS__{key_b}'
      rows=[]
      for vid,d in per_vector_runs.items():
        A=d[key_a];B=d[key_b]
        ea=A['fft_bin_abs_error'];eb=B['fft_bin_abs_error']
        assert ea.shape==eb.shape==(128,32)
        delta=ea-eb
        stat_a=A['stats'];stat_b=B['stats']
        stages={stage:{
          'MAX_error_A_minus_B':stat_a['stage_error'][stage]['MAX']-stat_b['stage_error'][stage]['MAX'],
          'RMS_error_A_minus_B':stat_a['stage_error'][stage]['RMS']-stat_b['stage_error'][stage]['RMS']}
          for stage in ('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5')}
        rows.append({'vector_id':vid,'common_no_saturation':vid in common,
           'stagewise_paired_deltas_original_float_amplitude':stages,
           'FFT5_per_bin_paired_error_A_minus_B':{
             'mean':float(np.mean(delta)),'max_signed':float(np.max(delta)),
             'min_signed':float(np.min(delta)),
             'A_smaller_count':int(np.sum(delta<0)),
             'B_smaller_count':int(np.sum(delta>0)),
             'equal_count':int(np.sum(delta==0))},
           'CFAR_changed_CUT_count_A_minus_B':stat_a['cut_changed_count']-stat_b['cut_changed_count'],
           'integer_CFAR_alarm_count_A_minus_B':stat_a['integer_CFAR_alarms']-stat_b['integer_CFAR_alarms'],
           'internal_events_A_minus_B':stat_a['internal_event_count']-stat_b['internal_event_count']})
      report['pairwise_per_vector'][pair]=rows
    ckey='C_hypothetical:DISTRIBUTED_3'
    comparisons={}
    for alt in ('A:DISTRIBUTED_3','B:DISTRIBUTED_3'):
      pair='__VS__'.join(sorted((ckey,alt)))
      assert pair in report['pairwise_per_vector']
      records=report['pairwise_per_vector'][pair]
      comparisons[alt]={'paired_key':pair,'common_count':sum(x['common_no_saturation'] for x in records),
        'all_count':len(records),
        'interpretation':'no engineering rank; matched deterministic vectors only'}
    report['hypothesis_C_distributed_3']=comparisons
    out=ROOT/'engineering/s04_numeric/S04-C02-paired-architecture-analysis-v0.6.json'
    out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('OUTPUT',out,'SHA256',hashlib.sha256(out.read_bytes()).hexdigest(),
      'runs',len(report['all_run_metrics']),'paired vector comparisons',sum(map(len,report['pairwise_per_vector'].values())),
      'common',len(report['common_set_ids']))
    return report
if __name__=='__main__':build()

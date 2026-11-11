"""One-shot, narrowly authorized S04-C06 A-E numeric qualification.

Exactly the 16 prelocked C01-profile input files, no generator or seed access.
The previous diagnostic runner stays locked. This reviewed authorization wrapper
validates frozen identities before enabling the exact same ENGINE + Recorder.
Never retries a CPI, changes C arithmetic, changes alpha, or runs statistical CPI.
"""
from __future__ import annotations
import hashlib, json, math, os, platform, sys, traceback
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
from s03_reference import model as S03
import s04_c06_final_runner_v1 as BASE
import s04_c04_selected_C_stage_capture_v1 as ENG
import s04_c03_independent_oracle_v1 as OR
import s04_c04_fullchain_qualification_v1 as CHAIN_ORACLE
import s04_c05_native_integer_v1 as NATIVE
import s04_c05_integrated_qualification_v1 as GROUP_ORACLE
import s04_c06_fulltrace_capture_v1 as TRACE
from fractions import Fraction as F

PACKAGE=ROOT/'engineering/S04-C06-16CPI-EXECUTION-DECISION-PACKAGE-v1.0.json'
MANIFEST=ROOT/'engineering/s04_numeric/c06_16cpi_inputs_v1/C06-16CPI-INPUT-MANIFEST-v1.0.json'
OUT=ROOT/'engineering/s04_numeric/c06_16cpi_qualification_v1'
PACKAGE_SHA='da5d758601cdd3569401be29f473895e87a1cfbdff960e6eed54186f909d8b7d'
MANIFEST_SHA='59365ab6aadb1e2c9203415fe5f5b48b4d3298c9d9cb31c4c649f621ecadddb1'
FROZEN_RUNNER_SHA='351209f907bff42d4435c2c1a9243634d2c1d20d38c2fba2d5efff9a608c4a27'
C_CAP={1:dict(zip(('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5'),
 (.00074,.00147,.00468,.01286,.03267,.07926,.18636))),
 5:dict(zip(('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5'),
 (.00366,.00731,.02337,.06428,.16335,.39629,.93177)))}
ALPHA_FLOAT=7.476912055027923
ALPHA_FIXED=F(490007,65536)
R_KEYS=('MF','MTI','FFT1','FFT2','FFT3','FFT4','FFT5')
SIDES={'NOISE_ONLY_UNIT':5,'SINGLE_TARGET_REFERENCE_LIKE_LAB':1}
def sha_bytes(data):return hashlib.sha256(data).hexdigest()
def sha(path):return sha_bytes(Path(path).read_bytes())
def save(path,obj):
    p=Path(path);temp=p.with_suffix(p.suffix+'.partial')
    data=(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    with temp.open('xb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    temp.replace(p)
def canonical(o):return json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def arrcode(data):
    a=np.asarray(data,dtype=np.int64)
    if a.shape[-1]!=2:raise AssertionError('expected IQ pair dimension')
    return a
def cplx(data,g,cum=0):
    a=arrcode(data)
    return (a[...,0].astype(float)+1j*a[...,1].astype(float))* (g*(1<<cum)/32768)
def stats(actual,ref):
    a=np.asarray(actual);b=np.asarray(ref);diff=np.abs(a-b)
    if a.shape!=b.shape:raise AssertionError(('stage shape mismatch',a.shape,b.shape))
    return {'MAX':float(diff.max()),'RMS':float(np.sqrt(np.mean(diff**2))),
            'complex_samples':int(diff.size),'signed_I_MAX':float(np.max(np.abs((a-b).real))),
            'signed_Q_MAX':float(np.max(np.abs((a-b).imag)))}
def check_shapes(result):
    c=result['captured']
    if np.asarray(c['mf']).shape!=(33,128,2):raise AssertionError('MF shape')
    if np.asarray(c['mti']).shape!=(32,128,2):raise AssertionError('MTI shape')
    for j in range(5):
        if np.asarray(c['fft_stages_range_major'][j]).shape!=(128,32,2):
            raise AssertionError(('FFT shape',j))
    if np.asarray(c['rd']).shape!=(128,32,2):raise AssertionError('RD shape')

def validate_package():
    if sha(PACKAGE)!=PACKAGE_SHA or sha(MANIFEST)!=MANIFEST_SHA:raise PermissionError('locked package/manifest SHA mismatch')
    pack=json.loads(PACKAGE.read_text());inputm=json.loads(MANIFEST.read_text())
    if sha(ROOT/pack['runner'])!=FROZEN_RUNNER_SHA or pack['runner_sha256']!=FROZEN_RUNNER_SHA:
        raise PermissionError('original approved runner changed')
    for f,digest in pack['oracle_versions'].items():
        if sha(ROOT/f)!=digest:raise PermissionError('frozen oracle changed: '+f)
    if sha(ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json')!=pack['selected_contract_sha256']:
        raise PermissionError('selected C numeric contract changed')
    if (pack['fft_shifts']!=[0,1,0,1,1] or pack['architecture']!='C'
       or pack['denominators']!={'noise_only':8,'lab_single_target':8,'total_CPI':16}):
        raise PermissionError('approved scope drift')
    if inputm['CPI_count_generated']!=16 or inputm['CPI_inconclusive']!=0:
        raise PermissionError('immutable input count drift')
    ids=pack['CPI_IDs'];rows=inputm['CPI_records']
    if len(ids)!=16 or [x['cpi_id'] for x in rows]!=ids or len(set(ids))!=16:
        raise PermissionError('CPI order/IDs drift')
    if sum(x['profile_id']=='NOISE_ONLY_UNIT' for x in rows)!=8 or sum(x['profile_id']=='SINGLE_TARGET_REFERENCE_LIKE_LAB' for x in rows)!=8:
        raise PermissionError('profile counts changed')
    for rec in rows:
        if SIDES.get(rec['profile_id'])!=rec['g'] or rec['disposition']!='INPUT_READY_ONLY_PENDING_AUTHORIZATION_AND_RUNTIME_C06':
            raise PermissionError(('unapproved profile/g/status',rec['cpi_id']))
        if not (rec['static_headroom_pass'] and rec['input_envelope_pass'] and rec['input_clip_component_count']==0):
            raise PermissionError(('failed immutable preflight',rec['cpi_id']))
        for key,field in (('float_file','float_sha256'),('raw_unclipped_IQ_file','raw_unclipped_IQ_sha256'),
                          ('IQ_Q15_payload_file','IQ_Q15_payload_sha256')):
            f=ROOT/rec[key]
            if not f.is_file() or sha(f)!=rec[field]:
                raise PermissionError(('input bytes mismatch',rec['cpi_id'],key))
        if rec['IQ_payload_bytes']!=16896:raise PermissionError('IQ length not frozen')
    return pack,rows

def load_frozen(rec):
    source=np.load(ROOT/rec['float_file'],allow_pickle=False)
    raw=np.load(ROOT/rec['raw_unclipped_IQ_file'],allow_pickle=False)
    rawbytes=(ROOT/rec['IQ_Q15_payload_file']).read_bytes()
    if source.shape!=(33,128) or raw.shape!=(33,128,2) or len(rawbytes)!=16896:
        raise ValueError('source/IQ shape')
    iq=np.frombuffer(rawbytes,dtype='<i2').reshape(33,128,2)
    if not np.array_equal(iq,raw):raise ValueError('CPI bit-exact IQ mismatch')
    return np.asarray(source,dtype=np.complex128),[[tuple(map(int,pair)) for pair in row] for row in iq]

def stage_references(source,iq,g):
    mf=S03.pulse_compress(source);mt=S03.mti(mf)
    a=CHAIN_ORACLE.s03_fft_stage_reference(mt)
    quant=cplx(iq,g)
    qm=S03.pulse_compress(quant);qt=S03.mti(qm)
    qa=CHAIN_ORACLE.s03_fft_stage_reference(qt)
    exact={'MF':mf,'MTI':mt};q_exact={'MF':qm,'MTI':qt}
    for j in range(5):
        # CHAIN_ORACLE returns stage-wise scaled DIT; multiply back by shift.
        cumulative=sum((0,1,0,1,1)[:j+1])
        exact[f'FFT{j+1}']=a[j]*(1<<cumulative)
        q_exact[f'FFT{j+1}']=qa[j]*(1<<cumulative)
    return exact,q_exact

def stage_codes(cap):
    return {'MF':cap['mf'],'MTI':cap['mti'],**{
        f'FFT{j+1}':cap['fft_stages_range_major'][j] for j in range(5)}}

def independent_oracle(iq):
    taps=OR.independent_mf_taps();tw=OR.independent_twiddles()
    mf=[[OR.mf_at(iq,p,r,taps) for r in range(128)] for p in range(33)]
    mt=[[OR.mti(mf[p][r],mf[p+1][r]) for r in range(128)] for p in range(32)]
    ff=[[] for _ in range(5)]
    for r in range(128):
        stages=OR.fft32_oracle([mt[p][r] for p in range(32)],tw)
        for j in range(5):ff[j].append(stages[j])
    return {'MF':mf,'MTI':mt,**{f'FFT{j+1}':ff[j] for j in range(5)}}

def stage_evaluation(source,iq,cap,g):
    original,qref=stage_references(source,iq,g)
    actual_codes=stage_codes(cap);expected=independent_oracle(iq)
    stage_result={};oracle_mismatches=0
    for key in R_KEYS:
        fixed=np.asarray(actual_codes[key],dtype=np.int64)
        oracle=np.asarray(expected[key],dtype=np.int64)
        if fixed.shape!=oracle.shape:raise AssertionError('oracle shape mismatch')
        bad=np.argwhere(fixed!=oracle)
        count=int(len(bad));oracle_mismatches+=count
        cum=(sum((0,1,0,1,1)[:int(key[-1])]) if key.startswith('FFT') else 0)
        reconstructed=cplx(fixed,g,cum)
        total=stats(reconstructed,original[key])
        source_part=stats(qref[key],original[key])
        process_part=stats(reconstructed,qref[key])
        stage_result[key]={'MAX_RMS_total':total,'MAX_RMS_input_only':source_part,
          'MAX_RMS_processing_only':process_part,
          'approved_cap_MAX_and_RMS':C_CAP[g][key],
          'cap_pass':total['MAX']<=C_CAP[g][key] and total['RMS']<=C_CAP[g][key],
          'oracle_mismatched_components':count,
          'integer_components_compared':int(fixed.size),
          'oracle_first_bad_component':bad[0].tolist() if count else None,
          'fixed_values_sha256':sha_bytes(fixed.tobytes()),
          'oracle_values_sha256':sha_bytes(oracle.tobytes()),
          'Float_reference_sha256':sha_bytes(np.ascontiguousarray(original[key]).tobytes()),
          'quantized_input_Float_reference_sha256':sha_bytes(np.ascontiguousarray(qref[key]).tobytes()),
          'reconstruction_scale':{'g':g,'fft_cumulative_shift':cum}}
    return stage_result,oracle_mismatches,original

def pow_and_cfar(cap,original,g,detail_path):
    rd=cap['rd']
    native=NATIVE.complete_map(rd)
    powers=native['power'];mask=native['mask'];cuts=native['cut_records']
    if len(cuts)!=2782 or len(powers)!=128:raise AssertionError('CFAR map geometry')
    independent_power=[];power_bad=0
    for r,row in enumerate(rd):
        values=[]
        for b,(i,q) in enumerate(row):
            power,_=OR.oracle_power(int(i),int(q))
            values.append(power)
            if power!=powers[r][b]:power_bad+=1
        independent_power.append(values)
    if power_bad:raise AssertionError(('power oracle mismatch',power_bad))
    train_bad=0;alarm_bad=0;margin_bad=0
    for cut in cuts:
        r=cut['range'];b=cut['doppler_bin']
        val=[independent_power[r+dr][b+db] for dr,db in S03.TRAIN_OFFSETS]
        train,_=OR.oracle_sum40(val)
        alarm=bool(OR.oracle_cfar(independent_power[r][b],train))
        delta=40*independent_power[r][b]*65536-490007*train
        train_bad+=train!=cut['SUM40']
        alarm_bad+=alarm!=cut['alarm'] or mask[r][b]!=alarm
        margin_bad+=int(cut['signed_unbounded_margin'])!=delta
    grouped=GROUP_ORACLE.independent_components(mask,powers)
    clusters=native['clusters']
    if len(grouped)!=len(clusters):raise AssertionError('independent group count mismatch')
    group_bad=0
    for i,(a,b) in enumerate(zip(grouped,clusters)):
        for field in ('range_bin','doppler_bin','cluster_cells','power_stored_integer','tie_flag','max_equal_power_cells'):
            group_bad+=a[field]!=b[field]
        group_bad+=b['record_id']!=i
    # original S03 Float reference; exact frozen alpha.
    z0=original['FFT5']
    pfloat=np.abs(z0)**2
    fmask,valid,train_avg=S03.cfar_2d(pfloat,alpha=ALPHA_FLOAT)
    fcluster=S03.clusters_8(fmask,pfloat)
    fixedp=np.asarray(powers,dtype=np.float64)*(g*8/32768)**2
    # Approved bound: error in amplitude at FFT5 (not observed deviation).
    E=C_CAP[g]['FFT5']
    epow=2*np.abs(z0)*E+E*E
    uncertainty=epow + float(ALPHA_FIXED)*sum(
       epow[3+dr:110+dr,3+db:29+db] for dr,db in S03.TRAIN_OFFSETS
    )/40 +abs(float(ALPHA_FIXED)-ALPHA_FLOAT)*train_avg[3:110,3:29]
    floatmargin=pfloat[3:110,3:29]-ALPHA_FLOAT*train_avg[3:110,3:29]
    fixedmargin=(fixedp[3:110,3:29]-float(ALPHA_FIXED)*(
        np.asarray([[cut['SUM40'] for cut in cuts[k*26:(k+1)*26]] for k in range(107)])*
        (g*8/32768)**2)/40)
    changed=[];all_cut_records=[]
    n0to1=n1to0=ambiguous=outside=0
    for k,cut in enumerate(cuts):
        r=cut['range'];b=cut['doppler_bin']
        fa=bool(fmask[r,b]);ba=bool(cut['alarm'])
        margin=float(floatmargin[r-3,b-3]);u=float(uncertainty[r-3,b-3])
        changed_here=fa!=ba
        classify='UNCHANGED'
        if changed_here:
            if not fa and ba:n0to1+=1
            if fa and not ba:n1to0+=1
            if abs(margin)>u:classify='FAIL_OUTSIDE_APPROVED_MARGIN';outside+=1
            else:classify='INCONCLUSIVE_AMBIGUOUS';ambiguous+=1
            changed.append({'range':r,'doppler':b,'Float_alarm':fa,'Fixed_alarm':ba,
                 'Float_margin':margin,'envelope_U':u,'classification':classify})
        all_cut_records.append({'range':r,'doppler':b,'Float_alarm':fa,'Fixed_alarm':ba,
            'Float_margin':margin,'Fixed_margin_original_power':float(fixedmargin[r-3,b-3]),
            'Fixed_exact_integer_margin':cut['signed_unbounded_margin'],
            'Pcut_Float':float(pfloat[r,b]),'Pcut_Fixed_stored':cut['Pcut'],
            'SUM40_Float':float(train_avg[r,b]*40),'SUM40_Fixed_stored':cut['SUM40'],
            'CUT_power_uncertainty':float(epow[r,b]),
            'training_power_uncertainty_sum':float(sum(epow[r+dr,b+db] for dr,db in S03.TRAIN_OFFSETS)),
            'alpha_quantization_uncertainty':float(abs(float(ALPHA_FIXED)-ALPHA_FLOAT)*train_avg[r,b]),
            'approved_uncertainty_U':u,'classification':classify})
    save(detail_path,{'CUTs':all_cut_records,'changed':changed,
        'Float_reference_clusters':fcluster,'Fixed_integer_clusters':clusters,
        'Float_mask_sha256':sha_bytes(np.asarray(fmask,dtype=np.uint8).tobytes()),
        'Fixed_mask_sha256':sha_bytes(np.asarray(mask,dtype=np.uint8).tobytes())})
    # For each component compare original Float grouping peaks; no general peak tolerance.
    float_peaks={(a['range_bin'],a['doppler_bin']) for a in fcluster}
    fixed_peaks={(a['range_bin'],a['doppler_bin']) for a in clusters}
    diff=sorted(float_peaks^fixed_peaks)
    return {'integer_oracle':{
       'power_cell_count':4096,'power_mismatches':power_bad,
       'CUT_training_comparisons':2782,'training_mismatches':int(train_bad),
       'CUT_alarm_comparisons':2782,'alarm_mismatches':int(alarm_bad),
       'CUT_margin_comparisons':2782,'margin_mismatches':int(margin_bad),
       'independent_cluster_count':len(grouped),'cluster_count':len(clusters),
       'cluster_record_mismatches':int(group_bad)},
       'Float_fixed_CFAR':{'changed_CUT_count':len(changed),'Float_0_to_fixed_1':n0to1,
         'Float_1_to_fixed_0':n1to0,'changed_OUTSIDE_envelope_FAIL':outside,
         'changed_WITHIN_envelope_INCONCLUSIVE':ambiguous,
         'total_CUT_denominator':2782,'unchanged_CUT_count':2782-len(changed),
         'details_file':str(detail_path.relative_to(ROOT)),
         'details_file_sha256':sha(detail_path)},
       'grouping_float_fixed':{'Float_cluster_count':len(fcluster),
         'Fixed_cluster_count':len(clusters),
         'peak_coordinate_symmetric_difference_count':len(diff),
         'changed_peak_coordinates':diff,
         'historical_tie_exception_automatically_applied':False},
       'power_map_sha256':sha_bytes(canonical(powers)),
       'native_mask_sha256':sha_bytes(canonical(mask)),
       'native_cluster_records_sha256':sha_bytes(canonical(clusters))}

def run_cpi(rec,ledger):
    cid=rec['cpi_id']
    sub=OUT/cid
    sub.mkdir(exist_ok=False)
    # Ledger is written before any integer processing; no retries even on failure.
    ledger['rows'][cid]={'state':'ATTEMPT_STARTED','profile_id':rec['profile_id'],
       'g':rec['g'],'seed':rec['child_seed_u64'],'attempts':1,
       'input_float_sha256':rec['float_sha256'],
       'input_Q15_sha256':rec['IQ_Q15_payload_sha256']}
    save(OUT/'attempt_ledger.json',ledger)
    src,iq=load_frozen(rec)
    profile,g=rec['profile_id'],rec['g']
    if BASE.envelope(src,g)['analytic_clip_count']!=0:raise AssertionError('prelocked input clipping')
    # Reuse existing recorder unmodified; no generators or optional extra vectors.
    def unit():
        inputtel=ENG.Telemetry()
        result=ENG.run_one(src,iq,inputtel,'C_hypothetical',(0,1,0,1,1),g,capture_stages=True)
        return result
    capture=TRACE.capture_with_executor(
        executor=unit,cpi_id=cid,profile_id=profile,gain=g,vector_id=cid,
        output_dir=sub,engine_module=ENG,
        input_payload_sha256=rec['IQ_Q15_payload_sha256'],
        engine_source_sha256=sha(ENG.__file__),
        arithmetic_contract_sha256=sha(ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json'))
    result=capture['result'];trace=capture['manifest']
    check_shapes(result)
    stage,oracle_bad,original=stage_evaluation(src,iq,result['captured'],g)
    cfar=pow_and_cfar(result['captured'],original,g,sub/'cfar_all_2782_CUTs.json')
    integer=cfar['integer_oracle']
    full_bad=oracle_bad+sum(integer[x] for x in (
        'power_mismatches','training_mismatches','alarm_mismatches',
        'margin_mismatches','cluster_record_mismatches'))
    cap_fail=[k for k,v in stage.items() if not v['cap_pass']]
    input_n=trace['per_scope'][0]['event_count']
    internal_n=trace['per_scope'][1]['event_count']
    inconclusive=[]
    fail=[]
    if input_n or internal_n:inconclusive.append('INPUT_OR_INTERNAL_SATURATION')
    if trace['status']!='COMPLETE_READBACK_VERIFIED':inconclusive.append('TRACE_INCOMPLETE')
    if full_bad:fail.append('B_INTEGER_ORACLE_MISMATCH')
    if cap_fail:fail.append('A_NUMERIC_STAGE_CAP_EXCEEDED:'+','.join(cap_fail))
    if cfar['Float_fixed_CFAR']['changed_OUTSIDE_envelope_FAIL']:
        fail.append('C_FLOAT_FIXED_CFAR_OUTSIDE_APPROVED_MARGIN')
    if cfar['Float_fixed_CFAR']['changed_WITHIN_envelope_INCONCLUSIVE']:
        inconclusive.append('C_FLOAT_FIXED_CFAR_AMBIGUOUS_CHANGED_CUT')
    if cfar['grouping_float_fixed']['peak_coordinate_symmetric_difference_count']:
        # Not waivable without the exact independent reference tie + same component.
        inconclusive.append('D_FLOAT_FIXED_GROUP_PEAK_DIFFERENCE_REQUIRES_TIE_CLASSIFICATION')
    status='FAIL' if fail else 'INCONCLUSIVE' if inconclusive else 'PASS'
    evidence={'cpi_id':cid,'profile_id':profile,'g':g,
      'status':status,'fail_reasons':fail,'inconclusive_reasons':inconclusive,
      'input_disposition_before_execution':rec['disposition'],
      'profile_denominator':8,'global_denominator':16,
      'input_source_sha256':rec['float_sha256'],
      'input_Q15_sha256':rec['IQ_Q15_payload_sha256'],
      'independent_stage_oracle_mismatch_count':oracle_bad,
      'stage_errors_and_oracle':stage,'integer_chain':integer,
      'Float_fixed_C_and_D':{'CFAR':cfar['Float_fixed_CFAR'],
        'grouping':cfar['grouping_float_fixed']},
      'trace_manifest':trace['manifest_file'],
      'trace_manifest_sha256':trace['manifest_sha256'],
      'trace_input_events':input_n,'trace_internal_events':internal_n,
      'trace_complete_ordered_stream_sha256':trace['complete_ordered_stream_sha256'],
      'trace_readback':'PASS' if trace['status']=='COMPLETE_READBACK_VERIFIED' else 'FAIL',
      'all_A_stage_CAPs_pass':not cap_fail,'B_complete_integer_oracle_matches':full_bad==0,
      'D_historical_vectors_replayed_in_current_16_CPI_authorization':False,
      'D_historical_evidence_existing_reference':'engineering/s04_numeric/S04-C05-integrated-power-cfar-grouping-v1.0.json',
      'source_quantization_decomposition':'reported stagewise; total MAX/RMS independently computed from paired complex differences',
      'statistics':'NOT_PFA_PD','acceptance_decision':'AWAIT_INDEPENDENT_REVIEW'}
    save(sub/'CPI-result.json',evidence)
    ledger['rows'][cid].update({'state':'COMPLETED','status':status,
         'result_file':str((sub/'CPI-result.json').relative_to(ROOT)),
         'result_SHA256':sha(sub/'CPI-result.json'),
         'trace_manifest_SHA256':trace['manifest_sha256']})
    save(OUT/'attempt_ledger.json',ledger)
    return evidence

def main():
    pack,records=validate_package()
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError('ONE_SHOT_NO_RETRIES: prior C06 output exists')
    OUT.mkdir(parents=True,exist_ok=False)
    # Immutable sealed 16-entry attempt roster.
    ledger={'scope':'S04_C06_AUTHORIZED_EXACT_16_CPI_ONE_SHOT',
            'authorization':'CURRENT_USER_EXPLICIT_INDEPENDENT_16_CPI_EXECUTION',
            'locked_package_SHA256':PACKAGE_SHA,'locked_input_manifest_SHA256':MANIFEST_SHA,
            'fixed_N':{'NOISE_ONLY_UNIT':8,'SINGLE_TARGET_REFERENCE_LIKE_LAB':8},
            'planned_ids':[rec['cpi_id'] for rec in records],
            'rows':{},'no_auto_retry':True}
    save(OUT/'attempt_ledger.json',ledger)
    results=[]
    for rec in records:
        cid=rec['cpi_id']
        try:
            e=run_cpi(rec,ledger)
            results.append(e)
            print('CPI',cid,e['status'],'B_oracle_bad',
                  e['independent_stage_oracle_mismatch_count'],
                  'CFAR_changed',e['Float_fixed_C_and_D']['CFAR']['changed_CUT_count'],
                  'A_MAX_FFT5',e['stage_errors_and_oracle']['FFT5']['MAX_RMS_total']['MAX'],
                  'trace',e['trace_input_events'],e['trace_internal_events'],flush=True)
        except Exception as err:
            # Never rerun or replace any CPI: preserve partial input/trace and error.
            trace={'type':type(err).__name__,'message':str(err),
                'traceback':traceback.format_exc(),'cpi_id':cid,
                'failure':'EXECUTION_ERROR_NO_RETRY'}
            sub=OUT/cid
            sub.mkdir(exist_ok=True)
            save(sub/'EXECUTION_ERROR.json',trace)
            if cid not in ledger['rows']:
                ledger['rows'][cid]={'attempts':1,'state':'ATTEMPT_STARTED'}
            ledger['rows'][cid].update({'state':'INCONCLUSIVE_EXECUTION_ERROR',
                  'status':'INCONCLUSIVE','reason':str(err),
                  'error_file':str((sub/'EXECUTION_ERROR.json').relative_to(ROOT))})
            save(OUT/'attempt_ledger.json',ledger)
            results.append({'cpi_id':cid,'profile_id':rec['profile_id'],'g':rec['g'],
               'status':'INCONCLUSIVE','inconclusive_reasons':['EXECUTION_ERROR:'+str(err)]})
            print('CPI',cid,'INCONCLUSIVE_EXECUTION_ERROR',str(err),flush=True)
    cnt={profile:{'denominator':8,'PASS':0,'FAIL':0,'INCONCLUSIVE':0} for profile in SIDES}
    for r in results:cnt[r['profile_id']][r['status']]+=1
    assert len(results)==16 and len(ledger['rows'])==16
    for prof in cnt:assert sum(cnt[prof][k] for k in ('PASS','FAIL','INCONCLUSIVE'))==8
    total={k:sum(cnt[pr][k] for pr in cnt) for k in ('PASS','FAIL','INCONCLUSIVE')}
    hist_path=ROOT/'engineering/s04_numeric/S04-C05-integrated-power-cfar-grouping-v1.0.json'
    historic=json.loads(hist_path.read_text())
    d_issues=[x for x in historic.get('v06_discrepancies',[]) if x.get('v06_vector_id') in
             ('g1:phase_interference','g5:phase_interference')]
    aggregate={'project':'AX309-RDSP-001','criterion':'S04-C06',
      'status':'EXECUTED_BOUNDED_16_CPI_AWAITING_INDEPENDENT_SIGNOFF',
      'architecture':'C','shifts':[0,1,0,1,1],
      'package_sha256':PACKAGE_SHA,'input_manifest_sha256':MANIFEST_SHA,
      'denominators':cnt,'total_denominator':16,'total_status_counts':total,
      'attempts_by_CPI':{k:ledger['rows'][k]['attempts'] for k in ledger['planned_ids']},
      'no_replacement':True,'no_auto_retry':True,
      'per_CPI_results':[{'cpi_id':x['cpi_id'],'profile_id':x['profile_id'],
         'status':x['status'],'fail_reasons':x.get('fail_reasons',[]),
         'inconclusive_reasons':x.get('inconclusive_reasons',[])}
         for x in results],
      'D_historical_reference':str(hist_path.relative_to(ROOT)),
      'D_historical_reference_sha256':sha(hist_path),
      'D_historical_phase_interference_records_reused_not_rerun':d_issues,
      'D_historical_replay_in_current_run':'NOT_AUTHORIZED_ONLY_16_PRELOCKED_CPI',
      'oracle':{'integer_stage':'C03 Fraction',
                 'power_sum_Cfar':'C03 Fraction',
                 'grouping':'C05 independent union-find'},
      'C06_PASS_not_authorized':True,'Gate_S04':'OPEN','REQ-SCR-01':'OPEN',
      'REQ-RNG-03':'OPEN','S04_percent':62.5,'overall_percent':30.208333333333332,
      'statistical_Pfa_Pd':'NOT_RUN','accepted_S03_seeds':'NOT_USED',
      'RTL_synthesis_FPGA':'NOT_RUN'}
    save(OUT/'S04-C06-16CPI-QUALIFICATION-AGGREGATE-v1.0.json',aggregate)
    print('AGGREGATE',json.dumps({'denominators':cnt,'total':total,
      'full_16_attempts':len(ledger['rows']),'D_historic_records':len(d_issues)},
      ensure_ascii=False),flush=True)
if __name__=='__main__':main()

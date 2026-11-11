"""S04-C06 final software execution runner: frozen C04 stage DUT + C05 native maps.
C06 acceptance execution is locked until separately approved. No RNG or CPI generator.
"""
from __future__ import annotations
import hashlib, json, sys, struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
from s03_reference import model as S03
import s04_c04_selected_C_stage_capture_v1 as ENGINE
import s04_c05_native_integer_v1 as NATIVE
import s04_c03_independent_oracle_v1 as ORACLE
import s04_c06_fulltrace_capture_v1 as TRACE
SHIFTS=(0,1,0,1,1)
PROFILE_GAIN={"NOISE_ONLY_UNIT":5,"SINGLE_TARGET_REFERENCE_LIKE_LAB":1}
# Explicit execution interlock: this release supports diagnostics only.
ACCEPTANCE_EXECUTION_ENABLED=False
CONTRACT=ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json'
VALID_R=range(3,110); VALID_B=range(3,29)
EXPECTED_COUNTS={"IQ_complex":4224,"IQ_components":8448,"MF":4224,"MTI":4096,
                 "FFT1":4096,"FFT2":4096,"FFT3":4096,"FFT4":4096,"FFT5":4096,
                 "POWER":4096,"CFAR_CUT":2782,"CFAR_TRAINING_PER_CUT":40}

def digest_bytes(data):return hashlib.sha256(data).hexdigest()
def digest_file(path):return digest_bytes(Path(path).read_bytes())
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def pack_iq(q):
    if len(q)!=33 or any(len(row)!=128 for row in q):raise ValueError('33x128 complex integer IQ required')
    return b''.join(struct.pack('<hh',i,j) for row in q for i,j in row)

def envelope(source,g):
    arr=np.asarray(source,dtype=np.complex128)
    if arr.shape!=(33,128):raise ValueError('33x128 complex Float source required')
    scaled=np.stack((arr.real/g,arr.imag/g),axis=-1)
    finite=bool(np.isfinite(scaled).all())
    cap=1+2**-15
    maxval=float(np.max(np.abs(scaled))) if finite else None
    clipped=None
    if finite:
        clipped=int(np.count_nonzero(np.logical_or(scaled>=65535/65536,
                                                  scaled<-(65537/65536))))
    return {"finite":finite,"all_components_in_envelope":bool(finite and maxval<=cap),
            "maximum_normalized_absolute_component":maxval,
            "bound":cap,"analytic_clip_count":clipped}

def source_from_existing_diagnostic(kind,g):
    return ENGINE.source_vector(kind,g)

def _validate_approved_package(meta,source,iq,engine_source_hash):
    if not isinstance(meta,dict):raise ValueError('immutable metadata required')
    if meta.get('authorization_status')!='INDEPENDENTLY_APPROVED':
        raise PermissionError('C06 ACCEPTANCE LOCKED: independent authorization is missing')
    if meta.get('authorized_profile') not in PROFILE_GAIN:
        raise ValueError('unknown approved population')
    if meta.get('g')!=PROFILE_GAIN[meta['authorized_profile']]:
        raise ValueError('unapproved profile/g pair')
    if meta.get('source_population') not in ('CN(0,1)_NO_TARGET_NO_CLUTTER',
        'LAB_K40_DOPPLER_POS4_AMP0.18_PHASE0_NOISE_POWER0.000324_NO_CLUTTER'):
        raise ValueError('unapproved population definition')
    desired=('CN(0,1)_NO_TARGET_NO_CLUTTER' if meta['authorized_profile']=='NOISE_ONLY_UNIT'
             else 'LAB_K40_DOPPLER_POS4_AMP0.18_PHASE0_NOISE_POWER0.000324_NO_CLUTTER')
    if meta['source_population']!=desired:raise ValueError('profile/population mismatch')
    if meta.get('planned_total_by_profile') is None or meta.get('fixed_denominator') is None:
        raise ValueError('N and denominator must be approved before execution')
    if meta.get('approved_input_manifest_sha256') is None:
        raise ValueError('approved immutable input manifest missing')
    if meta.get('execution_permission_document_sha256') is None:
        raise ValueError('separate execution-permission document missing')
    if not meta.get('oracle_independently_approved'):
        raise ValueError('oracle independent approval missing')
    if not meta.get('static_PF07_headroom_proof_pass'):
        raise ValueError('PF07 static headroom proof missing')
    if meta.get('engine_sha256')!=engine_source_hash:
        raise ValueError('frozen source identity changed')
    if meta.get('source_sha256')!=digest_bytes(np.asarray(source,dtype=np.complex128).tobytes()):
        raise ValueError('original Float source hash mismatch')
    if meta.get('iq_sha256')!=digest_bytes(pack_iq(iq)):
        raise ValueError('IQ payload hash mismatch')
    if meta.get('fixed_denominator')!=meta.get('planned_total_by_profile'):
        raise ValueError('fixed N denominator mismatch')
    return True

def execute(*,input_tel_factory,profile_id,g,vector_id,cpi_id,
            output_dir,mode,meta=None):
    """Only DIAGNOSTIC_ONLY is runnable without separate signed C06 authorization.
    Executor creates input Telemetry from the specified factory under capture adapter.
    For existing source_vector, pass a callable that creates source + IQ through the patched engine.
    """
    if mode not in ('DIAGNOSTIC_ONLY','C06_ACCEPTANCE'):
        raise ValueError('unknown operation mode')
    if mode=='DIAGNOSTIC_ONLY':
        if profile_id!='DIAGNOSTIC_ONLY':raise ValueError('diagnostic mode requires diagnostic label')
    else:
        # This guard executes before any source processing or trace creation.
        # Independent authorization must be accompanied by a separately reviewed
        # runner release enabling acceptance. A string field alone is insufficient.
        if not ACCEPTANCE_EXECUTION_ENABLED:
            raise PermissionError('C06 acceptance execution interlock OFF; independent authorization and reviewed runner release required')
        if not meta or meta.get('authorization_status')!='INDEPENDENTLY_APPROVED':
            raise PermissionError('C06 acceptance requires independent authorization')
        if profile_id not in PROFILE_GAIN or PROFILE_GAIN[profile_id]!=g:
            raise ValueError('frozen C01 profile/g violated')
    eng_hash=digest_file(ENGINE.__file__)
    contract_hash=digest_file(CONTRACT)
    # Validation of the actual approved payload follows input creation, before any processing.
    captured_preflight={}
    def task():
        src,packed,in_tel=input_tel_factory()
        assert np.asarray(src).shape==(33,128)
        actual_payload=pack_iq(packed)
        clip=envelope(src,g)
        captured_preflight.update({
            'source_sha256':digest_bytes(np.asarray(src,dtype=np.complex128).tobytes()),
            'iq_sha256':digest_bytes(actual_payload),
            'source_dimensions':[33,128], 'iq_components':8448,
            'source_envelope':clip,
            'input_telemetry_count':in_tel.summary()['total']})
        if mode=='C06_ACCEPTANCE':
            _validate_approved_package(meta,src,packed,eng_hash)
            if (not clip['finite'] or not clip['all_components_in_envelope']
                or clip['analytic_clip_count']!=0 or in_tel.summary()['total']!=0):
                raise ValueError('pre-execution source envelope/clipping failure; INCONCLUSIVE')
        result=ENGINE.run_one(src,packed,in_tel,'C_hypothetical',SHIFTS,g,capture_stages=True)
        mapped=NATIVE.complete_map(result['captured']['rd'])
        if len(mapped['power'])!=128 or len(mapped['cut_records'])!=2782:
            raise AssertionError('Native map/CFAR geometry broken')
        if result['cfar_valid_cut_count']!=2782:
            raise AssertionError('engine CFAR geometry broken')
        if result['cfar_alarm_count']!=sum(x['alarm'] for x in mapped['cut_records']):
            raise AssertionError('native and engine CFAR disagree')
        # C05 native and C03 independent Fraction oracle check only a deterministic
        # diagnostic smoke subset; C06 B full componentwise check is later.
        for cut in mapped['cut_records']:
            if cut['alarm']!=ORACLE.oracle_cfar(cut['Pcut'],cut['SUM40']):
                raise AssertionError('independent Fraction CFAR oracle mismatch')
        return {'metrics':result['metrics'],
                'overflow':result['overflow'],
                'native_alarm_count':sum(x['alarm'] for x in mapped['cut_records']),
                'cluster_count':len(mapped['clusters']),
                'target_record_sha256':digest_bytes(canonical(mapped['clusters'])),
                'native_power_sha256':digest_bytes(canonical(mapped['power'])),
                'native_mask_sha256':digest_bytes(canonical(mapped['mask'])),
                'cut_count':len(mapped['cut_records']),
                'rd_component_count':8192}
    # No acceptance run happens unless a separate permission has been explicitly supplied;
    # this runner does not generate authorized population CPIs or allocate seeds.
    executed=TRACE.capture_with_executor(
        executor=task,cpi_id=cpi_id,profile_id=profile_id,gain=g,vector_id=vector_id,
        output_dir=output_dir,engine_module=ENGINE,
        engine_source_sha256=eng_hash,arithmetic_contract_sha256=contract_hash)
    trace=executed['manifest'];summary=executed['result']
    if sum(x['event_count'] for x in trace['per_scope'])!=trace['total_event_count']:
        raise AssertionError('trace manifest count discrepancy')
    observed_count=trace['per_scope'][0]['event_count']
    if observed_count!=captured_preflight['input_telemetry_count']:
        raise AssertionError('input trace non-omission mismatch')
    if trace['per_scope'][1]['event_count']!=summary['overflow']['total']:
        raise AssertionError('processing trace non-omission mismatch')
    if not trace['no_truncation'] or trace['status']!='COMPLETE_READBACK_VERIFIED':
        raise AssertionError('PF08 readback/coverage failure')
    invalid_reasons=[]
    if not captured_preflight['source_envelope']['all_components_in_envelope']:
        invalid_reasons.append('INPUT_ENVELOPE')
    if captured_preflight['source_envelope']['analytic_clip_count']!=observed_count:
        invalid_reasons.append('INPUT_CLIP_COUNT_MISMATCH')
    if observed_count: invalid_reasons.append('INPUT_CLIPPING')
    if trace['per_scope'][1]['event_count']:invalid_reasons.append('INTERNAL_OVERFLOW')
    if mode=='DIAGNOSTIC_ONLY':
        disposition='STRESS_ONLY' if invalid_reasons else 'DIAGNOSTIC_ONLY'
    else:
        disposition='INCONCLUSIVE' if invalid_reasons else 'PRELIMINARY_VALID_PENDING_A_TO_E'
    return {'mode':mode,'disposition':disposition,'performance_eligible':False,
            'invalid_reasons':invalid_reasons,'preflight':captured_preflight,
            'trace':trace,'processing':summary,'expected_denominators':EXPECTED_COUNTS,
            'engine_module':'s04_c04_selected_C_stage_capture_v1',
            'oracle_module':'s04_c03_independent_oracle_v1',
            'grouping_module':'s04_c05_native_integer_v1',
            'architecture':'C','fft_shifts':list(SHIFTS)}

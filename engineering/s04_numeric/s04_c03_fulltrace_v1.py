"""C03 complete overflow/saturation stream for selected-C v0.5 engine.

No modifications to historical v0.5 code. Temporarily interposes only its
Telemetry class; integer arithmetic, sign, rounding, narrowing remain as C02.
All input + all internal events preserved in JSONL, never first_24 truncation.
"""
import sys,json,hashlib,contextlib,uuid
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c02_integer_bittrue_v05 as DUT
from s04_c03_independent_oracle_v1 import immutable_fingerprint
ROOTNS=uuid.UUID('f039d62a-b7fa-4bad-9c69-2c11ca52e80d')

class CompleteEventRecorder(DUT.Telemetry):
    instances=[]
    current_vector=None
    def __init__(self):
        super().__init__()
        self.events=[]
        self.source_scope='input' if not CompleteEventRecorder.instances else 'processing'
        CompleteEventRecorder.instances.append(self)
    def record(self,site,indices,component,before,W,under=False):
        super().record(site,indices,component,before,W,under=under)
        kind='intermediate_width_exceeded' if under else 'output_saturation'
        signed=(component!='unsigned')
        local=len(self.events)
        identifier=str(uuid.uuid5(ROOTNS,f'{self.current_vector}:{self.source_scope}:{local}:{site}:{indices}:{component}'))
        evt={'event_id':identifier,'vector_id':self.current_vector,
             'ordinal_in_stream':local,'source_scope':self.source_scope,
             'site':site,'indices':list(indices),'component':component,
             'signed':signed,'word_width':W,'fractional_bits':0 if site=='IQ' else None,
             'pre_narrow_integer':str(before),
             'min_integer':str(-(1<<(W-1)) if signed else 0),
             'max_integer':str((1<<(W-1))-1 if signed else (1<<W)-1),
             'direction':'negative' if before<0 else 'positive','kind':kind,
             'sticky':True}
        self.events.append(evt)
    def legacy_event_digest(self):
        return self.digest.hexdigest()

@contextlib.contextmanager
def traced_engine():
    previous=DUT.Telemetry
    DUT.Telemetry=CompleteEventRecorder
    try:yield
    finally:DUT.Telemetry=previous

def run_selected_with_full_trace(kind,g,vector_id):
    assert g in (1,5)
    CompleteEventRecorder.instances=[]
    CompleteEventRecorder.current_vector=vector_id
    with traced_engine():
        src,iq,input_tel=DUT.source_vector(kind,g)
        result=DUT.run_one(src,iq,input_tel,'C_hypothetical',(0,1,0,1,1),g)
    collectors=CompleteEventRecorder.instances
    assert len(collectors)==2
    all_events=[]
    for collector in collectors:
        assert len(collector.events)==collector.summary()['total']
        # Recalculate legacy original ordered-event digest independently.
        sha=hashlib.sha256()
        for evt in collector.events:
            original={k:evt[k] for k in ('site','indices','component','pre_narrow_integer','direction','kind')}
            original['signed_W']=evt['word_width']
            sha.update((json.dumps(original,sort_keys=True,separators=(',',':'))+'\n').encode())
        assert sha.hexdigest()==collector.legacy_event_digest()
        all_events.extend(collector.events)
    assert result['overflow']['total']==len(collectors[1].events)
    return {'events':all_events,'per_scope_counts':{
        'input':len(collectors[0].events),'processing':len(collectors[1].events)},
        'legacy_scope_sha256':{
            'input':collectors[0].legacy_event_digest(),
            'processing':collectors[1].legacy_event_digest()},
        'result':result}

def emit_and_verify(kind,g,output_dir):
    vid=f'S04-C03-g{g}-{kind}'
    data=run_selected_with_full_trace(kind,g,vid)
    outdir=Path(output_dir);outdir.mkdir(parents=True,exist_ok=True)
    target=outdir/f'{vid}-overflow-all.jsonl'
    h=hashlib.sha256()
    ids=set()
    with target.open('wb') as f:
        for count,evt in enumerate(data['events']):
            assert evt['event_id'] not in ids
            ids.add(evt['event_id'])
            record=json.dumps(evt,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()+b'\n'
            f.write(record);h.update(record)
        f.flush()
        import os
        os.fsync(f.fileno())
    on_disk=target.read_bytes()
    assert hashlib.sha256(on_disk).hexdigest()==h.hexdigest()
    reread=[json.loads(line) for line in on_disk.splitlines()]
    assert reread==data['events']
    assert len(reread)==sum(data['per_scope_counts'].values())
    assert len({evt['event_id'] for evt in reread})==len(reread)
    assert all(x['vector_id']==vid for x in reread)
    assert all(x['ordinal_in_stream']==i for scope in ('input','processing')
               for i,x in enumerate(evt for evt in reread if evt['source_scope']==scope))
    return {'vector_id':vid,'full_file':str(target.relative_to(ROOT)),
        'full_file_SHA256':h.hexdigest(),
        'retained_records':len(reread),
        'per_scope_counts':data['per_scope_counts'],
        'legacy_scope_sha256':data['legacy_scope_sha256'],
        'first_event':reread[0] if reread else None,
        'last_event':reread[-1] if reread else None,
        'full_re_read_and_uniqueness':'PASS',
        'fixed_integer_result_sha256':immutable_fingerprint({
            'alarm_count':data['result']['cfar_alarm_count'],
            'metric':data['result']['metrics'],
            'processing_trace_sha256':data['legacy_scope_sha256']['processing']}),
        'no_truncation':True}
if __name__=='__main__':
    entries=[emit_and_verify(pattern,g,ROOT/'engineering/s04_numeric/c03_complete_overflow_trace')
             for g in (1,5) for pattern in ('zero','near_clip','overrange_stress')]
    out=ROOT/'engineering/s04_numeric/S04-C03-complete-overflow-replay-v1.0.json'
    out.write_text(json.dumps({'status':'FULL_EVENT_TRACE_VERIFIED','event_count':sum(x['retained_records'] for x in entries),
        'total_cases':len(entries),'cases':entries,'no_historical_model_modified':True},ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'cases':len(entries),'event_count':sum(x['retained_records'] for x in entries),
        'manifest_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'per_case':[(x['vector_id'],x['retained_records']) for x in entries]},ensure_ascii=False))

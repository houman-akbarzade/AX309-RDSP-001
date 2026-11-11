"""Deterministic synthetic overflow fixtures, no CPI, no hardware."""
import json,hashlib,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c03_fulltrace_v1 as TR
import s04_c02_integer_bittrue_v05 as M
from s04_c03_independent_oracle_v1 import checked
TR.CompleteEventRecorder.instances=[]
TR.CompleteEventRecorder.current_vector='S04-C03-internal-overflow-injection-deterministic'
t=TR.CompleteEventRecorder()
for i in range(77):
    x=(1<<24)+i if i%2==0 else -(1<<24)-i
    output=M.bounded(x,25,t,'FFT5',(5,i%32),'I')
    assert output==checked(x,25)[0]
for i in range(41):
    x=(1<<46)+i
    output=M.ubounded(x,46,t,'POWER',(i%128,i%32))
    assert output==checked(x,46,False)[0]
for i in range(41):
    x=(1<<52)+i
    output=M.ubounded(x,52,t,'SUM40',(i%128,i%32))
    assert output==checked(x,52,False)[0]
assert len(t.events)==159 and t.summary()['total']==159
p=ROOT/'engineering/s04_numeric/c03_complete_overflow_trace/S04-C03-internal-overflow-injection-all.jsonl'
with p.open('wb') as f:
    for e in t.events:
        f.write(json.dumps(e,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()+b'\n')
    f.flush();os.fsync(f.fileno())
raw=p.read_bytes()
lines=[json.loads(x) for x in raw.splitlines()]
assert len(lines)==159 and lines==t.events
assert len({x['event_id'] for x in lines})==159
assert [e['ordinal_in_stream'] for e in lines]==list(range(159))
assert len(t.summary()['first_24'])==24
m={'status':'DETERMINISTIC_INTERNAL_OVERFLOW_FULL_TRACE_VERIFIED',
    'events':159,'FFT5_signed_output_overflow':77,'POWER_unsigned_overflow':41,
    'SUM40_unsigned_overflow':41,'legacy_summary_first24_only':24,
    'new_complete_trace_retained':159,'expected_results_independent_Fraction_oracle':'PASS',
    'replay_readback':'PASS','unique_ids':'PASS','ordered_sequence':'PASS',
    'source_file':str(p.relative_to(ROOT)),
    'source_SHA256':hashlib.sha256(raw).hexdigest(),
    'first_event':lines[0],'last_event':lines[-1],
    'no_CPI':True,'no_RTL_or_FPGA':True}
out=ROOT/'engineering/s04_numeric/S04-C03-forced-internal-overflow-evidence-v1.0.json'
out.write_text(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print('PASS_INTERNAL_OVERFLOW',len(lines),'TRACE_SHA',m['source_SHA256'],'MANIFEST_SHA',hashlib.sha256(out.read_bytes()).hexdigest())

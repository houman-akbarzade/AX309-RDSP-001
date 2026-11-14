"""Read-only paired replay of retained real-board CPIs against frozen FFT-IP fixed model."""
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'engineering/s04_numeric')]
from fft_ip_fullchain_v1 import full_chain,library_sha256,EXPECTED_LIB_SHA
BASE=ROOT/'engineering/s04_numeric'
OUT=ROOT/'engineering/audit/S11-PAIRED-REPLAY-20261114'
FIELDS=('record_id','range_bin','doppler_bin','signed_doppler_bin','power_stored_integer','cluster_cells','tie_flag','max_equal_power_cells')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 assert library_sha256()==EXPECTED_LIB_SHA
 OUT.mkdir(exist_ok=False)
 counts={};errors=[];started=time.monotonic()
 with (OUT/'PAIRS.jsonl').open('x') as out:
  for mode in ('pd','pfa'):
   folder=BASE/f'hardware_stat_campaign_20261113_{mode}_v1'
   rows=[json.loads(s) for s in (folder/'RAW.jsonl').read_text().splitlines()]
   assert [r['i'] for r in rows]==list(range(len(rows)))
   n_power=n_record=n_alarm=0
   for r in rows:
    iq=folder/r['iq_file'];journal=folder/r['board_journal'];capture=folder/r['board_capture_npz']
    assert sha(iq)==r['iq_sha256'] and sha(journal)==r['board_journal_sha256'] and sha(capture)==r['board_capture_sha256']
    data=np.fromfile(iq,dtype='<i2').reshape(33,128,2)
    j=json.loads(journal.read_text())
    with np.load(capture) as z:
     assert z['iq'].astype('<i2').tobytes()==data.tobytes()
     assert np.array_equal(z['power'],np.asarray(j['power'],dtype=np.uint64))
    model=full_chain(data)
    p=np.asarray(model['native']['power'],dtype='<u8')
    observed=np.asarray(j['power'],dtype='<u8')
    diff=int(np.count_nonzero(p!=observed))
    a=int(sum(bool(c['alarm']) for c in model['native']['cut_records']))
    pred=[[q[k] for k in FIELDS] for q in model['native']['clusters']]
    actual=[[q[k] for k in FIELDS] for q in j['records']]
    n_power+=int(diff==0);n_record+=int(pred==actual);n_alarm+=int(a==r['alarms'])
    rec=dict(profile=mode,i=r['i'],cpi_id=r['cpi_id'],iq_sha256=r['iq_sha256'],model_power_sha256=hashlib.sha256(p.tobytes()).hexdigest(),board_power_sha256=r['power_sha256'],power_mismatches=diff,records_exact=pred==actual,alarm_count_exact=a==r['alarms'],model_alarms=a,board_alarms=r['alarms'],model_events=int(model['mf_clip']+model['mti_clip']+model['fft_overflow']+model['power_clip']))
    out.write(json.dumps(rec,sort_keys=True)+'\n')
    if diff or pred!=actual or a!=r['alarms'] or rec['model_events']:
     errors.append(rec)
    if (r['i']+1)%100==0:
     out.flush();print(mode,r['i']+1,'/',len(rows),'errors',len(errors),flush=True)
   counts[mode]=dict(n=len(rows),power_exact=n_power,records_exact=n_record,alarms_exact=n_alarm)
 result=dict(counts=counts,errors=errors[:20],error_count=len(errors),pairs_sha256=sha(OUT/'PAIRS.jsonl'),vendor_sha256=library_sha256(),runner_sha256=sha(Path(__file__)),elapsed_seconds=time.monotonic()-started)
 (OUT/'SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
 print('FINAL',json.dumps({k:v for k,v in result.items() if k!='errors'}),flush=True)
if __name__=='__main__':main()

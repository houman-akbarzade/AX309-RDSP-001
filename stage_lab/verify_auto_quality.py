"""Release verification against actual stored UART evidence, not simulated board substitutes."""
import json,hashlib
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from .models import ROOT,decode,compare
from .auto_suite import plan
from .auto_metrics import interval,aggregate,association
from .auto_report import render_report,render_normal
from .auto_cases import build_source,spec
from .cockpit import Cockpit
def fixed_ok(m):
 return bool(m.get('exact_integer',m.get('exact_decisions',m.get('record_signatures_exact',False))))
def main():
 D=ROOT/'engineering/evidence/auto_lab_v0.3';runs=json.loads((D/'board-validation-runs.json').read_text());checks={}
 quickdir=Path(runs['quick']['directory']);quick=json.loads((quickdir/'suite.json').read_text());assert quick['status']=='COMPLETE' and len(quick['jobs'])==41
 for name in ['quick','statistics']:
  d=Path(runs[name]['directory']);s=json.loads((d/'suite.json').read_text());fixed=0
  for j in s['jobs']:
   assert j['physical_UART'] and j['input_echo_verified']
   z=np.load(d/j['artifact']);assert hashlib.sha256(z['input_words'].astype('<u8').tobytes()).hexdigest()==j['input_sha256']
   assert hashlib.sha256(z['output_words'].astype('<u8').tobytes()).hexdigest()==j['output_sha256']
   assert j['status']['flags']==0,(j['case'],j['status'])
   for metrics in [j['metrics'],j['full_chain_metrics']]:
    for label,m in metrics.items():
     if 'Fixed' in label:assert fixed_ok(m),(name,j['id'],label,m);fixed+=1
  # Re-evaluate analysis from unchanged captured words; zero valleys are explicit,
  # never replaced by an invented finite dB floor.
  from .auto_metrics import functional
  from desktop_app.scenarios import Flight
  for j in s['jobs']:
   z=np.load(d/j['artifact']);rows=z['input_words'].size//128
   inp=decode(z['input_words'],j['entry'],rows);got=decode(z['output_words'],j['stage'],rows-1 if j['stage']==2 else rows);ts=[Flight(**x) for x in j['targets']]
   measured=functional(s['cases'][j['case']],j['stage'],j['entry'],inp,got,True,ts)
   if measured!=j['functional']:
    j.setdefault('analysis_history',[]).append(dict(previous_functional=j['functional'],reason='Recomputed from preserved actual words; exact-zero valley is not an arbitrary finite dB floor.'))
    j['functional']=measured
    (d/(j['id']+'.json')).write_text(json.dumps(j,indent=2))
  (d/'suite.json').write_text(json.dumps(s,indent=2))
  render_report(s,d)
  assert (d/'index.html').exists()
  body=(d/'index.html').read_text()
  for j in s['jobs']:
   assert j['id']+'-summary.svg' in body and (d/(j['id']+'-summary.svg')).exists()
  checks[name+'_inline_summary_charts']=len(s['jobs'])
  checks[name]=dict(status=s['status'],jobs=len(s['jobs']),fixed_comparisons=fixed,unique_hardware_captures=len({j['output_sha256']+j['input_sha256']+str(j['stage']) for j in s['jobs']}),all_input_echo_and_output_hashes_verified=True)
 quick=json.loads((quickdir/'suite.json').read_text())
 mtis={j['case']:j['functional']['mti_target_response'][0] for j in quick['jobs'] if j['scope']=='isolated' and j['stage']==2 and j['case'].startswith('MTI ')}
 assert mtis['MTI stationary']['exact_zero_output']
 slow=mtis['MTI near-stationary'];assert slow['gain_db']<-30 and abs(slow['gain_db']-slow['analytic_gain_db'])<.01
 assert mtis['MTI moving']['gain_db']>0
 range_results=[j['functional']['range_resolution'] for j in quick['jobs'] if 'range_resolution' in j['functional']]
 speed_results=[j['functional']['velocity_resolution'] for j in quick['jobs'] if 'velocity_resolution' in j['functional']]
 assert len(range_results)==len(speed_results)==3
 statdir=Path(runs['statistics']['directory']);stats=json.loads((statdir/'suite.json').read_text())
 assert stats['statistics']['noise_CPIs']==stats['statistics']['target_CPIs']==3
 seeds=[j['seed'] for j in stats['jobs'] if j['stage']==5];assert len(seeds)==len(set(seeds))==6
 assert len(plan('statistics',3)[1])==12 and interval(0,3)[0]==0 and interval(3,3)[1]==1
 for name in ['normal','normal_file']:
  d=Path(runs[name]['directory']);s=json.loads((d/'suite.json').read_text());assert s['physical_UART'] and s['input_echo_verified'] and s['terminal']=='COMMIT' and s['released']
  assert all(fixed_ok(m) for label,m in s['metrics'].items() if 'Fixed' in label)
  checks[name]=dict(terminal='COMMIT',input_echo_verified=True,released=True,reference_engines=list(s['metrics']))
  if name=='normal_file':assert s['metadata']['truth']=='Not supplied' and not s['metadata']['targets']
 # Two-mode UI and full native renderer/navigation exercise on genuine reports.
 app=QApplication([]);w=Cockpit();w.show();app.processEvents();assert w.mode.count()==2
 w.mode.setCurrentIndex(1);assert not w.targets.isEnabled() and w.level.isEnabled()
 w.level.setCurrentIndex(1);assert w.repeats.isEnabled();w.repeats.setValue(3);assert '3' in w.plan_note.text()
 w.mode.setCurrentIndex(0);assert w.targets.isEnabled() and not w.level.isEnabled()
 w.scenario.setCurrentText('MTI mixed');assert w.targets.rowCount()==3
 w.noise.setValue(.012345);assert w.noise.value()==.012345
 for name in ['quick','statistics','normal']:
  d=Path(runs[name]['directory']);w.completed(dict(runs[name]));app.processEvents();assert 'AX309' in w.report.toPlainText()
  w.grab().save(str(D/('gui-'+name+'.png')))
 # Open an MTI detail with report's conceptual short sentence and SVG images.
 slowjob=next(j for j in quick['jobs'] if j['case']=='MTI near-stationary' and j['stage']==2)
 w.report.setSource(QUrl.fromLocalFile(str(quickdir/(slowjob['id']+'.html'))));app.processEvents();assert '33.5763' in w.report.toPlainText()
 w.grab().save(str(D/'gui-mti-detail.png'));w.close()
 checks.update(MTI=mtis,range_resolution=range_results,velocity_resolution=speed_results,statistics=stats['statistics'],UI='PASS: two modes, scenario controls, report and case navigation, SVG rendering')
 (D/'release-validation.json').write_text(json.dumps(checks,indent=2));print('AUTO_LAB_RELEASE_VALIDATION_PASS '+json.dumps({k:v for k,v in checks.items() if k not in ('statistics','MTI')}),flush=True)
if __name__=='__main__':main()

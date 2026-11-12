"""Presentation QA against preserved physical FPGA captures; does not program the board."""
import json,sys
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QApplication
from .gui import Window
from .models import ROOT,decode,reference,compare
from .visuals import architecture_svg,scenario_svg
from desktop_app.reference import prepare_with_source
from desktop_app.scenarios import LIBRARY,VELOCITY_STEP
def main():
 app=QApplication([]);w=Window();w.show();app.processEvents()
 E=ROOT/'engineering/evidence/stage_lab_v0.2';D=ROOT/'engineering/evidence/stage_lab_v0.2.1';D.mkdir(exist_ok=True);checks=[]
 _,truth,meta,src=prepare_with_source('Two aircraft')
 for t in range(1,7):
  z=np.load(E/f'board-{t}-scenario.npz');entry=t-1;rows=z['input'].size//128
  inp=decode(z['echo'],entry,rows);out=decode(z['output'],t,rows-1 if t==2 else rows)
  refs={};metrics={}
  for fixed in [False,True]:
   label='Python '+('Fixed' if fixed else 'Float');refs[label]=reference(inp,entry,t,fixed);metrics[label]=compare(out,refs[label],t,fixed)
  result=dict(target=t,entry=entry,actual_input=inp,output=out,references=refs,metrics=metrics,elapsed_s=1,origin={'origin':'Preserved actual FPGA capture','input_quantization_RMSE':0},truth=truth,metadata=meta,journal=str(E/f'board-{t}-scenario'),transport=[])
  w.result(result);app.processEvents();assert w.records.rowCount()>0
  assert w.metric_table.rowCount()>0
  for profile in range(2):
   w.profile.setCurrentIndex(profile)
   for comp in ['Magnitude','I','Q','Phase']:
    w.component.setCurrentText(comp);app.processEvents()
    assert w.pin.xlabel and w.pin.ylabel and w.pout.xlabel and w.pout.ylabel
    assert len(w.pout.lines['FPGA'])>0
   for axis in range(3):w.axis.setCurrentIndex(axis);app.processEvents()
  w.profile.setCurrentIndex(0);w.component.setCurrentText('Magnitude');w.axis.setCurrentIndex(0)
  for dom in range(2):
   w.map_domain.setCurrentIndex(dom)
   for q in range(3):w.map_quantity.setCurrentIndex(q);app.processEvents();assert w.maps[0].data.shape[1]==128
  w.map_domain.setCurrentIndex(0);w.map_quantity.setCurrentIndex(2 if t==6 else 1 if t==5 else 0)
  w.tabs.setCurrentIndex(1);app.processEvents();w.grab().save(str(D/f'stage-{t}-maps.png'))
  w.tabs.setCurrentIndex(0);app.processEvents();w.grab().save(str(D/f'stage-{t}-waveforms.png'))
  if t in (3,4):
   assert w.sweep_table.rowCount()==64
   assert len(w.pfa.lines)==2
   w.tabs.setCurrentIndex(4);app.processEvents();w.grab().save(str(D/f'stage-{t}-threshold.png'))
  checks.append(dict(stage=t,physical_capture=True,waveform_components=4,views=2,axes=3,map_modes=6,all_data_rows=w.records.rowCount(),metrics_rows=w.metric_table.rowCount()))
 # Maximal records with exact physical fixture.
 z=np.load(E/'board-6-edge.npz');inp=decode(z['echo'],5);out=decode(z['output'],6);r=reference(inp,5,6,True)
 result.update(target=6,entry=5,actual_input=inp,output=out,references={'Python Fixed':r},metrics={'Python Fixed':compare(out,r,6,True)})
 w.result(result);app.processEvents();assert w.records.rowCount()==1404
 w.tabs.setCurrentIndex(2);app.processEvents();w.grab().save(str(D/'702-clusters-compared.png'))
 # Empty records are valid, table explicitly explains.
 empty=(np.zeros((32,128),np.uint64),np.zeros((32,128),bool));result.update(actual_input=empty,output=[],references={'Python Fixed':[]},metrics={'Python Fixed':compare([],[],6,True)})
 w.result(result);app.processEvents();assert w.records.rowCount()==0 and 'No clusters' in w.record_note.text()
 for name in list(LIBRARY)+['Noise only']:
  w.scenario.setCurrentText(name);app.processEvents();assert w.scenario_svg.renderer().isValid()
  svg=scenario_svg(name,LIBRARY.get(name,[]),.002);(D/('scenario-'+name.lower().replace(' ','-')+'.svg')).write_text(svg)
 w.scenario.setCurrentText('Two aircraft');w.targets.cellWidget(0,2).setValue(-1.234567);assert w.velocities()[0]==-1.234567
 w.noise.setValue(.012345);assert w.noise.value()==.012345
 for t in range(1,7):
  w.target.setCurrentIndex(t-1);app.processEvents();assert w.arch_svg.renderer().isValid()
  (D/f'architecture-stage-{t}.svg').write_text(architecture_svg(t-1,t,input_mode='Software previous-stage'))
 w.tabs.setCurrentIndex(6);app.processEvents();w.grab().save(str(D/'persian-help.png'))
 assert 'B Nazanin' in w.help.toHtml() and 'Stored codes' in w.help.toPlainText()
 # Thresholds share the same numeric grid between FPGA and reference.
 from .statistics import sweep
 p=np.ones((32,128));sa=sweep(p,truth);sb=sweep(p*2,truth,thresholds=[r['threshold'] for r in sa['rows']])
 assert [r['threshold'] for r in sa['rows']]==[r['threshold'] for r in sb['rows']]
 report=dict(status='PASS',cases=checks,max_hardware_cluster_rows=702,total_compared_cluster_rows=1404,empty_clusters_explained=True,editable_individual_velocity=True,arbitrary_noise_decimal=True,svg_all_stages_scenarios=True,persian_font='B Nazanin',threshold_grid_shared=True,scope='Presentation QA on preserved real FPGA captures; not a new physical run or statistical acceptance')
 (D/'gui-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True);w.close()
if __name__=='__main__':main()

"""GUI rendering with real recorded hardware data; no synthetic hardware claims."""
import sys,json
import numpy as np
from PySide6.QtWidgets import QApplication
from .gui import Window
from .models import *
from desktop_app.reference import prepare_with_source
from pc_link.board_dsp import persist
def main():
 app=QApplication([]);w=Window();w.show();E=ROOT/'engineering/evidence/stage_lab_v0.2';results=[]
 _,truth,meta,src=prepare_with_source('Two aircraft')
 for target in range(1,7):
  z=np.load(E/f'board-{target}-scenario.npz');entry=target-1;rows=z['input'].size//128
  inp=decode(z['echo'],entry,rows);out=decode(z['output'],target,rows-1 if target==2 else rows)
  refs={};metrics={}
  for fixed in [False,True]:
   label='Python '+('Fixed' if fixed else 'Float');refs[label]=reference(inp,entry,target,fixed);metrics[label]=compare(out,refs[label],target,fixed)
  result=dict(target=target,entry=entry,actual_input=inp,output=out,references=refs,metrics=metrics,elapsed_s=1,origin={'origin':'Recorded physical FPGA case'},truth=truth,journal=str(E/f'board-{target}-scenario'),transport=[])
  w.result(result);app.processEvents()
  for component in ['Magnitude','I','Q','Phase']:
   w.component.setCurrentText(component);w.slice.setValue(0);app.processEvents();assert not w.grab().isNull()
  w.grab().save(str(E/f'gui-stage-{target}.png'))
  assert 'Python Fixed' in w.metrics.toPlainText()
  results.append(dict(target=target,actual_hardware_fixture=True,components=4,render='PASS'))
 # Maximal 702-record UI uses actual physical output.
 z=np.load(E/'board-6-edge.npz');inp=decode(z['echo'],5);out=decode(z['output'],6)
 result.update(target=6,entry=5,actual_input=inp,output=out,references={'Python Fixed':reference(inp,5,6,True)},metrics={'Python Fixed':compare(out,reference(inp,5,6,True),6,True)})
 w.result(result);app.processEvents();assert w.records.rowCount()==702;w.tabs.setCurrentWidget(w.records);w.grab().save(str(E/'gui-702-records.png'))
 # Threshold exploration and bad input are genuine logic checks, not acceptance.
 from .statistics import sweep
 p=np.ones((32,128));s=sweep(p,noise_only=True);assert s['independent_CPIs']==1 and all(r['valid_cells']==2782 for r in s['rows'])
 try:quantize(np.array([[complex(float('nan'),0)]]),0);raise AssertionError('NaN not rejected')
 except ValueError:pass
 persist(E/'gui-validation.json',dict(results=results,max_record_table_rows=702,threshold_snapshot='PASS (not statistical qualification)',nonfinite_input_rejected=True))
 print('PASS GUI all six hardware fixtures, four components, 702 records and exploratory threshold logic',flush=True)
 w.close()
if __name__=='__main__':main()

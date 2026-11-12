import sys,json
from dataclasses import replace
from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
sys.path.insert(0,'/home/houman/AX309-RDSP-001-stage-lab')
from stage_lab.gui import Window
from stage_lab.models import ROOT,decode
from desktop_app.scenarios import LIBRARY
app=QApplication([]);w=Window();w.showMaximized()
D=ROOT/'engineering/evidence/stage_lab_v0.2.1';proof=json.loads((D/'live-board-gui.json').read_text());j=Path(proof['journal']);o=json.loads(j.with_suffix('.json').read_text());z=np.load(j.with_suffix('.npz'))
w.scenario.setCurrentText('Two aircraft');w.noise.setValue(.012345)
for i,v in enumerate(proof['velocities_m_s']):w.targets.cellWidget(i,2).setValue(v)
o['actual_input']=decode(z['input_words'],int(z['entry']));o['output']=decode(z['output_words'],int(z['target']))
o['references']={k.replace('_',' '):z[k] for k in ['Python_Float','Python_Fixed','MATLAB_Float','MATLAB_Fixed']}
o['truth']=[replace(t,velocity=v) for t,v in zip(LIBRARY['Two aircraft'],proof['velocities_m_s'])];o['journal']=str(j)
w.result(o)
def snapshot():
 for idx,name in [(0,'final-waveforms'),(1,'final-maps'),(2,'final-records'),(3,'final-metrics'),(4,'final-threshold'),(5,'final-scenario'),(6,'final-help')]:
  w.tabs.setCurrentIndex(idx);app.processEvents();w.grab().save(str(D/(name+'.png')))
 w.tabs.setCurrentIndex(1);app.processEvents();print('FINAL_NATIVE_VIEW_READY: preserved fresh physical run; all four saved reference arrays loaded; no new board programming',flush=True)
QTimer.singleShot(500,snapshot);sys.exit(app.exec())

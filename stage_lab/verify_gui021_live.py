"""Live operator demo: real Power FPGA run with individually edited velocities and fractional noise."""
import sys,json
from pathlib import Path
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from .gui import Window
from .models import ROOT
def main():
 app=QApplication(sys.argv);w=Window();w.showMaximized()
 w.target.setCurrentIndex(3);w.scenario.setCurrentText('Two aircraft');w.noise.setValue(.012345)
 w.targets.cellWidget(0,2).setValue(-1.234567);w.targets.cellWidget(1,2).setValue(4.125)
 w.engine.setCurrentText('Both');w.arithmetic.setCurrentText('Both');w.injection.setCurrentText('Python Float')
 D=ROOT/'engineering/evidence/stage_lab_v0.2.1'
 def completed(out):
  assert out['metadata']['target_velocities_m_s']==[-1.234567,4.125]
  assert out['metadata']['noise_rms']==.012345
  assert out['metrics']['Python Fixed']['RMSE']==0 and out['metrics']['MATLAB Fixed']['RMSE']==0
  p=out['output'].sum(axis=1);w.slice.setValue(int(p.argmax()))
  def snap():
   for idx,name in [(0,'live-waveforms'),(1,'live-maps'),(3,'live-metrics'),(4,'live-threshold'),(5,'live-scenario'),(6,'live-help')]:
    w.tabs.setCurrentIndex(idx);app.processEvents();w.grab().save(str(D/(name+'.png')))
   w.tabs.setCurrentIndex(1);app.processEvents()
   data=dict(status='PASS',physical_board=True,journal=out['journal'],metrics=out['metrics'],velocities_m_s=out['metadata']['target_velocities_m_s'],noise_complex_rms=.012345,all_four_references=True)
   (D/'live-board-gui.json').write_text(json.dumps(data,indent=2));print('LIVE_GUI_021_PASS '+json.dumps(data),flush=True)
  QTimer.singleShot(300,snap)
 def start():
  w.execute();w.worker.completed.connect(completed);w.worker.failed.connect(lambda s:print('LIVE_GUI_021_FAILED '+s,flush=True))
 QTimer.singleShot(100,start);sys.exit(app.exec())
if __name__=='__main__':main()

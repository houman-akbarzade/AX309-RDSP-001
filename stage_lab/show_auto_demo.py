"""Show the completed real-board report without reprogramming or rerunning hardware."""
import sys,json
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from .cockpit import Cockpit
from .models import ROOT
def main():
 app=QApplication(sys.argv);w=Cockpit();w.showMaximized();D=ROOT/'engineering/evidence/auto_lab_v0.3';runs=json.loads((D/'board-validation-runs.json').read_text())
 w.mode.setCurrentIndex(1);w.completed(runs['quick'])
 def capture():
  w.grab().save(str(D/'native-main-report.png'))
  if w.report.find('MTI near-stationary'):
   w.report.ensureCursorVisible();app.processEvents();w.report.verticalScrollBar().setValue(w.report.verticalScrollBar().value()+w.report.cursorRect().top()-25);app.processEvents();w.grab().save(str(D/'native-mti-summary.png'))
  print('AUTO_LAB_NATIVE_REPORT_READY: real completed board suite, inline summary charts; no new hardware run',flush=True)
 QTimer.singleShot(1500,capture);sys.exit(app.exec())
if __name__=='__main__':main()

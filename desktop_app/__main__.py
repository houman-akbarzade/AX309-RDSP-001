"""Native PySide6 desktop application. Run: python3 -m desktop_app."""
import os,sys,json,time,secrets,subprocess,traceback
from pathlib import Path
from dataclasses import asdict
import numpy as np
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QPointF,QRectF
from PySide6.QtGui import QColor,QPainter,QPen,QImage,QPolygonF,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
 QLabel,QComboBox,QPushButton,QDoubleSpinBox,QSpinBox,QTableWidget,QTableWidgetItem,
 QTextEdit,QSplitter,QGroupBox,QFormLayout,QLineEdit)
from .scenarios import LIBRARY,prepare,exact_reference,score,RANGE_STEP,VELOCITY_STEP,ROOT
PROGRAMMER=Path.home()/'.local/opt/ax309-programmer/usr/bin/openFPGALoader'
BITSTREAM=ROOT/'rtl/build/ise_uart_s05_ax309/uart_s05_ax309_top.bit'
class Plot(QWidget):
 def __init__(self,kind):
  super().__init__();self.kind=kind;self.data=None;self.targets=[];self.duration=10;self.records=[]
  self.setMinimumSize(320,250)
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
  p.fillRect(self.rect(),QColor('#111f31'));p.setPen(QColor('#dce8f8'))
  p.drawText(15,24,'RANGE–DOPPLER / actual selected source' if self.kind=='map' else 'COMMANDED trajectories / never FPGA-estimated')
  area=QRectF(55,45,self.width()-80,self.height()-95)
  if self.kind=='map':
   if self.data is not None:
    db=10*np.log10(np.maximum(np.array(self.data,dtype=float),1))
    db=np.fft.fftshift(db,axes=1);hi=float(db.max());norm=np.clip((db-(hi-65))/65,0,1)
    rgb=np.stack([255*norm**1.7,230*np.minimum(1,norm*1.7),255*np.sqrt(norm)],axis=-1).astype(np.uint8)
    image=QImage(rgb.data,32,128,96,QImage.Format_RGB888).copy()
    p.drawImage(area,image)
    p.setPen(QPen(QColor('#ffca68'),2))
    for r in self.records:
     x=area.left()+(r['signed_doppler_bin']+16+.5)/32*area.width()
     y=area.top()+(r['range_bin']+.5)/128*area.height()
     p.drawEllipse(QPointF(x,y),4,4)
   else:p.drawText(area,Qt.AlignCenter,'No range–Doppler data from selected source')
   p.setPen(QColor('#dce8f8'));p.drawRect(area)
   p.drawText(55,self.height()-20,'Radial velocity: −7.5 … +7.03 m/s')
   p.drawText(8,55,'0 km');p.drawText(8,self.height()-55,'19 km')
  else:
   t=np.linspace(-self.duration/2,self.duration/2,81)
   palette=['#75d8fa','#ffca68','#e099fa','#72e0b2']
   paths=[]
   for target in self.targets:
    theta=target.bearing;r=target.delay*RANGE_STEP
    x=r*np.sin(theta)+t*(target.velocity*np.sin(theta)+target.tangential*np.cos(theta))
    y=r*np.cos(theta)+t*(target.velocity*np.cos(theta)-target.tangential*np.sin(theta))
    paths.append((target,x,y))
   span=max([float(np.max(np.abs(x))) for _,x,y in paths]+[1500])
   ymax=max([float(np.max(y)) for _,x,y in paths]+[1500])*1.08
   for i,(target,x,y) in enumerate(paths):
    p.setPen(QPen(QColor(palette[i%4]),2))
    points=[QPointF(area.center().x()+xx/span*area.width()*.45,area.bottom()-yy/ymax*area.height()) for xx,yy in zip(x,y)]
    p.drawPolyline(QPolygonF(points));p.drawEllipse(points[40],5,5);p.drawText(points[40],target.name)
   p.setPen(QColor('#dce8f8'));p.drawRect(area)
   p.drawText(55,self.height()-20,'Known simulator paths; arrows/time are reference only')
class Worker(QThread):
 completed=Signal(object);failed=Signal(str)
 def __init__(self,config):super().__init__();self.config=config
 def run(self):
  try:
   c=self.config;start=time.monotonic()
   raw,targets,meta=prepare(c['scenario'],c['range'],c['velocity'],c['amplitude'],c['noise'])
   out=dict(mode=c['mode'],targets=targets,metadata=meta,records=[],power=None)
   if c['mode']=='Hardware':
    # This deployed bitstream has UART/IQ only. Never label host DSP as FPGA.
    if not PROGRAMMER.exists() or not BITSTREAM.exists():raise RuntimeError('UART/IQ programmer or bitstream missing')
    env=os.environ.copy();env['LD_LIBRARY_PATH']=str(PROGRAMMER.parents[1]/'lib/x86_64-linux-gnu')
    pr=subprocess.run([str(PROGRAMMER),'-c','digilent_hs2','--freq','1000000','-m',str(BITSTREAM)],env=env,capture_output=True,text=True,timeout=30)
    if pr.returncode:raise RuntimeError(pr.stdout+pr.stderr)
    from pc_link.serial_io import connect_serial_port
    from pc_link.board_iq import run_board_iq_smoke
    uart=connect_serial_port(c['port'])
    try:
     transfer_start=time.monotonic()
     result=run_board_iq_smoke(uart,secrets.token_bytes(16),23,raw=raw)
     out['transfer_s']=time.monotonic()-transfer_start
     out['hardware_iq']=asdict(result)
    finally:uart.io.close()
    out['status']='IQ PASS | DSP NOT VERIFIED (deployed UART/IQ-only design)'
   elif c['mode']=='Reference':
    begin=time.monotonic();result,telemetry=exact_reference(raw)
    out.update(records=result['clusters'],power=result['power'],telemetry=telemetry,
     processing_s=time.monotonic()-begin)
    out['comparison']=score(result['clusters'],targets)
    out['status']='REFERENCE ONLY | '+('ASSOCIATION PASS' if out['comparison']['all_targets_matched'] else 'ASSOCIATION FAIL')
   else:
    # Deliberately artificial picture; no detector or hardware claim.
    power=np.ones((128,32))
    for t in targets:
     r,b=np.indices((128,32));db=(b-t.velocity/VELOCITY_STEP+16)%32-16
     power+=1e7*t.amplitude**2*np.exp(-((r-t.delay)/2)**2-db**2)
    out.update(power=power.tolist(),status='DEMO ONLY | synthetic image | NOT VERIFIED')
   out['elapsed_s']=time.monotonic()-start
   self.completed.emit(out)
  except Exception:self.failed.emit(traceback.format_exc())
class Window(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('AX309 Radar Lab');self.resize(1350,880)
  root=QWidget();self.setCentralWidget(root);layout=QVBoxLayout(root)
  title=QLabel('AX309  /  Radar Signal Processing Lab');title.setFont(QFont('Sans',20,QFont.Bold));layout.addWidget(title)
  self.banner=QLabel('Choose a source. Hardware currently verifies UART/IQ; full DSP deployment is OPEN.')
  self.banner.setWordWrap(True);layout.addWidget(self.banner)
  row=QHBoxLayout();layout.addLayout(row)
  form=QFormLayout();row.addLayout(form,1)
  self.scenario=QComboBox();self.scenario.addItems(LIBRARY);form.addRow('Scenario',self.scenario)
  self.mode=QComboBox();self.mode.addItems(['Hardware','Reference','Demo']);form.addRow('Result source',self.mode)
  self.port=QLineEdit('/dev/ttyUSB1');form.addRow('UART · 115200 / 8N1',self.port)
  self.range=QSpinBox();self.range.setRange(-15,15);form.addRow('Range offset · bins',self.range)
  self.velocity=QDoubleSpinBox();self.velocity.setRange(-5,5);self.velocity.setSingleStep(.46875);self.velocity.setDecimals(4);form.addRow('Radial velocity offset · m/s',self.velocity)
  self.amplitude=QDoubleSpinBox();self.amplitude.setRange(.1,2);self.amplitude.setValue(1);self.amplitude.setSingleStep(.1);form.addRow('Amplitude multiplier',self.amplitude)
  self.noise=QDoubleSpinBox();self.noise.setDecimals(4);self.noise.setRange(0,.15);self.noise.setValue(.002);self.noise.setSingleStep(.002);form.addRow('Complex noise RMS',self.noise)
  self.duration=QDoubleSpinBox();self.duration.setRange(1,30);self.duration.setValue(10);form.addRow('Reference path span · s',self.duration)
  self.run=QPushButton('Run selected source');self.run.clicked.connect(self.execute);form.addRow(self.run)
  limits=QLabel('Frozen radar: 10 GHz · Fs 1 MHz · PRI 1 ms\n33 × 128 IQ · LFM16 / 250 kHz · FFT32\nRange grid 149.896 m; Doppler grid 0.46875 m/s\nOne CPI per run. Reference path span affects drawing only.\nAircraft tangential speed is illustrative; radial speed is constrained.\nREQ-RNG-03 FAIL; statistical qualification OPEN.');limits.setWordWrap(True);form.addRow(limits)
  self.path=Plot('path');row.addWidget(self.path,2);self.map=Plot('map');row.addWidget(self.map,2)
  self.truth=QTableWidget(0,5);self.truth.setHorizontalHeaderLabels(['Reference target','Range bin','Range · m','Radial velocity · m/s','Amplitude'])
  self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(['Record','Range bin','Range · m','Doppler bin','Velocity · m/s','Peak integer','Cells'])
  for table in (self.truth,self.table):table.horizontalHeader().setStretchLastSection(True);layout.addWidget(table)
  self.log=QTextEdit();self.log.setReadOnly(True);self.log.setMaximumHeight(160);layout.addWidget(self.log)
  self.setStyleSheet('QMainWindow,QWidget{background:#17283d;color:#e7edf8;} QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QTextEdit,QTableWidget{background:#223952;padding:4px;} QPushButton{background:#176d92;padding:12px;font-weight:bold;} QHeaderView::section{background:#29445e;color:#e7edf8;padding:4px;}')
  self.worker=None
 def execute(self):
  if self.worker and self.worker.isRunning():return
  config=dict(scenario=self.scenario.currentText(),mode=self.mode.currentText(),port=self.port.text(),range=self.range.value(),velocity=self.velocity.value(),amplitude=self.amplitude.value(),noise=self.noise.value())
  self.run.setEnabled(False);self.banner.setText(config['mode']+' · running…')
  self.map.data=None;self.map.records=[];self.map.update();self.table.setRowCount(0)
  self.worker=Worker(config);self.worker.completed.connect(self.show_result);self.worker.failed.connect(self.show_error);self.worker.start()
 def show_error(self,text):
  self.run.setEnabled(True);self.banner.setText('FAIL · execution failed; no accepted result');self.log.setPlainText(text)
 def show_result(self,out):
  self.run.setEnabled(True);self.banner.setText(out['status'])
  self.path.targets=out['targets'];self.path.duration=self.duration.value();self.path.update()
  self.map.data=out['power'];self.map.records=out['records'];self.map.update()
  self.truth.setRowCount(len(out['targets']))
  for i,t in enumerate(out['targets']):
   for j,v in enumerate([t.name,t.delay,f'{t.delay*RANGE_STEP:.2f}',t.velocity,t.amplitude]):self.truth.setItem(i,j,QTableWidgetItem(str(v)))
  self.table.setRowCount(len(out['records']))
  for i,r in enumerate(out['records']):
   values=[r['record_id'],r['range_bin'],f"{r['range_bin']*RANGE_STEP:.2f}",r['doppler_bin'],f"{r['signed_doppler_bin']*VELOCITY_STEP:.4f}",r['power_stored_integer'],r['cluster_cells']]
   for j,v in enumerate(values):self.table.setItem(i,j,QTableWidgetItem(str(v)))
  summary={k:v for k,v in out.items() if k not in ('power','targets','records')}
  self.log.setPlainText(json.dumps(summary,indent=2,default=str))
  self.last_result=out
 def closeEvent(self,event):
  if self.worker and self.worker.isRunning():event.ignore();return
  event.accept()
def main():
 app=QApplication(sys.argv);window=Window();window.show()
 if '--smoke' in sys.argv:
  window.mode.setCurrentText('Reference');window.noise.setValue(0);window.execute()
  def finish():
   if window.worker.isRunning():QTimer.singleShot(200,finish);return
   if not hasattr(window,'last_result'):print('GUI_SMOKE_FAIL');app.exit(1);return
   path=ROOT/'engineering/evidence/s11/bringup-20261112-r2/desktop-reference.png'
   window.grab().save(str(path));print('GUI_SMOKE_PASS',window.last_result['status'],flush=True);app.quit()
  QTimer.singleShot(200,finish)
 sys.exit(app.exec())
if __name__=='__main__':main()

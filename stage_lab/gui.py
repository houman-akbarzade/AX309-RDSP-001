"""Separate Stage Lab v0.2 GUI. The stable v0.1 GUI/shortcut remains unchanged."""
import sys,json,os,subprocess
from pathlib import Path
import numpy as np
from PySide6.QtCore import Qt,QRectF,QPointF,QTimer
from PySide6.QtGui import QPainter,QColor,QPen,QPolygonF,QFont
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QSpinBox,QDoubleSpinBox,QCheckBox,QPushButton,QLineEdit,QLabel,QTabWidget,QTextEdit,QTableWidget,QTableWidgetItem,QFileDialog,QSplitter
from .application import Worker
from .models import NAMES,ROOT
from .transport import PROGRAMMER,stable_bitstream
from desktop_app.scenarios import LIBRARY,RANGE_STEP,VELOCITY_STEP
from desktop_app.__main__ import Plot
HELP="""<h2>آزمایشگاه مرحله‌ای AX309، نسخه 0.2</h2>
<p>این برنامه و Bitstreamهای تست از نسخه پایدار 0.1 جدا هستند. Run با گزینه Program، نسخه تست را فقط در SRAM بارگذاری می‌کند؛ Flash تغییر نمی‌کند.</p>
<p><b>Stage:</b> انتخاب MF، MTI، FFT، Power، CFAR یا Grouping. حالت File raw ورودی خام فایل را از مراحل سخت‌افزاری عبور می‌دهد؛ File FFT برای ورودی FFT فایل و اجرای ترکیبی Power/CFAR است. خروجی انتخابی واقعاً از FPGA دریافت می‌شود.</p>
<p><b>Input:</b> Software previous-stage یعنی تولید داده مرحله قبل با مدل Float نرم‌افزاری و سپس کوانتیزه‌کردن به قالب ورودی سخت‌افزار. برای Power، FFT نرم‌افزاری تزریق می‌شود؛ برای CFAR، Power نرم‌افزاری و برای Grouping ماسک CFAR و Power نرم‌افزاری تزریق می‌شود. مدل Fixed/IP در تولید این ورودی‌ها دخالت ندارد.</p>
<p>گزینه Software FFT → hardware Power + CFAR دو بلوک را با هم تست می‌کند. اختلاف این حالت مربوط به ترکیب Power و CFAR است؛ حالت پیش‌فرض CFAR، خود CFAR را مستقل می‌سنجد.</p>
<p>Raw PRI/CPI through hardware، داده خام را مرحله‌به‌مرحله از نسخه‌های سخت‌افزاری عبور می‌دهد؛ بین مراحل فقط انتقال UART و تعویض Bitstream انجام می‌شود، نه پردازش نرم‌افزاری. بنابراین زمان آن بیشتر است. نرم‌افزار مقایسه مستقل مرحله آخر و مقایسه کل زنجیره را جدا ثبت می‌کند.</p>
<p>File: فایل MAT یا NPY مختلط یا NPZ با data/codes برای مراحل مختلط؛ برای Power ورودی FFT مختلط است؛ برای CFAR آرایه Power و برای Grouping فایل NPZ شامل power و mask لازم است. قالب Normalized float یا Stored codes را صریح انتخاب کنید. آرایه‌ها slow-time/bin-major و دارای 128 ستون برد هستند؛ MF می‌تواند 1 تا 33 PRI، MTI دارای 2 تا 33 ردیف و FFT/Power/CFAR/Grouping دارای 32 ردیف هستند.</p>
<p>Engine و Arithmetic انتخاب Python، MATLAB یا هر دو، و Float، Fixed یا هر دو هستند. MATLAB واقعاً اجرا می‌شود. Fixed FFT در هر دو زبان از C-model رسمی v7.1 استفاده می‌کند؛ Float FFT با NumPy/MATLAB جدا محاسبه می‌شود.</p>
<p>ورودی نمایش‌داده‌شده از FPGA بازخوانی و بایت‌به‌بایت کنترل شده است. تمام مراجع مقایسه مستقل، همان داده کوانتیزه‌شده ورودی را استفاده می‌کنند. خطای کوانتیزه‌کردن ورودی جدا گزارش می‌شود.</p>
<p>Slice شماره PRI یا bin برای نمودار ردیفی، Component مؤلفه I/Q، دامنه یا فاز است. Hardware، چهار مرجع انتخابی و نمودار اختلاف در کنار ورودی بازخوانی‌شده دیده می‌شوند. در نماهای CFAR، ماسک از سخت‌افزار خوانده می‌شود. جدول رکوردها بدون حذف هدف/خوشه اضافی است.</p>
<p>Restore stable FPGA نسخه کامل پایدار را به SRAM برمی‌گرداند. این کار را هنگام بازگشت به برنامه اصلی انجام دهید. این آزمون‌ها به‌تنهایی تأیید Pd/Pfa نیستند؛ قبل از CFAR نیز قاعده آستانه‌گذاری و مجموعه نویز/هدف مستقل لازم است.</p>"""
class Curves(QWidget):
 def __init__(self,title):
  super().__init__();self.title=title;self.lines={};self.setMinimumSize(280,260)
 def paintEvent(self,event):
  p=QPainter(self);p.fillRect(self.rect(),QColor('#101c2c'));p.setRenderHint(QPainter.Antialiasing)
  p.setPen(QColor('#e7edf8'));p.drawText(12,22,self.title);a=QRectF(62,80,self.width()-82,self.height()-126)
  p.drawRect(a)
  if not self.lines:return
  arrays=[np.asarray(y,float).reshape(-1) for y in self.lines.values() if len(y)]
  if not arrays:return
  hi=max(float(y.max()) for y in arrays);lo=min(float(y.min()) for y in arrays)
  if hi==lo:hi+=max(1,abs(hi)*.05);lo-=max(1,abs(lo)*.05)
  colors=['#ffca68','#75d8fa','#72e0b2','#e099fa','#ff8585']
  for i,(name,y) in enumerate(self.lines.items()):
   y=np.asarray(y,float).reshape(-1)
   if len(y)==0:continue
   p.setPen(QPen(QColor(colors[i%len(colors)]),2))
   pts=[QPointF(a.left()+k/max(1,len(y)-1)*a.width(),a.bottom()-(v-lo)/(hi-lo)*a.height()) for k,v in enumerate(y)]
   if len(pts)>1:p.drawPolyline(QPolygonF(pts))
   p.drawText(12+(i%2)*int(self.width()/2),42+(i//2)*15,name)
  p.setPen(QColor('#e7edf8'));p.drawText(3,84,f'{hi:.3g}');p.drawText(3,int(a.bottom()),f'{lo:.3g}')
  p.drawText(62,self.height()-16,'Range cell / record index')
class StageMap(Plot):
 def paintEvent(self,event):
  if self.data is not None and not np.any(np.asarray(self.data)>0):
   p=QPainter(self);p.fillRect(self.rect(),QColor('#101c2c'));p.setPen(QColor('#e7edf8'));p.drawText(self.rect(),Qt.AlignCenter,'All-zero Power map / no positive Power cells');return
  super().paintEvent(event)
class Window(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('AX309 Stage Lab v0.2 · stable v0.1 preserved');self.resize(1440,950);self.worker=None;self.last=None
  root=QWidget();self.setCentralWidget(root);outer=QVBoxLayout(root)
  title=QLabel('AX309 Stage Lab v0.2 / isolated stage measurements');title.setFont(QFont('Sans',19,QFont.Bold));outer.addWidget(title)
  self.banner=QLabel('Stable v0.1 preserved. Each stage uses a separate test image.');self.banner.setWordWrap(True);outer.addWidget(self.banner)
  row=QHBoxLayout();outer.addLayout(row)
  form=QFormLayout();row.addLayout(form)
  self.target=QComboBox()
  for k in range(1,7):self.target.addItem(NAMES[k],k)
  self.target.setCurrentIndex(3);form.addRow('Stage',self.target)
  self.input=QComboBox();form.addRow('Input',self.input);self.target.currentIndexChanged.connect(self.update_inputs);self.update_inputs()
  self.injection=QComboBox();self.injection.addItems(['Python Float','MATLAB Float']);form.addRow('Software input engine',self.injection)
  self.engine=QComboBox();self.engine.addItems(['Both','Python','MATLAB']);form.addRow('Reference engine',self.engine)
  self.arithmetic=QComboBox();self.arithmetic.addItems(['Both','Float','Fixed']);form.addRow('Reference arithmetic',self.arithmetic)
  self.scenario=QComboBox();self.scenario.addItems(list(LIBRARY)+['Noise only']);form.addRow('Scenario',self.scenario)
  self.noise=QDoubleSpinBox();self.noise.setDecimals(4);self.noise.setRange(0,.15);self.noise.setValue(.002);form.addRow('Noise RMS',self.noise)
  self.scenario.currentTextChanged.connect(lambda name:self.noise.setValue(.06 if name=='Low SNR' else .002))
  self.seed=QSpinBox();self.seed.setRange(0,2147483647);self.seed.setValue(20261112);form.addRow('Seed',self.seed)
  self.pris=QSpinBox();self.pris.setRange(1,33);self.pris.setValue(33);self.pris.setEnabled(False);form.addRow('MF / MTI PRI count',self.pris)
  self.file=QLineEdit();form.addRow('Input file',self.file)
  self.format=QComboBox();self.format.addItems(['Normalized float','Stored codes']);form.addRow('File format',self.format)
  choose=QPushButton('Choose NPY / NPZ / MAT');choose.clicked.connect(self.choose);form.addRow(choose)
  self.port=QLineEdit('/dev/ttyUSB1');form.addRow('UART · 115200 / 8N1',self.port)
  self.program=QCheckBox('Program selected test image · SRAM');self.program.setChecked(True);form.addRow(self.program)
  self.run=QPushButton('Run stage comparison');self.run.clicked.connect(self.execute);form.addRow(self.run)
  self.restore=QPushButton('Restore stable FPGA v0.1');self.restore.clicked.connect(self.restore_stable);form.addRow(self.restore)
  self.slice=QSpinBox();self.slice.setRange(0,32);form.addRow('Slice · PRI / Doppler bin',self.slice)
  self.component=QComboBox();self.component.addItems(['Magnitude','I','Q','Phase']);form.addRow('Component',self.component)
  self.save=QPushButton('Save comparison JSON + NPZ');self.save.clicked.connect(self.save_result);self.save.setEnabled(False);form.addRow(self.save)
  self.slice.valueChanged.connect(self.refresh);self.component.currentTextChanged.connect(self.refresh)
  self.tabs=QTabWidget();row.addWidget(self.tabs,1)
  plots=QSplitter(Qt.Horizontal);self.pin=Curves('Actual input echoed by FPGA');self.pout=Curves('Hardware / independent references');self.perr=Curves('Hardware minus reference')
  for p in [self.pin,self.pout,self.perr]:plots.addWidget(p)
  self.tabs.addTab(plots,'Waveforms / differences')
  self.map=StageMap('map');self.map.cfar=True;self.tabs.addTab(self.map,'Power / actual CFAR / clusters')
  self.records=QTableWidget();self.tabs.addTab(self.records,'All hardware records')
  self.metrics=QTextEdit();self.metrics.setReadOnly(True);self.tabs.addTab(self.metrics,'RMSE / exact comparison / transport')
  self.sweep=QTextEdit();self.sweep.setReadOnly(True);self.tabs.addTab(self.sweep,'Threshold exploration · not Pd/Pfa acceptance')
  help=QTextEdit();help.setReadOnly(True);help.setHtml(HELP);help.setLayoutDirection(Qt.RightToLeft);self.tabs.addTab(help,'راهنمای فارسی')
  self.setStyleSheet('QWidget{background:#17283d;color:#e7edf8;} QComboBox,QLineEdit,QTextEdit,QTableWidget,QSpinBox,QDoubleSpinBox{background:#223952;padding:4px;} QPushButton{background:#176d92;padding:9px;} QHeaderView::section{background:#29445e;color:white;}')
 def update_inputs(self):
  if hasattr(self,'pris'):
   self.pris.setEnabled(self.target.currentData() in (1,2));self.pris.setMinimum(2 if self.target.currentData()==2 else 1)
  self.input.clear();self.input.addItems(['Software previous-stage','Raw PRI/CPI through hardware','File','File raw PRI/CPI through hardware'])
  if self.target.currentData()==5:self.input.addItems(['Software FFT → hardware Power + CFAR','File FFT → hardware Power + CFAR'])
 def choose(self):
  p,_=QFileDialog.getOpenFileName(self,'Stage input',str(ROOT),'Arrays (*.npz *.npy *.mat)')
  if p:
   self.file.setText(p)
   if not self.input.currentText().startswith('File'):self.input.setCurrentText('File')
 def execute(self):
  if self.worker and self.worker.isRunning():return
  c=dict(injection_engine=self.injection.currentText(),target=self.target.currentData(),input_mode=self.input.currentText(),engine=self.engine.currentText(),arithmetic=self.arithmetic.currentText(),scenario=self.scenario.currentText(),noise=self.noise.value(),seed=self.seed.value(),pri_count=self.pris.value(),file=self.file.text(),file_format=self.format.currentText(),port=self.port.text(),program=self.program.isChecked())
  if hasattr(self,'velocities'):c['target_velocities']=self.velocities()
  self.run.setEnabled(False);self.restore.setEnabled(False);self.save.setEnabled(False)
  self.worker=Worker(c);self.worker.progress.connect(self.banner.setText);self.worker.completed.connect(self.result);self.worker.failed.connect(self.error);self.worker.start()
 def error(self,text):
  self.run.setEnabled(True);self.restore.setEnabled(True);self.banner.setText('FAILED / no valid comparison');self.metrics.setPlainText(text);self.tabs.setCurrentWidget(self.metrics)
 def result(self,out):
  self.run.setEnabled(True);self.restore.setEnabled(True);self.save.setEnabled(True);self.last=out
  self.banner.setText(f"Hardware {NAMES[out['target']]} received / input echo verified / {out['elapsed_s']:.1f} s / "+out['origin']['origin'])
  summary={k:v for k,v in out.items() if k not in ('actual_input','output','references','source_input','truth')}
  self.metrics.setPlainText(json.dumps(summary,indent=2,default=str))
  t=out['target']
  if t<=2:self.slice.setMaximum(out['output'].shape[0]-1)
  else:
   self.slice.setMaximum(31)
   power=np.abs(out['output']/32768)**2 if t==3 else np.asarray(out['output'],float) if t==4 else np.asarray(out['output'][0],float) if t==5 else np.asarray(out['actual_input'][0],float)
   self.slice.setValue(int(np.argmax(np.sum(power,axis=1))))
  self.sweep.setPlainText(json.dumps(out.get('threshold_exploration',{'note':'Select FFT or Power. Noise only gives cell exceedance fractions; target scenarios give exploratory target fractions.'}),indent=2));self.refresh()
 def values(self,a,stage,fixed=True):
  if stage<=3:
   z=np.asarray(a)/(32768 if fixed else 1);z=z[min(self.slice.value(),z.shape[0]-1)]
   return {'I':z.real,'Q':z.imag,'Magnitude':np.abs(z),'Phase':np.angle(z)}[self.component.currentText()]
  if stage==4:return np.asarray(a,float)[min(self.slice.value(),len(a)-1)]/((1<<30) if fixed else 1)
  if stage==5:return np.asarray(a[1],float)[min(self.slice.value(),31)]
  return np.array([r.get('power_stored_integer',0)/(1<<30) if fixed else r.get('power_linear',0) for r in a])
 def refresh(self,*args):
  if not self.last:return
  o=self.last;t=o['target'];entry=o['entry']
  self.pin.lines={'FPGA input':self.values(o['actual_input'],entry)}
  y=self.values(o['output'],t);self.pout.lines={'Hardware':y};self.perr.lines={}
  for label,a in o['references'].items():
   z=self.values(a,t,'Fixed' in label);self.pout.lines[label]=z
   if z.shape==y.shape:self.perr.lines[label]=np.angle(np.exp(1j*(y-z))) if self.component.currentText()=='Phase' and t<=3 else y-z
  for p in [self.pin,self.pout,self.perr]:p.update()
  self.map.source='Actual FPGA output';self.map.targets=o['truth'];self.map.records=[]
  self.map.data=None;self.map.mask=None
  if t==3:self.map.data=(np.abs(np.asarray(o['output'])/32768)**2).T
  if t==4:self.map.data=np.asarray(o['output'],float).T/(1<<30)
  if t==5:self.map.data=np.asarray(o['output'][0],float).T/(1<<30);self.map.mask=o['output'][1].T
  if t==6:
   self.map.source='FPGA input CFAR map + hardware clusters'
   self.map.data=np.asarray(o['actual_input'][0],float).T/(1<<30);self.map.mask=o['actual_input'][1].T;self.map.records=o['output']
   rows=o['output'];keys=['record_id','range_bin','doppler_bin','signed_doppler_bin','power_stored_integer','cluster_cells','tie_flag','max_equal_power_cells']
   self.records.setColumnCount(len(keys));self.records.setHorizontalHeaderLabels(keys);self.records.setRowCount(len(rows))
   for i,r in enumerate(rows):
    for j,k in enumerate(keys):self.records.setItem(i,j,QTableWidgetItem(str(r[k])))
   self.records.resizeColumnsToContents()
  self.map.update()
 def save_result(self):
  if not self.last:return
  path,_=QFileDialog.getSaveFileName(self,'Comparison summary',str(ROOT/'deliverables/stage_comparison.json'),'JSON (*.json)')
  if path:
   import shutil
   src=Path(self.last['journal'])
   for ext in ['.json','.npz']:
    dst=Path(path).with_suffix(ext);original=src.with_suffix(ext)
    if dst.resolve()!=original.resolve():shutil.copyfile(original,dst)
 def restore_stable(self):
  if self.worker and self.worker.isRunning():return
  stable=stable_bitstream()
  env=os.environ.copy();env['LD_LIBRARY_PATH']=str(PROGRAMMER.parents[1]/'lib/x86_64-linux-gnu')
  p=subprocess.run([str(PROGRAMMER),'-c','digilent_hs2','--freq','1000000','-m',str(stable)],env=env,capture_output=True,text=True,timeout=40)
  if p.returncode:self.error(p.stdout+p.stderr)
  else:self.banner.setText('Stable v0.1 full radar restored to SRAM. Next Stage Run loads its test image.')
 def closeEvent(self,event):
  if self.worker and self.worker.isRunning():event.ignore()
  else:event.accept()
from .gui_upgrade import upgrade_window
Window=upgrade_window(Window)

def main():
 app=QApplication(sys.argv);w=Window();w.show()
 if '--show-power' in sys.argv:
  w.target.setCurrentIndex(3);w.engine.setCurrentText('Both');
  if '--matlab-input' in sys.argv:w.injection.setCurrentText('MATLAB Float')
  w.execute()
  def snapshot():
   if w.worker.isRunning():QTimer.singleShot(200,snapshot);return
   if not w.last:print('STAGE_GUI_FAIL',w.metrics.toPlainText(),flush=True);return
   out=ROOT/'engineering/evidence/stage_lab_v0.2';out.mkdir(parents=True,exist_ok=True);w.grab().save(str(out/'gui-power.png'))
   print('STAGE_GUI_HARDWARE_PASS',json.dumps(w.last['metrics']),flush=True)
  QTimer.singleShot(200,snapshot)
 sys.exit(app.exec())
if __name__=='__main__':main()

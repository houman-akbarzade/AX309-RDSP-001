"""AX309 Radar Lab: physical DSP results, independent Float reference, explicit sources."""
import os,sys,json,time,traceback,csv
from pathlib import Path
from dataclasses import asdict
import numpy as np
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QPointF,QRectF
from PySide6.QtGui import QColor,QPainter,QPen,QImage,QPolygonF,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
 QLabel,QComboBox,QPushButton,QDoubleSpinBox,QSpinBox,QTableWidget,QTableWidgetItem,
 QTextEdit,QSplitter,QGroupBox,QFormLayout,QLineEdit,QCheckBox,QTabWidget,QFileDialog,
 QMessageBox,QScrollArea)
from .scenarios import LIBRARY,exact_reference,score,RANGE_STEP,VELOCITY_STEP,ROOT
from .reference import prepare_with_source,float_reference,native_from_power,compare_geometry
from pc_link.board_dsp import BITSTREAM,program_sram,run_board_dsp
HELP="""<h2>راهنمای AX309 Radar Lab</h2>
<p><b>نمای چپ: مسیر معلوم اهداف</b><br>مسیرها از سناریوی ورودی رسم می‌شوند. دایره، موقعیت در مرکز بازه نمایشی است. این مسیرها رهگیری یا تخمین زاویه توسط FPGA نیستند. پردازش فعلی فقط برد و سرعت شعاعی را برآورد می‌کند.</p>
<p><b>نمای راست: نتیجه پردازش منبع انتخاب‌شده</b><br>در حالت Hardware، نقشه Power و رکوردهای کلاستر از خود FPGA دریافت می‌شوند. محور افقی سرعت شعاعی و محور عمودی برد است. حلقه زرد قله کلاستر، ضربدر سبز هدف معلوم و نقطه قرمز سلول CFAR است.</p>
<h3>کنترل‌های ورودی</h3>
<ul><li>Scenario: تک‌هدف، دوهدف، مسیرهای متقاطع، چندهدف، هدف ضعیف کنار قوی، کلاتر، اهداف نزدیک و SNR پایین.</li>
<li>Result source: Hardware اجرای واقعی برد؛ Float reference مرجع Float64؛ Legacy fixed reference مدل عددصحیح FFT قبلی؛ Demo فقط تصویر مصنوعی.</li>
<li>UART: نام پایدار CP2102؛ ارتباط 115200 baud و 8N1.</li>
<li>Range offset: جابه‌جایی برد همه اهداف بر حسب سلول 149.896 متری.</li>
<li>Velocity offset: تغییر سرعت شعاعی همه اهداف؛ شبکه داپلر 0.46875 متر بر ثانیه است. سرعت خارج بازه [-7.5,7.5) رد می‌شود.</li>
<li>Amplitude multiplier: ضریب دامنه اهداف؛ توان با مربع دامنه تغییر می‌کند.</li>
<li>Complex noise RMS: RMS نویز مختلط ورودی، بر حسب دامنه نرمال‌شده؛ 0 برای بدون نویز.</li>
<li>Seed: بذر نویز برای تکرارپذیری. انتخاب Low SNR مقدار پیش‌فرض نویز را 0.06 می‌کند.</li>
<li>Path span: طول زمانی مسیر نمایشی؛ نرخ واقعی یا مدت انتقال داده نیست. هر Run تنها یک CPI از 33×128 نمونه مختلط است.</li></ul>
<h3>اتصال و اجرا</h3>
<p>Refresh ports درگاه‌های سریال را فهرست می‌کند. Program FPGA طرح کامل را فقط در SRAM پروگرام می‌کند و نشست قبلی را پاک می‌کند؛ Flash تغییر نمی‌کند. پس از یک بار پروگرام، چند Run متوالی بدون پروگرام مجدد ممکن است. Hardware Run به ترتیب IQ را می‌فرستد، بازخوانی را بایت‌به‌بایت کنترل می‌کند، RUN می‌دهد، همه کلاسترها را می‌گیرد، COMMIT را بررسی و ثبت می‌کند، نقشه واقعی Power را می‌خواند و CPI را RELEASE می‌کند.</p>
<p>اگر ارتباط قطع شد، نتیجه ناقص معتبر نمایش داده نمی‌شود. پیش از پروگرام مجدد، گزارش خطا و وضعیت CPI قبلی نگه داشته می‌شود. بازیابی خودکار نشست نیمه‌تمام هنوز فراهم نیست.</p>
<h3>کنترل‌های نمایش</h3>
<ul><li>Range–Doppler: نقشه دوبعدی توان با جابه‌جایی FFT به سرعت‌های منفی/مثبت.</li>
<li>Range profile: بیشینه توان روی داپلر برای هر سلول برد.</li>
<li>Doppler slice: توان داپلر در سلول برد انتخاب‌شده؛ با انتخاب یک رکورد جدول نیز تغییر می‌کند.</li>
<li>Power dB / Linear: توان نرمال‌شده؛ dB برابر 10log10(P)، بدون کالیبراسیون به dBm.</li>
<li>Dynamic range: دامنه رنگ نسبت به قوی‌ترین سلول، بر حسب dB؛ فقط نمایش را تغییر می‌دهد.</li>
<li>Clusters / Truth: روشن و خاموش کردن قله‌های واقعی و موقعیت معلوم اهداف.</li>
<li>CFAR cells: در Hardware از نقشه Power دریافت‌شده، با همان محاسبه عددصحیح روی PC بازسازی می‌شود؛ خود رکوردهای کلاستر از FPGA هستند.</li>
<li>Valid CUT region: محدوده CFAR با برد 3..109 و داپلر 3..28؛ بیرون آن آشکارسازی انجام نمی‌شود.</li>
<li>Compare Float: مقایسه توان و مشخصات قله/اندازه کلاسترها با مرجع مستقل Float64 روی منبع پیش از کوانتیزه‌کردن IQ؛ مقایسه کامل عضویت خوشه از رکوردهای نهایی ممکن نیست.</li>
<li>Save results: ذخیره JSON و CSV همه رکوردها همراه منبع نتیجه؛ هیچ کلاستر اضافی حذف نمی‌شود.</li></ul>
<p>زمان انتقال IQ، انتظار نتیجه و کل اجرا جدا نمایش داده می‌شوند. زمان انتظار نتیجه شامل انتقال UART رکوردها است و اندازه‌گیری خالص تأخیر DSP نیست. تطبیق اهداف یک معیار توسعه است؛ تأیید آماری Pd/Pfa و حل محدودیت اهداف نزدیک محسوب نمی‌شود.</p>"""
class Plot(QWidget):
 def __init__(self,kind):
  super().__init__();self.kind=kind;self.data=None;self.mask=None;self.targets=[];self.duration=10;self.records=[]
  self.view='Range–Doppler';self.db=True;self.dr=65;self.clusters=True;self.truth=True;self.cfar=False;self.roi=True;self.slice=40
  self.source='No data';self.setMinimumSize(320,240)
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);p.fillRect(self.rect(),QColor('#101c2c'))
  p.setPen(QColor('#dce8f8'));p.drawText(12,23,'Commanded truth paths (not tracks)' if self.kind=='path' else self.source+' / '+self.view)
  area=QRectF(65,46,self.width()-90,self.height()-96)
  if self.kind=='path':
   t=np.linspace(-self.duration/2,self.duration/2,81);paths=[]
   for target in self.targets:
    a=target.bearing;r=target.delay*RANGE_STEP
    x=r*np.sin(a)+t*(target.velocity*np.sin(a)+target.tangential*np.cos(a))
    y=r*np.cos(a)+t*(target.velocity*np.cos(a)-target.tangential*np.sin(a));paths.append((target,x,y))
   span=max([float(np.max(np.abs(x))) for _,x,y in paths]+[1500])
   ymax=max([float(np.max(y)) for _,x,y in paths]+[1500])*1.08
   for i,(target,x,y) in enumerate(paths):
    p.setPen(QPen(QColor(['#75d8fa','#ffca68','#e099fa','#72e0b2'][i%4]),2))
    pts=[QPointF(area.center().x()+xx/span*area.width()*.45,area.bottom()-yy/ymax*area.height()) for xx,yy in zip(x,y)]
    p.drawPolyline(QPolygonF(pts));p.drawEllipse(pts[40],5,5);p.drawText(pts[40],target.name)
   p.setPen(QColor('#dce8f8'));p.drawRect(area)
   p.drawText(15,42,f'{ymax/1000:.1f} km');p.drawText(18,int(area.bottom()),'0 km')
   p.drawText(65,self.height()-18,f'Known input paths / {self.duration:g} s illustration')
   return
  if self.data is None:
   p.drawText(area,Qt.AlignCenter,'Run a source to receive data');p.drawRect(area);return
  a=np.asarray(self.data,float);db=10*np.log10(np.maximum(a,1e-30));hi=float(db.max())
  if self.view=='Range–Doppler':
   shifted=np.fft.fftshift(db if self.db else a,axes=1)
   norm=np.clip((shifted-(hi-self.dr))/self.dr,0,1) if self.db else np.clip(shifted/max(float(a.max()),1e-30),0,1)
   rgb=np.stack([255*norm**1.7,230*np.minimum(1,norm*1.7),255*np.sqrt(norm)],axis=-1).astype(np.uint8)
   rgb=np.ascontiguousarray(rgb);image=QImage(rgb.data,32,128,96,QImage.Format_RGB888).copy();p.drawImage(area,image)
   def xy(r,b):return QPointF(area.left()+((b+16)%32+.5)/32*area.width(),area.top()+(r+.5)/128*area.height())
   if self.roi:
    p.setPen(QPen(QColor('#c9d4e1'),1,Qt.DashLine))
    # Unshifted 3..28 is two regions after fftshift; excluded bins straddle zero.
    for left,right in [(19,32),(0,13)]:
     p.drawRect(QRectF(area.left()+left/32*area.width(),area.top()+3/128*area.height(),(right-left)/32*area.width(),107/128*area.height()))
   if self.cfar and self.mask is not None:
    p.setPen(QPen(QColor('#ff7474'),3))
    for r,b in np.argwhere(self.mask):p.drawPoint(xy(int(r),int(b)))
   if self.clusters:
    p.setPen(QPen(QColor('#ffca68'),2))
    for r in self.records:p.drawEllipse(xy(r['range_bin'],r['doppler_bin']),5,5)
   if self.truth:
    p.setPen(QPen(QColor('#76f0b3'),2))
    for t in self.targets:
     point=xy(t.delay,t.velocity/VELOCITY_STEP);x,y=point.x(),point.y()
     p.drawLine(QPointF(x-5,y),QPointF(x+5,y));p.drawLine(QPointF(x,y-5),QPointF(x,y+5))
   p.setPen(QColor('#dce8f8'));p.drawRect(area)
   for v in [-7.5,0,7.5]:
    x=area.left()+(v+7.5)/15*area.width();p.drawText(int(x)-15,self.height()-30,f'{v:g}')
   p.drawText(65,self.height()-10,'Radial velocity (m/s)')
   for r in [0,32,64,96,127]:
    y=area.top()+(r+.5)/128*area.height();p.drawText(5,int(y)+4,f'{r*RANGE_STEP/1000:.1f}')
   p.drawText(4,40,'km')
   label=f'{hi-self.dr:.1f} … {hi:.1f} dB' if self.db else f'0 … {a.max():.3g} linear'
   p.drawText(int(area.left())+5,40,label)
  else:
   profile=np.max(a,axis=1) if self.view=='Range profile' else np.fft.fftshift(a[self.slice])
   y=10*np.log10(np.maximum(profile,1e-30)) if self.db else profile
   ymax=float(y.max());ymin=ymax-self.dr if self.db else 0.
   scaled=np.clip((y-ymin)/max(ymax-ymin,1e-30),0,1)
   pts=[QPointF(area.left()+i/(len(y)-1)*area.width(),area.bottom()-v*area.height()) for i,v in enumerate(scaled)]
   p.setPen(QPen(QColor('#75d8fa'),2));p.drawPolyline(QPolygonF(pts));p.setPen(QColor('#dce8f8'));p.drawRect(area)
   p.drawText(5,55,f'{ymax:.2g}');p.drawText(5,int(area.bottom()),f'{ymin:.2g}')
   label='Range (km): 0 … 19.04' if self.view=='Range profile' else f'Velocity (m/s): −7.5 … +7.03 / range bin {self.slice}'
   p.drawText(65,self.height()-18,label)
class Worker(QThread):
 completed=Signal(object);failed=Signal(str);progress=Signal(str)
 def __init__(self,config):super().__init__();self.config=config
 def run(self):
  try:
   c=self.config;start=time.monotonic()
   if c.get('program'):
    self.progress.emit('Programming full DSP into FPGA SRAM…')
    result=program_sram();self.completed.emit(dict(program_only=True,programming=result));return
   raw,targets,meta,source=prepare_with_source(c['scenario'],c['range'],c['velocity'],c['amplitude'],c['noise'],seed=c['seed'])
   out=dict(mode=c['mode'],targets=targets,metadata=meta,records=[],power=None,mask=None)
   if c['mode']=='Hardware':
    h=run_board_dsp(raw,c['port'],progress=self.progress.emit)
    out.update(records=h['records'],power=np.asarray(h.pop('power'),float)/(1<<30),hardware=h)
    mask,recs=native_from_power(np.rint(out['power']*(1<<30)).astype(np.uint64))
    out['mask']=mask
    keys=['record_id','range_bin','doppler_bin','signed_doppler_bin','power_stored_integer','cluster_cells','tie_flag','max_equal_power_cells']
    check=all(tuple(a[k] for k in keys)==tuple(b[k] for k in keys) for a,b in zip(recs,out['records'])) and len(recs)==len(out['records'])
    if not check:raise RuntimeError('Hardware records disagree with exact C05 on downloaded FPGA Power')
    out['postprocessing_check']='FPGA records exactly match C05 on actual FPGA Power'
    out['status']='FPGA DSP COMMIT / IQ verified / actual Power + clusters'
   elif c['mode']=='Legacy fixed reference':
    r,telemetry=exact_reference(raw);out.update(records=r['clusters'],power=np.asarray(r['power'],float)/(1<<30),mask=np.array(r['mask'],bool),telemetry=telemetry,status='HOST ONLY / legacy fixed FFT reference')
   elif c['mode']=='Float reference':
    out.update(float_reference(source));out['status']='HOST ONLY / Float64 reference / pre-ADC source'
   else:
    a=np.ones((128,32))*1e-10
    for t in targets:
     r,b=np.indices(a.shape);d=(b-t.velocity/VELOCITY_STEP+16)%32-16
     a+=t.amplitude**2*np.exp(-((r-t.delay)/2)**2-d**2)
    out.update(power=a,status='DEMO ONLY / synthetic picture')
   if c['compare'] and c['mode'] not in ('Demo','Float reference'):
    self.progress.emit('Comparing with independent Float64 reference')
    f=float_reference(source);delta=out['power']-f['power']
    out['float_comparison']=dict(power_RMSE=float(np.sqrt(np.mean(delta**2))),power_units='normalized amplitude squared',
      geometry=compare_geometry(out['records'],f['records']),
      note='Power-map error; complex FFT output is not downloaded. FFT RMSE is in the separate 11-CPI engineering evaluation.')
   out['comparison']=score(out['records'],targets) if c['mode']!='Demo' else None
   out['elapsed_s']=time.monotonic()-start
   self.completed.emit(out)
  except Exception:self.failed.emit(traceback.format_exc())
class Window(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('AX309 Radar Lab · FFT IP / full FPGA DSP');self.resize(1430,970)
  root=QWidget();self.setCentralWidget(root);layout=QVBoxLayout(root)
  title=QLabel('AX309 / Radar DSP Lab');title.setFont(QFont('Sans',19,QFont.Bold));layout.addWidget(title)
  self.banner=QLabel('Program FPGA once, choose Hardware, then Run. Every result carries its source.');self.banner.setWordWrap(True);layout.addWidget(self.banner)
  self.metrics=QLabel('Yellow: cluster peaks · Green: known truth · Red: CFAR cells reconstructed on PC');self.metrics.setWordWrap(True);layout.addWidget(self.metrics)
  tabs=QTabWidget();layout.addWidget(tabs,1);runpage=QWidget();tabs.addTab(runpage,'Radar Lab')
  helpview=QTextEdit();helpview.setReadOnly(True);helpview.setHtml(HELP);helpview.setLayoutDirection(Qt.RightToLeft);tabs.addTab(helpview,'راهنمای نماها و گزینه‌ها')
  body=QVBoxLayout(runpage);row=QHBoxLayout();body.addLayout(row,3)
  controls=QWidget();form=QFormLayout(controls);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(controls);scroll.setMaximumWidth(380);row.addWidget(scroll)
  self.scenario=QComboBox();self.scenario.addItems(LIBRARY);form.addRow('Scenario',self.scenario)
  self.mode=QComboBox();self.mode.addItems(['Hardware','Float reference','Legacy fixed reference','Demo']);form.addRow('Result source',self.mode)
  self.port=QComboBox();self.port.setEditable(True);form.addRow('UART · 115200 / 8N1',self.port)
  refresh=QPushButton('Refresh ports');refresh.clicked.connect(self.refresh_ports);form.addRow(refresh);self.refresh_ports()
  self.program=QPushButton('Program FPGA · SRAM');self.program.clicked.connect(self.program_fpga);form.addRow(self.program)
  self.range=QSpinBox();self.range.setRange(-15,15);form.addRow('Range offset · bins',self.range)
  self.velocity=QDoubleSpinBox();self.velocity.setRange(-5,5);self.velocity.setSingleStep(.46875);self.velocity.setDecimals(4);form.addRow('Velocity offset · m/s',self.velocity)
  self.amplitude=QDoubleSpinBox();self.amplitude.setRange(.1,2);self.amplitude.setValue(1);self.amplitude.setSingleStep(.1);form.addRow('Amplitude multiplier',self.amplitude)
  self.noise=QDoubleSpinBox();self.noise.setDecimals(4);self.noise.setRange(0,.15);self.noise.setValue(.002);self.noise.setSingleStep(.002);form.addRow('Complex noise RMS',self.noise)
  self.seed=QSpinBox();self.seed.setRange(0,2147483647);self.seed.setValue(20261112);form.addRow('Noise seed',self.seed)
  self.scenario.currentTextChanged.connect(lambda s:self.noise.setValue(.06 if s=='Low SNR' else .002))
  self.duration=QDoubleSpinBox();self.duration.setRange(1,30);self.duration.setValue(10);form.addRow('Truth path span · s',self.duration)
  self.compare=QCheckBox('Compare with Float64');self.compare.setChecked(True);form.addRow(self.compare)
  self.run=QPushButton('Run selected source');self.run.clicked.connect(self.execute);form.addRow(self.run)
  self.save=QPushButton('Save results · JSON + CSV');self.save.clicked.connect(self.save_result);self.save.setEnabled(False);form.addRow(self.save)
  self.view=QComboBox();self.view.addItems(['Range–Doppler','Range profile','Doppler slice']);form.addRow('Result view',self.view)
  self.scale=QComboBox();self.scale.addItems(['Power dB','Power linear']);form.addRow('Power scale',self.scale)
  self.dr=QSpinBox();self.dr.setRange(10,140);self.dr.setValue(65);form.addRow('Display range · dB',self.dr)
  self.slice=QSpinBox();self.slice.setRange(0,127);self.slice.setValue(40);form.addRow('Doppler slice · range bin',self.slice)
  self.clusterbox=QCheckBox('Cluster peaks');self.clusterbox.setChecked(True);form.addRow(self.clusterbox)
  self.truthbox=QCheckBox('Known truth positions');self.truthbox.setChecked(True);form.addRow(self.truthbox)
  self.cfarbox=QCheckBox('CFAR cells · PC reconstruction');form.addRow(self.cfarbox)
  self.roibox=QCheckBox('Valid CUT region');self.roibox.setChecked(True);form.addRow(self.roibox)
  limits=QLabel('10 GHz · Fs 1 MHz · PRI 1 ms\n33×128 IQ · LFM16 · FFT32 /8\nOne CPI per Run.\nAssociation is development scoring;\nstatistical qualification remains OPEN.');form.addRow(limits)
  plots=QSplitter(Qt.Horizontal);row.addWidget(plots,1)
  self.path=Plot('path');self.map=Plot('map');plots.addWidget(self.path);plots.addWidget(self.map)
  tables=QTabWidget();body.addWidget(tables,1)
  self.truth=QTableWidget(0,5);self.truth.setHorizontalHeaderLabels(['Known target','Range bin','Range · m','Radial velocity · m/s','Amplitude']);tables.addTab(self.truth,'Input truth')
  self.table=QTableWidget(0,9);self.table.setHorizontalHeaderLabels(['Record','Range bin','Range · m','Doppler bin','Velocity · m/s','Peak power normalized','Cells','Peak tie','Equal maxima']);tables.addTab(self.table,'All output clusters')
  self.table.setSelectionBehavior(QTableWidget.SelectRows)
  self.table.cellClicked.connect(lambda r,c:self.select_record(r))
  self.log=QTextEdit();self.log.setReadOnly(True);tables.addTab(self.log,'Connection / verification / timings')
  for table in (self.truth,self.table):table.horizontalHeader().setStretchLastSection(True)
  for control in [self.view,self.scale]:control.currentTextChanged.connect(self.refresh_plot)
  for control in [self.dr,self.slice,self.duration]:control.valueChanged.connect(self.refresh_plot)
  for control in [self.clusterbox,self.truthbox,self.cfarbox,self.roibox]:control.toggled.connect(self.refresh_plot)
  self.setStyleSheet('QMainWindow,QWidget{background:#17283d;color:#e7edf8;} QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QTextEdit,QTableWidget{background:#223952;padding:4px;} QPushButton{background:#176d92;padding:9px;font-weight:bold;} QHeaderView::section{background:#29445e;color:#e7edf8;padding:4px;} QCheckBox{padding:3px;}')
  self.worker=None
 def refresh_ports(self):
  from serial.tools import list_ports
  selected=self.port.currentText();self.port.clear()
  ports=list(list_ports.comports());ports.sort(key=lambda p:('CP210' not in (p.description or ''),p.device))
  for p in ports:self.port.addItem(p.device)
  if selected:self.port.setCurrentText(selected)
 def busy(self,on):
  self.run.setEnabled(not on);self.program.setEnabled(not on)
 def program_fpga(self):
  if self.worker and self.worker.isRunning():return
  self.start_worker(dict(program=True))
 def execute(self):
  if self.worker and self.worker.isRunning():return
  self.map.data=None;self.map.records=[];self.map.mask=None;self.map.update();self.table.setRowCount(0);self.save.setEnabled(False)
  self.start_worker(dict(scenario=self.scenario.currentText(),mode=self.mode.currentText(),port=self.port.currentText(),range=self.range.value(),velocity=self.velocity.value(),amplitude=self.amplitude.value(),noise=self.noise.value(),seed=self.seed.value(),compare=self.compare.isChecked()))
 def start_worker(self,config):
  self.busy(True);self.banner.setText('Running…')
  self.worker=Worker(config);self.worker.completed.connect(self.show_result);self.worker.failed.connect(self.show_error);self.worker.progress.connect(self.banner.setText);self.worker.start()
 def show_error(self,text):
  self.busy(False);self.banner.setText('FAILED · incomplete result rejected; inspect connection log');self.log.setPlainText(text)
 def refresh_plot(self,*args):
  self.map.view=self.view.currentText();self.map.db=self.scale.currentIndex()==0;self.map.dr=self.dr.value();self.map.slice=self.slice.value()
  self.map.clusters=self.clusterbox.isChecked();self.map.truth=self.truthbox.isChecked();self.map.cfar=self.cfarbox.isChecked();self.map.roi=self.roibox.isChecked()
  self.path.duration=self.duration.value();self.path.update();self.map.update()
 def select_record(self,row):
  if hasattr(self,'last_result') and row<len(self.last_result['records']):self.slice.setValue(self.last_result['records'][row]['range_bin'])
 def show_result(self,out):
  self.busy(False)
  if out.get('program_only'):
   self.banner.setText('FPGA SRAM programmed · full FFT IP DSP ready');self.log.setPlainText(json.dumps(out,indent=2));return
  self.last_result=out;self.save.setEnabled(True);self.banner.setText(out['status'])
  matches=sum(v['matched'] for v in (out.get('comparison') or {}).get('matches',[]))
  metric=f"Clusters: {len(out['records'])} (all shown) · Matched truth: {matches}/{len(out['targets'])} · Total: {out['elapsed_s']:.2f} s"
  if out.get('float_comparison'):metric+=f" · Power RMSE vs Float: {out['float_comparison']['power_RMSE']:.3g}"
  self.metrics.setText(metric)
  self.path.targets=out['targets'];self.map.targets=out['targets'];self.map.source=out['mode'];self.map.data=out['power'];self.map.mask=out['mask'];self.map.records=out['records'];self.refresh_plot()
  self.truth.setRowCount(len(out['targets']))
  for i,t in enumerate(out['targets']):
   for j,v in enumerate([t.name,t.delay,f'{t.delay*RANGE_STEP:.2f}',t.velocity,t.amplitude]):self.truth.setItem(i,j,QTableWidgetItem(str(v)))
  self.table.setRowCount(len(out['records']))
  for i,r in enumerate(out['records']):
   peak=r.get('peak_power_linear',r.get('power_stored_integer',0)/(1<<30))
   values=[r['record_id'],r['range_bin'],f"{r['range_bin']*RANGE_STEP:.2f}",r['doppler_bin'],f"{r['signed_doppler_bin']*VELOCITY_STEP:.4f}",f'{peak:.8g}',r['cluster_cells'],r.get('tie_flag','Float'),r.get('max_equal_power_cells','—')]
   for j,v in enumerate(values):self.table.setItem(i,j,QTableWidgetItem(str(v)))
  self.table.resizeColumnsToContents();self.truth.resizeColumnsToContents()
  summary={k:v for k,v in out.items() if k not in ('power','mask','targets','records')}
  self.log.setPlainText(json.dumps(summary,indent=2,default=str))
 def save_result(self):
  if not hasattr(self,'last_result'):return
  path,_=QFileDialog.getSaveFileName(self,'Save result',str(ROOT/'deliverables/radar_result.json'),'JSON (*.json)')
  if not path:return
  self.export_result(path)
  self.banner.setText('Saved '+str(path))
 def export_result(self,path):
  out=self.last_result.copy();out['targets']=[asdict(t) for t in out['targets']]
  def conv(x):
   if isinstance(x,np.ndarray):return x.tolist()
   if isinstance(x,np.generic):return x.item()
   raise TypeError(type(x).__name__)
  p=Path(path);p.write_text(json.dumps(out,indent=2,ensure_ascii=False,default=conv)+'\n')
  rows=out['records']
  keys=list(dict.fromkeys(k for r in rows for k in r)) or ['record_id','range_bin','doppler_bin','cluster_cells']
  with p.with_suffix('.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
 def closeEvent(self,event):
  if self.worker and self.worker.isRunning():event.ignore()
  else:event.accept()
def main():
 app=QApplication(sys.argv);window=Window();window.show()
 if '--show-hardware' in sys.argv:
  window.scenario.setCurrentText('Two aircraft');window.mode.setCurrentText('Hardware');window.execute()
  def show_hardware():
   if window.worker.isRunning():QTimer.singleShot(200,show_hardware);return
   if not hasattr(window,'last_result'):print('HARDWARE_GUI_FAIL',window.log.toPlainText(),flush=True);return
   outdir=ROOT/'engineering/evidence/s11/full_ip_20261112';outdir.mkdir(parents=True,exist_ok=True)
   window.grab().save(str(outdir/'gui-hardware.png'));window.export_result(outdir/'gui-hardware-result.json')
   print('HARDWARE_GUI_PASS',window.last_result['status'],len(window.last_result['records']),flush=True)
  QTimer.singleShot(200,show_hardware)
 if '--smoke' in sys.argv:
  window.mode.setCurrentText('Float reference');window.execute()
  def finish():
   if window.worker.isRunning():QTimer.singleShot(200,finish);return
   if not hasattr(window,'last_result'):print('GUI_SMOKE_FAIL',window.log.toPlainText());app.exit(1);return
   p=ROOT/'engineering/evidence/s10/full_ip_20261112';p.mkdir(parents=True,exist_ok=True);window.grab().save(str(p/'gui-reference.png'))
   print('GUI_SMOKE_PASS',window.last_result['status'],flush=True);app.quit()
  QTimer.singleShot(200,finish)
 sys.exit(app.exec())
if __name__=='__main__':main()

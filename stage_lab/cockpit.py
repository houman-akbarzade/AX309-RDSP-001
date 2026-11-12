"""Two operator modes; detailed stage controls remain a separate advanced window."""
import sys,json,shutil
from pathlib import Path
from dataclasses import replace
from PySide6.QtCore import Qt,QUrl,QByteArray
from PySide6.QtGui import QFont
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QComboBox,QSpinBox,QDoubleSpinBox,QPushButton,QLabel,QTextBrowser,QLineEdit,QTableWidget,QTableWidgetItem,QFileDialog,QScrollArea,QSplitter
from .auto_cases import SCENARIOS,spec
from .auto_suite import AutoWorker,plan
from .models import ROOT
from .visuals import scenario_svg
from desktop_app.scenarios import Flight,RANGE_STEP
class Cockpit(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('AX309 Radar Test v0.3.0');self.resize(1550,1000);self.worker=None;self.last_report=None;self.advanced=None
  root=QWidget();self.setCentralWidget(root);layout=QVBoxLayout(root)
  title=QLabel('آزمایش و مقایسه رادار AX309');title.setFont(QFont('B Nazanin',24,QFont.Bold));title.setAlignment(Qt.AlignRight);layout.addWidget(title)
  self.banner=QLabel('یک سناریو را تا خروجی نهایی مقایسه کنید، یا مجموعه آزمون خودکار را اجرا کنید.');self.banner.setWordWrap(True);self.banner.setFont(QFont('B Nazanin',16));layout.addWidget(self.banner)
  split=QSplitter(Qt.Horizontal);layout.addWidget(split,1)
  settings=QWidget();form=QFormLayout(settings);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(settings);scroll.setMinimumWidth(360);scroll.setMaximumWidth(460);split.addWidget(scroll)
  self.mode=QComboBox();self.mode.addItem('۱. تزریق IQ و مقایسه کلاسترینگ','normal');self.mode.addItem('۲. آزمون جامع خودکار','auto');form.addRow('حالت اصلی',self.mode)
  self.scenario=QComboBox();self.scenario.addItems(list(SCENARIOS));self.scenario.setCurrentText('Two aircraft');form.addRow('سناریو',self.scenario)
  self.targets=QTableWidget();self.targets.setColumnCount(4);self.targets.setHorizontalHeaderLabels(['هدف','سلول برد','سرعت m/s','دامنه']);self.targets.setMaximumHeight(205);form.addRow(self.targets)
  self.noise=QDoubleSpinBox();self.noise.setRange(0,1);self.noise.setDecimals(6);self.noise.setSingleStep(.001);self.noise.setValue(.002);form.addRow('RMS نویز مختلط نرمال‌شده',self.noise)
  self.seed=QSpinBox();self.seed.setRange(0,2147000000);self.seed.setValue(20261112);form.addRow('Seed',self.seed)
  self.file=QLineEdit();form.addRow('فایل IQ اختیاری',self.file);choose=QPushButton('انتخاب MAT / NPY / NPZ');choose.clicked.connect(self.choose);form.addRow(choose);self.choose_button=choose
  self.file_format=QComboBox();self.file_format.addItems(['Normalized float','Stored codes']);form.addRow('قالب فایل',self.file_format)
  self.level=QComboBox();self.level.addItem('بررسی جامع عملکرد و تفکیک','quick');self.level.addItem('تکرار آماری مستقل CFAR و کلاسترینگ','statistics');form.addRow('مجموعه آزمون خودکار',self.level)
  self.repeats=QSpinBox();self.repeats.setRange(2,1000);self.repeats.setValue(32);form.addRow('تعداد CPI برای هر گروه آماری',self.repeats)
  self.engine=QComboBox();self.engine.addItems(['Python','MATLAB','Both']);form.addRow('زبان مراجع Float و Fixed',self.engine)
  self.port=QLineEdit('/dev/ttyUSB1');form.addRow('UART 115200 / 8N1',self.port)
  self.plan_note=QLabel();self.plan_note.setWordWrap(True);self.plan_note.setFont(QFont('B Nazanin',15));form.addRow(self.plan_note)
  self.run=QPushButton('اجرا و تهیه گزارش');self.run.clicked.connect(self.execute);form.addRow(self.run)
  self.stop=QPushButton('توقف پس از آزمون جاری');self.stop.setEnabled(False);self.stop.clicked.connect(self.cancel);form.addRow(self.stop)
  self.export=QPushButton('ذخیره پوشه گزارش و نمودارها');self.export.setEnabled(False);self.export.clicked.connect(self.save_report);form.addRow(self.export)
  self.expert=QPushButton('عیب‌یابی پیشرفته: نقاط تزریق و برداشت');self.expert.clicked.connect(self.open_advanced);form.addRow(self.expert)
  self.help_button=QPushButton('راهنمای دو حالت و گزارش‌ها');self.help_button.clicked.connect(self.show_help);form.addRow(self.help_button)
  right=QWidget();rl=QVBoxLayout(right);split.addWidget(right);self.scene=QSvgWidget();self.scene.setMinimumHeight(200);self.scene.setMaximumHeight(270);rl.addWidget(self.scene)
  self.report=QTextBrowser();self.report.setFont(QFont('B Nazanin',17));self.report.setLayoutDirection(Qt.RightToLeft);rl.addWidget(self.report,1)
  self.setStyleSheet('QWidget{background:#17283d;color:#e7edf8} QComboBox,QLineEdit,QSpinBox,QDoubleSpinBox,QTableWidget,QTextBrowser{background:#223952;padding:4px} QPushButton{background:#176d92;padding:9px} QHeaderView::section{background:#29445e;color:white}')
  self.mode.currentIndexChanged.connect(self.mode_changed);self.level.currentIndexChanged.connect(self.mode_changed);self.repeats.valueChanged.connect(self.mode_changed);self.scenario.currentTextChanged.connect(self.update_targets);self.noise.valueChanged.connect(self.draw_scene)
  self.update_targets();self.mode_changed();self.show_help()
 def current_case(self):
  case=spec(self.scenario.currentText(),self.noise.value(),self.seed.value())
  for i,t in enumerate(case['targets']):
   t['delay']=self.targets.cellWidget(i,1).value();t['velocity']=self.targets.cellWidget(i,2).value();t['amplitude']=self.targets.cellWidget(i,3).value()
  return case
 def update_targets(self,*args):
  ts=SCENARIOS[self.scenario.currentText()];self.targets.setRowCount(len(ts))
  for i,t in enumerate(ts):
   self.targets.setItem(i,0,QTableWidgetItem(t['name']))
   for col,key,lo,hi,dec,step in [(1,'delay',0,112,0,1),(2,'velocity',-7.5,7.499999,6,.05),(3,'amplitude',0,.9,4,.01)]:
    w=QSpinBox() if col==1 else QDoubleSpinBox();w.setRange(lo,hi)
    if col>1:w.setDecimals(dec);w.setSingleStep(step)
    w.setValue(t[key]);w.valueChanged.connect(self.draw_scene);self.targets.setCellWidget(i,col,w)
  self.targets.setFixedHeight(max(55,34+len(ts)*35));self.targets.resizeColumnsToContents()
  if self.scenario.currentText().startswith('MTI '):self.noise.setValue(0)
  elif self.scenario.currentText()=='Low SNR':self.noise.setValue(.06)
  self.draw_scene()
 def draw_scene(self,*args):
  case=self.current_case();targets=[Flight(**t) for t in case['targets']];self.scene.load(QByteArray(scenario_svg(case['name'],targets,case['noise']).encode()))
 def mode_changed(self,*args):
  normal=self.mode.currentData()=='normal';stats=self.level.currentData()=='statistics'
  for w in [self.scenario,self.targets,self.noise,self.file,self.file_format,self.choose_button]:w.setEnabled(normal)
  self.scene.setVisible(normal);self.level.setEnabled(not normal);self.repeats.setEnabled(not normal and stats)
  if normal:self.plan_note.setText('IQ خام → زنجیره کامل پایدار FPGA → کلاسترینگ. ورودی کنترل و خروجی نهایی با Float و Fixed مقایسه می‌شود. برای فایل، 33×128 نمونه IQ لازم است؛ حقیقت هدف از فایل فرض نمی‌شود.')
  elif stats:self.plan_note.setText(f'{self.repeats.value()} CPI مستقل بدون هدف و {self.repeats.value()} CPI مستقل دارای یک هدف؛ CFAR از توان FFT نرم‌افزاری تغذیه و ماسک واقعی آن به کلاسترینگ داده می‌شود. RMS نویز 0.02، دامنه هدف 0.18، SNR ورودی فعال حدود 19.08 dB. این آزمون Pd/Pfa انتهابه‌انتهای IQ خام نیست.')
  else:self.plan_note.setText('۴۱ گزارش آزمون: زنجیره تجمعی چهار سناریو، آزمون مستقل شش بلوک، MTI ساکن/بسیارکند/متحرک، فاصله بردی ۲/۴/۸ سلول، فاصله سرعتی ۱/۲/۴ بین، داپلر خارج مرکز بین و SNR پایین. اجرا با UART چند دقیقه زمان می‌برد.')
 def choose(self):
  path,_=QFileDialog.getOpenFileName(self,'IQ input',str(ROOT),'Arrays (*.mat *.npy *.npz)')
  if path:self.file.setText(path)
 def execute(self):
  if self.worker and self.worker.isRunning():return
  config=dict(mode=self.mode.currentData(),level=self.level.currentData(),repeats=self.repeats.value(),engine=self.engine.currentText(),port=self.port.text(),seed=self.seed.value(),case=self.current_case(),file=self.file.text().strip(),file_format=self.file_format.currentText())
  self.run.setEnabled(False);self.expert.setEnabled(False);self.stop.setEnabled(config['mode']=='auto');self.mode.setEnabled(False);self.export.setEnabled(False)
  self.worker=AutoWorker(config);self.worker.progress.connect(self.banner.setText);self.worker.completed.connect(self.completed);self.worker.failed.connect(self.failed);self.worker.start()
 def cancel(self):
  if self.worker:self.worker.cancelled=True;self.banner.setText('درخواست توقف ثبت شد؛ تراکنش جاری کامل و گزارش جزئی ذخیره می‌شود.')
 def completed(self,result):
  self.run.setEnabled(True);self.expert.setEnabled(True);self.stop.setEnabled(False);self.mode.setEnabled(True);self.last_report=result['report'];self.export.setEnabled(True);self.report.setSource(QUrl.fromLocalFile(result['report']));self.banner.setText(f"وضعیت: {result['status']} | آزمون تکمیل‌شده: {result['jobs']} از {result['planned']} | گزارش ذخیره شد.")
 def failed(self,error):
  self.run.setEnabled(True);self.expert.setEnabled(True);self.stop.setEnabled(False);self.mode.setEnabled(True);self.banner.setText('اجرا ناموفق بود؛ نتیجه معتبر تازه اعلام نشده است.');self.report.setPlainText(error)
 def save_report(self):
  if not self.last_report:return
  dest=QFileDialog.getExistingDirectory(self,'Save complete report folder')
  if dest:
   source=Path(self.last_report).parent;target=Path(dest)/('AX309-report-'+source.name)
   if source.resolve() in target.resolve().parents:self.banner.setText('پوشه مقصد را بیرون از پوشه گزارش انتخاب کنید.');return
   if target.exists():self.banner.setText('پوشه گزارش با این نام وجود دارد؛ پوشه دیگری انتخاب کنید.');return
   shutil.copytree(source,target);self.banner.setText('گزارش، نمودارها و داده‌ها ذخیره شد: '+str(target))
 def open_advanced(self):
  from .gui import Window
  self.advanced=Window();self.advanced.show()
 def show_help(self):
  self.report.setHtml('<html dir="rtl"><body style="font-family:B Nazanin;font-size:18pt"><h2>دو حالت اصلی</h2><p>حالت اول برای تزریق IQ سناریو یا فایل و مقایسه کلاسترینگ نهایی است. برد، سرعت و دامنه هر هدف قابل تغییرند. فایل IQ باید 33 ردیف PRI و 128 ستون برد داشته باشد. Normalized float مقدار نرمال‌شده و Stored codes عدد صحیح Q1.15 است. فایل MAT معمولی v7 پشتیبانی می‌شود؛ v7.3 و شیء fi پشتیبانی نمی‌شوند.</p><p>حالت دوم مجموعه آزمون را خودکار اجرا می‌کند. نقاط تزریق و برداشت داخل برنامه انتخاب می‌شوند. گزارش اصلی جمله‌های کوتاه هر آزمون را نشان می‌دهد؛ لینک جزئیات همان آزمون، نمودارها و جدول‌ها را باز می‌کند. اعداد برابری Fixed از نتیجه تفکیک دو هدف و آمار Pd/Pfa جدا هستند.</p><h3>آزمون MTI</h3><p>هدف ساکن 0 m/s، هدف بسیار کند 0.05 m/s و هدف متحرک 2.8125 m/s با نویز صفر بررسی می‌شوند. برای هدف ساکن خروجی صفر و برای هدف کند تضعیف نزدیک داپلر صفر اندازه‌گیری می‌شود. سناریوی MTI mixed هر سه را در بردهای جدا دارد؛ ممکن است هدف ساکن پس از MTI/CFAR دیده نشود و این الزاماً خطا نیست.</p><h3>آمار</h3><p>گروه بدون هدف برای Pfa سلولی CFAR، احتمال وجود هشدار در CPI و کلاستر کاذب به ازای CPI است. گروه دارای یک هدف برای Pd با تطبیق ±2 سلول برد و ±1 بین داپلر است. فاصله اطمینان همراه عدد می‌آید؛ سلول‌های هم‌بسته یک CPI مستقل شمرده نمی‌شوند. SNR بر پایه دامنه اکو فعال و RMS نویز مختلط تعریف شده است.</p><p>آزمون‌ها فقط SRAM را پروگرام می‌کنند و Flash تغییر نمی‌کند. برنامه و tagهای قبلی محفوظ‌اند. با دکمه عیب‌یابی پیشرفته می‌توان آزمون مرحله‌ای را جدا اجرا کرد. همزمان دو برنامه را به UART وصل نکنید.</p></body></html>')
 def closeEvent(self,e):
  if self.worker and self.worker.isRunning():e.ignore();self.banner.setText('ابتدا توقف پس از آزمون جاری را بزنید.')
  else:e.accept()
def main():
 app=QApplication(sys.argv);w=Cockpit();w.showMaximized();sys.exit(app.exec())
if __name__=='__main__':main()

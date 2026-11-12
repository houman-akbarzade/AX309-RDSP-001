"""Operator presentation v0.2.1. Uses actual captured arrays, never a substitute FPGA model."""
import json
from dataclasses import replace
import numpy as np
from PySide6.QtCore import Qt,QByteArray
from PySide6.QtGui import QFont
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QComboBox,QSpinBox,QDoubleSpinBox,QLabel,QSplitter,QTableWidget,QTableWidgetItem,QTextBrowser,QTextEdit,QScrollArea,QHeaderView,QPushButton,QDialog
from .visuals import Curves,Heatmap,architecture_svg,scenario_svg
from .guide_fa import HELP
from .models import NAMES
from desktop_app.scenarios import LIBRARY,RANGE_STEP,VELOCITY_STEP
from s03_reference import model as M
def table(headers):
 w=QTableWidget();w.setColumnCount(len(headers));w.setHorizontalHeaderLabels(headers);w.setEditTriggers(QTableWidget.NoEditTriggers);w.setAlternatingRowColors(True);w.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents);return w
def fill(w,rows):
 w.setRowCount(len(rows))
 for i,row in enumerate(rows):
  for j,v in enumerate(row):w.setItem(i,j,QTableWidgetItem(str(v)))
def number(v):
 if v is None:return 'N/A (zero reference RMS)'
 if isinstance(v,bool):return 'Yes' if v else 'No'
 if isinstance(v,float):return f'{v:.7g}'
 return str(v)
def normalized(a,stage,fixed):
 if stage<=3:return np.asarray(a)/(32768 if fixed else 1)
 if stage==4:return np.asarray(a,float)/((1<<30) if fixed else 1)
 if stage==5:return np.asarray(a[0],float)/((1<<30) if fixed else 1),np.asarray(a[1],bool)
 return a
def upgrade_window(Base):
 class Window(Base):
  def __init__(self):
   self.ready=False;super().__init__();self.setWindowTitle('AX309 Stage Lab v0.2.1 · dimensioned comparison');self.resize(1650,1030)
   self.centralWidget().layout().itemAt(0).widget().setText('AX309 Stage Lab v0.2.1 / FPGA and software comparison')
   # Make the long operator form scrollable on laptop displays.
   row=self.centralWidget().layout().itemAt(2).layout();form=row.takeAt(0).layout();fw=QWidget();fw.setLayout(form);scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(fw);scroll.setMinimumWidth(315);scroll.setMaximumWidth(390);row.insertWidget(0,scroll)
   self.noise.setRange(0,1);self.noise.setDecimals(6);self.noise.setSingleStep(.001);self.noise.setToolTip('sqrt(E[|n|²]); normalized complex amplitude. Each I/Q sigma = RMS / sqrt(2).')
   form.labelForField(self.noise).setText('Noise RMS · normalized amplitude')
   self.targets=QTableWidget();self.targets.setColumnCount(3);self.targets.setHorizontalHeaderLabels(['Target','Range (m)','Velocity (m/s)']);self.targets.setMinimumHeight(110);self.targets.setMaximumHeight(175);form.insertRow(7,self.targets)
   self.scenario_svg=QSvgWidget();self.scenario_svg.setMinimumSize(850,330)
   self.pri=QSpinBox();self.pri.setRange(0,32);form.addRow('PRI index · zero-based',self.pri)
   self.cell=QSpinBox();self.cell.setRange(0,127);self.cell.setValue(40);form.addRow('Range cell · zero-based',self.cell)
   form.labelForField(self.slice).setText('Natural Doppler bin · 0..31')
   self.profile=QComboBox();self.profile.addItems(['Range profile','Slow-time / spectrum at range cell']);form.addRow('Waveform view',self.profile)
   self.axis=QComboBox();self.axis.addItems(['Doppler frequency (Hz)','Radial velocity (m/s)','Signed Doppler bin']);form.addRow('Spectral axis',self.axis)
   # Keep slice controls visible above all tabs instead of below the scroll fold.
   toolbar=QWidget();tl=QVBoxLayout(toolbar);tr1=QHBoxLayout();tr2=QHBoxLayout();tl.addLayout(tr1);tl.addLayout(tr2)
   for label,widget,layout in [('View',self.profile,tr1),('Component',self.component,tr1),('Spectral axis',self.axis,tr1),('PRI index',self.pri,tr2),('Natural Doppler bin',self.slice,tr2),('Range cell',self.cell,tr2)]:
    taken=form.takeRow(widget)
    if taken.labelItem:taken.labelItem.widget().deleteLater()
    layout.addWidget(QLabel(label));layout.addWidget(widget)
   pane=QWidget();pl=QVBoxLayout(pane);pl.setContentsMargins(0,0,0,0);row.removeWidget(self.tabs);row.addWidget(pane,1);pl.addWidget(toolbar);pl.addWidget(self.tabs)
   self.tabs.clear()
   plots=QSplitter(Qt.Horizontal);self.pin=Curves('Actual FPGA input echo');self.pout=Curves('FPGA / software references');self.perr=Curves('FPGA minus reference')
   for p in [self.pin,self.pout,self.perr]:plots.addWidget(p)
   self.tabs.addTab(plots,'Waveforms / differences')
   maps=QWidget();ml=QVBoxLayout(maps);controls=QHBoxLayout();ml.addLayout(controls)
   self.map_domain=QComboBox();self.map_domain.addItems(['Output comparison','Actual injected input']);controls.addWidget(self.map_domain)
   self.map_ref=QComboBox();controls.addWidget(QLabel('Reference'));controls.addWidget(self.map_ref)
   self.map_quantity=QComboBox();self.map_quantity.addItems(['Power','CFAR mask','Cluster peaks']);controls.addWidget(self.map_quantity)
   split=QSplitter(Qt.Horizontal);self.maps=[Heatmap('FPGA'),Heatmap('Software'),Heatmap('Difference')]
   for p in self.maps:split.addWidget(p)
   ml.addWidget(split,1);self.map_note=QLabel();self.map_note.setWordWrap(True);self.map_note.setMaximumHeight(65);ml.addWidget(self.map_note);self.map=maps;self.tabs.addTab(maps,'Range / PRI / Doppler comparison')
   rec=QWidget();rl=QVBoxLayout(rec);self.record_note=QLabel();self.record_note.setWordWrap(True);rl.addWidget(self.record_note);self.records=table(['Index']);rl.addWidget(self.records);self.tabs.addTab(rec,'All data / cluster records')
   met=QWidget();vl=QVBoxLayout(met);self.status=QLabel();self.status.setWordWrap(True);vl.addWidget(self.status);self.metric_table=table(['Reference','Measure','Value','Unit / meaning']);vl.addWidget(self.metric_table)
   self.metrics=QTextEdit();self.metrics.setReadOnly(True);self.metrics.hide();details=QPushButton('Optional technical JSON details');vl.addWidget(details);details.clicked.connect(self.show_details);self.tabs.addTab(met,'Accuracy / RMSE / link status')
   sw=QWidget();sl=QVBoxLayout(sw);self.sweep_note=QLabel();self.sweep_note.setWordWrap(True);sl.addWidget(self.sweep_note);self.sweep_plots=QSplitter(Qt.Horizontal);self.pd=Curves('Defined targets above threshold');self.pfa=Curves('Cells above threshold outside target gates')
   for p in [self.pd,self.pfa]:p.xlabel='Threshold · normalized power';p.ylabel='Fraction (0..1)';self.sweep_plots.addWidget(p)
   sl.addWidget(self.sweep_plots);self.sweep_table=table(['Threshold (normalized power)','FPGA target fraction','Reference target fraction','FPGA outside-gate fraction','Reference outside-gate fraction']);sl.addWidget(self.sweep_table);self.sweep=sw;self.tabs.addTab(sw,'Threshold / detection / false alarms')
   scene=QWidget();sc=QVBoxLayout(scene);sc.addWidget(self.scenario_svg);self.scenario_note=QLabel('Velocity edits apply on the next Run. Illustration is schematic, not a trajectory simulation.');self.scenario_note.setWordWrap(True);sc.addWidget(self.scenario_note);self.tabs.addTab(scene,'Scenario / target velocity')
   helpw=QWidget();hl=QVBoxLayout(helpw);self.arch_svg=QSvgWidget();self.arch_svg.setMinimumSize(850,510);hs=QScrollArea();hs.setWidget(self.arch_svg);hs.setWidgetResizable(True);hl.addWidget(hs,3)
   self.help=QTextBrowser();self.help.setFont(QFont('B Nazanin',16));self.help.setLayoutDirection(Qt.RightToLeft);self.help.setHtml(HELP);hl.addWidget(self.help,2);self.tabs.addTab(helpw,'ساختار و راهنمای فارسی')
   for w in [self.pri,self.cell]:w.valueChanged.connect(self.refresh)
   for w in [self.profile,self.axis,self.map_domain,self.map_ref,self.map_quantity]:w.currentTextChanged.connect(self.refresh)
   self.scenario.currentTextChanged.connect(self.update_scenario)
   self.input.currentTextChanged.connect(self.update_architecture);self.target.currentIndexChanged.connect(self.update_architecture);self.pris.valueChanged.connect(self.update_architecture);self.noise.valueChanged.connect(self.draw_scenario)
   self.ready=True;self.update_scenario();self.update_architecture()
  def update_scenario(self,*args):
   if not self.ready:return
   ts=LIBRARY.get(self.scenario.currentText(),[]);self.targets.setRowCount(len(ts))
   for i,t in enumerate(ts):
    for j,value in enumerate([t.name,f'{t.delay*RANGE_STEP:.3f}']):
     it=QTableWidgetItem(value);it.setFlags(it.flags()&~Qt.ItemIsEditable);self.targets.setItem(i,j,it)
    v=QDoubleSpinBox();v.setRange(-7.5,7.499999);v.setDecimals(6);v.setSingleStep(float(VELOCITY_STEP));v.setValue(t.velocity);v.setSuffix(' m/s');v.valueChanged.connect(self.draw_scenario);self.targets.setCellWidget(i,2,v)
   self.targets.setFixedHeight(max(55,35+len(ts)*34));self.targets.resizeColumnsToContents();self.draw_scenario()
  def velocities(self):
   return [self.targets.cellWidget(i,2).value() for i in range(self.targets.rowCount())]
  def draw_scenario(self,*args):
   if not self.ready:return
   ts=[replace(t,velocity=v) for t,v in zip(LIBRARY.get(self.scenario.currentText(),[]),self.velocities())]
   self.scenario_svg.load(QByteArray(scenario_svg(self.scenario.currentText(),ts,self.noise.value()).encode()))
  def update_architecture(self,*args):
   if not self.ready:return
   mode=self.input.currentText();t=self.target.currentData();raw='raw' in mode.lower();entry=0 if raw else 3 if 'FFT →' in mode else t-1
   self.arch_svg.load(QByteArray(architecture_svg(entry,t,raw,mode,self.pris.value()).encode()))
  def show_details(self):
   d=QDialog(self);d.setWindowTitle('Technical details · optional JSON');l=QVBoxLayout(d);e=QTextEdit();e.setReadOnly(True);e.setPlainText(self.metrics.toPlainText());l.addWidget(e);d.resize(850,650);d.exec()
  def error(self,text):
   super().error(text);self.status.setText('Execution failed. No new valid FPGA comparison. See technical details.');self.tabs.setCurrentIndex(3)
  def result(self,out):
   self._record_key=None;self._sweep_key=None;self.last=out;self.run.setEnabled(True);self.restore.setEnabled(True);self.save.setEnabled(True)
   self.banner.setText(f"FPGA {NAMES[out['target']]} · echo verified · {out['elapsed_s']:.1f} s · "+out['origin']['origin'])
   if out['target'] in (3,4,5):
    z=normalized(out['output'],out['target'],True);pwr=np.abs(z)**2 if out['target']==3 else z if out['target']==4 else z[0]
    self.slice.blockSignals(True);self.cell.blockSignals(True);self.slice.setValue(int(np.argmax(np.sum(pwr,axis=1))));self.cell.setValue(int(np.argmax(np.sum(pwr,axis=0))));self.slice.blockSignals(False);self.cell.blockSignals(False)
   self.metrics.setPlainText(json.dumps({k:v for k,v in out.items() if k not in ('actual_input','output','references','source_input','truth')},indent=2,default=str))
   self.pri.setMaximum(max(0,(np.asarray(out['actual_input']).shape[0] if out['entry']<=3 else 33)-1));self.slice.setMaximum(31)
   old=self.map_ref.currentText();self.map_ref.blockSignals(True);self.map_ref.clear();self.map_ref.addItems(list(out['references']));self.map_ref.setCurrentText(old if old in out['references'] else next(iter(out['references']),''));self.map_ref.blockSignals(False)
   self.status.setText(f"Actual FPGA data received | input echo: verified | elapsed: {out['elapsed_s']:.2f} s\nInput quantization RMSE: {number(out['origin'].get('input_quantization_RMSE'))} (separate from block error).\nMetrics below cover the complete output, not just the displayed slice.")
   rows=[]
   meanings={'RMSE':'normalized amplitude' if out['target']<=3 else 'normalized power','NRMSE_percent':'% of reference RMS','max_abs_error':'maximum absolute difference','decision_mismatches':'different CFAR cells','extra_alarms_vs_reference':'FPGA-only CFAR decisions','missing_alarms_vs_reference':'software-only CFAR decisions','exact_integer':'all stored output codes equal','record_signatures_exact':'complete compared record signatures'}
   for label,m in out['metrics'].items():
    for k,v in m.items():
     if k in ('units','compared_fields'):continue
     rows.append([label,k.replace('_',' '),number(v),meanings.get(k,'count / comparison')])
   for label,m in out.get('full_chain_metrics',{}).items():
    for k,v in m.items():rows.append(['Whole chain '+label,k.replace('_',' '),number(v),'raw CPI end-to-end'])
   fill(self.metric_table,rows);self.refresh()
  def row_axis(self,stage,rows):
   if stage<3:return np.arange(rows),'PRI index (zero-based)'
   b=np.arange(-16,16)
   if self.axis.currentIndex()==0:return b/(32*M.PRI),'Doppler frequency (Hz)'
   if self.axis.currentIndex()==1:return b*VELOCITY_STEP,'Radial velocity (m/s)'
   return b,'Signed Doppler bin'
  def wave(self,a,stage,fixed):
   z=normalized(a,stage,fixed)
   if stage==6:
    return np.arange(len(z)),np.array([r.get('power_stored_integer',0)/(1<<30) if fixed else r.get('power_linear',r.get('peak_power_linear',0)) for r in z]),'Cluster record index','Peak normalized power'
   if stage==5:z=z[1].astype(float)
   if self.profile.currentIndex()==0:
    row=self.pri.value() if stage<3 else self.slice.value();v=z[min(row,z.shape[0]-1)];x=np.arange(len(v))*RANGE_STEP;xl='Range (m)'
   else:
    v=z[:,self.cell.value()]
    if stage>=3:v=np.fft.fftshift(v)
    x,xl=self.row_axis(stage,len(v))
   if stage<=3:
    v={'Magnitude':np.abs(v),'I':v.real,'Q':v.imag,'Phase':np.angle(v)}[self.component.currentText()]
    yl='Phase (rad)' if self.component.currentText()=='Phase' else 'Normalized amplitude'
   else:yl='CFAR decision (0 / 1)' if stage==5 else 'Normalized power (amplitude²)'
   return x,v,xl,yl
  def refresh(self,*args):
   if not self.ready or not self.last:return
   o=self.last;t=o['target'];entry=o['entry'];x,y,xl,yl=self.wave(o['actual_input'],entry,True)
   self.pin.lines={'Actual input echo':y};self.pin.x=x;self.pin.xlabel=xl;self.pin.ylabel=yl
   x,y,xl,yl=self.wave(o['output'],t,True);self.pout.lines={'FPGA':y};self.pout.x=x;self.pout.xlabel=xl;self.pout.ylabel=yl;self.perr.lines={};self.perr.x=x;self.perr.xlabel=xl;self.perr.ylabel='Difference · '+yl
   for label,a in o['references'].items():
    _,z,_,_=self.wave(a,t,'Fixed' in label);self.pout.lines[label]=z
    if t!=6 and z.shape==y.shape:self.perr.lines[label]=np.angle(np.exp(1j*(y-z))) if self.component.currentText()=='Phase' and t<=3 else y-z
   if t==6:self.perr.title='Record geometry: see table / accuracy tab'
   else:self.perr.title='FPGA minus reference'
   for p in [self.pin,self.pout,self.perr]:p.update()
   self.pri.setEnabled(self.profile.currentIndex()==0 and (t<3 or entry<3));self.cell.setEnabled(self.profile.currentIndex()==1);self.slice.setEnabled(self.profile.currentIndex()==0 and t>=3)
   self.refresh_maps()
   key=(id(o),self.map_ref.currentText())
   if getattr(self,'_record_key',None)!=key:self.refresh_records();self._record_key=key
   if getattr(self,'_sweep_key',None)!=key:self.refresh_sweep();self._sweep_key=key
  def map_values(self,a,stage,fixed):
   z=normalized(a,stage,fixed);kind=self.map_quantity.currentText();pts=[]
   if stage<=3:arr=np.abs(z)**2
   elif stage==4:arr=z
   elif stage==5:arr=z[1].astype(float) if kind!='Power' else z[0]
   else:
    # Clustering preserves the input map; only peak coordinates are returned by the FPGA.
    inp=normalized(self.last['actual_input'],5,True)
    arr=inp[0] if kind=='Power' else inp[1].astype(float) if kind=='CFAR mask' else np.zeros((32,128))
    for r in z:
     b=int(r['doppler_bin']);rr=int(r['range_bin']);pts.append((rr,(b+16)%32))
     if kind=='Cluster peaks':arr[b,rr]+=1
   if stage>=3:arr=np.fft.fftshift(arr,axes=0)
   return arr,pts
  def refresh_maps(self):
   o=self.last;t=o['target'];input_view=self.map_domain.currentIndex()==1;stage=o['entry'] if input_view else t;label=self.map_ref.currentText()
   a,pts=self.map_values(o['actual_input'] if input_view else o['output'],stage,True)
   if input_view:b=a.copy();bpts=pts
   elif label in o['references']:b,bpts=self.map_values(o['references'][label],stage,'Fixed' in label)
   else:b=np.zeros_like(a);bpts=[]
   y,yl=self.row_axis(stage,a.shape[0]);x=np.arange(a.shape[1])*RANGE_STEP;lo=min(float(a.min()),float(b.min()));hi=max(float(a.max()),float(b.max()));d=a-b;lim=max(float(np.max(np.abs(d))),1e-30)
   unit='Normalized power (amplitude²)' if stage<5 or self.map_quantity.currentText()=='Power' else 'Decision (0/1)' if stage==5 or self.map_quantity.currentText()=='CFAR mask' else 'Peak count per cell'
   for i,(p,z) in enumerate(zip(self.maps,[a,b,d])):
    p.title=('Actual input echo' if input_view else 'FPGA') if i==0 else ('Input echo copy' if input_view else label) if i==1 else ('Input self-check difference' if input_view else 'FPGA minus reference')
    p.data=z;p.x=x;p.y=y;p.xlabel='Range (m)';p.ylabel=yl;p.unit=unit;p.limits=(-lim,lim) if i==2 else (lo,hi);p.diverging=i==2;p.points=pts if i==0 else bpts if i==1 else [];p.update()
   self.map_note.setText('Input view shows the verified quantized injection; software references below compare the output.' if input_view else 'FPGA and software share the same color limits. Difference uses its own symmetric scale. '+('Clustering Power/mask are the shared injected map; peak circles and peak-count difference compare returned records.' if t==6 else 'FFT/MTI maps use actual captured arrays.'))
  def refresh_records(self):
   o=self.last;t=o['target'];label=self.map_ref.currentText();ref=o['references'].get(label);rows=[]
   if t==6:
    hdr=['Source','Record ID','Range cell','Range (m)','Natural bin','Velocity (m/s)','Peak power','Cells','Equal-power tie']
    for name,a,fixed in [('FPGA',o['output'],True),(label,ref or [],'Fixed' in label)]:
     for r in a:
      rows.append([name,r.get('record_id',''),r['range_bin'],number(r['range_bin']*RANGE_STEP),r['doppler_bin'],number(r['signed_doppler_bin']*VELOCITY_STEP),number(r.get('power_stored_integer',0)/(1<<30) if fixed else r.get('power_linear',r.get('peak_power_linear',0))),r.get('cluster_cells',''),r.get('tie_flag','N/A')])
    self.record_note.setText(f"All returned clusters: FPGA {len(o['output'])}; {label} {len(ref or [])}. No records hidden." if rows else 'No clusters returned by FPGA or selected reference. This is a valid empty result.')
   else:
    a=normalized(o['output'],t,True);b=normalized(ref,t,'Fixed' in label) if ref is not None else None
    hdr=['PRI / bin','Range cell','Range (m)','FPGA I / power','FPGA Q / decision','Reference I / power','Reference Q / decision','Difference I / power','Difference Q / decision']
    aa=a[0] if t==5 else a;bb=b[0] if t==5 and b is not None else b
    for idx,v in np.ndenumerate(aa):
     r,c=idx;rv=bb[idx] if bb is not None else 0
     aq=int(a[1][idx]) if t==5 else v.imag if t<=3 else '';bq=int(b[1][idx]) if t==5 and b is not None else rv.imag if t<=3 else ''
     rows.append([r,c,number(c*RANGE_STEP),number(float(v.real)),number(aq),number(float(rv.real)),number(bq),number(float((v-rv).real)),number(aq-bq) if t<=3 or t==5 else ''])
    self.record_note.setText(f'All {aa.size} FPGA output samples / cells with {label}. Indices are zero-based; complex amplitudes and power are normalized.')
   self.records.setColumnCount(len(hdr));self.records.setHorizontalHeaderLabels(hdr);fill(self.records,rows)
  def refresh_sweep(self):
   from .statistics import sweep
   o=self.last;t=o['target'];label=self.map_ref.currentText()
   self.pd.lines={};self.pfa.lines={};fill(self.sweep_table,[])
   self.sweep_plots.setVisible(t in (3,4))
   if t in (5,6):
    self.sweep_table.setColumnCount(3);self.sweep_table.setHorizontalHeaderLabels(['Measure / target','FPGA',label])
    def mask_of(data):
     if t==5:return np.asarray(data[1],bool)
     m=np.zeros((32,128),bool)
     for record in data:m[int(record['doppler_bin']),int(record['range_bin'])]=True
     return m
    ma=mask_of(o['output']);mb=mask_of(o['references'].get(label,([],[]) if t==5 else []))
    gates=np.zeros((32,128),bool);rows=[];hits=[0,0]
    for target in o.get('truth',[]):
     gate=np.zeros((32,128),bool);bin=int(np.rint(target.velocity/VELOCITY_STEP))%32
     for rr in range(max(3,target.delay-2),min(110,target.delay+3)):
      for bb in range(3,29):
       if abs((bb-bin+16)%32-16)<=1:gate[bb,rr]=True
     gates|=gate;ha=bool(np.any(ma&gate));hb=bool(np.any(mb&gate));hits[0]+=int(ha);hits[1]+=int(hb);rows.append([target.name+' matched within ±2 range / ±1 bin','Yes' if ha else 'No','Yes' if hb else 'No'])
    rows=[['Returned alarm cells' if t==5 else 'Returned clusters',int(ma.sum()) if t==5 else len(o['output']),int(mb.sum()) if t==5 else len(o['references'].get(label,[]))],['Defined targets',len(o.get('truth',[])),len(o.get('truth',[]))],['Matched defined targets',*hits],['Alarms / peaks outside defined target gates',int(np.count_nonzero(ma&~gates)),int(np.count_nonzero(mb&~gates))]]+rows
    fill(self.sweep_table,rows);self.sweep_note.setText('Actual fixed-configuration CFAR decisions / returned cluster peaks, compared with software. No threshold sweep is applied at these stages. Counts outside target gates are unassociated returns, not a validated false-alarm probability. File input without target truth cannot support a detection probability.');return
   self.sweep_table.setColumnCount(5);self.sweep_table.setHorizontalHeaderLabels(['Threshold (normalized power)','FPGA target fraction','Reference target fraction','FPGA outside-gate fraction','Reference outside-gate fraction'])
   if t not in (3,4):
    self.sweep_note.setText('Threshold sweep is available for FFT and Power output. CFAR decision differences and cluster matching are reported in the Accuracy tab. No Pd/Pfa estimate is asserted from one CPI.');self.pd.update();self.pfa.update();return
   a=normalized(o['output'],t,True);a=np.abs(a)**2 if t==3 else a
   ref=o['references'].get(label);b=normalized(ref,t,'Fixed' in label) if ref is not None else a;b=np.abs(b)**2 if t==3 else b
   sa=sweep(a,o.get('truth',()),noise_only=not o.get('truth'));thresholds=[r['threshold'] for r in sa['rows']];sb=sweep(b,o.get('truth',()),noise_only=not o.get('truth'),thresholds=thresholds)
   rows=[]
   for ra,rb in zip(sa['rows'],sb['rows']):
    rows.append([number(ra['threshold']),number(ra.get('target_fraction')),number(rb.get('target_fraction')),number(ra['outside_target_cell_fraction']),number(rb['outside_target_cell_fraction'])])
   for name,s in [('FPGA',sa),(label,sb)]:
    if o.get('truth'):self.pd.lines[name]=[r.get('target_fraction',0) for r in s['rows']]
    self.pfa.lines[name]=[r['outside_target_cell_fraction'] for r in s['rows']]
   for p in [self.pd,self.pfa]:p.x=np.log10(thresholds);p.xlabel='log10(threshold / normalized power)';p.update()
   fill(self.sweep_table,rows);self.sweep_note.setText('Exploratory single-CPI fractions, not qualified Pd/Pfa. Target association: ±2 range cells / ±1 Doppler bin; outside-target cells exclude these gates. '+('No target truth supplied: only cell exceedance is shown; use Noise only for an initial noise test.' if not o.get('truth') else 'Use independent noise-only and target CPI ensembles for statistical probabilities.'))
 return Window

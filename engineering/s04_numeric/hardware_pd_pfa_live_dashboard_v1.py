"""AX309 statistical test live monitor, read-only PySide6 desktop UI.
Reads own isolated candidate campaign RAW/RESULT. Never writes project evidence.
"""
from __future__ import annotations
import json, os, sys, time, math
from collections import deque
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QRectF,QPointF
from PySide6.QtGui import QColor,QFont,QPainter,QPen,QBrush
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,
 QHBoxLayout,QLabel,QFrame,QProgressBar,QGridLayout,QSizePolicy)
BASE=Path(__file__).resolve().parent
SETS={
 'pd':BASE/'hardware_stat_campaign_20261113_pd_v1',
 'pfa':BASE/'hardware_stat_campaign_20261113_pfa_v1'
}
PANEL='#151f32';EDGE='#2b3a53';TEXT='#eaf2ff';MUTED='#99abc3'
GREEN='#42d9a0';BLUE='#68b6ff';AMBER='#ffca74';RED='#ff758a'
APPSTYLE=f"""
QWidget {{background:#0b1220;color:{TEXT};font-family:'DejaVu Sans';}}
QFrame#panel {{background:{PANEL};border:1px solid {EDGE};border-radius:16px;}}
QLabel#h1 {{font-size:25px;font-weight:750;}}
QLabel#h2 {{font-size:18px;font-weight:700;}}
QLabel#big {{font-size:30px;font-weight:700;}}
QLabel#muted {{color:{MUTED};font-size:12px;}}
QLabel#kpi {{font-size:19px;font-weight:650;}}
QProgressBar {{background:#25324a;border:none;border-radius:8px;height:16px;text-align:center;}}
QProgressBar::chunk {{background:{BLUE};border-radius:8px;}}
"""
class Stream:
 def __init__(self,kind):
  self.kind=kind;self.root=SETS[kind];self.pos=0;self.rest='';self.count=0
  self.alarms=0;self.ok=0;self.clips=0;self.over=0;self.last=None;self.history=deque(maxlen=240)
  self.started=False;self.finished=None;self.problem=None
  self.expected=1000 if kind=='pd' else 20000
 def poll(self):
  if self.finished is None and (self.root/'RESULT.json').exists():
   try:self.finished=json.loads((self.root/'RESULT.json').read_text())
   except (OSError,json.JSONDecodeError):pass
  path=self.root/'RAW.jsonl'
  if not path.exists():return
  try:
   with path.open('r',encoding='utf8') as f:
    f.seek(self.pos);part=f.read();self.pos=f.tell()
   buf=self.rest+part;lines=buf.split('\n');self.rest=lines.pop()
   for line in lines:
    if not line:continue
    r=json.loads(line)
    if r['i']!=self.count:
     self.problem=f'Unexpected CPI index {r["i"]} at {self.count}'
    self.count+=1;self.alarms+=r['alarms'];self.clips+=r['clips'];self.over+=r['internal_events']
    if self.kind=='pd':self.ok+=int(r['D'])
    self.last=r;self.history.append(self.ok/self.count if self.kind=='pd' else self.alarms/(2782*self.count))
   self.started=self.count>0
  except (OSError,ValueError,json.JSONDecodeError) as exc:self.problem=str(exc)
 def status(self):
  if not self.finished:return ('RUNNING' if self.count else 'WAITING',BLUE)
  r=self.finished.get('hardware_candidate_statistical_result','INCONCLUSIVE')
  if r=='PASS_CANDIDATE':return ('PASS · SOFTWARE CANDIDATE',GREEN)
  if r=='FAIL_CANDIDATE':return ('FAIL · SOFTWARE CANDIDATE',RED)
  return ('INCONCLUSIVE',AMBER)

class Chart(QWidget):
 def __init__(self,stream):
  super().__init__();self.s=stream;self.setMinimumHeight(100)
 def paintEvent(self,event):
  p=QPainter(self);p.setRenderHint(QPainter.Antialiasing)
  w,h=self.width(),self.height()
  p.setPen(QPen(QColor(EDGE),1))
  for i in (1,2,3):p.drawLine(0,i*h//4,w,i*h//4)
  a=list(self.s.history)
  if len(a)<2:return
  # Show relative drift over latest recorded observations without exaggerating scale.
  if self.s.kind=='pd':lo,hi=0.,1.02
  else:lo,hi=0.,max(.002,max(a)*1.15)
  p.setPen(QPen(QColor(GREEN if self.s.kind=='pd' else BLUE),2.2))
  points=[QPointF(4+(w-8)*i/(len(a)-1),h-6-(h-12)*(v-lo)/(hi-lo)) for i,v in enumerate(a)]
  for a,b in zip(points,points[1:]):p.drawLine(a,b)
  p.end()
class Panel(QFrame):
 def __init__(self,kind,stream):
  super().__init__();self.setObjectName('panel');self.s=stream
  v=QVBoxLayout(self);v.setSpacing(12);v.setContentsMargins(20,20,20,18)
  h=QHBoxLayout()
  head=QLabel('Pd  |  Detection probability' if kind=='pd' else 'Pfa  |  False-alarm probability')
  head.setObjectName('h2');h.addWidget(head)
  h.addStretch();self.tag=QLabel('WAITING');self.tag.setStyleSheet(f'color:{BLUE};font-weight:700');h.addWidget(self.tag);v.addLayout(h)
  self.big=QLabel('0 / '+str(stream.expected));self.big.setObjectName('big');v.addWidget(self.big)
  self.bar=QProgressBar();self.bar.setRange(0,stream.expected);self.bar.setTextVisible(False);v.addWidget(self.bar)
  self.percent=QLabel('0.00% completed');self.percent.setObjectName('muted');v.addWidget(self.percent)
  g=QGridLayout();g.setHorizontalSpacing(30);g.setVerticalSpacing(5)
  self.l1=QLabel('0');self.l1.setObjectName('kpi');self.l2=QLabel('—');self.l2.setObjectName('kpi')
  self.l3=QLabel('0');self.l3.setObjectName('kpi');self.l4=QLabel('0');self.l4.setObjectName('kpi')
  names=(('Successful detections','Observed Pd','Input clips','Internal overflows')
         if kind=='pd' else ('CFAR alarms','Observed Pfa','Input clips','Internal overflows'))
  for i,(name,label) in enumerate(zip(names,(self.l1,self.l2,self.l3,self.l4))):
   r=i//2;c=i%2
   namew=QLabel(name);namew.setObjectName('muted');g.addWidget(namew,2*r,c)
   g.addWidget(label,2*r+1,c)
  v.addLayout(g)
  caption=QLabel('Detection rate per CPI' if kind=='pd' else 'Cumulative alarms / valid CUTs')
  caption.setObjectName('muted');v.addWidget(caption)
  self.chart=Chart(stream);v.addWidget(self.chart)
  self.conf=QLabel('Statistical decision: pending full fixed-N sample')
  self.conf.setWordWrap(True);self.conf.setObjectName('muted');v.addWidget(self.conf)
  self.setMinimumWidth(420)
 def update_values(self):
  s=self.s;state,color=s.status()
  self.tag.setText(state);self.tag.setStyleSheet(f'color:{color};font-weight:700')
  self.big.setText(f'{s.count:,} / {s.expected:,}')
  self.bar.setValue(min(s.count,s.expected))
  self.percent.setText(f'{100*s.count/s.expected:.2f}% completed')
  self.l1.setText(f'{s.ok:,}' if s.kind=='pd' else f'{s.alarms:,}')
  self.l2.setText('—' if not s.count else (f'{s.ok/s.count:.5f}' if s.kind=='pd'
                             else f'{s.alarms/(2782*s.count):.7f}'))
  self.l3.setText(f'{s.clips:,}');self.l4.setText(f'{s.over:,}')
  self.l3.setStyleSheet(f'color:{RED if s.clips else GREEN}')
  self.l4.setStyleSheet(f'color:{RED if s.over else GREEN}')
  result=s.finished
  if result:
   if s.kind=='pd':
    self.conf.setText(f'95% CP lower: {result.get("lower95_CP_D",0):.6f}  |  D ≥ 916/1000  |  Pre-group CFAR hits: {result.get("pre_grouping_Cfar_detection_count",0)}')
   else:
    b=result.get('empirical_bernstein') or {}
    self.conf.setText(f'95% Empirical Bernstein upper: {b.get("upper95",float("nan")):.7f}  |  Acceptance ≤ 0.0015')
  elif s.kind=='pd':
   self.conf.setText('Pending fixed-N decision: exact 95% lower CP ≥ 0.90 (≥916/1000)')
  else:
   self.conf.setText('Pending fixed-N decision: 95% CPI-level empirical Bernstein upper ≤ 0.0015')
  if s.problem:self.conf.setText('READ ERROR: '+s.problem)
  self.chart.update()

class Window(QMainWindow):
 def __init__(self):
  super().__init__();self.setWindowTitle('AX309 | REAL AX309 FPGA Pd & Pfa Live Monitor')
  self.resize(1060,710);self.setMinimumSize(900,630)
  central=QWidget();self.setCentralWidget(central)
  v=QVBoxLayout(central);v.setSpacing(18);v.setContentsMargins(28,26,28,22)
  head=QLabel('AX309  /  REAL FPGA / Statistical Capture');head.setObjectName('h1');v.addWidget(head)
  sub=QLabel('LIVE • Verified bitstream • UART • Actual FPGA Power and records • 2 independent fixed-sample campaigns')
  sub.setObjectName('muted');v.addWidget(sub)
  self.pd=Stream('pd');self.pfa=Stream('pfa')
  h=QHBoxLayout();h.setSpacing(18)
  self.p1=Panel('pd',self.pd);self.p2=Panel('pfa',self.pfa)
  h.addWidget(self.p1);h.addWidget(self.p2);v.addLayout(h)
  foot=QFrame();foot.setObjectName('panel');f=QVBoxLayout(foot);f.setContentsMargins(18,12,18,12)
  self.aggregate=QLabel('OFFICIAL PROJECT STATUS: OPEN · not yet accepted');self.aggregate.setStyleSheet(f'color:{AMBER};font-weight:700;font-size:15px')
  f.addWidget(self.aggregate)
  note=QLabel('A candidate PASS/FAIL applies only to the real AX309 FPGA numeric path. Final FFT-IP / RTL / hardware equivalence and independent approval remain separate.')
  note.setWordWrap(True);note.setObjectName('muted');f.addWidget(note)
  v.addWidget(foot)
  self.footer=QLabel('Reading project evidence locally every 1 second · read-only dashboard')
  self.footer.setObjectName('muted');v.addWidget(self.footer)
  self.tick()
  timer=QTimer(self);timer.timeout.connect(self.tick);timer.start(1000)
 def tick(self):
  self.pd.poll();self.pfa.poll();self.p1.update_values();self.p2.update_values()
  total=self.pd.count+self.pfa.count
  if self.pd.finished and self.pfa.finished:
   a=self.pd.finished.get('software_candidate_statistical_result')
   b=self.pfa.finished.get('software_candidate_statistical_result')
   both='BOTH PASS CANDIDATE' if a==b=='PASS_CANDIDATE' else 'AT LEAST ONE FAIL/INCONCLUSIVE'
   self.aggregate.setText('HARDWARE RESULTS: '+both+'  |  OFFICIAL PROJECT: OPEN')
  self.footer.setText(f'Live record updates: {total:,} CPI observed  •  Files: docs-audit worktree  •  Read-only')
def main():
 os.environ.setdefault('QT_QPA_PLATFORM','xcb')
 a=QApplication(sys.argv);a.setStyleSheet(APPSTYLE)
 w=Window();w.show();w.raise_();w.activateWindow()
 sys.exit(a.exec())
if __name__=='__main__':main()

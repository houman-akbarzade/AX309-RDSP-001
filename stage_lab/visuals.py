"""Dimensioned Qt plots and live SVG illustrations for Stage Lab; no DSP operations."""
import html
import numpy as np
from PySide6.QtCore import Qt,QRectF,QPointF
from PySide6.QtGui import QPainter,QColor,QPen,QPolygonF,QImage
from PySide6.QtWidgets import QWidget
BG='#101c2c';FG='#e7edf8'
COLORS=['#ffca68','#75d8fa','#72e0b2','#e099fa','#ff8585']
class Curves(QWidget):
 def __init__(self,title):
  super().__init__();self.title=title;self.lines={};self.x=None;self.xlabel='Range cell index';self.ylabel='Normalized amplitude';self.setMinimumSize(250,280)
 def paintEvent(self,e):
  p=QPainter(self);p.fillRect(self.rect(),QColor(BG));p.setRenderHint(QPainter.Antialiasing);p.setPen(QColor(FG));p.drawText(12,23,self.title)
  a=QRectF(78,120,max(20,self.width()-100),max(20,self.height()-185))
  arrays=[np.asarray(v,float).ravel() for v in self.lines.values() if len(v)]
  if not arrays:p.drawText(a,Qt.AlignCenter,'No samples for this selection');return
  lo=min(float(np.nanmin(v)) for v in arrays);hi=max(float(np.nanmax(v)) for v in arrays)
  if lo==hi:hi+=max(1e-12,abs(hi)*.05);lo-=max(1e-12,abs(lo)*.05)
  pad=(hi-lo)*.04;lo-=pad;hi+=pad
  n=max(map(len,arrays));x=np.arange(n) if self.x is None or len(self.x)!=n else np.asarray(self.x)
  xl=float(x.min());xh=float(x.max());xh=xh if xh>xl else xl+1
  p.setPen(QPen(QColor('#30465b'),1))
  for j in range(5):
   f=j/4;xx=a.left()+a.width()*f;yy=a.bottom()-a.height()*f
   p.drawLine(QPointF(xx,a.top()),QPointF(xx,a.bottom()));p.drawLine(QPointF(a.left(),yy),QPointF(a.right(),yy))
   p.setPen(QColor(FG));p.drawText(QRectF(min(max(xx-36,a.left()-12),self.width()-74),a.bottom()+5,72,22),Qt.AlignCenter,f'{xl+(xh-xl)*f:.4g}')
   p.drawText(QRectF(0,yy-10,72,20),Qt.AlignRight|Qt.AlignVCenter,f'{lo+(hi-lo)*f:.4g}');p.setPen(QColor('#30465b'))
  for i,(name,v) in enumerate(self.lines.items()):
   y=np.asarray(v,float).ravel()
   if not len(y):continue
   xx=x if len(y)==len(x) else np.linspace(xl,xh,len(y))
   pts=[QPointF(a.left()+(u-xl)/(xh-xl)*a.width(),a.bottom()-(z-lo)/(hi-lo)*a.height()) for u,z in zip(xx,y) if np.isfinite(z)]
   p.setPen(QPen(QColor(COLORS[i%5]),2))
   if len(pts)>1:p.drawPolyline(QPolygonF(pts))
   elif pts:p.drawEllipse(pts[0],3,3)
   p.drawText(12,43+15*i,name)
  p.setPen(QColor(FG));p.drawText(QRectF(a.left(),self.height()-30,a.width(),22),Qt.AlignCenter,self.xlabel)
  p.save();p.translate(16,a.center().y());p.rotate(-90);p.drawText(QRectF(-a.height()/2,-12,a.height(),24),Qt.AlignCenter,self.ylabel);p.restore()
class Heatmap(QWidget):
 def __init__(self,title):
  super().__init__();self.title=title;self.data=None;self.x=None;self.y=None;self.xlabel='Range (m)';self.ylabel='Doppler frequency (Hz)';self.unit='Normalized power';self.limits=None;self.diverging=False;self.points=[];self.setMinimumSize(260,320)
 def paintEvent(self,e):
  p=QPainter(self);p.fillRect(self.rect(),QColor(BG));p.setPen(QColor(FG));p.drawText(12,24,self.title)
  a=QRectF(76,65,max(20,self.width()-100),max(20,self.height()-133))
  if self.data is None:p.drawText(a,Qt.AlignCenter,'No map available');return
  z=np.nan_to_num(np.asarray(self.data,float));lo,hi=self.limits or (float(z.min()),float(z.max()))
  if hi<=lo:hi=lo+1
  t=np.clip((z-lo)/(hi-lo),0,1)
  if self.diverging:
   r=np.where(t>.5,255,510*t);b=np.where(t<.5,255,510*(1-t));g=255*(1-np.abs(2*t-1))
  else:r=255*np.clip(2*t-.5,0,1);g=240*np.clip(2*t,0,1);b=90+140*(1-t)
  rgba=np.empty((*z.shape,4),np.uint8);rgba[...,0]=r;rgba[...,1]=g;rgba[...,2]=b;rgba[...,3]=255
  rgba=np.ascontiguousarray(rgba[::-1]);im=QImage(rgba.data,z.shape[1],z.shape[0],rgba.strides[0],QImage.Format_RGBA8888).copy();p.drawImage(a,im)
  x=np.arange(z.shape[1]) if self.x is None else self.x;y=np.arange(z.shape[0]) if self.y is None else self.y
  for j in range(5):
   f=j/4;xx=a.left()+a.width()*(.5+f*(z.shape[1]-1))/z.shape[1];yy=a.bottom()-a.height()*(.5+f*(z.shape[0]-1))/z.shape[0]
   p.drawText(QRectF(min(max(xx-35,a.left()-12),self.width()-72),a.bottom()+4,70,20),Qt.AlignCenter,f'{x[0]+(x[-1]-x[0])*f:.4g}')
   p.drawText(QRectF(0,yy-10,71,20),Qt.AlignRight|Qt.AlignVCenter,f'{y[0]+(y[-1]-y[0])*f:.4g}')
  for col,row in self.points:
   p.setPen(QPen(QColor('#ffffff'),2));p.drawEllipse(QPointF(a.left()+(col+.5)/z.shape[1]*a.width(),a.bottom()-(row+.5)/z.shape[0]*a.height()),5,5)
  p.drawText(12,47,f'{lo:.4g} .. {hi:.4g} | {self.unit}')
  p.drawText(QRectF(a.left(),self.height()-30,a.width(),23),Qt.AlignCenter,self.xlabel)
  p.save();p.translate(16,a.center().y());p.rotate(-90);p.drawText(QRectF(-a.height()/2,-12,a.height(),24),Qt.AlignCenter,self.ylabel);p.restore()
def svg_start(w,h):
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="#101c2c"/><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3Z" fill="#75d8fa"/></marker></defs><g font-family="DejaVu Sans" fill="#e7edf8">'
def text(x,y,s,size=15,color='#e7edf8'):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{html.escape(str(s))}</text>'
def box(x,y,w,h,label,color='#223952'):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{color}" stroke="#75d8fa"/>'+text(x+12,y+h/2+5,label)
def arrow(x,y,xx,yy):
 return f'<path d="M{x},{y} L{xx},{yy}" fill="none" stroke="#75d8fa" stroke-width="2" marker-end="url(#arrow)"/>'
def architecture_svg(entry,target,raw=False,input_mode='',pri_count=33):
 names=['Raw IQ','MF16','MTI2','FFT32 IP','Power','CA-CFAR','Grouping']
 s=svg_start(1040,620)+text(24,30,'AX309 Stage Lab v0.2.1 | separate SRAM test images',22)
 s+=box(25,65,460,65,'PC: Float input / Python + MATLAB references')+box(555,65,460,65,'PC: compare echo + FPGA output / save JSON + NPZ')
 s+=box(25,185,285,70,'UART RX / CRC / case + sequence')+box(365,185,300,70,'Shared banked test RAM / input echo')+box(725,185,290,70,'UART TX / status + output words')
 s+=arrow(255,130,167,185)+arrow(310,220,365,220)+arrow(665,220,725,220)+arrow(870,185,800,130)
 for k in range(1,7):
  x=25+((k-1)%3)*345;y=325+((k-1)//3)*110;active=entry<k<=target
  s+=box(x,y,300,65,names[k], '#176d92' if active else '#263341')
  if k not in (3,6):s+=arrow(x+300,y+32,x+345,y+32)
  if k==3:s+=arrow(x+150,y+65,x+150,y+100)+arrow(x+150,y+100,175,y+100)+arrow(175,y+100,175,y+110)
 inject=0 if raw else entry
 s+=text(30,290,f'Injection: {names[inject]} | capture: {names[target]} | '+('raw hardware cascade' if raw else 'isolated stage'),18,'#ffca68')
 symbol='single PRI' if target==1 and pri_count==1 else f'{pri_count} PRI / CPI' if target<=2 else 'CPI / 32 x 128 cells'
 # Explicit injection/capture arrows point to the first/last active hardware block.
 first=1 if raw else entry+1
 ix=25+((first-1)%3)*345;iy=325+((first-1)//3)*110
 ox=25+((target-1)%3)*345;oy=325+((target-1)//3)*110
 s+=f'<path d="M{ix+35},{iy-40} L{ix+35},{iy}" stroke="#ffca68" stroke-width="4" marker-end="url(#arrow)"/>'
 s+=text(ix+45,iy-12,'IN: '+names[inject],14,'#ffca68')
 s+=f'<path d="M{ox+265},{oy+65} L{ox+265},{oy+88}" stroke="#72e0b2" stroke-width="4" marker-end="url(#arrow)"/>'
 s+=text(ox+135,oy+104,'OUT: '+names[target],14,'#72e0b2')
 s+=f'<rect x="18" y="538" width="12" height="30" fill="#ffca68"/><path d="M35,550 L45,550 L45,540 L50,540 L50,550 L60,550 L60,540 L65,540 L65,550" fill="none" stroke="#ffca68" stroke-width="2"/>'
 s+=text(80,550,f'Input object: {symbol}. Mode: {input_mode}',16)
 s+=text(30,580,'Cyan blocks: executed hardware. Raw mode: UART handoff + reprogram between stages.',15)
 return s+'</g></svg>'
def scenario_svg(name,targets,noise):
 s=svg_start(1040,400)+text(25,32,name,23)+text(25,62,f'One CPI | complex noise RMS = {noise:.6g} normalized amplitude',16)
 s+='<path d="M70,300 L70,135 M35,165 Q70,120 105,165 M20,145 Q70,90 120,145" fill="none" stroke="#75d8fa" stroke-width="4"/>'
 s+=text(30,335,'Radar')
 if name=='Aircraft in clutter':s+='<path d="M160,285 L220,180 L280,285 L340,210 L410,285 Z" fill="#4a5b48"/>'+text(175,310,'Stationary clutter')
 for i,t in enumerate(targets):
  x=190+t.delay/128*700;y=110+(i%4)*55
  s+=f'<path d="M{x-18},{y} L{x+20},{y} L{x-2},{y-10} L{x-2},{y+10}Z" fill="{COLORS[i%5]}"/>'
  s+=text(x-60,y+30,f'{t.name}: {t.velocity:g} m/s',14,COLORS[i%5])
  s+=arrow(x,y-18,x+(45 if t.velocity>=0 else -45),y-18)
  s+=f'<path d="M75,275 L{x},{y+8}" stroke="#30465b" stroke-dasharray="5 5"/>'
 if not targets:s+=text(340,200,'Noise only: no defined target',24)
 s+=text(170,375,'Radial velocity sign follows the existing radar model; target positions are schematic.',14)
 return s+'</g></svg>'

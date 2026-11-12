import json
from pathlib import Path
from PySide6.QtWidgets import QApplication,QTextBrowser
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage,QPainter
from PySide6.QtCore import qInstallMessageHandler,QUrl
from .models import ROOT

def main():
 app=QApplication([]);warnings=[];qInstallMessageHandler(lambda t,c,m:warnings.append(m));D=ROOT/'engineering/evidence/auto_lab_v0.3';runs=json.loads((D/'board-validation-runs.json').read_text());count=0;seen=set()
 for name in ['quick','statistics']:
  d=Path(runs[name]['directory']);state=json.loads((d/'suite.json').read_text())
  for job in state['jobs']:
   if job['stage']<3:continue
   path=d/(job['id']+'-summary.svg');renderer=QSvgRenderer(str(path));assert renderer.isValid();im=QImage(1840,400,QImage.Format_ARGB32);im.fill(0);p=QPainter(im);renderer.render(p);p.end()
   for x in [100,1020]:
    col=im.pixelColor(x,70);assert col.alpha()==255 and col.name()!='#101c2c',(path,x,col.name())
   count+=1
   if job['stage'] not in seen:
    seen.add(job['stage']);im.save(str(D/f'qt-fixed-stage-{job["stage"]}.png'))
    browser=QTextBrowser();browser.resize(1100,600);browser.setSearchPaths([str(d)]);browser.setHtml('<h2>FPGA / reference</h2><img src="'+path.name+'" width="1000">');browser.show();app.processEvents();browser.grab().save(str(D/f'qt-browser-stage-{job["stage"]}.png'));browser.close()
 assert not any('nested svg' in m.lower() for m in warnings),warnings
 (D/'qt-render-validation.json').write_text(json.dumps(dict(status='PASS',paired_maps=count,stages=sorted(seen),both_panels_painted=True,nested_svg_warnings=False),indent=2));print('PASS_REAL_QT_RENDER',count,'paired maps; both panels painted; browser screenshots for FFT/Power/CFAR/Grouping')
if __name__=='__main__':main()

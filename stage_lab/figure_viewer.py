"""Vector figure viewer with wheel zoom, pan, fit and explicit zoom buttons."""
from pathlib import Path
from PySide6.QtCore import Qt,QUrl
from PySide6.QtWidgets import QTextBrowser,QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QGraphicsView,QGraphicsScene,QLabel
from PySide6.QtSvgWidgets import QGraphicsSvgItem
class ZoomView(QGraphicsView):
 def __init__(self,path):
  super().__init__();scene=QGraphicsScene(self);self.item=QGraphicsSvgItem(str(path));scene.addItem(self.item);self.setScene(scene);self.setDragMode(QGraphicsView.ScrollHandDrag);self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse);self.setBackgroundBrush(Qt.darkGray)
 def zoom(self,factor):
  current=self.transform().m11()
  if .02<current*factor<100:self.scale(factor,factor)
 def wheelEvent(self,event):
  self.zoom(1.2 if event.angleDelta().y()>0 else 1/1.2);event.accept()
 def fit(self):self.fitInView(self.item.boundingRect(),Qt.KeepAspectRatio)
class FigureDialog(QDialog):
 def __init__(self,path,parent=None):
  super().__init__(parent);self.setWindowTitle('نمای بزرگ شکل · Zoom / Pan');self.resize(1450,850);layout=QVBoxLayout(self);bar=QHBoxLayout();layout.addLayout(bar);self.view=ZoomView(path);layout.addWidget(self.view)
  for label,callback in [('بزرگ‌تر +',lambda:self.view.zoom(1.25)),('کوچک‌تر −',lambda:self.view.zoom(.8)),('اندازه پنجره',self.view.fit),('اندازه اصلی 100%',self.view.resetTransform)]:
   b=QPushButton(label);b.clicked.connect(callback);bar.addWidget(b)
  bar.addWidget(QLabel('چرخ ماوس: زوم | کشیدن با ماوس: جابه‌جایی'))
 def showEvent(self,event):super().showEvent(event);self.view.fit()
class ReportBrowser(QTextBrowser):
 def __init__(self):
  super().__init__();self.setOpenLinks(False);self.anchorClicked.connect(self.open_link);self.figure=None
 def open_link(self,url):
  resolved=self.source().resolved(url);path=Path(resolved.toLocalFile())
  if path.suffix.lower()=='.svg' and path.is_file():
   self.figure=FigureDialog(path,self);self.figure.showMaximized()
  else:self.setSource(resolved)

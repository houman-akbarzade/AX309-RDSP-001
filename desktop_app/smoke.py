"""GUI rendering/export checks; --hardware executes the currently programmed full DSP."""
import sys,json
from pathlib import Path
from PySide6.QtWidgets import QApplication
from .scenarios import LIBRARY,ROOT
from .__main__ import Worker,Window
def main():
 app=QApplication([]);results=[];errors=[];w=Window()
 outdir=ROOT/'engineering/evidence/s10/full_ip_20261112';outdir.mkdir(parents=True,exist_ok=True)
 modes=['Float reference','Legacy fixed reference','Demo']+(['Hardware'] if '--hardware' in sys.argv else [])
 for mode in modes:
  worker=Worker(dict(scenario='Two aircraft',mode=mode,port=w.port.currentText(),range=0,velocity=0,amplitude=1,noise=.002,seed=20261112,compare=True))
  outputs=[];worker.completed.connect(outputs.append);worker.failed.connect(errors.append);worker.run()
  if errors:raise RuntimeError(errors)
  assert len(outputs)==1;out=outputs[0];w.show_result(out);w.show();app.processEvents()
  views=[]
  for view in ['Range–Doppler','Range profile','Doppler slice']:
   w.view.setCurrentText(view)
   for scale in ['Power dB','Power linear']:
    w.scale.setCurrentText(scale);w.cfarbox.setChecked(True);app.processEvents()
    image=w.grab();assert not image.isNull();views.append([view,scale])
  w.view.setCurrentText('Range–Doppler');w.scale.setCurrentText('Power dB');w.cfarbox.setChecked(False);app.processEvents()
  w.grab().save(str(outdir/(mode.replace(' ','_')+'.png')))
  path=outdir/(mode.replace(' ','_')+'-export.json');w.export_result(path)
  restored=json.loads(path.read_text());assert restored['mode']==mode
  assert len(restored['records'])==w.table.rowCount();assert path.with_suffix('.csv').is_file()
  if mode=='Hardware':
   assert out['hardware']['terminal']=='COMMIT' and out['hardware']['released']
   assert len(out['records'])==9 and out['power'].shape==(128,32)
  results.append(dict(mode=mode,records=len(out['records']),views=views,export='PASS'))
 print(json.dumps(dict(gui_render_export='PASS',results=results),indent=2))
 w.close()
if __name__=='__main__':main()

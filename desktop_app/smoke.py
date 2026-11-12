"""Small reproducible desktop smoke; --hardware programs SRAM only."""
import sys,json
from PySide6.QtWidgets import QApplication
from .scenarios import LIBRARY,prepare,exact_reference,score,ROOT
from .__main__ import Worker
def main():
 app=QApplication([]);results=[]
 for name in LIBRARY:
  raw,targets,meta=prepare(name)
  assert len(raw)==16896 and not meta['input_saturations']
  result,telemetry=exact_reference(raw)
  results.append(dict(scenario=name,records=len(result['clusters']),
   comparison=score(result['clusters'],targets),saturation=telemetry['total']))
 if '--hardware' in sys.argv:
  hardware=[];errors=[]
  for name in ['Single aircraft','Two aircraft']:
   w=Worker(dict(scenario=name,mode='Hardware',port='/dev/ttyUSB1',range=0,velocity=0.,amplitude=1.,noise=.002))
   w.completed.connect(lambda out:hardware.append({k:v for k,v in out.items() if k not in ('targets','power','records')}))
   w.failed.connect(errors.append);w.run()
   if errors:raise RuntimeError(errors)
  assert len(hardware)==2 and all(v['hardware_iq']['bytewise_match'] for v in hardware)
  print(json.dumps(dict(hardware_iq=hardware,hardware_dsp='NOT_VERIFIED'),indent=2))
 print(json.dumps(dict(scenarios=results,smoke='PASS execution; association failures remain visible'),indent=2))
if __name__=='__main__':main()

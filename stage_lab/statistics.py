"""Exploratory threshold sweeps; never statistical Pd/Pfa qualification."""
import numpy as np
from desktop_app.scenarios import VELOCITY_STEP
def sweep(power,truth=(),noise_only=False):
 p=np.asarray(power,float)
 if p.shape!=(32,128):raise ValueError('32 Doppler bins x 128 range cells required')
 valid=p[3:29,3:110];positive=valid[valid>0]
 low=max(float(np.quantile(positive,.1))*.01,1e-30) if positive.size else 1e-30
 high=max(float(valid.max())*1.01,low*10)
 thresholds=np.geomspace(low,high,64);rows=[]
 for threshold in thresholds:
  row=dict(threshold=float(threshold))
  if noise_only:row.update(false_alarm_cells=int(np.count_nonzero(valid>threshold)),valid_cells=2782,cell_exceedance_fraction=float(np.mean(valid>threshold)))
  else:
   detected=0
   for t in truth:
    b=int(np.rint(t.velocity/VELOCITY_STEP))%32
    cells=[p[bb,rr] for rr in range(max(3,t.delay-2),min(110,t.delay+3)) for bb in range(3,29) if abs((bb-b+16)%32-16)<=1]
    detected+=int(bool(cells) and max(cells)>threshold)
   row.update(detected_defined_targets=detected,defined_targets=len(truth),target_fraction=detected/len(truth) if truth else None)
  rows.append(row)
 return dict(scope='One-CPI exploratory threshold sweep, NOT statistical Pd/Pfa/ROC qualification. Correlated cells are not independent trials.',noise_only=noise_only,independent_CPIs=1,rows=rows)

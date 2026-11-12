"""Bounded physical release checks, run after the quick suite owns/releases the UART."""
import json,time,sys
from pathlib import Path
from .auto_suite import execute_suite,execute_normal
from .auto_cases import spec
from .models import ROOT
def main():
 quick_log=Path('/tmp/auto_lab_quick.log');deadline=time.monotonic()+1200
 while True:
  content=quick_log.read_text() if quick_log.exists() else ''
  lines=[s for s in content.splitlines() if s.startswith('SUITE_RESULT ')]
  if lines:break
  if time.monotonic()>deadline:raise TimeoutError('Quick suite did not finish; refusing concurrent UART use')
  time.sleep(1)
 quick=json.loads(lines[-1].split(' ',1)[1]);assert quick['status']=='COMPLETE',quick
 print('QUICK_SUITE_COMPLETE',quick['directory'],flush=True)
 stats=execute_suite(dict(mode='auto',level='statistics',repeats=3,engine='Python',port='/dev/ttyUSB1',seed=20261112),progress=lambda s:print(s,flush=True))
 print('STATISTICAL_PATH_RESULT',json.dumps(stats),flush=True);assert stats['status']=='COMPLETE',stats
 config=dict(mode='normal',case=spec('Two aircraft',noise=.002),engine='Both',port='/dev/ttyUSB1')
 normal=execute_normal(config,progress=lambda s:print(s,flush=True));print('NORMAL_RESULT',json.dumps(normal),flush=True)
 # Replay our own saved raw Q1.15 IQ as file input, with truth explicitly absent.
 filecase=execute_normal(dict(config,engine='Python',file=str(Path(normal['directory'])/'normal.npz'),file_format='Stored codes'),progress=lambda s:print(s,flush=True));print('NORMAL_FILE_RESULT',json.dumps(filecase),flush=True)
 d=ROOT/'engineering/evidence/auto_lab_v0.3';d.mkdir(exist_ok=True);report=dict(quick=quick,statistics=stats,normal=normal,normal_file=filecase,scope='Finite development release checks, not statistical acceptance campaign')
 (d/'board-validation-runs.json').write_text(json.dumps(report,indent=2));print('AUTO_LAB_BOARD_PATHS_COMPLETE',flush=True)
if __name__=='__main__':main()

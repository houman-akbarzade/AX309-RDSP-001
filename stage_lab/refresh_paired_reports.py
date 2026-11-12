from pathlib import Path
import sys,json,subprocess
import numpy as np
from scipy.io import savemat,loadmat
sys.path.insert(0,'/home/houman/AX309-RDSP-001-stage-lab')
from stage_lab.models import ROOT,decode,compare,software_input
from stage_lab.auto_cases import build_source
from stage_lab.auto_suite import jsonable
from stage_lab.auto_report import render_report
D=ROOT/'engineering/evidence/auto_lab_v0.3';runs=json.loads((D/'board-validation-runs.json').read_text());tasks=[];commands=[];B=ROOT/'rtl/build/stage_lab/paired_matlab';B.mkdir(exist_ok=True)
for kind in ['quick','statistics']:
 d=Path(runs[kind]['directory']);s=json.loads((d/'suite.json').read_text())
 for j in s['jobs']:
  if j['stage'] not in (5,6):continue
  z=np.load(d/j['artifact']);rows=z['input_words'].size//128;entry=j['entry'];a=decode(z['input_words'],entry,rows)
  if j['scope']=='accumulated':entry=0;a=software_input(build_source(s['cases'][j['case']])[0],0)[0]
  i=len(tasks);inp=B/f'in{i}.mat';out=B/f'out{i}.mat';savemat(inp,{'input_a':a[0],'input_mask':a[1]} if entry==5 else {'input_a':a});commands.append(f"stage_lab_ref('{inp}','{out}',{entry},{j['stage']},1);");tasks.append((d,s,j,out))
script=B/'batch.m';script.write_text(f"addpath('{ROOT/'stage_lab/matlab'}');"+'\n'.join(commands));p=subprocess.run([str(Path.home()/'.local/bin/matlab'),'-batch',f"run('{script}')"],capture_output=True,text=True,timeout=600);assert p.returncode==0,p.stdout+p.stderr
for d,s,j,out in tasks:
 m=loadmat(out,simplify_cells=True);t=j['stage'];r=(np.asarray(m['result_power']),np.asarray(m['result_mask'],bool)) if t==5 else [m['result']] if isinstance(m['result'],dict) else [] if np.asarray(m['result']).size==0 else list(m['result']);zpath=d/j['artifact'];z=dict(np.load(zpath));got=decode(z['output_words'],t)
 key='chain' if j['scope']=='accumulated' else 'ref';metrics=compare(got,r,t,True);j['full_chain_metrics' if key=='chain' else 'metrics']['MATLAB Fixed']=metrics
 if t==5:z[key+'_MATLAB_Fixed_power']=r[0];z[key+'_MATLAB_Fixed_mask']=r[1];np.savez_compressed(zpath,**z)
 else:j['record_references'][key+' MATLAB Fixed']=jsonable(r)
 (d/(j['id']+'.json')).write_text(json.dumps(jsonable(j),ensure_ascii=False,indent=2))
for d,s,j,out in tasks:
 if (d/'suite.json').exists():(d/'suite.json').write_text(json.dumps(jsonable(s),ensure_ascii=False,indent=2))
for d in {x[0] for x in tasks}:render_report(json.loads((d/'suite.json').read_text()),d)
print('PASS: MATLAB executed once for',len(tasks),'CFAR/grouping reference cases; paired maps and shared colorbars generated',flush=True)

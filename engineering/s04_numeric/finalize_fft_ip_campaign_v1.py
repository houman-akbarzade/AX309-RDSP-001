"""Local one-shot finalize of both FFT-IP statistical runs.
Waits for two complete RESULTS then verifies raw hashes and commits only named evidence.
Does not change test data, project requirements, or unrelated working-tree changes.
"""
from __future__ import annotations
import hashlib,json,subprocess,time,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'engineering/s04_numeric'
IDS=('pd','pfa')
BRANCH='docs/fpga-engineering-repository-audit'
def git(*args):
 return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def main():
 while True:
  if git('branch','--show-current')!=BRANCH:
   print('FINALIZER ABORT: selected branch changed',flush=True);return 2
  result_paths=[BASE/f'fft_ip_stat_campaign_20261113_{q}_v1'/'RESULT.json' for q in IDS]
  if all(p.is_file() for p in result_paths):
   break
  time.sleep(20)
 for q,p in zip(IDS,result_paths):
  result=json.loads(p.read_text())
  raw=p.parent/'RAW.jsonl'
  digest=hashlib.sha256(raw.read_bytes()).hexdigest()
  expected=1000 if q=='pd' else 20000
  if result['completed']!=expected or result['raw_sha256']!=digest:
   print('FINALIZER REFUSAL: incomplete or raw hash mismatch',q,flush=True);return 3
  if sum(1 for _ in raw.open())!=expected:
   print('FINALIZER REFUSAL: line count',q,flush=True);return 4
  print(q,'verified:',result['software_candidate_statistical_result'],flush=True)
 # Intentional narrow staging. No replay file, no diagnostic outputs.
 paths=[]
 for q in IDS:
  rel=Path(f'engineering/s04_numeric/fft_ip_stat_campaign_20261113_{q}_v1')
  paths.extend([str(rel/f) for f in ('RAW.jsonl','CHECKPOINT.json','RESULT.json')])
 subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
 if not git('diff','--cached','--name-only'):
  print('Nothing staged',flush=True);return 0
 commit=subprocess.run(['git','commit','-m','test: preserve full Xilinx FFT-IP Pd Pfa statistical results'],cwd=ROOT,capture_output=True,text=True)
 print(commit.stdout,commit.stderr,flush=True)
 return commit.returncode
if __name__=='__main__':sys.exit(main())

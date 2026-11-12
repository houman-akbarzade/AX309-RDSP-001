#!/usr/bin/env python3
"""Analyze a completed structural ISim FFT trace; never grant acceptance."""
from pathlib import Path
import sys,json,math,argparse
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c05_native_integer_v1 as C05
def signed(v,w):return v-(1<<w) if v&(1<<(w-1)) else v
def pair(v):return signed(v&((1<<25)-1),25),signed((v>>25)&((1<<25)-1),25)
def analyze(trace):
 data=[[[None]*32 for _ in range(128)] for _ in range(3)]
 for line in Path(trace).read_text().splitlines():
  case,r,b,value=line.split();case,r,b=map(int,(case,r,b))
  assert data[case][r][b] is None
  data[case][r][b]=pair(int(value,16))
 report=[]
 for case in range(3):
  assert all(v is not None for row in data[case] for v in row)
  vals=[pair(int(v,16)) for v in (ROOT/f'rtl/tb/vectors/radar_cpi/{case}_rd.hex').read_text().splitlines()]
  golden=[vals[r*32:(r+1)*32] for r in range(128)]
  errors=[];mismatch=0;energy=0
  for r in range(128):
   for b in range(32):
    got,ref=data[case][r][b],golden[r][b]
    mismatch+=got!=ref;errors.extend(a-v for a,v in zip(got,ref));energy+=sum(v*v for v in ref)
  got,old=C05.complete_map(data[case]),C05.complete_map(golden)
  geom=lambda rows:[(v['range_bin'],v['doppler_bin'],v['cluster_cells'],v['tie_flag'],v['max_equal_power_cells']) for v in rows]
  report.append(dict(case=case,complex_words=4096,mismatched_complex_words=mismatch,
   max_abs_component_error_lsb=max(map(abs,errors)),
   rms_component_error_lsb=math.sqrt(sum(v*v for v in errors)/len(errors)),
   relative_rms_error=math.sqrt(sum(v*v for v in errors)/energy) if energy else 0,
   reference_clusters=len(old['clusters']),ip_clusters=len(got['clusters']),
   mask_disagreements=sum(a!=b for x,y in zip(got['mask'],old['mask']) for a,b in zip(x,y)),
   cluster_geometry_equal=geom(got['clusters'])==geom(old['clusters']),
   ip_clusters_detail=got['clusters']))
 return dict(strict_C02_bittrue_status='FAIL' if any(v['mismatched_complex_words'] for v in report) else 'PASS',
  scope='Three deterministic CPIs; not Pfa/Pd qualification; no approval of numeric baseline change',cases=report)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('trace',type=Path);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 result=analyze(args.trace);args.out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(strict_C02_bittrue_status=result['strict_C02_bittrue_status'],cases=[{k:v for k,v in row.items() if k!='ip_clusters_detail'} for row in result['cases']]),indent=2))
if __name__=='__main__':main()

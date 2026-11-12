"""Functional measurements and conservative, CPI-based statistical summaries."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import beta
from desktop_app.scenarios import RANGE_STEP,VELOCITY_STEP
from s03_reference import model as M
def association(records,targets):
 n=len(targets);m=len(records);cost=np.full((n,m+n),1e6,float)
 for i,t in enumerate(targets):
  b=int(np.rint(t.velocity/VELOCITY_STEP))%32
  for j,r in enumerate(records):
   dr=abs(r['range_bin']-t.delay);db=abs((r['doppler_bin']-b+16)%32-16)
   if dr<=2 and db<=1:cost[i,j]=dr+db*.25
  cost[i,m+i]=100
 ri,ci=linear_sum_assignment(cost) if n else ([],[]);matched=[];used=set()
 for i,j in zip(ri,ci):
  t=targets[i];ok=j<m and cost[i,j]<100
  row=dict(target=t.name,matched=bool(ok),expected_range_m=t.delay*RANGE_STEP,expected_velocity_m_s=t.velocity)
  if ok:
   r=records[j];used.add(int(j));row.update(record_id=r['record_id'],range_error_m=(r['range_bin']-t.delay)*RANGE_STEP,velocity_error_m_s=r['signed_doppler_bin']*VELOCITY_STEP-t.velocity)
  matched.append(row)
 return dict(matches=matched,matched_targets=sum(x['matched'] for x in matched),defined_targets=n,unassociated_clusters=m-len(used),all_targets_resolved=bool(n and len(used)==n),criterion='One-to-one association; ±2 range cells and ±1 natural Doppler bin, circular distance for association only; clustering itself is nonwrapped.')
def resolve_profile(power,expected):
 """Two distinct local maxima within ±1 cell; valley >=3dB below weaker peak."""
 p=np.asarray(power,float);peaks=[i for i in range(1,len(p)-1) if p[i]>=p[i-1] and p[i]>=p[i+1] and (p[i]>p[i-1] or p[i]>p[i+1])]
 candidates=[(a,b) for a in peaks for b in peaks if a<b and abs(a-expected[0])<=1 and abs(b-expected[1])<=1]
 best=None;best_score=-np.inf
 for a,b in candidates:
  weaker=min(p[a],p[b]);valley=float(p[a+1:b].min()) if b>a+1 else weaker
  depth=float(10*np.log10(weaker/valley)) if weaker>0 and valley>0 else None
  score=depth if depth is not None else np.inf if weaker>0 and valley==0 else 0.
  if best is None or score>best_score:
   best=dict(peaks=[a,b],valley_depth_db=depth,valley_exact_zero=bool(valley==0),resolved=bool(score>=3));best_score=score
 return best or dict(peaks=[],valley_depth_db=None,resolved=False)
def functional(case,stage,entry,injected,output,fixed=True,truth=()):
 result={}
 if stage==2:
  a=np.asarray(injected)/32768;b=np.asarray(output)/(32768 if fixed else 1);rows=[]
  for t in truth:
   pin=float(np.mean(np.abs(a[:,t.delay])**2));pout=float(np.mean(np.abs(b[:,t.delay])**2))
   rows.append(dict(target=t.name,velocity_m_s=t.velocity,input_power=pin,output_power=pout,gain_db=float(10*np.log10(pout/pin)) if pin and pout else None,exact_zero_output=bool(pout==0),analytic_gain_db=float(20*np.log10(abs(2*np.sin(np.pi*2*t.velocity*M.FC*M.PRI/M.C_NOMINAL)))) if t.velocity else None))
  result['mti_target_response']=rows
 if stage==1 and 'range_separation_cells' in case:
  z=np.asarray(output)/(32768 if fixed else 1);profile=np.mean(np.abs(z)**2,axis=0);expected=[t.delay for t in truth]
  result['range_resolution']=dict(separation_m=case['range_separation_cells']*RANGE_STEP,**resolve_profile(profile,expected),criterion='Two distinct local maxima, each within ±1 cell of true delay; intervening valley >=3 dB below weaker peak. Coherent equal-amplitude noise-free test, not a general resolution guarantee.')
 if stage==3 and 'velocity_separation_bins' in case:
  z=np.asarray(output)/(32768 if fixed else 1);profile=np.abs(z[:,truth[0].delay])**2;expected=[int(np.rint(t.velocity/VELOCITY_STEP))%32 for t in truth]
  result['velocity_resolution']=dict(separation_m_s=case['velocity_separation_bins']*VELOCITY_STEP,**resolve_profile(profile,expected),criterion='Two distinct spectral local maxima within ±1 bin of truth; intervening valley >=3 dB. No Doppler wrap in these tests.')
 if stage==6:result['association']=association(output,truth)
 return result
def cfar_observation(mask,records,truth):
 mask=np.asarray(mask,bool);valid=mask[3:29,3:110];detected=[]
 for t in truth:
  b=int(np.rint(t.velocity/VELOCITY_STEP))%32
  detected.append(any(mask[bb,rr] for rr in range(max(3,t.delay-2),min(110,t.delay+3)) for bb in range(3,29) if abs((bb-b+16)%32-16)<=1))
 return dict(false_alarm_cells=int(valid.sum()) if not truth else None,valid_cells=valid.size,any_false_alarm=bool(valid.any()) if not truth else None,clusters=len(records),cfar_detected_targets=sum(detected),defined_targets=len(truth),grouping_detected_targets=association(records,truth)['matched_targets'])
def interval(k,n,confidence=.95):
 if not n:return None
 a=(1-confidence)/2
 return [0. if k==0 else float(beta.ppf(a,k,n-k+1)),1. if k==n else float(beta.ppf(1-a,k+1,n-k))]
def aggregate(noise,target):
 n=len(noise);k=sum(int(v['any_false_alarm']) for v in noise);tn=len(target)
 pfa=sum(v['false_alarm_cells'] for v in noise)/(2782*n) if n else None
 eps=np.sqrt(np.log(40)/(2*n)) if n else None
 return dict(scope='Independent seeded CPIs; CFAR receives quantized software Float Power after software Float FFT. Grouping receives actual hardware CFAR output. Not end-to-end raw-IQ Pd/Pfa qualification.',noise_CPIs=n,target_CPIs=tn,cells_per_CPI=2782,cell_Pfa=pfa,cell_Pfa_95pct_CPI_Hoeffding=[max(0,pfa-eps),min(1,pfa+eps)] if n else None,cell_CI_note='Conservative independent-CPI bound; cells within a CPI are NOT treated as independent.',CPI_any_false_alarm_probability=k/n if n else None,CPI_any_false_alarm_95pct=interval(k,n),false_clusters_per_CPI=float(np.mean([v['clusters'] for v in noise])) if n else None,CFAR_Pd=sum(v['cfar_detected_targets'] for v in target)/tn if tn else None,CFAR_Pd_95pct=interval(sum(v['cfar_detected_targets'] for v in target),tn),Grouping_Pd=sum(v['grouping_detected_targets'] for v in target)/tn if tn else None,Grouping_Pd_95pct=interval(sum(v['grouping_detected_targets'] for v in target),tn),qualification='Development estimate; finite CI and defined SNR/association conditions must accompany the number.')

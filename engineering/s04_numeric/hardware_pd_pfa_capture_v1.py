"""AX309 real-board independent statistical capture (candidate, NOT S11 approval).
Sequential physical CPIs via 115200 UART. Preserves full input IQ, actual FPGA
Power map, grouping records and durable transaction journals per CPI.
Runs Pd first (N=1000), then Pfa (N=20000). An invalid CPI stops the campaign;
there is NO substitution, repeated attempt, adaptive stopping or retuning.
"""
from __future__ import annotations
import datetime, hashlib, json, os, sys, traceback, time, subprocess
from pathlib import Path
import numpy as np
from scipy.stats import beta
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
from s03_reference import model as s03
from s03_reference import pd_acceptance_candidate as pd
from pc_link.board_dsp import run_board_dsp,BITSTREAM
import s04_c05_native_integer_v1 as C05
from fixed_pd_pfa_diagnostic_v1 import empirical_bernstein

FOLDER=Path(__file__).resolve().parent
PORT='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_f4d179353796ed11aa2f634ce259fb3e-if00-port0'
BIT_SHA='fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb'
PROFILES={
 'pd':dict(N=1000,master=761113261,seed_namespace=611,input_gain=1,base_cpi_id=200000000),
 'pfa':dict(N=20000,master=761113262,seed_namespace=611,input_gain=5,base_cpi_id=300000000)
}
def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
 return h.hexdigest()
def persist(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 t=path.with_name(path.name+'.tmp')
 with t.open('w',encoding='utf8') as f:
  json.dump(data,f,indent=2,sort_keys=True,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,path)
 fd=os.open(path.parent,os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def source_for(profile,i):
 cfg=PROFILES[profile]
 seed=np.random.SeedSequence([cfg['master'],i,cfg['seed_namespace']])
 if profile=='pd':
  return s03.generate_cpi(targets=[s03.Target(40,1.875,0.18+0j,0.)],snr_db=20,seed=seed,clutter=None)
 return s03.noise_only_cpi(sigma2=1.0,seed=seed)
def quantized_iq(src,g):
 a=np.stack((src.real/g,src.imag/g),axis=-1)
 q=np.rint(a*32768).astype(np.int64)
 clips=int(np.count_nonzero((q < -32768)|(q > 32767)))
 return np.clip(q,-32768,32767).astype('<i2').tobytes(),clips
def persist_bytes(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():raise FileExistsError(path)
 with path.open('xb') as f:
  f.write(data);f.flush();os.fsync(f.fileno())
def score_power_and_records(profile,power,records):
 # FPGA Power is the source of these pre-grouping CFAR decisions, NOT direct RTL mask readback.
 mask,detail=C05.native_cfar(power.tolist())
 alarms=sum(bool(v['alarm']) for v in detail)
 out=dict(alarms=alarms,valid_cut_count=len(detail),cluster_count=len(records),
          pre_grouping_mask_origin='C05 reconstructed from actual FPGA Power')
 if profile=='pd':
  det=[dict(record_id=x['record_id'],range_bin=x['range_bin'],doppler_bin=x['doppler_bin'],
            velocity_m_s_nominal=float(s03.bin_velocity(x['doppler_bin']))) for x in records]
  pairs=s03.truth_match(det,[pd.fixed_target_truth()])
  out['D']=len(pairs)==1
  matched=next((x for x in det if pairs and x['record_id']==pairs[0][1]),None)
  out['R']=bool(matched and abs(matched['range_bin']-40)<=1)
  out['V']=False
  if matched:
   status=pd.doppler_peak_eligibility(power[matched['range_bin']],matched['doppler_bin'])
   if status['status']!='VALID':raise ValueError('Doppler eligibility undefined')
   out['V']=bool(status['eligible'] and abs(matched['velocity_m_s_nominal']-1.875)<=.234375)
  out['J']=out['D'] and out['R'] and out['V']
  out['pre_grouping_cfar_target_alarm']=any(mask[r][b] for r in range(38,43) for b in range(3,6))
 return out
def run_profile(profile):
 cfg=PROFILES[profile];N=cfg['N']
 folder=FOLDER/f'hardware_stat_campaign_20261113_{profile}_v1'
 if folder.exists():raise FileExistsError('Cannot reuse or overwrite '+str(folder))
 folder.mkdir()
 manifest=dict(project='AX309-RDSP-001',profile=profile,N=N,
  master_seed=cfg['master'],seed_namespace=cfg['seed_namespace'],
  seed_derivation='numpy.SeedSequence([master_seed,i,seed_namespace]); independent i=0..N-1',
  input_gain=cfg['input_gain'],input_binary_format='little endian int16 interleaved I,Q; 33x128; Q1.15; 16896 bytes/CPI',
  source_scenario='single k40, Doppler bin +4, SNR20, amplitude .18, no clutter' if profile=='pd' else 'CN(0,1) noise-only',
  acceptance='Pd N1000 Clopper-Pearson 95% lower >= 0.90' if profile=='pd' else 'Pfa N20000 95% CPI-level empirical Bernstein upper <=0.0015',
  measurement='hardware Power map downloaded via UART, exact C05 postprocessed CFAR; grouped records from actual FPGA RESULT',
  uart_port=PORT,uart_baud=115200,
  expected_bitstream_sha256=BIT_SHA,bitstream_sha256=digest(BITSTREAM),
  git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
  generator_sha256=digest(Path(__file__)),scorer_sha256=digest(Path(C05.__file__)),
  reference_model_sha256=digest(Path(s03.__file__)),pd_protocol_sha256=digest(Path(pd.__file__)),
  source_phase='PREDECLARED_HARDWARE_CANDIDATE_NOT_FORMAL_S11_APPROVAL',
  no_sample_replacement=True,no_optional_stop=True,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 if manifest['bitstream_sha256']!=BIT_SHA:raise RuntimeError('Wrong bitstream!')
 persist(folder/'STARTED.json',manifest)
 # Evidence storage: IQ binary per CPI; board_dsp captures full actual Power+IQ in compressed npz
 # and actual FPGA result records in a durable JSON journal.
 iqdir=folder/'iq';iqdir.mkdir()
 boarddir=folder/'board';boarddir.mkdir()
 records=[];total_alarms=0;total_D=total_R=total_V=total_J=total_pre=0;invalid=0;failure=None
 t0=time.monotonic()
 try:
  with (folder/'RAW.jsonl').open('x') as rawlog:
   for i in range(N):
    src=source_for(profile,i)
    data,clips=quantized_iq(src,cfg['input_gain'])
    assert len(data)==16896
    iqfile=iqdir/f'{i:05d}.iq'
    persist_bytes(iqfile,data)
    assert clips==0, f'Input clipping at CPI {i}: {clips}; cannot replace CPI'
    hw=run_board_dsp(data,PORT,cpi_id=cfg['base_cpi_id']+i,journal_dir=boarddir,
                     download_power=True,progress=lambda text:None)
    assert hw['terminal']=='COMMIT' and hw['released'] and hw['input_bytewise_verified']
    assert hw['bitstream_sha256']==BIT_SHA and hw['iq_sha256']==digest(iqfile)
    assert hw['power_bytes']==24576 and len(hw['power'])==128 and len(hw['power'][0])==32
    power=np.asarray(hw['power'],dtype=np.uint64)
    journal=Path(hw['journal_path']).resolve()
    npz=journal.with_suffix('.npz')
    assert journal.is_file() and npz.is_file()
    with np.load(npz) as z:
     assert np.array_equal(z['power'],power)
     assert z['iq'].astype('<i2').tobytes()==data
    derived=score_power_and_records(profile,power,hw['records'])
    # Separate exact record-equivalence oracle over actual FPGA Power.
    mask,_=C05.native_cfar(power.tolist())
    predicted=C05.native_clusters(mask,power.tolist())
    fields=('record_id','range_bin','doppler_bin','signed_doppler_bin','power_stored_integer','cluster_cells','tie_flag','max_equal_power_cells')
    if [[r[k] for k in fields] for r in predicted]!=[[r[k] for k in fields] for r in hw['records']]:
     raise RuntimeError(f'FPGA Grouping mismatch with C05 at CPI {i}; evidence retained')
    r=dict(i=i,cpi_id=cfg['base_cpi_id']+i,profile=profile,clips=clips,internal_events=0,
     source_sha256=hashlib.sha256(src.tobytes()).hexdigest(),
     iq_sha256=digest(iqfile),iq_file=str(iqfile.relative_to(folder)),
     power_sha256=hashlib.sha256(power.astype('<u8').tobytes()).hexdigest(),
     board_journal=str(journal.relative_to(folder)),board_journal_sha256=digest(journal),
     board_capture_npz=str(npz.relative_to(folder)),board_capture_sha256=digest(npz),
     terminal=hw['terminal'],released=hw['released'],power_bytes=hw['power_bytes'],
     record_count=hw['terminal_count'],elapsed_s=hw['elapsed_s'],**derived)
    rawlog.write(json.dumps(r,sort_keys=True)+'\n');rawlog.flush();os.fsync(rawlog.fileno())
    records.append(r);total_alarms+=r['alarms']
    if profile=='pd':
     total_D+=int(r['D']);total_R+=int(r['R']);total_V+=int(r['V']);total_J+=int(r['J'])
     total_pre+=int(r['pre_grouping_cfar_target_alarm'])
    if len(records)%10==0 or len(records)==N:
     ck=dict(completed=len(records),planned=N,alarms=total_alarms,successes_D=total_D,
      successes_R=total_R,successes_V=total_V,successes_J=total_J,
      pre_grouping_hits=total_pre,clips=0,internal_events=0,
      elapsed_seconds=time.monotonic()-t0)
     persist(folder/'CHECKPOINT.json',ck)
     print('HARDWARE',profile,ck['completed'],'/',N,'alarms',total_alarms,'D',total_D,flush=True)
 except BaseException:
  failure=traceback.format_exc()
  persist(folder/'FAILURE.json',dict(profile=profile,completed=len(records),
   planned=N,error=failure,policy='STOP ON FAILURE; no lost/replaced CPI'))
 result=dict(profile=profile,N=N,completed=len(records),total_alarms=total_alarms,
  error=failure,model='REAL FPGA AX309 SRAM bitstream',bitstream_sha256=BIT_SHA,
  statistical_scope='independent IQ population and physical DSP, CPU reconstructed CFAR from FPGA Power',
  total_inputs_stored=len(list(iqdir.glob('*.iq'))),raw_sha256=digest(folder/'RAW.jsonl'),
  elapsed_seconds=time.monotonic()-t0,formal_S11_acceptance='OPEN_PEND_ENGINEER_REVIEW')
 if profile=='pd':
  L=float(beta.ppf(.05,total_D,N-total_D+1)) if total_D else 0.
  result.update(successes_D=total_D,successes_R=total_R,successes_V=total_V,
                successes_J=total_J,pre_grouping_Cfar_detection_count=total_pre,lower95_CP_D=L)
  passed=L>=.9
 else:
  stat=empirical_bernstein([r['alarms'] for r in records]) if len(records)>=2 else None
  result['empirical_bernstein']=stat
  passed=bool(stat and stat['upper95']<=.0015)
 complete=not failure and len(records)==N and invalid==0
 result['hardware_candidate_statistical_result']=('PASS_CANDIDATE' if passed else 'FAIL_CANDIDATE') if complete else 'INCONCLUSIVE'
 persist(folder/'RESULT.json',result)
 print('FINAL',profile,result['hardware_candidate_statistical_result'],flush=True)
 return complete
def main():
 if not Path(PORT).exists():raise FileNotFoundError(PORT)
 if not BITSTREAM.is_file() or digest(BITSTREAM)!=BIT_SHA:raise RuntimeError('Wrong/missing FPGA image')
 for profile in ('pd','pfa'):
  if not run_profile(profile):
   print('ABORT OTHER PROFILE; first campaign incomplete',flush=True)
   return 2
 return 0
if __name__=='__main__':sys.exit(main())

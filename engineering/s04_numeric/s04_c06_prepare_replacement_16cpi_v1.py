"""Prepare and preflight the separately authorized replacement 16-CPI S04-C06 input set.
Uses the existing S03 source generators only. Does not execute C04/C06 processing.
"""
from __future__ import annotations
import hashlib, json, math, os, platform, sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from s03_reference import model as S03

PLAN=ROOT/'engineering/S04-C06-REPLACEMENT-PRELOCK-MANIFEST-v1.0.json'
OUT=ROOT/'engineering/s04_numeric/c06_replacement_16cpi_inputs_v1'
CONTRACT_PATH=ROOT/'engineering/S04-C02-SELECTED-C-EXECUTABLE-ARITHMETIC-CONTRACT-v1.0.json'
CONTRACT=json.loads(CONTRACT_PATH.read_text())
assert CONTRACT['architecture']=='C' and CONTRACT['schedule']==[0,1,0,1,1]
SHIFTS=(0,1,0,1,1)
DENOMINATORS={'IQ_complex':4224,'IQ_components':8448,'MF':4224,'MTI':4096,
 'FFT1':4096,'FFT2':4096,'FFT3':4096,'FFT4':4096,'FFT5':4096,
 'POWER':4096,'CFAR_CUT':2782,'CFAR_training_per_CUT':40}

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p):return sha_bytes(Path(p).read_bytes())
def dump_json(path,obj):
 Path(path).write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def max_signed(W):return (1<<(W-1))-1
def max_unsigned(W):return (1<<W)-1
def rne_abs_bound(A,den):return (int(A)+den//2)//den

def seed_for(master,index):
 ss=np.random.SeedSequence([int(master),int(index),191])
 return int(ss.generate_state(1,dtype=np.uint64)[0])

def make_source(profile,seed):
 if profile=='NOISE_ONLY_UNIT':
  return S03.noise_only_cpi(sigma2=1.0,seed=seed)
 if profile=='SINGLE_TARGET_REFERENCE_LIKE_LAB':
  target=S03.Target(delay=40,velocity=1.875,amplitude=0.18+0j,phase=0.0)
  assert abs(S03.noise_variance(target,20.0)-0.000324)<1e-15
  return S03.generate_cpi(targets=[target],snr_db=20.0,seed=seed,clutter=None)
 raise ValueError(profile)

def headroom_proof(raw_iq):
 """Conservative absolute interval propagation; no DSP candidate execution."""
 q=np.asarray(raw_iq,dtype=np.int64)
 imax=int(np.max(np.abs(q[:,:,0]))); qmax=int(np.max(np.abs(q[:,:,1])))
 mf=CONTRACT['MF']; taps=mf['mf16_stored_pairs']
 prod_bounds=[]; pair_i=[]; pair_q=[]
 for hr,hi in taps:
  vals=[imax*abs(hr),qmax*abs(hi),imax*abs(hi),qmax*abs(hr)]
  prod_bounds.extend(vals)
  pair_i.append(vals[0]+vals[1]);pair_q.append(vals[2]+vals[3])
 mf_prod=max(prod_bounds)
 mf_pair=max(max(pair_i),max(pair_q))
 mf_acc_i=sum(pair_i);mf_acc_q=sum(pair_q)
 mf_acc=max(mf_acc_i,mf_acc_q)
 mf_out=rne_abs_bound(mf_acc,1<<15)
 checks=[]
 def check(site,bound,width,signed=True):
  limit=max_signed(width) if signed else max_unsigned(width)
  checks.append({'site':site,'width_bits':width,'signed':signed,
                 'conservative_abs_or_unsigned_max':int(bound),
                 'positive_limit':int(limit),'fits':int(bound)<=int(limit),
                 'required_bits':(int(bound).bit_length()+1 if signed and bound else int(bound).bit_length())})
 check('IQ_INPUT',max(imax,qmax),16,True)
 check('MF_PRODUCT',mf_prod,mf['four_exact_signed_products_W'],True)
 check('MF_PAIR',mf_pair,mf['complex_pair_signed_W'],True)
 check('MF_ACC',mf_acc,mf['raw_16tap_accumulator_signed_W'],True)
 check('MF_OUTPUT',mf_out,mf['output']['W'],True)
 mti_in=int(mf_out)
 mti_bound=2*mti_in
 check('MTI_RAW_SUBTRACT',mti_bound,CONTRACT['MTI']['raw_subtract_signed_W'],True)
 check('MTI_OUTPUT',mti_bound,CONTRACT['MTI']['output']['W'],True)
 stage_input=mti_bound
 fft_bounds=[]
 for stage in CONTRACT['FFT']['stages']:
  j=stage['stage'];tw=stage['twiddle_stage_stored_pairs']
  maxcoef=max(max(abs(a),abs(b)) for a,b in tw)
  maxpair=max(abs(a)+abs(b) for a,b in tw)
  prod=stage_input*maxcoef
  pair=stage_input*maxpair
  align=stage_input*(1<<15)
  butterfly=align+pair
  shift=int(stage['shift'])
  out=rne_abs_bound(butterfly,1<<(15+shift))
  rec={'stage':j,'input_component_bound':stage_input,
       'max_twiddle_component_abs':max(abs(a) for a,b in tw),
       'max_twiddle_component_abs_any':max(max(abs(a),abs(b)) for a,b in tw),
       'max_twiddle_L1_component_sum':maxpair,
       'product_bound':prod,'pair_bound':pair,'aligned_u_bound':align,
       'butterfly_bound':butterfly,'shift':shift,'output_component_bound':out}
  fft_bounds.append(rec)
  check(f'FFT{j}_INPUT',stage_input,stage['signed_input_format']['W'],True)
  check(f'FFT{j}_PRODUCT',prod,stage['signed_real_product_W'],True)
  check(f'FFT{j}_TW_PAIR',pair,stage['signed_real_complex_pair_W'],True)
  check(f'FFT{j}_ALIGNED_U',align,stage['aligned_u_signed_W'],True)
  check(f'FFT{j}_BUTTERFLY',butterfly,stage['pre_shift_butterfly_signed_W'],True)
  check(f'FFT{j}_OUTPUT',out,stage['post_butterfly_output_format']['W'],True)
  stage_input=out
 fft5=stage_input
 power_raw=2*fft5*fft5
 check('POWER_RAW',power_raw,CONTRACT['power']['raw_I_squared_plus_Q_squared_unsigned_W'],False)
 check('POWER_U46_STORED',power_raw,CONTRACT['power']['stored_power']['W'],False)
 sum40=40*power_raw
 check('SUM40_RAW',sum40,CONTRACT['SUM40']['raw_sum_unsigned_W'],False)
 check('SUM40_U52_STORED',sum40,CONTRACT['SUM40']['stored_sum']['W'],False)
 cf=CONTRACT['CFAR'];left=40*power_raw*65536;right=490007*sum40
 check('CFAR_LEFT_PRE_POWER_NARROW',left,cf['pre_power_narrowing_full_product_conservative_W'][0],False)
 check('CFAR_RIGHT_PRE_POWER_NARROW',right,cf['pre_power_narrowing_full_product_conservative_W'][1],False)
 check('CFAR_LEFT_STORED_OPERANDS',left,cf['left_unsigned_fullproduct_conservative_W'],False)
 check('CFAR_RIGHT_STORED_OPERANDS',right,cf['right_unsigned_fullproduct_conservative_W'],False)
 return {'method':'conservative_absolute_interval_propagation_over_all_input_components_and_frozen_coefficients',
  'not_C06_processing_execution':True,'input_max_abs_I_integer':imax,'input_max_abs_Q_integer':qmax,
  'MF':{'product_bound':mf_prod,'pair_bound':mf_pair,'accumulator_bound':mf_acc,
        'output_component_bound':mf_out,'tap_count':16},
  'MTI':{'difference_component_bound':mti_bound},
  'FFT':fft_bounds,'POWER':{'raw_power_bound':power_raw},
  'SUM40':{'raw_sum_bound':sum40,'training_cells':40},
  'CFAR':{'left_product_bound':left,'right_product_bound':right,
          'strict_expression':'40*Pcut*65536 versus 490007*SUM40'},
  'all_contract_points_fit':all(x['fits'] for x in checks),
  'checks':checks}

def main():
 plan=json.loads(PLAN.read_text())
 own=Path(__file__)
 if sha_file(own)!=plan['generator_script_sha256']:
  raise RuntimeError('generator source changed after pre-lock')
 if plan['source_model_sha256_pinned_from_previous_manifest']!='2b4e28c6afaebc5d5240cfc1c80d94bbcbca325b48937ed8a8855087bef85c1b':
  raise RuntimeError('source model identity not the previously pinned S03 model')
 if OUT.exists() and any(OUT.iterdir()):
  raise FileExistsError('refuse overwrite: CPI input directory is not empty')
 OUT.mkdir(parents=True,exist_ok=True)
 records=[]
 seen_seeds=set();seen_source_hashes=set()
 for item in plan['CPI_plan']:
  profile=item['profile_id'];g=int(item['g']);seed=int(item['child_seed_u64'])
  if seed in seen_seeds:raise RuntimeError('duplicate child seed')
  seen_seeds.add(seed)
  source=np.asarray(make_source(profile,seed),dtype=np.complex128)
  if source.shape!=(33,128):raise AssertionError('source generator geometry changed')
  if not np.isfinite(source.real).all() or not np.isfinite(source.imag).all():
   finite=False
  else:finite=True
  normalized=np.stack((source.real/g,source.imag/g),axis=-1)
  envelope=bool(finite and np.all(np.abs(normalized)<=1+2**-15))
  raw_float=np.rint(normalized*32768.0)
  if not np.isfinite(raw_float).all():raise ValueError('non-finite quantizer result')
  raw_iq=raw_float.astype('<i8')
  clip_mask=(raw_iq < -32768)|(raw_iq > 32767)
  clip_count=int(np.count_nonzero(clip_mask))
  iq_fit=(clip_count==0)
  # Preserve every unbounded rounded integer. Never SAT/clip/replace a sample.
  raw_path=OUT/f"{item['cpi_id']}.iqraw_i64.npy"
  np.save(raw_path,raw_iq,allow_pickle=False)
  float_path=OUT/f"{item['cpi_id']}.float_c128.npy"
  np.save(float_path,source.astype('<c16'),allow_pickle=False)
  iq_path=None;iq_sha=None;recon_sha=None;quant_err=None
  if iq_fit:
   iqbytes=raw_iq.astype('<i2').tobytes(order='C')
   iq_path=OUT/f"{item['cpi_id']}.iq_q15_iq_le.bin"
   iq_path.write_bytes(iqbytes);iq_sha=sha_file(iq_path)
   reconstructed=(g*raw_iq.astype(np.float64)/32768.0)
   reconstructed_c=(reconstructed[:,:,0]+1j*reconstructed[:,:,1])
   recon_sha=sha_bytes(reconstructed_c.astype('<c16').tobytes(order='C'))
   delta=np.abs(reconstructed_c-source)
   quant_err={'complex_MAX':float(np.max(delta)),
              'complex_RMS':float(np.sqrt(np.mean(delta**2))),
              'component_MAX':float(np.max(np.abs(np.stack((reconstructed_c.real-source.real,reconstructed_c.imag-source.imag),axis=-1))))}
  else:
   # Keep the full int64 raw result; no signed-Q15 payload can truthfully be emitted.
   iq_sha=sha_file(raw_path)
  head=headroom_proof(raw_iq)
  reasons=[]
  if not finite:reasons.append('NONFINITE_FLOAT_INPUT')
  if not envelope:reasons.append('INPUT_ENVELOPE_EXCEEDED_OR_UNESTABLISHED')
  if clip_count:reasons.append(f'INPUT_CLIPPING_COMPONENT_COUNT_{clip_count}')
  if not head['all_contract_points_fit']:reasons.append('STATIC_HEADROOM_WIDTH_PROOF_FAILED')
  source_hash=sha_file(float_path)
  if source_hash in seen_source_hashes:reasons.append('DUPLICATE_FLOAT_SOURCE_HASH')
  seen_source_hashes.add(source_hash)
  disposition='INCONCLUSIVE' if reasons else 'INPUT_READY_ONLY_PENDING_AUTHORIZATION_AND_RUNTIME_C06'
  rec={'cpi_id':item['cpi_id'],'profile_id':profile,'g':g,'profile_index':item['profile_index'],
   'master_seed':item['master_seed'],'child_seed_u64':seed,'seed_derivation':item['seed_derivation'],
   'generator':'s03_reference.model.noise_only_cpi' if profile=='NOISE_ONLY_UNIT' else 's03_reference.model.generate_cpi',
   'generator_config':item['generator_config'],'float_shape':[33,128],
   'float_complex_sample_count':4224,'IQ_component_count':8448,
   'float_file':str(float_path.relative_to(ROOT)),'float_sha256':source_hash,
   'raw_unclipped_IQ_file':str(raw_path.relative_to(ROOT)),'raw_unclipped_IQ_sha256':sha_file(raw_path),
   'IQ_Q15_payload_file':str(iq_path.relative_to(ROOT)) if iq_path else None,
   'IQ_Q15_payload_sha256':iq_sha,'IQ_payload_bytes':16896 if iq_fit else None,
   'IQ_signed16_fit':iq_fit,'input_clip_component_count':clip_count,
   'input_clip_locations_pulse_range_component':[[int(p),int(r),int(c)] for p,r,c in np.argwhere(clip_mask)[:100]],
   'input_envelope_bound':1+2**-15,'input_envelope_pass':envelope,
   'quantization_error_original_amplitude':quant_err,
   'reconstructed_float_sha256':recon_sha,
   'static_headroom':head,'static_headroom_pass':head['all_contract_points_fit'],
   'disposition':disposition,'inconclusive_reasons':reasons}
  dump_json(OUT/f"{item['cpi_id']}.manifest.json",rec)
  records.append(rec)
  print(item['cpi_id'],disposition,'clip',clip_count,'headroom',head['all_contract_points_fit'],
        'max IQ',head['input_max_abs_I_integer'],head['input_max_abs_Q_integer'])
 if len(records)!=16:raise AssertionError('fixed total CPI count changed')
 for profile in ('NOISE_ONLY_UNIT','SINGLE_TARGET_REFERENCE_LIKE_LAB'):
  group=[x for x in records if x['profile_id']==profile]
  if len(group)!=8:raise AssertionError('fixed per-profile denominator changed')
  if len({x['cpi_id'] for x in group})!=8:raise AssertionError('duplicate CPI ID')
  if len({x['child_seed_u64'] for x in group})!=8:raise AssertionError('duplicate seed within profile')
  if len({x['float_sha256'] for x in group})!=8:raise AssertionError('duplicate CPI source')
 all_ready=sum(x['disposition']!='INCONCLUSIVE' for x in records)
 aggregate={'project':'AX309-RDSP-001','criterion':'S04-C06',
  'status':'INPUTS_PREPARED_NOT_C06_EXECUTED','plan_manifest':str(PLAN.relative_to(ROOT)),
  'prelocked':True,'architecture':'C','fft_shifts':list(SHIFTS),
  'profile_fixed_denominators':{'NOISE_ONLY_UNIT':8,'SINGLE_TARGET_REFERENCE_LIKE_LAB':8},
  'global_fixed_denominator':16,'no_replacement_or_deletion':True,
  'CPI_count_generated':len(records),'CPI_input_ready_only':all_ready,
  'CPI_inconclusive':len(records)-all_ready,'CPI_records':records,
  'campaign_stage_denominators_per_profile':{k:v*8 for k,v in DENOMINATORS.items()},
  'campaign_stage_denominators_total':{k:v*16 for k,v in DENOMINATORS.items()},
  'no_C06_processing':True,'no_acceptance_runner_invocation':True,
  'no_statistical_Pd_Pfa_claim':True,'no_RTL_synthesis_FPGA':True,
  'no_accepted_S03_seed_used':True}
 dump_json(OUT/'C06-16CPI-INPUT-MANIFEST-v1.0.json',aggregate)
 print('SUMMARY',json.dumps({'generated':len(records),'input_ready_only':all_ready,
    'inconclusive':len(records)-all_ready,'output':str(OUT.relative_to(ROOT))}))
if __name__=='__main__':main()

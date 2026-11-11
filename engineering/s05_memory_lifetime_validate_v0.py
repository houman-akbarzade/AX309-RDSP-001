#!/usr/bin/env python3
"""Symbolic, non-RTL lifetime/address proof for proposed single 4224x50 store.

No CPI is simulated. No existing RTL is changed or retested. Checks a
potential future controller's address schedule; approval and actual port-level
RTL simulation/synthesis remain open.
"""
import json,hashlib
from pathlib import Path
PULSES=33
RANGES=128
BINS=32
WORDS=PULSES*RANGES
RAW,MF,POWER='RAW_IQ','MF_OUTPUT','POWER_OUTPUT'
state=[RAW]*WORDS
reads={'raw_taps':0,'mf_samples':0,'power_cells':0}
for p in range(PULSES):
 for r in range(RANGES):
  for k in range(r,min(RANGES,r+16)):
   addr=p*RANGES+k
   assert state[addr]==RAW,(p,r,k,'raw tapped after overwrite')
   reads['raw_taps']+=1
  assert state[p*RANGES+r]==RAW
  state[p*RANGES+r]=MF
assert all(s==MF for s in state)
for r in range(RANGES):
 for p in range(PULSES):
  assert state[p*RANGES+r]==MF,(p,r,'MF overwritten before MTI/FFT')
  reads['mf_samples']+=1
 for b in range(BINS):
  addr=b*RANGES+r
  assert state[addr]==MF,(b,r,'power overwrites an unconsumed MF value')
  state[addr]=POWER
assert state[:4096]==[POWER]*4096
assert state[4096:]==[MF]*128
for r in range(3,110):
 for b in range(3,29):
  assert state[b*RANGES+r]==POWER
  reads['power_cells']+=1
  for dr in range(-3,4):
   for db in range(-3,4):
    if abs(dr)<=1 and abs(db)<=1:continue
    assert state[(b+db)*RANGES+(r+dr)]==POWER
    reads['power_cells']+=1
assert reads['power_cells']==2782*41
output={
 'project':'AX309-RDSP-001','scope':'symbolic address/lifetime proof ONLY',
 'no_CPI_processing':True,'no_RTL_mutation':True,
 'storage_words':WORDS,'storage_width_bits':50,
 'input_upload_layout':'addr=p*128+r, p=0..32, r=0..127, lower 32 bits are Q1.15 I/Q',
 'MF_overwrite_layout':'same addr=p*128+r after all raw source samples [r:min(127,r+15)] have been read for pulse p; pulse-major, range ascending',
 'range_processing':'r=0..127 ascending, read all MF[p*128+r], p=0..32, before any power write at that range',
 'power_overwrite_layout':'addr=b*128+r for b=0..31, r=0..127, Doppler-major, after all 33 MF samples for r consumed',
 'power_map_final':'addresses 0..4095 as b*128+r, final 128 words 4096..4223 are stale consumed MF',
 'CFAR_address_translation':'external shared memory address b*128+r; existing scanner power_mem uses r*32+b and must not silently be treated as shared',
 'checks':{'no_raw_read_after_MF_overwrite':True,'no_unread_MF_overwritten_by_power':True,'no_power_map_clobber':True,'all_2782_CUTs_with_40_training_cells_addressed':True},
 'symbolic_reads':reads,
 'unproven':['actual synchronous BRAM read latency and port arbitration','data-path cycle budget and FIFO depth','integrated synthesized common-ram mapping','upload/readback/rerun semantics after destructive overwrite','full RTL/clock/PAR verification'],
 'decision':'PROPOSED_ONLY_NOT_ARCHITECTURE_CHANGE'
}
path=Path('engineering/S05-MEMORY-LIFETIME-SYMBOLIC-EVIDENCE-v0.1.json')
path.write_text(json.dumps(output,indent=2)+'\n')
print('SYMBOLIC_LIFETIME_PASS',reads,'stored_words',WORDS)
print('EVIDENCE_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())

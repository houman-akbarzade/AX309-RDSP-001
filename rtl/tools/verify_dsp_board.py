"""Explicit physical-board full-chain check against independent prior IP traces."""
from pathlib import Path
import sys,json,gzip
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'engineering/s04_numeric'),str(R/'rtl/experiments/ip_evaluation_20261112')]
from analyze_float import load_trace
from pc_link.board_dsp import run_board_dsp,persist
from desktop_app.scenarios import LIBRARY,prepare,score
import s04_c05_native_integer_v1 as C
B=R/'engineering/evidence/s11/full_ip_20261112';B.mkdir(parents=True,exist_ok=True)
data=[[[None]*32 for _ in range(128)] for _ in range(11)]
t=R/'rtl/build/board-oracle-old.txt';t.parent.mkdir(parents=True,exist_ok=True);t.write_text(gzip.open(R/'engineering/evidence/s05/fft_ip_20261112/lite_bram/fft-ip-output.txt.gz','rt').read())
more=R/'rtl/build/board-oracle-more.txt';more.write_text(gzip.open(R/'engineering/evidence/s05/ip_evaluation_20261112/numeric/more-ip-output.txt.gz','rt').read());load_trace(t,data);load_trace(more,data)
port='/dev/serial/by-id/usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_f4d179353796ed11aa2f634ce259fb3e-if00-port0'
results=[]
for case in list(range(3,11))+[0]:
 if case:
  name=list(LIBRARY)[case-3];raw,targets,meta=prepare(name,noise_rms=.06 if name=='Low SNR' else .002)
 else:name='Zero input';raw=bytes(16896);targets=[];meta={}
 print('RUN',case,name,flush=True)
 got=run_board_dsp(raw,port,progress=lambda s:None,cpi_id=200+case)
 expected=C.complete_map(data[case])
 pg=np.array(got['power'],dtype=np.uint64);pe=np.array(expected['power'],dtype=np.uint64)
 keys=['record_id','range_bin','doppler_bin','signed_doppler_bin','power_stored_integer','cluster_cells','tie_flag','max_equal_power_cells']
 same_records=[tuple(r[k] for k in keys) for r in got['records']]==[tuple(r[k] for k in keys) for r in expected['clusters']]
 row=dict(case=case,scenario=name,cpi_id=got['cpi_id'],iq_verified=got['input_bytewise_verified'],commit=got['terminal'],
  released=got['released'],power_cells=pg.size,power_mismatches=int(np.count_nonzero(pg!=pe)),all_record_fields_exact=same_records,
  records=got['terminal_count'],total_s=got['elapsed_s'],transfer_s=got['transfer_s'],result_wait_s=got['result_wait_s'],
  journal=got['journal_path'],association=score(got['records'],targets) if targets else None)
 results.append(row);persist(B/'board-scenario-checks.json',dict(physical_board=True,oracle='Prior independent direct structural IP FFT trace + exact C05 downstream',results=results))
 print(row,flush=True)
 if row['power_mismatches'] or not same_records:raise RuntimeError('physical board mismatch')
print('PASS physical board: 9 consecutive CPIs without reprogramming; all 36864 Power cells and every record field exact',flush=True)

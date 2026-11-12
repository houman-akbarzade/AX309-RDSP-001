"""Physical FPGA DSP CPI transaction. Host never substitutes results for hardware."""
from __future__ import annotations
import os,json,struct,time,hashlib,secrets,subprocess
from pathlib import Path
import numpy as np
from .codec import Frame,Type,Command,Status,PacketError
from .serial_io import connect_serial_port,handshake,send_stop_and_wait
from .session import PCSession
from .arq import ReliableEndpoint
from .iq import CPI_SIZE,upload_chunks,readback_requests,parse_result
ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'rtl/build/ise_radar_ip_ax309'
BITSTREAM=BUILD/'radar_ip_ax309_top.bit'
PROGRAMMER=Path.home()/'.local/opt/ax309-programmer/usr/bin/openFPGALoader'
def program_sram():
 if not BITSTREAM.is_file():raise RuntimeError('Build the full DSP bitstream first')
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(PROGRAMMER.parents[1]/'lib/x86_64-linux-gnu')
 p=subprocess.run([str(PROGRAMMER),'-c','digilent_hs2','--freq','1000000','-m',str(BITSTREAM)],env=env,capture_output=True,text=True,timeout=40)
 log=p.stdout+p.stderr
 if p.returncode:raise RuntimeError(log)
 return dict(log=log,bitstream_sha256=hashlib.sha256(BITSTREAM.read_bytes()).hexdigest())
def persist(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp')
 with open(tmp,'w') as f:json.dump(data,f,indent=2,ensure_ascii=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)
 fd=os.open(path.parent,os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def record_dict(r):
 return dict(record_id=r.record_id,range_bin=r.range_bin,doppler_bin=r.doppler_bin,
 signed_doppler_bin=r.signed_doppler,power_stored_integer=r.peak_power,
 cluster_cells=r.cluster_cells,tie_flag=bool(r.peak_tie),max_equal_power_cells=r.equal_power_cells)
def run_board_dsp(raw,port,*,progress=lambda s:None,download_power=True,cpi_id=None,journal_dir=None):
 raw=bytes(raw)
 if len(raw)!=CPI_SIZE:raise PacketError('CPI must be exactly 16896 bytes')
 cpi_id=secrets.randbits(31) if cpi_id is None else cpi_id
 sid=secrets.token_bytes(16);pc=PCSession(sid,mode=0,max_retries=3)
 ep=ReliableEndpoint(sid,max_retries=3,timeout_s=2)
 uart=connect_serial_port(port);records=[];readback=bytearray();power=bytearray()
 expected_stage=None;terminal=None;running=False;result_frames=0;started=time.monotonic()
 jd=Path(journal_dir or ROOT/'engineering/evidence/s11/full_ip_20261112/runs')
 journal=jd/(time.strftime('%Y%m%dT%H%M%S',time.gmtime())+f'-cpi{cpi_id}.json')
 identity=dict(cpi_id=cpi_id,sid=sid.hex(),iq_sha256=hashlib.sha256(raw).hexdigest(),
 bitstream_sha256=hashlib.sha256(BITSTREAM.read_bytes()).hexdigest() if BITSTREAM.is_file() else None)
 def apply(kind,body):
  nonlocal terminal,result_frames
  if kind==Type.STAGE_DATA:
   if expected_stage is None or len(body)<10:raise PacketError('unsolicited STAGE_DATA')
   cpi,stage,off=struct.unpack_from('<IBI',body);want_stage,want_off,count=expected_stage
   chunk=body[9:]
   if (cpi,stage,off,len(chunk))!=(cpi_id,want_stage,want_off,count):raise PacketError('stage identity/coverage mismatch')
   if stage==0:
    if chunk!=raw[off:off+count] or off!=len(readback):raise PacketError('IQ byte mismatch')
    readback.extend(chunk)
   elif stage==4:
    if off!=len(power) or count%6:raise PacketError('power map alignment')
    if any(chunk[j+5]&0xc0 for j in range(0,count,6)):raise PacketError('power padding bits')
    power.extend(chunk)
  elif kind==Type.RESULT:
   if not running or terminal is not None:raise PacketError('RESULT outside RUN')
   cpi,rs=parse_result(body)
   if cpi!=cpi_id:raise PacketError('RESULT wrong CPI')
   for i,r in enumerate(rs):
    if r.record_id!=len(records)+i or r.record_id>=702 or not 3<=r.range_bin<=109 or not 3<=r.doppler_bin<=28:raise PacketError('invalid record identity/ROI')
    if r.signed_doppler!=(r.doppler_bin if r.doppler_bin<16 else r.doppler_bin-32):raise PacketError('signed Doppler mismatch')
    if not 1<=r.equal_power_cells<=r.cluster_cells<=2782 or r.peak_tie!=int(r.equal_power_cells>1):raise PacketError('invalid record counts/tie')
   records.extend(rs);result_frames+=1
  elif kind==Type.STATUS:
   if not running or len(body)!=7:raise PacketError('unexpected STATUS')
   code,cpi,count=struct.unpack('<BIH',body)
   if cpi!=cpi_id or code not in (Status.CPI_COMMIT,Status.CPI_ABORT):raise PacketError('terminal status mismatch')
   if terminal is not None and terminal!=(code,count):raise PacketError('conflicting terminal')
   if code==Status.CPI_COMMIT and (count!=len(records) or count>702):raise PacketError('incomplete COMMIT')
   terminal=(code,count)
   # Durable evidence is written BEFORE ReliableEndpoint emits terminal ACK.
   persist(journal,dict(**identity,terminal='COMMIT' if code==6 else 'ABORT',terminal_count=count,
     records=[record_dict(r) for r in records],input_bytewise_verified=True,
     released=False,physical_UART=True,elapsed_s=time.monotonic()-started))
  else:raise PacketError('unexpected FPGA frame')
 def send(kind,body):send_stop_and_wait(uart,ep,kind,body,apply,wait_s=2)
 def receive_until(pred,timeout=10):
  deadline=time.monotonic()+timeout
  while not pred():
   if time.monotonic()>deadline:raise TimeoutError('FPGA response deadline; no accepted result')
   f=uart.read_frame(.5)
   if f:
    for wire in ep.receive(f,apply).replies:uart.write(wire)
 try:
  progress('Connecting / R1 handshake');handshake(uart,pc,2)
  if pc.application_locked:raise PacketError('FPGA retained session requires recovery/reset')
  progress('Uploading 16896 IQ bytes')
  send(Type.COMMAND,struct.pack('<BI',Command.OPEN_CPI,cpi_id))
  for chunk in upload_chunks(cpi_id,raw):send(Type.IQ_UPLOAD,chunk)
  progress('Reading back IQ / byte-for-byte verification')
  for req in readback_requests(cpi_id):
   _,stage,off,count=struct.unpack('<IBIH',req);expected_stage=(stage,off,count)
   send(Type.STAGE_REQUEST,req);receive_until(lambda:len(readback)==off+count)
  expected_stage=None
  if bytes(readback)!=raw:raise PacketError('incomplete IQ verification')
  transfer_s=time.monotonic()-started
  send(Type.COMMAND,struct.pack('<BI',Command.HOST_VERIFIED_INPUT,cpi_id))
  running=True;begin=time.monotonic();progress('FPGA MF / MTI / FFT IP / Power / CFAR / Grouping')
  send(Type.COMMAND,struct.pack('<BI',Command.RUN_CPI,cpi_id))
  receive_until(lambda:terminal is not None,timeout=30)
  result_wait_s=time.monotonic()-begin
  if terminal[0]!=Status.CPI_COMMIT:raise RuntimeError(f'FPGA CPI_ABORT; provisional records discarded; journal={journal}')
  if download_power:
   progress('Downloading actual FPGA Power map (24576 bytes)')
   for off in range(0,24576,480):
    count=min(480,24576-off);expected_stage=(4,off,count)
    send(Type.STAGE_REQUEST,struct.pack('<IBIH',cpi_id,4,off,count))
    receive_until(lambda:len(power)==off+count)
   expected_stage=None
  progress('Releasing completed CPI')
  send(Type.COMMAND,struct.pack('<BI',Command.RELEASE_CPI,cpi_id))
  result=dict(**identity,terminal='COMMIT',terminal_count=terminal[1],records=[record_dict(r) for r in records],
    input_bytewise_verified=True,released=True,physical_UART=True,result_frames=result_frames,
    transfer_s=transfer_s,result_wait_s=result_wait_s,elapsed_s=time.monotonic()-started,
    power_bytes=len(power),journal_path=str(journal),rx_rejected=ep.rejected,rx_duplicates=ep.duplicate)
  if power:
   arr=np.array([int.from_bytes(power[i:i+6],'little') for i in range(0,len(power),6)],dtype=np.uint64).reshape(128,32)
   result['power']=arr.tolist()
   np.savez_compressed(journal.with_suffix('.npz'),power=arr,iq=np.frombuffer(raw,dtype='<i2').reshape(33,128,2))
  persist(journal,result)
  return result
 except Exception as exc:
  persist(journal.with_suffix('.failure.json'),dict(**identity,error=str(exc),terminal=terminal,
    provisional_records=[record_dict(r) for r in records],physical_UART=True,released=False))
  raise
 finally:uart.io.close()

"""Stage Lab request/response UART v0.2, separate from stable R1 full-chain firmware."""
import struct,secrets,time,subprocess,os,hashlib,json
from pathlib import Path
import numpy as np
from pc_link.codec import Frame,Type,active_payload,split_active,PacketError
from pc_link.serial_io import connect_serial_port
ROOT=Path(__file__).resolve().parents[1]
IMAGES={1:'mf',2:'mti',3:'fft',4:'power',5:'cfar',6:'grouping'}
PROGRAMMER=Path.home()/'.local/opt/ax309-programmer/usr/bin/openFPGALoader'
def program(image,progress=lambda s:None):
 path=ROOT/'rtl/build/stage_lab'/image/'top.bit'
 if not path.exists():raise FileNotFoundError(f'Image not built: {image}')
 progress('Programming test image '+image+' into SRAM')
 env=os.environ.copy();env['LD_LIBRARY_PATH']=str(PROGRAMMER.parents[1]/'lib/x86_64-linux-gnu')
 p=subprocess.run([str(PROGRAMMER),'-c','digilent_hs2','--freq','1000000','-m',str(path)],env=env,capture_output=True,text=True,timeout=40)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return dict(image=image,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),program_log=p.stdout+p.stderr)
def run_stage(words,target,port,*,entry=None,do_program=True,progress=lambda s:None,drop_response_once=False):
 entry=target-1 if entry is None else entry;image='cfar_fft' if target==5 and entry==3 else IMAGES[target]
 programmed=program(image,progress) if do_program else None
 raw=np.asarray(words,dtype='<u8').tobytes()
 if len(raw)%1024 or len(raw)>33792:raise ValueError('Input must have 128-cell rows, at most 33 rows')
 sid=secrets.token_bytes(16);case=secrets.randbits(31);seq=0;uart=connect_serial_port(port);trace=[];start=time.monotonic()
 def transaction(kind,body):
  nonlocal seq
  wire=Frame(kind,seq,active_payload(sid,body)).encode()
  for attempt in range(4):
   uart.write(wire)
   deadline=time.monotonic()+2
   while time.monotonic()<deadline:
    f=uart.read_frame(.5)
    if f is None:continue
    if f.seq!=seq:continue
    try:b=split_active(f,sid)
    except PacketError:continue
    if f.type==Type.NACK:raise PacketError('Stage Lab NACK (wrong image/state/schema)')
    if f.type not in (Type.ACK,Type.STAGE_DATA):continue
    if drop_response_once and seq==2 and attempt==0:break
    trace.append(dict(sequence=seq,kind=int(kind),attempt=attempt,response_type=int(f.type),request_sha256=hashlib.sha256(wire).hexdigest(),response_sha256=hashlib.sha256(f.encode()).hexdigest()))
    seq+=1;return f.type,b
  raise TimeoutError('Stage Lab response exhausted; no accepted result')
 def status(b):
  if len(b)!=32-16:raise PacketError('Stage status size')
  ack,stage,state,flags,cpi,ni,no=struct.unpack('<IBBHIHH',b)
  if ack!=seq-1 or stage!=target or cpi!=case:raise PacketError('Wrong stage image or case')
  return dict(target=stage,state=state,flags=flags,input_words=ni,output_words=no)
 try:
  progress('Configuring isolated stage case')
  _,b=transaction(Type.COMMAND,struct.pack('<BIBH',0x40,case,entry,len(raw)//8));status(b)
  for off in range(0,len(raw),480):transaction(Type.IQ_UPLOAD,struct.pack('<II',case,off)+raw[off:off+480])
  progress('Bytewise input echo from FPGA')
  echo=bytearray()
  for off in range(0,len(raw),480):
   count=min(480,len(raw)-off);kind,b=transaction(Type.STAGE_REQUEST,struct.pack('<IBIH',case,0,off,count))
   if kind!=Type.STAGE_DATA or struct.unpack_from('<IBI',b)!=(case,0,off) or len(b)!=9+count:raise PacketError('Input echo identity/coverage')
   echo.extend(b[9:])
  if bytes(echo)!=raw:raise PacketError('FPGA input differs from transmitted source')
  transaction(Type.COMMAND,struct.pack('<BI',3,case));transaction(Type.COMMAND,struct.pack('<BI',4,case))
  progress('Executing hardware stage')
  deadline=time.monotonic()+10
  while True:
   _,b=transaction(Type.COMMAND,struct.pack('<BI',5,case));st=status(b)
   if st['state']==3:break
   if time.monotonic()>deadline:raise TimeoutError('Stage hardware timeout')
   time.sleep(.01)
  if st['flags']&0xff00:raise RuntimeError(f'Hardware protocol/overflow failure {st}')
  output=bytearray();progress('Reading actual hardware output')
  for off in range(0,st['output_words']*8,480):
   count=min(480,st['output_words']*8-off);kind,b=transaction(Type.STAGE_REQUEST,struct.pack('<IBIH',case,1,off,count))
   if kind!=Type.STAGE_DATA or struct.unpack_from('<IBI',b)!=(case,1,off) or len(b)!=9+count:raise PacketError('Output identity/coverage mismatch')
   output.extend(b[9:])
  return dict(case_id=case,target=target,entry=entry,input_echo=np.frombuffer(echo,dtype='<u8').copy(),output=np.frombuffer(output,dtype='<u8').copy(),status=st,programming=programmed,trace=trace,elapsed_s=time.monotonic()-start,input_sha256=hashlib.sha256(raw).hexdigest(),output_sha256=hashlib.sha256(output).hexdigest(),physical_UART=True)
 finally:uart.io.close()


def stable_bitstream():
 import gzip
 source=ROOT/'engineering/evidence/s10/full_ip_20261112/implementation/radar_ip_ax309_top.bit.gz'
 data=gzip.decompress(source.read_bytes())
 if hashlib.sha256(data).hexdigest()!='fa51f7d050ff52d3772777fd1b1829386ef3708ddbed43c9f7775232d57c1cfb':raise RuntimeError('Stable bitstream archive hash mismatch')
 dest=ROOT/'rtl/build/stage_lab/stable_v0.1.bit';dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists() or dest.read_bytes()!=data:dest.write_bytes(data)
 return dest

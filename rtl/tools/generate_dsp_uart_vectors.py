"""Finite end-to-end UART/RTL oracle, C05 postprocessing on independent direct-IP trace."""
from pathlib import Path
import sys,json,struct,gzip
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'engineering/s04_numeric'),str(R/'rtl/experiments/ip_evaluation_20261112')]
from pc_link.codec import *
from pc_link.iq import *
import s04_c05_native_integer_v1 as C
from analyze_float import load_trace
B=R/'rtl/build/dsp_uart_sim';B.mkdir(exist_ok=True)
data=[[[None]*32 for _ in range(128)] for _ in range(11)]
tmp=B/'old.txt';tmp.write_text(gzip.open(R/'engineering/evidence/s05/fft_ip_20261112/lite_bram/fft-ip-output.txt.gz','rt').read())
more=B/'more-trace.txt';more.write_text(gzip.open(R/'engineering/evidence/s05/ip_evaluation_20261112/numeric/more-ip-output.txt.gz','rt').read());load_trace(tmp,data);load_trace(more,data)
sid=bytes.fromhex('aabbccdd01234567899876543210abcd')
actions=[];responses=bytearray();inputs=bytearray();descs=[]
def action(wire,expected=b'',label=''):
 actions.append((len(inputs),len(wire),len(responses)+len(expected)))
 inputs.extend(wire);responses.extend(expected);descs.append(label)
def ctrl(t,seq,value):return Frame(t,seq,active_payload(sid,struct.pack('<I',value))).encode()
action(bootstrap(SessionOp.HELLO,sid),bootstrap(SessionOp.OFFER,sid),'HELLO')
action(bootstrap(SessionOp.ACTIVATE,sid),bootstrap(SessionOp.READY,sid),'ACTIVATE')
rx=tx=0
def send(t,p):
 global rx
 wire=Frame(t,rx,active_payload(sid,p)).encode()
 action(wire,ctrl(Type.ACK,rx,rx),f'{t.name} rx={rx}');rx+=1
def outbound(t,p,lost=False):
 global tx
 wire=Frame(t,tx,active_payload(sid,p)).encode()
 action(b'',wire,'FPGA '+t.name)
 if lost: action(b'',wire,'lost ACK -> exact replay')
 action(ctrl(Type.ACK,tx,tx),b'','ACK FPGA');tx+=1
for case in (3,0):
 cpi=100+case
 z=np.load(R/f'engineering/evidence/s05/ip_evaluation_20261112/numeric/{case}_arrays.npz')
 a=np.stack([np.rint(z['iq'].real*32768),np.rint(z['iq'].imag*32768)],axis=-1).astype('<i2')
 raw=a.tobytes();result=C.complete_map(data[case])
 codes=data[case];np.savez_compressed(B/f'case{case}_expected.npz',power=np.array(result['power']),fft=np.array(codes),iq=a)
 send(Type.COMMAND,struct.pack('<BI',Command.OPEN_CPI,cpi))
 # RUN before verification must NACK and must not consume inbound seq.
 action(Frame(Type.COMMAND,rx,active_payload(sid,struct.pack('<BI',Command.RUN_CPI,cpi))).encode(),ctrl(Type.NACK,rx,rx),'premature RUN rejected')
 for chunk in upload_chunks(cpi,raw):send(Type.IQ_UPLOAD,chunk)
 for i,req in enumerate(readback_requests(cpi)):
  send(Type.STAGE_REQUEST,req)
  _,_,offset,count=struct.unpack('<IBIH',req)
  outbound(Type.STAGE_DATA,struct.pack('<IBI',cpi,0,offset)+raw[offset:offset+count],lost=(case==3 and i==0))
 send(Type.COMMAND,struct.pack('<BI',Command.HOST_VERIFIED_INPUT,cpi))
 # Lost RUN ACK: exact duplicate must ACK, not start twice.
 run=Frame(Type.COMMAND,rx,active_payload(sid,struct.pack('<BI',Command.RUN_CPI,cpi))).encode()
 send(Type.COMMAND,struct.pack('<BI',Command.RUN_CPI,cpi))
 action(run,ctrl(Type.ACK,rx-1,rx-1),'duplicate RUN')
 recs=[]
 for v in result['clusters']:
  recs.append(Record(v['record_id'],v['range_bin'],v['doppler_bin'],v['signed_doppler_bin'],v['power_stored_integer'],v['cluster_cells'],int(v['tie_flag']),v['max_equal_power_cells']))
 for i,r in enumerate(recs):outbound(Type.RESULT,struct.pack('<I',cpi)+r.pack(),lost=(case==3 and i==0))
 outbound(Type.STATUS,struct.pack('<BIH',Status.CPI_COMMIT,cpi,len(recs)),lost=(case==0))
 if case==3:
  power=b''.join(int(v).to_bytes(6,'little') for row in result['power'] for v in row)
  for off in range(0,len(power),480):
   chunk=power[off:off+480];send(Type.STAGE_REQUEST,struct.pack('<IBIH',cpi,4,off,len(chunk)))
   outbound(Type.STAGE_DATA,struct.pack('<IBI',cpi,4,off)+chunk)
 send(Type.COMMAND,struct.pack('<BI',Command.RELEASE_CPI,cpi))
 print('case',case,'records',len(recs))
def hexfile(name,vals,w=2):(B/name).write_text(''.join(f'{int(v):0{w}x}\n' for v in vals))
hexfile('input.hex',inputs);hexfile('expected.hex',responses)
hexfile('actions.hex',[(off<<48)|(size<<32)|target for off,size,target in actions],20)
(B/'descriptions.json').write_text(json.dumps(descs,indent=2))
tb="""`timescale 1ns/1ps
module tb_dsp_uart;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,rxd=1;wire txd;
 wire [31:0] activations;
 uart_s05_dsp_top #(.CLOCK_HZ(1152000),.BAUD(115200),.TIMEOUT_CLKS(16000),.TX_ACK_TIMEOUT_CLKS(120000)) dut(
 .clk(clk),.rst(rst),.uart_rxd(rxd),.uart_txd(txd),.activation_count(activations));
 reg [7:0] inputs[0:INMAX],expected[0:OUTMAX];
 reg [79:0] actions[0:ACTMAX];
 integer ai,k,b,n=0,cycles=0,before_wait;reg [7:0] value;
 always @(posedge clk)cycles=cycles+1;
 initial forever begin
  @(negedge txd);repeat(15)@(posedge clk);
  for(b=0;b<8;b=b+1)begin value[b]=txd;repeat(10)@(posedge clk);end
  if(txd!==1'b1 || n>OUTMAX || value!==expected[n])begin
   $display("FAIL UART byte n=%d got=%h expected=%h action=%d corestate=%d",n,value,expected[n],ai,dut.u_core.state);$finish;
  end
  n=n+1;
 end
 task serial_byte;input [7:0] v;integer j;
 begin
  @(negedge clk);rxd=0;repeat(10)@(negedge clk);
  for(j=0;j<8;j=j+1)begin rxd=v[j];repeat(10)@(negedge clk);end
  rxd=1;repeat(10)@(negedge clk);
 end endtask
 initial begin
  $readmemh("input.hex",inputs);$readmemh("expected.hex",expected);$readmemh("actions.hex",actions);
  repeat(20)@(negedge clk);rst=0;repeat(20)@(negedge clk);
  for(ai=0;ai<=ACTMAX;ai=ai+1)begin
   for(k=0;k<actions[ai][47:32];k=k+1)serial_byte(inputs[actions[ai][79:48]+k]);
   before_wait=cycles;
   while(n<actions[ai][31:0] && cycles-before_wait<2000000)@(negedge clk);
   if(n!=actions[ai][31:0])begin $display("FAIL timeout action=%d bytes=%d target=%d core=%d session=%d error=%b sat=%b",ai,n,actions[ai][31:0],dut.u_core.state,dut.u_session.state,dut.dsp_error,dut.dsp_sat);$finish;end
   repeat(100)@(negedge clk);
  end
  if(dut.cpi_open || activations!=1 || dut.tx_retry_exhausted)begin $display("FAIL final flags");$finish;end
  $display("PASS tb_dsp_uart: two full CPIs, independent exact IP/C05 output and power map, premature RUN, duplicate RUN, lost IQ/RESULT/COMMIT ACK, RELEASE and reuse; bytes=%d",n);$finish;
 end
 initial begin #1000000000;$display("FAIL global timeout");$finish;end
endmodule
"""
tb=tb.replace('INMAX',str(len(inputs)-1)).replace('OUTMAX',str(len(responses)-1)).replace('ACTMAX',str(len(actions)-1))
(B/'tb_dsp_uart.v').write_text(tb)
sources=(R/'rtl/build/ise_radar_ip_ax309/radar_ip_ax309_top.prj').read_text().splitlines()
sources=[s for s in sources if '/ip_stub.v' not in s and '/radar_ip_ax309_top.v' not in s]
ip=R/'rtl/build/fft32_ip/fft32_ip.v'
sources += [f'verilog work {ip}',f'verilog work /opt/Xilinx/14.7/ISE_DS/ISE/verilog/src/glbl.v',f'verilog work {B}/tb_dsp_uart.v']
(B/'sim.prj').write_text('\n'.join(sources)+'\n')
print('actions',len(actions),'input',len(inputs),'output',len(responses))

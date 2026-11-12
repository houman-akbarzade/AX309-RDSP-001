"""Real serial RTL + CRC byte oracle; no board programming."""
from pathlib import Path
import struct,json,subprocess
from .models import *
from .verify import corpus,expected_words
from pc_link.codec import Frame,Type,active_payload
from rtl.stage_lab.build import prepare
def main():
 B,_=prepare('power');S=ROOT/'rtl/build/stage_lab/uart_sim';S.mkdir(parents=True,exist_ok=True)
 inp,_=corpus(4);raw=encode(inp,3).astype('<u8').tobytes()
 output=expected_words(reference(inp,3,4,True),4).astype('<u8').tobytes()
 sid=bytes.fromhex('0123456789abcdefaabbccddeeff0011');case=123456
 seq=0;inputs=bytearray();expected=bytearray();actions=[]
 def add(wire,answer=b'',wait_done=False):
  actions.append((len(inputs),len(wire),len(expected)+len(answer),int(wait_done)))
  inputs.extend(wire);expected.extend(answer)
 def frame(t,n,b):return Frame(t,n,active_payload(sid,b)).encode()
 def ack(n,state=0,nout=0,kind=Type.ACK):return frame(kind,n,struct.pack('<IBBHIHH',n,4,state,0,case,4096,nout))
 def send(t,b,state=0,nout=0,reply=None):
  nonlocal seq
  w=frame(t,seq,b);add(w,ack(seq,state,nout) if reply is None else reply);seq+=1;return w
 w=send(Type.COMMAND,struct.pack('<BIBH',0x40,case,3,4096))
 add(w,ack(0)) # lost CONFIG response / exact retry
 bad=bytearray(frame(Type.IQ_UPLOAD,seq,struct.pack('<II',case,0)+raw[:480]));bad[-1]^=1
 add(bytes(bad),b'') # invalid CRC must not advance state
 for off in range(0,len(raw),480):
  w=send(Type.IQ_UPLOAD,struct.pack('<II',case,off)+raw[off:off+480])
  if off==0:add(w,ack(seq-1)) # lost upload ACK
 # Premature RUN: no input echo/VERIFY yet.
 add(frame(Type.COMMAND,seq,struct.pack('<BI',4,case)),ack(seq,kind=Type.NACK))
 for off in range(0,len(raw),480):
  count=min(480,len(raw)-off)
  answer=frame(Type.STAGE_DATA,seq,struct.pack('<IBI',case,0,off)+raw[off:off+count])
  w=send(Type.STAGE_REQUEST,struct.pack('<IBIH',case,0,off,count),reply=answer)
  if off==0:add(w,answer) # lost echo response; exact same read again
 send(Type.COMMAND,struct.pack('<BI',3,case),state=1)
 w=send(Type.COMMAND,struct.pack('<BI',4,case),state=2,nout=4096)
 add(b'',b'',True) # wait for real compute completion, no signal forcing
 add(w,ack(seq-1,3,4096)) # duplicate RUN must not start twice
 send(Type.COMMAND,struct.pack('<BI',5,case),state=3,nout=4096)
 for off in range(0,len(output),480):
  count=min(480,len(output)-off)
  answer=frame(Type.STAGE_DATA,seq,struct.pack('<IBI',case,1,off)+output[off:off+count])
  send(Type.STAGE_REQUEST,struct.pack('<IBIH',case,1,off,count),reply=answer)
 def hexfile(name,values,width=2):(S/name).write_text(''.join(f'{int(v):0{width}x}\n' for v in values))
 hexfile('input.hex',inputs);hexfile('expected.hex',expected)
 hexfile('actions.hex',[(off<<49)|(size<<33)|(n<<1)|wait for off,size,n,wait in actions],21)
 tb="""`timescale 1ns/1ps
module tb_uart;
 reg clk=0;always #10 clk=~clk;reg rst=1,rxd=1;wire txd;
 stage_lab_top #(.TARGET(4),.FIRST(4),.CLOCK_HZ(1152000),.BAUD(115200)) dut(.clk(clk),.rst(rst),.uart_rxd(rxd),.uart_txd(txd));
 reg [7:0] inputs[0:IMAX],expected[0:OMAX];reg [80:0] actions[0:AMAX];
 integer n=0,ai,k,b,cycles=0,mark,starts=0;reg [7:0] value;
 always @(posedge clk)begin cycles=cycles+1;if(dut.run_engine)starts=starts+1;end
 initial forever begin
  @(negedge txd);repeat(15)@(posedge clk);
  for(b=0;b<8;b=b+1)begin value[b]=txd;repeat(10)@(posedge clk);end
  if(txd!==1 || n>OMAX || value!==expected[n])begin $display("FAIL byte=%d got=%h expected=%h action=%d",n,value,expected[n],ai);$finish;end
  n=n+1;
 end
 task send_byte;input [7:0] v;integer j;
 begin @(negedge clk);rxd=0;repeat(10)@(negedge clk);
  for(j=0;j<8;j=j+1)begin rxd=v[j];repeat(10)@(negedge clk);end
  rxd=1;repeat(10)@(negedge clk);
 end endtask
 initial begin
  $readmemh("input.hex",inputs);$readmemh("expected.hex",expected);$readmemh("actions.hex",actions);
  repeat(20)@(negedge clk);rst=0;repeat(20)@(negedge clk);
  for(ai=0;ai<=AMAX;ai=ai+1)begin
   for(k=0;k<actions[ai][48:33];k=k+1)send_byte(inputs[actions[ai][80:49]+k]);
   mark=cycles;
   while(n<actions[ai][32:1] && cycles-mark<200000)@(negedge clk);
   if(n!=actions[ai][32:1])begin $display("FAIL timeout action=%d state=%d",ai,dut.state);$finish;end
   if(actions[ai][0])while(!dut.complete)@(negedge clk);
   repeat(12000)@(negedge clk);
  end
  if(starts!=1)begin $display("FAIL duplicate RUN started %d times",starts);$finish;end
  $display("PASS Stage UART: CRC corruption, duplicate CONFIG/upload/read/RUN, premature RUN NACK, complete exact echo and 4096 Power words; bytes=%d",n);$finish;
 end
 initial begin #1000000000;$display("FAIL UART global timeout");$finish;end
endmodule
"""
 for token,n in [('IMAX',len(inputs)-1),('OMAX',len(expected)-1),('AMAX',len(actions)-1)]:tb=tb.replace(token,str(n))
 (S/'tb.v').write_text(tb)
 files=[l.split(' ',2)[2] for l in (B/'top.prj').read_text().splitlines() if 'configured_top.v' not in l]
 (S/'sim.prj').write_text(''.join('verilog work '+v+'\n' for v in files)+f'verilog work {S}/tb.v\n')
 shell=f"""source /opt/Xilinx/14.7/ISE_DS/settings64.sh
cd {S}
LD_PRELOAD=/home/houman/AX309-RDSP-001/rtl/build/redirect_gcc_exec.so fuse -mt off -prj sim.prj -o tb work.tb_uart > compile.log 2>&1
test -x tb || exit 1
./tb -tclbatch {ROOT}/rtl/tb/run_all.tcl > sim.log 2>&1
grep -q '^PASS Stage UART:' sim.log
"""
 (S/'run.sh').write_text(shell);p=subprocess.run(['bash',str(S/'run.sh')])
 log=(S/'sim.log').read_text() if (S/'sim.log').exists() else (S/'compile.log').read_text();print(log[-3000:])
 if p.returncode or 'FAIL ' in log:raise RuntimeError('Stage UART simulation failed')
if __name__=='__main__':main()

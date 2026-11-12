"""Finite meaningful simulation + physical-stage checks. Never upgrades statistical acceptance."""
from pathlib import Path
import sys,json,hashlib,gzip,subprocess,re
import numpy as np
from .models import *
from .transport import run_stage
from desktop_app.reference import prepare_with_source
from pc_link.board_dsp import persist
from pc_link.iq import Record
from rtl.stage_lab.build import prepare
R=ROOT;E=R/'engineering/evidence/stage_lab_v0.2';E.mkdir(parents=True,exist_ok=True)
KEYS=['record_id','range_bin','doppler_bin','signed_doppler_bin','power_stored_integer','cluster_cells','tie_flag','max_equal_power_cells']
def expected_words(a,target):
 if target<6:
  w=encode(a,target)
  if target==5:
   valid=np.zeros((32,128),np.uint64);valid[3:29,3:110]=1
   w=w|(valid.reshape(-1)<<np.uint64(62))
  return w
 result=[]
 for r in a:
  v=int.from_bytes(Record(*[r[k] for k in KEYS]).pack(),'little');result += [v&((1<<64)-1),v>>64]
 return np.asarray(result,dtype=np.uint64)
def corpus(target,kind='scenario'):
 raw,targets,meta,src=prepare_with_source('Two aircraft')
 a,info=software_input(src,target-1)
 if target==1:a=a[:2]
 if kind=='edge' and target==4:
  q=np.zeros((32,128),complex);rng=np.random.default_rng(8762)
  q.real[:]=rng.integers(-(1<<24),(1<<24),q.shape);q.imag[:]=rng.integers(-(1<<24),(1<<24),q.shape)
  q.flat[:8]=[0,1,-1,1j,-1j,-(1<<24),complex((1<<24)-1,(1<<24)-1),complex(-(1<<24),-(1<<24))]
  a=q
 if kind=='edge' and target==5:
  a=np.zeros((32,128),np.uint64);a[3:29,3:110]=1<<30
  a[6,20]=1<<40;a[10,50]=(1<<46)-1;a[20,90]=123456789
 if kind=='edge' and target==6:
  p=np.zeros((32,128),np.uint64);mask=np.zeros((32,128),bool)
  # All 702 maximal independent components, with maximum U46 powers/ties.
  mask[3:29:2,3:110:2]=True;p[mask]=(1<<46)-1;a=(p,mask)
 return a,info
def engine_sim(target,kind='scenario'):
 a,info=corpus(target,kind);words=encode(a,target-1);oracle=expected_words(reference(a,target-1,target,True),target)
 image={1:'mf',2:'mti',3:'fft',4:'power',5:'cfar',6:'grouping'}[target]
 B,_=prepare(image);S=R/'rtl/build/stage_lab/sim'/f'{image}_{kind}';S.mkdir(parents=True,exist_ok=True)
 for name,arr in [('input',words),('expected',oracle)]:(S/(name+'.hex')).write_text(''.join(f'{int(v):016x}\n' for v in arr))
 tb="""`timescale 1ns/1ps
module tb_engine;
 reg clk=0;always #10 clk=~clk;reg rst=1,start=0;wire busy,done;
 wire [12:0] ra,wa,ow;wire [63:0] wd;wire we;wire [15:0] flags;
 reg [63:0] mem[0:4223],expected[0:OMAX];reg [63:0] q;
 integer cycles=0,k;
 stage_lab_engine #(.TARGET(TARGET),.FIRST(TARGET)) dut(.clk(clk),.rst(rst),.start(start),
 .input_stage(ENTRY),.input_words(NWORDS),.read_addr(ra),.read_data(q),.write_en(we),.write_addr(wa),.write_data(wd),
 .busy(busy),.done(done),.output_words(ow),.flags(flags));
 always @(posedge clk)begin q<=mem[ra];if(we)mem[wa]<=wd;cycles<=cycles+1;end
 initial begin
  $readmemh("input.hex",mem,0,IMAX);$readmemh("expected.hex",expected);
  repeat(20)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;
  while(!done && cycles<2000000)@(negedge clk);
  if(!done || ow!=OWORDS || flags[15:8]!=0)begin $display("FAIL timeout/flags count=%d flags=%h state=%d",ow,flags,dut.state);$finish;end
  repeat(3)@(negedge clk);
  for(k=0;k<OWORDS;k=k+1)if(mem[k]!==expected[k])begin $display("FAIL output word=%d got=%h expected=%h",k,mem[k],expected[k]);$finish;end
  $display("PASS stage engine target=%d words=%d flags=%h cycles=%d",TARGET,ow,flags,cycles);$finish;
 end
endmodule
"""
 for key,val in [('TARGET',target),('ENTRY',f"3'd{target-1}"),('NWORDS',f"13'd{len(words)}"),('IMAX',len(words)-1),('OMAX',max(0,len(oracle)-1)),('OWORDS',len(oracle))]:tb=re.sub(r'(?<![.A-Za-z_])'+key+r'\b',str(val),tb)
 (S/'tb.v').write_text(tb)
 files=[l.split(' ',2)[2] for l in (B/'top.prj').read_text().splitlines() if 'configured_top.v' not in l and 'ip_stub.v' not in l]
 files += [str(R/'rtl/build/stage_lab/ip/fft32_ip.v'),str(S/'tb.v')]
 (S/'sim.prj').write_text(''.join('verilog work '+v+'\n' for v in files)+ 'verilog work /opt/Xilinx/14.7/ISE_DS/ISE/verilog/src/glbl.v\n')
 sh=f"""source /opt/Xilinx/14.7/ISE_DS/settings64.sh
cd {S}
LD_PRELOAD=/home/houman/AX309-RDSP-001/rtl/build/redirect_gcc_exec.so fuse -mt off -L unisims_ver -L xilinxcorelib_ver -prj sim.prj -o tb work.tb_engine work.glbl > compile.log 2>&1
test -x tb || exit 1
./tb -tclbatch {R}/rtl/tb/run_all.tcl > sim.log 2>&1
grep -q '^PASS stage engine' sim.log
"""
 (S/'run.sh').write_text(sh);p=subprocess.run(['bash',str(S/'run.sh')])
 log=(S/'sim.log').read_text() if (S/'sim.log').exists() else (S/'compile.log').read_text()[-3000:]
 print(log[-2000:],flush=True)
 if p.returncode or 'FAIL ' in log:raise RuntimeError(f'Engine simulation failed {image} {kind}')
 return dict(target=target,kind=kind,words=len(oracle),simulator='ISim',exact=True)
def board(target,kind='scenario'):
 a,info=corpus(target,kind)
 r=run_stage(encode(a,target-1),target,'/dev/ttyUSB1',progress=lambda s:print(s,flush=True),drop_response_once=(target==4))
 got=decode(r['output'],target,rows=(a.shape[0] if target==1 else a.shape[0]-1 if target==2 else 32))
 ref=reference(a,target-1,target,True);metrics=compare(got,ref,target,True)
 exact=metrics.get('exact_integer',metrics.get('exact_decisions',metrics.get('record_signatures_exact')))
 if not exact:raise RuntimeError(f'Hardware mismatch {target}: {metrics}')
 meta=dict(target=target,kind=kind,source=info,metrics=metrics,status=r['status'],elapsed_s=r['elapsed_s'],input_sha256=r['input_sha256'],output_sha256=r['output_sha256'],programming=r['programming'],trace=r['trace'])
 persist(E/f'board-{target}-{kind}.json',meta)
 np.savez_compressed(E/f'board-{target}-{kind}.npz',input=encode(a,target-1),echo=r['input_echo'],output=r['output'])
 print('BOARD_PASS',target,kind,metrics,flush=True);return meta
if __name__=='__main__':
 results=[]
 action=sys.argv[1]
 for arg in sys.argv[2:] or ['1','2','3','4','5','6']:
  parts=arg.split(':');target=int(parts[0]);kind=parts[1] if len(parts)>1 else 'scenario'
  results.append(engine_sim(target,kind) if action=='sim' else board(target,kind))
 persist(E/('simulation-results.json' if action=='sim' else 'board-results.json'),dict(results=results))

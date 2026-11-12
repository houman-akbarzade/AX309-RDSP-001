#!/usr/bin/env python3
"""Small deterministic development comparison corpus; no statistical campaign."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'engineering/s04_numeric')]
from s03_reference import model as M
from desktop_app.scenarios import LIBRARY,prepare
import s04_c04_selected_C_stage_capture_v1 as C04
B=ROOT/'rtl/build/ip_evaluation_numeric';B.mkdir(parents=True,exist_ok=True)
def signed(v,w):return v-(1<<w) if v&(1<<(w-1)) else v
def unpack(v,w):return signed(v&((1<<w)-1),w),signed((v>>w)&((1<<w)-1),w)
def packed(pair,w):return (int(pair[0])&((1<<w)-1))|((int(pair[1])&((1<<w)-1))<<w)
cases=[];new_mti=[];new_rd=[];sources={}
old_targets=[[],[M.Target(40,2.8125,.18)],[M.Target(35,2.8125,.18),M.Target(80,-3.75,.12)]]
for case in range(3):
 words=[int(v,16) for v in (ROOT/f'rtl/tb/vectors/radar_cpi/{case}_iq.hex').read_text().splitlines()]
 a=np.array([unpack(v,16) for v in words],dtype=np.int16).reshape(33,128,2)
 mti=np.array([unpack(int(v,16),23) for v in (ROOT/f'rtl/tb/vectors/radar_cpi/{case}_mti.hex').read_text().splitlines()],dtype=np.int64).reshape(32,128,2)
 rd=np.array([unpack(int(v,16),25) for v in (ROOT/f'rtl/tb/vectors/radar_cpi/{case}_rd.hex').read_text().splitlines()],dtype=np.int64).reshape(128,32,2)
 targets=[dict(id=i,delay=t.delay,velocity=t.velocity,amplitude=float(abs(t.amplitude))) for i,t in enumerate(old_targets[case])]
 source=M.generate_cpi(old_targets[case])
 assert M.quantize_iq(source)[0]==a.astype('<i2').tobytes()
 sources[f'existing_{case}']=source
 cases.append((f'existing_{case}',a,mti,rd,targets,dict(source='existing immutable vectors',noise_rms=0.)))
for i,name in enumerate(LIBRARY):
 noise=.06 if name=='Low SNR' else .002
 capture={};original_quantize=M.quantize_iq
 def copy_then_quantize(x):
  capture['source']=np.array(x,copy=True)
  return original_quantize(x)
 M.quantize_iq=copy_then_quantize
 try:raw,targets,meta=prepare(name,noise_rms=noise)
 finally:M.quantize_iq=original_quantize
 sources[name]=capture['source']
 a=np.frombuffer(raw,dtype='<i2').reshape(33,128,2).copy()
 iq=[[tuple(map(int,v)) for v in row] for row in a]
 src=a[:,:,0]/32768+1j*a[:,:,1]/32768
 out=C04.run_one(src,iq,C04.Telemetry(),'C_hypothetical',(0,1,0,1,1),1,capture_stages=True)
 assert out['overflow']['total']==0, (name,out['overflow'])
 mti=np.array(out['captured']['mti'],dtype=np.int64)
 rd=np.array(out['captured']['rd'],dtype=np.int64)
 truth=[dict(id=j,delay=t.delay,velocity=t.velocity,amplitude=t.amplitude) for j,t in enumerate(targets)]
 cases.append((name,a,mti,rd,truth,meta))
 new_mti.extend(packed(v,23) for row in mti for v in row)
 new_rd.extend(packed(v,25) for row in rd for v in row)
manifest=[]
for case,(name,a,mt,old,truth,meta) in enumerate(cases):
 iq=a[:,:,0]/32768+1j*a[:,:,1]/32768
 float_full=M.doppler(M.mti(M.pulse_compress(iq)))/8
 float_source=M.doppler(M.mti(M.pulse_compress(sources[name])))/8
 mt_complex=(mt[:,:,0]+1j*mt[:,:,1])/32768
 float_isolated=M.doppler(mt_complex)/8
 np.savez_compressed(B/f'{case}_arrays.npz',iq=iq,fixed_mti=mt,fixed_fft=old,source_iq=sources[name],float_source=float_source,float_full=float_full,float_isolated=float_isolated)
 manifest.append(dict(case=case,name=name,truth=truth,metadata=meta,
  array_sha256=hashlib.sha256((B/f'{case}_arrays.npz').read_bytes()).hexdigest()))
(B/'all_new_mti.hex').write_text(''.join(f'{v:012x}\n' for v in new_mti))
(B/'all_new_fixed_fft.hex').write_text(''.join(f'{v:013x}\n' for v in new_rd))
(B/'cases.json').write_text(json.dumps(manifest,indent=2,default=str)+'\n')
# All eight new cases are tested with the same generated structural IP.
tb=ROOT/'rtl/experiments/ip_evaluation_20261112/tb_more_ip.v'
tb.write_text("""`timescale 1ns/1ps
module tb_more_ip;
 reg clk=0;always #10 clk=~clk;
 reg rst=1,start=0;wire dv,ovflo;wire [4:0] xi,ki;wire [24:0] yr,yi;
 reg [45:0] all_samples[0:32767];
 integer scenario,range_index=0,cycles=0,seen=0,fd,start_cycle;
 wire [45:0] sample=all_samples[(scenario-3)*4096+xi*128+range_index];
 fft32_ip dut(.clk(clk),.ce(1'b1),.sclr(rst),.start(start),.unload(1'b1),
 .fwd_inv(1'b1),.fwd_inv_we(1'b1),.scale_sch(10'h144),.scale_sch_we(1'b1),
 .xn_re({{2{sample[22]}},sample[22:0]}),.xn_im({{2{sample[45]}},sample[45:23]}),
 .rfd(),.xn_index(xi),.busy(),.edone(),.done(),.dv(dv),.ovflo(ovflo),
 .xk_index(ki),.xk_re(yr),.xk_im(yi));
 always @(posedge clk)begin
  cycles=cycles+1;
  if(!rst && dv)begin
   if((^yr===1'bx)||(^yi===1'bx)||ovflo||ki!==seen)begin $display("FAIL IP sequence/data/overflow");$finish;end
   $fdisplay(fd,"%0d %0d %0d %h",scenario,range_index,ki,{yi,yr});seen=seen+1;
  end
 end
 initial begin
  $readmemh("NEW_INPUT_PATH",all_samples);
  fd=$fopen("more-ip-output.txt","w");
  for(scenario=3;scenario<11;scenario=scenario+1)begin
   for(range_index=0;range_index<128;range_index=range_index+1)begin
    rst=1;start=0;repeat(10)@(negedge clk);rst=0;
    repeat(4)@(negedge clk);seen=0;start_cycle=cycles;start=1;
    @(negedge clk);start=0;
    while(seen<32 && cycles-start_cycle<3000)@(negedge clk);
    if(seen!=32)begin $display("FAIL IP timeout");$finish;end
    repeat(5)@(negedge clk);
   end
   $display("EXECUTED development scenario=%d",scenario);
  end
  $fclose(fd);$display("PASS tb_more_ip: 32768 ordered complex outputs, no observed overflow");$finish;
 end
 initial begin #100000000;$display("FAIL global timeout");$finish;end
endmodule
""".replace('NEW_INPUT_PATH',str(B/'all_new_mti.hex')))
print('Prepared',len(cases),'cases; new IP frames',8*128)

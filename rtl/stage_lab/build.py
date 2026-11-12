"""Build isolated stage images; stable source arithmetic and firmware are untouched."""
from pathlib import Path
import subprocess,sys,shutil,json,hashlib,os
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
CONFIGS={'mf':(1,1),'mti':(2,2),'fft':(3,3),'power':(4,4),'cfar':(5,5),'cfar_fft':(5,4),'grouping':(6,6)}
def prepare(name):
 target,first=CONFIGS[name];B=R/'rtl/build/stage_lab'/name;B.mkdir(parents=True,exist_ok=True)
 ipdir=R/'rtl/build/stage_lab/ip';ipdir.mkdir(exist_ok=True)
 stable=Path('/home/houman/AX309-RDSP-001/rtl/build/fft32_ip')
 for ext in ['ngc','v']:
  if (stable/f'fft32_ip.{ext}').exists():shutil.copyfile(stable/f'fft32_ip.{ext}',ipdir/f'fft32_ip.{ext}')
 if not (ipdir/'fft32_ip.ngc').exists() or not (ipdir/'fft32_ip.v').exists():
  shutil.copyfile(R/'rtl/experiments/fft_ip_20261112/configs/lite_bram.xco',ipdir/'fft32_ip.xco')
  (ipdir/'coregen.cgp').write_text(''.join(line+chr(10) for line in (ipdir/'fft32_ip.xco').read_text().splitlines() if line.startswith('SET ')))
  subprocess.run(['bash','-c','source /opt/Xilinx/14.7/ISE_DS/settings64.sh; cd '+str(ipdir)+'; coregen -b fft32_ip.xco -p coregen.cgp > coregen.log 2>&1'],check=True)
 sources=['uart/uart_rx_8n1','uart/uart_tx_8n1','uart/s02_frame_echo','common/rne_sat_signed','mf16/mf16_coeff_rom','mf16/mf16_serial_mac','mti/mti2_diff','fft32_ip/fft32_ip_adapter','fft32_ip/ip_stub','power_cfar/power_q25_u46_serial','power_cfar/cfar_compare','grouping/grouping_8conn']
 files=[R/f'rtl/{s}.v' for s in sources]+[D/f'{s}.v' for s in ['stage_lab_cfar_external','stage_lab_engine','stage_lab_top']]
 (B/'configured_top.v').write_text(f'module stage_lab_ax309_top(input clk50,reset_n,uart_rxd,output uart_txd);\n wire clk_g;BUFG u_global_clock(.I(clk50),.O(clk_g));\n reg [2:0] reset_pipe=3\'b111;always @(posedge clk_g or negedge reset_n)if(!reset_n)reset_pipe<=3\'b111;else reset_pipe<=\u007breset_pipe[1:0],1\'b0\u007d;\n stage_lab_top #(.TARGET({target}),.FIRST({first})) u(.clk(clk_g),.rst(reset_pipe[2]),.uart_rxd(uart_rxd),.uart_txd(uart_txd));\nendmodule\n')
 files.append(B/'configured_top.v')
 (B/'top.prj').write_text(''.join(f'verilog work {s}\n' for s in files))
 (B/'top.xst').write_text(f'run\n-ifn {B}/top.prj\n-ifmt mixed\n-ofn {B}/top.ngc\n-p xc6slx9-2-ftg256\n-top stage_lab_ax309_top\n-opt_mode Area\n-opt_level 2\n-keep_hierarchy No\n-rtlview No\n')
 commands=[['xst','-ifn','top.xst','-ofn','top.srp'],['ngdbuild','-sd',str(ipdir),'-dd','_ngo','-nt','timestamp','-uc',str(R/'rtl/uart/AX309_UART_S05.ucf'),'top.ngc','top.ngd'],['map','-p','xc6slx9-2-ftg256','-w','-o','top_map.ncd','top.ngd','top.pcf'],['par','-w','-ol','high','top_map.ncd','top.ncd','top.pcf'],['trce','-v','10','-s','2','-n','10','top.ncd','-o','top.twr','top.pcf'],['bitgen','-w','top.ncd','top.bit']]
 shell='source /opt/Xilinx/14.7/ISE_DS/settings64.sh\ncd '+str(B)+'\nset -e\n'
 import shlex
 for cmd in commands:shell+=' '.join(shlex.quote(v) for v in cmd)+' > '+cmd[0]+'.log 2>&1\n'
 shell+='grep -q "Timing errors: 0" top.twr\n'
 (B/'build.sh').write_text(shell)
 return B,files
def build(name):
 B,_=prepare(name);print('BUILD',name,flush=True)
 p=subprocess.run(['bash',str(B/'build.sh')])
 if p.returncode:
  print('BUILD_FAIL',name,flush=True)
  for tool in ['bitgen','trce','par','map','ngdbuild','xst']:
   log=B/(tool+'.log')
   if log.exists():print(log.read_text()[-2500:]);break
  return False
 print('BUILD_PASS',name,hashlib.sha256((B/'top.bit').read_bytes()).hexdigest(),flush=True)
 print('\n'.join(l for l in (B/'top_map.mrp').read_text().splitlines() if any(s in l for s in ['Number of Slice LUTs:','Number of Slice Registers:','Number of RAMB','Number of DSP'])),flush=True)
 return True
if __name__=='__main__':
 names=sys.argv[1:] or list(CONFIGS)
 if not all(build(name) for name in names):sys.exit(1)

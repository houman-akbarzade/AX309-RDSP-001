#!/usr/bin/env python3
"""Optional, independent VHDL unit regressions (not S08-S11 qualification).

Run: python3 verify_ghdl.py [--ghdl /path/to/ghdl].
Requires GHDL 5.x (or a compatible GHDL). No Xilinx vendor IP simulation.
"""
import argparse, os, pathlib, subprocess, shutil, sys, json
ROOT=pathlib.Path(__file__).resolve().parent
cases={
 'rne':(['src/common/rne_sat_signed.vhd','tb/tb_rne_vhdl.vhd'],
        'tb_rne_vhdl','PASS RNE VHDL','100ns'),
 'mti':(['src/mti/mti2_diff.vhd','tb/tb_mti_vhdl.vhd'],
        'tb_mti_vhdl','PASS MTI VHDL','100ns'),
 'cfar_compare':(['src/power_cfar/cfar_compare.vhd','tb/tb_cfar_compare_vhdl.vhd'],
        'tb_cfar_compare_vhdl','PASS CFAR comparator VHDL','100ns'),
 'grouping':(['src/grouping/grouping_8conn.vhd','tb/tb_grouping_vhdl.vhd'],
        'tb_grouping_vhdl','PASS GROUPING VHDL','10ms')
}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--ghdl',default=os.environ.get('GHDL',shutil.which('ghdl') or shutil.which('ghdl-mcode')))
 a=ap.parse_args()
 if not a.ghdl:
  print('GHDL missing: install ghdl or use --ghdl /path/to/ghdl',file=sys.stderr)
  return 2
 results={}
 for name,(sources,top,marker,stop) in cases.items():
  work=ROOT/'check_ghdl'/name;work.mkdir(parents=True,exist_ok=True)
  commands=[[a.ghdl,'-a','--std=08',*[str(ROOT/s) for s in sources]],
            [a.ghdl,'-e','--std=08',top],
            [a.ghdl,'-r','--std=08',top,'--stop-time='+stop]]
  logs=[];rc=0
  for cmd in commands:
   x=subprocess.run(cmd,cwd=work,stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,text=True,timeout=90)
   logs.append(x.stdout)
   if x.returncode!=0:
    rc=x.returncode;break
  record='\n'.join(logs)
  (work/'test.log').write_text(record,encoding='utf8')
  passed=rc==0 and marker in record
  results[name]={'pass':passed,'returncode':rc,
       'marker':marker,'ieee_metavalue_warnings':record.count('metavalue detected')}
  print(('PASS' if passed else 'FAIL'),name,'warnings',results[name]['ieee_metavalue_warnings'])
  if not passed:
   print(record[-1600:]);break
 (ROOT/'check_ghdl'/'RESULT.json').write_text(json.dumps(results,indent=2)+'\n')
 return 0 if len(results)==len(cases) and all(r['pass'] for r in results.values()) else 1
if __name__=='__main__':sys.exit(main())

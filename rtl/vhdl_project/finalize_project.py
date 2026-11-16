"""Final VHDL ISE project associations. No RTL source modifications."""
from pathlib import Path
from lxml import etree
p=Path(__file__).parent/'AX309_RadarDSP_VHDL.xise'
t=etree.parse(str(p))
N='http://www.xilinx.com/XMLSchema'
attr=lambda s:'{%s}%s'%(N,s)
files=t.xpath('//*[local-name()="file"]')
vhdl=[f for f in files if f.get(attr('type'))=='FILE_VHDL']
tb=[f for f in vhdl if f.get(attr('name'),'').startswith('tb/') or '/tb/' in f.get(attr('name'),'')]
for f in tb:
 for a in list(f):
  if a.tag.endswith('association') and a.get(attr('name'))=='Implementation':
   f.remove(a)
 assert any(a.get(attr('name'))=='BehavioralSimulation' for a in f)
for prop in t.xpath('//*[local-name()="property"]'):
 name=prop.get(attr('name'))
 if name=='Auto Implementation Top':
  prop.set(attr('value'),'false');prop.set(attr('valueState'),'non-default')
 if name=='Optimization Goal':
  prop.set(attr('value'),'Area');prop.set(attr('valueState'),'non-default')
assert len(vhdl)>=20,len(vhdl)
assert any(x.get(attr('name'))=='Implementation Top' and 'radar_ip_ax309_top' in x.get(attr('value'),'') for x in t.xpath('//*[local-name()="property"]'))
t.write(str(p),xml_declaration=True,encoding='UTF-8',pretty_print=True)
print('VHDL_PROJECT_VALID files=',len(files),'VHDL=',len(vhdl),'SIM_ONLY_TB=',len(tb))

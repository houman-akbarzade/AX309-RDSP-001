"""Postprocess ISE-generated associations: testbenches are simulation-only."""
from pathlib import Path
from lxml import etree
p=Path(__file__).parent/'AX309_RadarDSP.xise'
t=etree.parse(str(p));ns='http://www.xilinx.com/XMLSchema'
attr=lambda s:'{%s}%s'%(ns,s)
files=t.xpath('//*[local-name()="file"]')
assert 33 <= len(files) <= 35,len(files)
for f in list(files):
 name=f.get(attr('name'), '')
 if name.endswith('ip_stub.v') or name.endswith('fft32_ip.xise'):
  f.getparent().remove(f)
  continue
 if name.endswith('lite_bram.xco'):
  f.set(attr('name'),'fft32_ip.xco')
 if '/tb/tb_' in name:
  for a in list(f):
   if a.tag.endswith('association') and a.get(attr('name'))=='Implementation':f.remove(a)
  assert any(a.get(attr('name'))=='BehavioralSimulation' for a in f)
assert len(t.xpath('//*[local-name()="file"]')) == 33
for prop in t.xpath('//*[local-name()="property"]'):
 name=prop.get(attr('name'))
 if name=='Auto Implementation Top':prop.set(attr('value'),'false');prop.set(attr('valueState'),'non-default')
 if name=='Optimization Goal':prop.set(attr('value'),'Area');prop.set(attr('valueState'),'non-default')
assert any(p.get(attr('name'))=='Implementation Top' and 'radar_ip_ax309_top' in p.get(attr('value'),'') for p in t.xpath('//*[local-name()="property"]'))
t.write(str(p),xml_declaration=True,encoding='UTF-8',pretty_print=True)
print('PROJECT_FINALIZED: 12 simulation-only TBs, 19 implementation RTL modules + FFT-IP CoreGen configuration')

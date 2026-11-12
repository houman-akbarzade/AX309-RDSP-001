#!/usr/bin/env python3
"""Independent constructive/partition checks for the 107x26 CUT king graph.
This verifies the arguments in the companion mathematical proof; it is not
an exhaustive search of 2^2782 masks and does not run prior radar CPI tests.
"""
import json,hashlib
from pathlib import Path
R0,R1=3,109
B0,B1=3,28
vertices={(r,b) for r in range(R0,R1+1) for b in range(B0,B1+1)}
assert len(vertices)==2782
r_tiles=[list(range(r,min(r+2,R1+1))) for r in range(R0,R1+1,2)]
b_tiles=[list(range(b,min(b+2,B1+1))) for b in range(B0,B1+1,2)]
assert (len(r_tiles),len(b_tiles))==(54,13)
blocks=[]
for rs in r_tiles:
 for bs in b_tiles:
  block={(r,b) for r in rs for b in bs}
  assert len(block) in (1,2,4)
  for r,b in block:
   for x,y in block:
    assert max(abs(x-r),abs(y-b))<=1
  blocks.append(block)
assert len(blocks)==702 and set.union(*blocks)==vertices
assert sum(map(len,blocks))==len(vertices)
# Blocks are disjoint, so no 8-independent set can have more than one
# vertex from each block. The following construction attains the bound.
construction={(r,b) for r in range(R0,R1+1,2) for b in range(B0,B1+1,2)}
assert len(construction)==702
for r,b in construction:
 for dr in (-1,0,1):
  for db in (-1,0,1):
   if dr==db==0:continue
   assert (r+dr,b+db) not in construction
assert all(len(block & construction)==1 for block in blocks)
# The software components contain only alarmed vertices in the accepted
# CUT raster, no non-CUT or Doppler-wrapped vertex participates in an edge.
result={
 'project':'AX309-RDSP-001',
 'definition':'Induced 8-neighbour (king) graph on alarmed CUT vertices only, R=3..109, unshifted Doppler=3..28, with no boundary wrapping',
 'valid_vertices':len(vertices),'r_size':107,'b_size':26,
 'upper_bound':'Partition into disjoint at-most-2x2 cliques: ceil(107/2)*ceil(26/2)=54*13=702; any distinct 8-connected components provide one mutually nonadjacent representative each',
 'blocks':len(blocks),'r_tile_count':len(r_tiles),'b_tile_count':len(b_tiles),
 'attaining_construction':'Alarms at (r,b)=(3+2i,3+2j), 0<=i<=53, 0<=j<=12; all 702 vertices mutually nonadjacent and each forms an isolated component',
 'constructed_isolated_components':len(construction),
 'maximum_components_exact':702,
 'outside_cut_participation':False,'doppler_wrap':False,
 'checked_partition_covers_domain':True,
 'checked_every_block_forms_clique':True,
 'checked_construction_independent':True,
 'note':'Mathematical proof is general over all 2^2782 alarm masks. Program verifies constructive partition/independence, not a radar qualification campaign.'
}
p=Path('engineering/S05-COMPONENT-BOUND-702-PROOF-v0.1.json')
p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PROOF PASS upper_bound=',len(blocks),'attained=',len(construction),'domain=',len(vertices),'r_tiles=',len(r_tiles),'b_tiles=',len(b_tiles))
print('EVIDENCE',p,'sha256',hashlib.sha256(p.read_bytes()).hexdigest())

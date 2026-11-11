#!/usr/bin/env python3
"""Generate deterministic RTL grouping stimuli from synthetic CFAR masks.

This NEVER invokes the upstream CPI pipeline or reruns REQ-RNG-03/C06.
Ground truth is the unchanged approved S04-C05 native integer grouping,
cross-checked against a separately implemented 8-neighbour union-find.
"""
from pathlib import Path
import hashlib
import json
import random
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"engineering"/"s04_numeric"))
import s04_c05_native_integer_v1 as oracle

V=ROOT/"rtl"/"tb"/"vectors"/"grouping"
V.mkdir(parents=True,exist_ok=True)
R=range(3,110)
B=range(3,29)
MASK=(1<<46)-1

def empty():
    return [[False for _ in range(32)] for _ in range(128)],[[0 for _ in range(32)] for _ in range(128)]

def add(a,p,r,b,power):
    assert r in R and b in B and 0<=power<=MASK
    a[r][b]=True;p[r][b]=power

def independent_components(a,p):
    # Own integer union-find, distinct from approved native BFS.
    pts={(r,b) for r in R for b in B if a[r][b]}
    root={x:x for x in pts}
    def find(x):
        while root[x]!=x:
            root[x]=root[root[x]]
            x=root[x]
        return x
    def join(a,b):
        x,y=find(a),find(b)
        if x!=y:root[max(x,y)]=min(x,y)
    for r,b in sorted(pts):
        for dr,db in ((0,-1),(-1,-1),(-1,0),(-1,1)):
            v=(r+dr,b+db)
            if v in pts:join((r,b),v)
    components={}
    for x in sorted(pts):
        components.setdefault(find(x),[]).append(x)
    got=[]
    for cells in components.values():
        mx=max(p[r][b] for r,b in cells)
        equal=[(r,b) for r,b in cells if p[r][b]==mx]
        r,b=min(equal,key=lambda x:(x[1] if x[1]<=15 else x[1]-32,x[0],x[1]))
        got.append((r,b,b if b<=15 else b-32,mx,len(cells),len(equal)))
    got.sort(key=lambda x:(x[0],x[2]))
    return got

cases=[]
cases.append(("empty",empty()))
a,p=empty()
for r,b,v in ((3,3,101),(3,28,103),(109,3,104),(109,28,102)):
    add(a,p,r,b,v)
cases.append(("corners_isolated",(a,p)))
a,p=empty()
for r,b,v in ((20,12,9),(20,13,12),(20,14,7),(30,20,40),(31,20,41),(32,20,43)):
    add(a,p,r,b,v)
cases.append(("horizontal_vertical",(a,p)))
a,p=empty()
for r,b,v in ((10,10,20),(11,11,10),(12,12,5),(20,20,13),(21,19,33),(22,18,6)):
    add(a,p,r,b,v)
cases.append(("diagonal_is_8conn",(a,p)))
a,p=empty()
for r,b,v in ((40,10,25),(40,12,40),(41,11,99),
              (50,6,4),(50,8,6),(51,7,7),(52,7,8),(51,9,2)):
    add(a,p,r,b,v)
cases.append(("late_union",(a,p)))
a,p=empty()
for r,b,v in ((15,15,500),(15,16,500),(16,16,500),
              (5,20,111),(4,20,111),(5,21,111),
              (25,3,12),(25,28,12)):
    add(a,p,r,b,v)
cases.append(("ties_signed_range",(a,p)))
a,p=empty(); rr=random.Random(20261112)
for r in R:
    for b in B:
        if rr.randrange(1000)<83:
            add(a,p,r,b,1+rr.randrange(0,1000))
cases.append(("sparse_deterministic",(a,p)))
a,p=empty()
for r in R:
    for b in B:
        add(a,p,r,b,((r*977+b*31)%701)+1)
cases.append(("dense_single_cluster",(a,p)))
a,p=empty()
for r in range(3,110,2):
    for b in range(3,29,2):
        add(a,p,r,b,100000+r*32+b)
cases.append(("capacity_702",(a,p)))
# Exact deterministic repetition of a prior nontrivial bridge/merge case.
a0,p0=cases[4][1]
cases.append(("repeat_late_union",([row[:] for row in a0],[row[:] for row in p0])))
a,p=empty()
add(a,p,10,3,5); add(a,p,10,28,9)
cases.append(("no_doppler_wrap",(a,p)))

in_lines=[]
gold_lines=[]
counts=[]
manifest=[]
for caseid,(name,(a,p)) in enumerate(cases):
    independent=independent_components(a,p)
    native=oracle.native_clusters(a,p)
    assert len(independent)==len(native),(name,len(independent),len(native))
    for index,(truth,rec) in enumerate(zip(independent,native)):
        r,b,signed,power,ncells,nties=truth
        assert (r,b,signed,power,ncells,nties)==(
            rec["range_bin"],rec["doppler_bin"],rec["signed_doppler_bin"],
            rec["power_stored_integer"],rec["cluster_cells"],rec["max_equal_power_cells"])
        assert rec["record_id"]==index and rec["tie_flag"]==(nties>1)
        packed=(r<<(5+6+46+12+1+12) |
                b<<(6+46+12+1+12) |
                (signed&63)<<(46+12+1+12) |
                power<<(12+1+12) |
                ncells<<(1+12) |
                ((nties>1)<<12) | nties)
        assert packed < (1<<89)
        gold_lines.append(f"{packed:023x}")
    counts.append(len(native))
    for r in R:
        for b in B:
            packed=((1 if a[r][b] else 0)<<46)|p[r][b]
            in_lines.append(f"{packed:012x}")
    manifest.append({
        "id":caseid,"name":name,"input_CUTs":2782,
        "alarms":sum(a[r][b] for r in R for b in B),
        "output_clusters":len(native),
        "max_cluster_cells":max([x["cluster_cells"] for x in native],default=0),
        "equal_peak_ties":sum(x["tie_flag"] for x in native)
    })

# Deliberately pad unused expected slots so ISim $readmemh is silent.
assert len(gold_lines)<=2048
total_golden=len(gold_lines)
gold_lines += ["0"*23]*(2048-len(gold_lines))
(V/"input.mem").write_text("\n".join(in_lines)+"\n")
(V/"expected.mem").write_text("\n".join(gold_lines)+"\n")
(V/"counts.mem").write_text("\n".join(f"{c:03x}" for c in counts)+"\n")
evidence={
  "project":"AX309-RDSP-001",
  "method":"Synthetic mask/power scenarios only, no archived CPI execution",
  "approved_software_reference":"engineering/s04_numeric/s04_c05_native_integer_v1.py::native_clusters",
  "reference_sha256":hashlib.sha256((ROOT/"engineering"/"s04_numeric"/"s04_c05_native_integer_v1.py").read_bytes()).hexdigest(),
  "independent_cross_check":"Separate 8-neighbor union-find implemented in this generator",
  "cases":manifest,"case_count":len(cases),
  "input_entries":len(in_lines),"output_entries":total_golden,
  "input_sha256":hashlib.sha256((V/"input.mem").read_bytes()).hexdigest(),
  "expected_sha256":hashlib.sha256((V/"expected.mem").read_bytes()).hexdigest(),
  "counts_sha256":hashlib.sha256((V/"counts.mem").read_bytes()).hexdigest(),
  "maximum_internal_label_stress":702,
  "REQ_RNG_03_retest":False,"C06_or_statistical_CPI_executed":False
}
(V/"manifest.json").write_text(json.dumps(evidence,indent=2)+"\n")
for item in manifest: print(f"CASE {item['id']:02d} {item['name']:28s} alarms={item['alarms']:4d} clusters={item['output_clusters']:3d}")
print("GOLDEN RECORDS",total_golden,"INPUTS",len(in_lines))
print("ORACLE CROSS-CHECK PASS",len(cases),"cases")

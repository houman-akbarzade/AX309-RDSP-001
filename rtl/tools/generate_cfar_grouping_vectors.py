#!/usr/bin/env python3
"""Fresh synthetic 128x32 U46.30 maps for connected CFAR/grouping tests.

Approved S04-C05 native integer CA-CFAR + clustering is used unchanged.
A separately coded direct 40-neighbour sum and union-find implementation
cross-checks both decisions and component records. No archived CPI is used.
"""
from pathlib import Path
import sys, json, hashlib

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"engineering"/"s04_numeric"))
import s04_c05_native_integer_v1 as oracle

# Independent union-find intentionally does not import the standalone grouping
# generator, because that script produces files as an import side effect.
def independent_components(a,p):
    points={(r,b) for r in range(3,110) for b in range(3,29) if a[r][b]}
    roots={v:v for v in points}
    def find(x):
        while roots[x]!=x:
            roots[x]=roots[roots[x]]
            x=roots[x]
        return x
    for r,b in sorted(points):
        for dr,db in ((0,-1),(-1,-1),(-1,0),(-1,1)):
            y=(r+dr,b+db)
            if y in points:
                x1,x2=find((r,b)),find(y)
                if x1!=x2: roots[max(x1,x2)]=min(x1,x2)
    components={}
    for v in sorted(points):components.setdefault(find(v),[]).append(v)
    result=[]
    for cells in components.values():
        maximum=max(p[r][b] for r,b in cells)
        tied=[v for v in cells if p[v[0]][v[1]]==maximum]
        r,b=min(tied,key=lambda v:(v[1] if v[1]<=15 else v[1]-32,v[0],v[1]))
        result.append((r,b,b if b<=15 else b-32,maximum,len(cells),len(tied)))
    return sorted(result,key=lambda v:(v[0],v[2]))

D=ROOT/"rtl"/"tb"/"vectors"/"cfar_grouping"
D.mkdir(parents=True,exist_ok=True)
CUT_R=range(3,110)
CUT_B=range(3,29)
MAX_POWER=(1<<46)-1

def blank(base=0):
    return [[base for b in range(32)] for r in range(128)]
def put(p,coords):
    for r,b,v in coords:
        assert r in CUT_R and b in CUT_B and 0<=v<=MAX_POWER
        p[r][b]=v

cases=[]
cases.append(("zero_map",blank()))
p=blank(1000)
put(p,[(3,3,50000000),(3,28,60000000),
       (109,3,55000000),(109,28,65000000)])
cases.append(("four_boundary_corners",p))
p=blank(1000)
put(p,[(20,10,100000000),(21,11,90000000),(22,12,80000000),
       (40,10,70000000),(40,12,70000000),(41,11,100000000),
       (51,15,120000000),(51,16,120000000),
       (65,3,140000000),(65,28,145000000)])
cases.append(("diagonal_late_merge_signed_peak_tie",p))
p=blank(65536)
# A strict equality: Pcut=490007, 40 training cells all at 65536.
put(p,[(44,10,490007)])
cases.append(("strict_equal_threshold_no_alarm",p))
cases.append(("repeat_bridge", [row[:] for row in cases[2][1]]))
assert len(cases)==5

def secondary_cfar(p):
    a=[[False]*32 for _ in range(128)]
    result=[]
    for r in CUT_R:
        for b in CUT_B:
            vals=[]
            for y in range(r-3,r+4):
                for x in range(b-3,b+4):
                    if abs(y-r)<=1 and abs(x-b)<=1:continue
                    vals.append(p[y][x])
            assert len(vals)==40
            train=sum(vals)
            hit=(40*p[r][b]*65536 > 490007*train)
            a[r][b]=hit
            result.append((int(hit),p[r][b],train))
    return a,result

maps=[]
cuts=[]
gold=[]
counts=[]
details=[]
for ix,(name,p) in enumerate(cases):
    mask,cut_records=oracle.native_cfar(p)
    independent_mask,independent_cut=secondary_cfar(p)
    assert mask==independent_mask,(name,"mask")
    assert len(cut_records)==len(independent_cut)==2782
    for k,(record,secondary) in enumerate(zip(cut_records,independent_cut)):
        assert (int(record["alarm"]),record["Pcut"],record["SUM40"])==secondary,(name,k)
        flag,power,training=secondary
        cuts.append(f"{((flag<<98)|(power<<52)|training):025x}")
    clusters=oracle.native_clusters(mask,p)
    independent=independent_components(mask,p)
    assert len(clusters)==len(independent),(name,"cluster count")
    for k,(rec,own) in enumerate(zip(clusters,independent)):
        r,b,signed,power,ncells,nties=own
        assert (r,b,signed,power,ncells,nties)==(
            rec["range_bin"],rec["doppler_bin"],rec["signed_doppler_bin"],
            rec["power_stored_integer"],rec["cluster_cells"],
            rec["max_equal_power_cells"]),(name,k)
        assert rec["record_id"]==k
        packed=(r<<82)|(b<<77)|((signed&63)<<71)|(power<<25)|(ncells<<13)|((nties>1)<<12)|nties
        assert packed.bit_length()<=89
        gold.append(f"{packed:023x}")
    counts.append(len(clusters))
    for row in p:
        for power in row:
            maps.append(f"{power:012x}")
    info={"id":ix,"name":name,"map_cells":4096,"CUTs":2782,
          "alarms":sum(int(x["alarm"]) for x in cut_records),
          "clusters":len(clusters),"peak_coordinates":
            [[x["range_bin"],x["doppler_bin"]] for x in clusters]}
    details.append(info)
    print("CASE",ix,name,"alarms",info["alarms"],"clusters",len(clusters),flush=True)

assert len(maps)==5*4096 and len(cuts)==5*2782
expected_count=len(gold)
assert expected_count<=256
gold.extend(["0"*23]*(256-expected_count))
for name,lines in (("map.mem",maps),("cut.mem",cuts),
                   ("expected.mem",gold),
                   ("counts.mem",[f"{n:03x}" for n in counts])):
    (D/name).write_text("\n".join(lines)+"\n")
def sha(path):return hashlib.sha256((D/path).read_bytes()).hexdigest()
m={"project":"AX309-RDSP-001","scope":"connected RTL synthetic map only; no archived CPI",
   "approved_C05_oracle":"engineering/s04_numeric/s04_c05_native_integer_v1.py",
   "approved_oracle_SHA256":hashlib.sha256((ROOT/"engineering"/"s04_numeric"/"s04_c05_native_integer_v1.py").read_bytes()).hexdigest(),
   "second_independent_Cfar":"own 7x7/3x3 integer window loop and exact comparator",
   "second_independent_grouping":"rtl/tools/generate_grouping_vectors.py::independent_components",
   "cases":details,"map_entries":len(maps),"CUT_records":len(cuts),
   "golden_records":expected_count,
   "map_sha256":sha("map.mem"),"cut_sha256":sha("cut.mem"),
   "expected_sha256":sha("expected.mem"),"counts_sha256":sha("counts.mem"),
   "geometry":"range 3..109 and Doppler 3..28; 2782 valid CUTs; no wrap",
   "numeric":"U46.30 stored integer power; 40*Pcut*65536 > 490007*sum40",
   "historical_CPI_retested":False}
(D/"manifest.json").write_text(json.dumps(m,indent=2)+"\n")
print("ORACLE PASS",len(cases),"maps",len(cuts),"CUT records",expected_count,"cluster records")

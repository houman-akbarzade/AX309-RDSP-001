"""Stage-isolation ablations for extra radar target clusters, not an authorized change.
Pure floating-point one-CPI deterministic diagnostic using analytic initializer alpha0.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from . import model as m
SEED=3342011
TARGET_DELAYS=[20,40,60]
TARGET_VELOCITIES=[-3.,1.5,5.]
ALPHA0=40*(.001**(-1/40)-1)

def ideal_pulse_compression(targets):
    """Artificially remove range sidelobes while retaining coherent slow-time phase."""
    arr=np.zeros((33,128),dtype=np.complex128)
    for tar in targets:
        fd=2*tar.velocity*m.FC/m.C_NOMINAL
        arr[:,tar.delay]+=16*tar.amplitude*np.exp(1j*(2*np.pi*fd*m.PRI*np.arange(33)+tar.phase))
    return arr

def metric(pc):
    d=m.doppler(m.mti(pc))
    power=m.rd_power(d)
    alarm,valid,z=m.cfar_2d(power,alpha=ALPHA0)
    records=m.clusters_8(alarm,power)
    return {'alarm_cells':int(alarm.sum()),'clusters':len(records),
            'range_bins_with_alarms':sorted(set(int(q[0]) for q in np.argwhere(alarm))),
            'per_range_clusters':{str(k):sum(r['range_bin']==k for r in records) for k in sorted(set(r['range_bin'] for r in records))},
            'top_10_RD_powers':[{'range':int(k),'bin':int(b),'power':float(power[k,b])} for k,b in sorted((tuple(t) for t in np.argwhere(valid)),key=lambda j:-power[j])[:10]]}

def run(folder):
    scenarios={}
    def tar(vels):return [m.Target(k,v,.18) for k,v in zip(TARGET_DELAYS,vels)]
    for name,targs in [('off_grid',tar(TARGET_VELOCITIES)),
                       ('on_grid',tar([(-6)*.46875,3*.46875,11*.46875]))]:
        x=m.generate_cpi(targs)
        actual=m.pulse_compress(x)
        ideal=ideal_pulse_compression(targs)
        scenarios[name]={'actual_matched_filter':metric(actual),
                         'ideal_compression_no_range_sidelobes':metric(ideal)}
        print(name,'real',scenarios[name]['actual_matched_filter']['clusters'],
              'ideal',scenarios[name]['ideal_compression_no_range_sidelobes']['clusters'],flush=True)
    # One-target vs three target nonlinearity and merging
    for i,targ in enumerate(tar(TARGET_VELOCITIES)):
        real=m.pulse_compress(m.generate_cpi([targ]))
        scenarios[f'isolated_target_{i}']={'actual_matched_filter':metric(real)}
    out={'scope':'exploratory stage-isolation software diagnostics; no approved algorithm changed',
         'cases':scenarios,'alpha':'UNCALIBRATED analytic alpha0',
         'interpretation_limitations':['Replacing MF output with ideal range impulse breaks the physical pulse-compression contract; diagnostic only','On-bin velocities change original target velocities and are diagnostic only','Differences show contribution of range sidelobes and Doppler off-bin leakage, but no population false alarm probabilities'],
         'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    dest=Path(folder)/'S03_extra_cluster_ablation_software.json'
    dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':run(sys.argv[1])

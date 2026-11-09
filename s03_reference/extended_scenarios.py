"""Developmental edge/multi-target reference tests, NOT population Pd or Pfa.

Seeds and cases are separate from formal approved C04 qualification, alpha
calibration, and final Pfa testing; no threshold tuning.
"""
import json,hashlib,sys
from pathlib import Path
from . import model as m
import numpy as np

SEED=98340017
ALPHA0=40*(.001**(-1/40)-1)
CASES=[
 ('single_valid_start_0',[m.Target(0,1.5,.18)],20,None),
 ('single_valid_end_112',[m.Target(112,1.5,.18)],20,None),
 ('single_cut_start_3',[m.Target(3,1.5,.18)],20,None),
 ('single_cut_end_109',[m.Target(109,1.5,.18)],20,None),
 ('excluded_cut_2',[m.Target(2,1.5,.18)],20,None),
 ('excluded_cut_110',[m.Target(110,1.5,.18)],20,None),
 ('stationary_target',[m.Target(20,0,.18)],None,None),
 ('same_range_two_doppler',[m.Target(20,-3,.18),m.Target(20,5,.18)],20,None),
 ('same_speed_two_ranges',[m.Target(20,1.5,.18),m.Target(40,1.5,.18)],20,None),
 ('two_ranges_1bin',[m.Target(20,1.5,.18),m.Target(21,1.5,.18)],None,None),
 ('two_ranges_2bin',[m.Target(20,1.5,.18),m.Target(22,1.5,.18)],None,None),
 ('two_ranges_4bin',[m.Target(20,1.5,.18),m.Target(24,1.5,.18)],None,None),
 ('two_ranges_5bin',[m.Target(20,1.5,.18),m.Target(25,1.5,.18)],None,None),
 ('three_targets_quiet',[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)],None,None),
 ('three_targets_snr20',[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)],20,None),
 ('three_targets_snr10',[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)],10,None),
 ('three_targets_snr0',[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)],0,None),
 ('three_targets_snr20_clutter_plus10',[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)],20,10),
 ('three_targets_snr20_clutter_minus10',[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)],20,-10),
]
def trial(outdir):
    rec=[]
    for i,(label,targets,snr,scr) in enumerate(CASES):
        seed=SEED+i*11119
        cl=None
        if scr is not None:
            amp=abs(targets[0].amplitude)/np.sqrt(10**(scr/10))
            cl=np.full(128,amp+0j)
        x=m.generate_cpi(targets,snr_db=snr,seed=seed,clutter=cl)
        x_repeated=m.generate_cpi(targets,snr_db=snr,seed=seed,clutter=cl)
        assert np.array_equal(x,x_repeated)
        z=m.pipeline(x,alpha=ALPHA0)
        counts=int(np.count_nonzero(z['cfar']))
        extra=int(len(z['targets'])-len(targets))
        truth=[{'id':j,'range_m_nominal':t.delay*150,'velocity_m_s':t.velocity} for j,t in enumerate(targets)]
        score=m.separation_metrics(z['targets'],truth)
        blob,clip=m.quantize_iq(x)
        rec.append({'scenario':label,'seed':seed,'input_sha256':hashlib.sha256(x.astype('<c16').tobytes()).hexdigest(),
                    'replay_exact':True,'truth_target_count':len(targets),'matched_truth_count':score['matched'],
                    'unmatched_detections':score['false'],'missed_truth_count':score['missed'],
                    'raw_cfar_detected_cells':counts,'cluster_count':len(z['targets']),
                    'quantization_saturated_components':clip,'nominal_20db_snr':snr,
                    'SCR_db':scr,'cfar_alpha_uncalibrated':ALPHA0,
                    'truth_match_pairs':score['pairs'],
                    'note':'Single deterministic trial only; not statistical probability estimate'})
    dest=Path(outdir);dest.mkdir(exist_ok=True,parents=True)
    obj={'category':'S03 developmental boundary/multitarget suite','status':'NOT_MAIN_PFA_NOT_Pd_QUALIFICATION',
         'seed_master':SEED,'cases_count':len(rec),'cases':rec,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'excess_detection_note':'Sidelobes, leakage, local CA-CFAR tests, 8-neighbor clustering and threshold alpha0 all can influence extra detections; no causal claim without ablations',
         'alpha_not_calibrated':True}
    (dest/'S03_extended_boundary_multitarget_cases.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
    for r in rec:
        print(r['scenario'],'target',r['truth_target_count'],'matched',r['matched_truth_count'],
              'extra',r['unmatched_detections'],'clusters',r['cluster_count'],flush=True)
    return obj
if __name__=='__main__':trial(sys.argv[1])

"""Reproducible S03 reference smoke scenarios; not a Pd/Pfa acceptance study."""
import json,sys,hashlib,platform
from pathlib import Path
import numpy as np
from . import model as m

MASTER_SEED=20261109
TRUTH=[{'id':i,'range_m_nominal':k*150.0,'velocity_m_s':v}
       for i,(k,v) in enumerate([(20,-3.0),(40,1.5),(60,5.0)])]
TARGS=[m.Target(20,-3.0),m.Target(40,1.5),m.Target(60,5.0)]

def execute(outdir):
    folder=Path(outdir);folder.mkdir(parents=True,exist_ok=True)
    cases=[('clean',None,None),('snr_0',0,None),('snr_10',10,None),
           ('snr_20',20,None),('scr_plus10_snr20',20,10),
           ('scr_minus10_snr20',20,-10)]
    records=[]
    for idx,(name,snr,scr) in enumerate(cases):
        clutter=None
        if scr is not None:
            # uniform stationary clutter, constant over range for all pulses.
            # Derived per target active-cell SCR matches design value before noise.
            A=abs(TARGS[0].amplitude)/np.sqrt(10**(scr/10))
            clutter=np.full(m.N,A+0j,np.complex128)
        seed=MASTER_SEED+idx*7919
        iq=m.generate_cpi(TARGS,snr_db=snr,seed=seed,clutter=clutter)
        out=m.pipeline(iq)
        rb,clip=m.quantize_iq(iq)
        scores=m.separation_metrics(out['targets'],TRUTH)
        rec={'case':name,'snr_db_input':snr,'scr_db_input':scr,'seed':seed,
             'cpi_shape':list(iq.shape),
             'input_complex128_le_sha256':hashlib.sha256(iq.astype('<c16').tobytes()).hexdigest(),
             'input_signed_Q15_bytes_sha256':hashlib.sha256(rb).hexdigest(),
             'input_quantized_clipped_components':clip,
             'cfar_design_initializer_alpha':float(40*(.001**(-1/40)-1)),
             'candidate_detection_cells':int(out['cfar'].sum()),
             'clusters':len(out['targets']),
             'truth_match':scores,
             'first_12_target_records':out['targets'][:12]}
        records.append(rec)
        print(name,'alarm_cells',rec['candidate_detection_cells'],'clusters',rec['clusters'],
              'matched',scores['matched'],'clipped',clip,flush=True)
    report={'stage':'S03','status':'EXPLORATORY_FLOAT_REFERENCE_ONLY',
            'note':'6 deterministic CPI only; not statistically valid Pd/Pfa; fixed alpha is analytic initializer, not calibrated; no FPGA execution',
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'model_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
            'python':platform.python_version(),'numpy':np.__version__,
            'source_truth':TRUTH,'cases':records}
    (folder/'S03_six_case_reference_smoke.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report

if __name__=='__main__':
    execute(sys.argv[1])

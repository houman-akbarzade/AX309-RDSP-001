"""Extended exploratory noise-only radar-chain diagnostics, not main Pfa acceptance.
Predeclared 1024 CPI, independent new seed namespace, uncalibrated alpha0.
"""
from pathlib import Path
import json,hashlib,sys,platform
import numpy as np
from . import model as m

N_CPI=1024
SEED=902110987
ALPHA0=40*(0.001**(-1/40)-1)

def summarize(outdir):
    dest=Path(outdir);dest.mkdir(parents=True,exist_ok=True)
    counts=np.zeros(N_CPI,dtype=np.int64)
    # 2D locally paired cells over actual valid region
    adjacent_range=np.zeros(N_CPI,dtype=np.int64)
    adjacent_doppler=np.zeros(N_CPI,dtype=np.int64)
    neighbor_diagonal=np.zeros(N_CPI,dtype=np.int64)
    occupancy=np.zeros((107,26),dtype=np.int32)
    sample_masks=[]
    for i in range(N_CPI):
        iq=m.noise_only_cpi(sigma2=1.0,seed=SEED+i*128527)
        power=m.rd_power(m.doppler(m.mti(m.pulse_compress(iq))))
        alarms,mask,estimate=m.cfar_2d(power,alpha=ALPHA0)
        core=alarms[3:110,3:29]
        counts[i]=int(core.sum())
        adjacent_range[i]=int((core[:-1,:]&core[1:,:]).sum())
        adjacent_doppler[i]=int((core[:,:-1]&core[:,1:]).sum())
        neighbor_diagonal[i]=int((core[:-1,:-1]&core[1:,1:]).sum())
        occupancy+=core
        if i in (0,1,31,128,1023):
            sample_masks.append({'cpi':i,'mask_sha256':hashlib.sha256(core.tobytes()).hexdigest()})
        if (i+1)%256==0:print('spatial',i+1,'/',N_CPI,flush=True)
    avg=float(np.mean(counts))
    var=float(np.var(counts,ddof=1))
    per_cut=avg/2782
    ideal=2782*per_cut*(1-per_cut)
    acf1=float(np.corrcoef(counts[:-1],counts[1:])[0,1])
    quantiles={str(q):float(np.quantile(counts,q)) for q in (0.,.5,.9,.95,.99,1.)}
    result={'scope':'S03 exploratory diagnostics not independent qualification or main Pfa trial',
            'status':'UNCALIBRATED_ALPHA0_NO_PASS_FAIL_VERDICT','N_CPI':N_CPI,
            'seed_master':SEED,'noise_sigma2':1.0,'alpha0':ALPHA0,
            'seeds_formula':'seed_master + i*128527 for CPI i',
            'CPI_independent':True,
            'M_valid_CUT':2782,
            'mean_alarms_per_CPI':avg,
            'variance_alarms_per_CPI':var,
            'count_variance_iid_at_observed_rate':ideal,
            'fano_variance_to_mean':var/avg if avg else None,
            'overdispersion_to_independent_cells':var/ideal if ideal else None,
            'sample_lag1_cpi_count_correlation':acf1,
            'per_CPI_counts':counts.tolist(),
            'per_CPI_count_quantiles':quantiles,
            'sum_adjacent_range_alarm_pairs':int(adjacent_range.sum()),
            'sum_adjacent_doppler_alarm_pairs':int(adjacent_doppler.sum()),
            'sum_adjacent_diagonal_alarm_pairs':int(neighbor_diagonal.sum()),
            'total_alarms':int(counts.sum()),
            'spatial_occupancy_min':int(occupancy.min()),'spatial_occupancy_max':int(occupancy.max()),
            'selected_masks':sample_masks,
            'model_sha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'numpy':np.__version__,'python':platform.python_version(),
            'caveats':['0/10/20dB target performance not inferred','No calibrated alpha; sample Pfa not a validation result','Overdispersion can be due to correlated CUTs and heterogeneous CUT rates; no causal proof','No final acceptance Pfa performed']}
    out=dest/'S03_spatial_extended_1024CPI_DIAGNOSTIC.json'
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('MEAN',avg,'VAR',var,'OVERDISP',result['overdispersion_to_independent_cells'])
    return result
if __name__=='__main__':summarize(sys.argv[1])

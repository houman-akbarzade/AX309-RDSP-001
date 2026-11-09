"""Exploratory S03 spatial diagnostics only; not alpha calibration nor Pfa acceptance."""
import sys,json,hashlib,platform
from pathlib import Path
import numpy as np
from . import model as m
MASTER_SEED=884211
N_CPI=128

def run(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    counts=[]; adjacent_pairs=[];alarms_by_bin=np.zeros((m.N,m.FFT_N),int)
    for i in range(N_CPI):
        x=m.noise_only_cpi(seed=MASTER_SEED+i*100003)
        o=m.pipeline(x)
        a=o['cfar']
        counts.append(int(a.sum()))
        alarms_by_bin+=a.astype(int)
        adjacent_pairs.append(int(np.sum(a[3:109,3:29]&a[4:110,3:29])))
    counts=np.array(counts)
    mean=float(counts.mean())
    variance=float(counts.var(ddof=1))
    # Raw variance for independent rare-Bernoulli CUTs would be M*p*(1-p)
    p_hat=mean/2782
    variance_iid=2782*p_hat*(1-p_hat)
    result={'category':'exploratory_spatial_diagnostic_not_qualification_or_main_Pfa',
            'num_CPI':N_CPI,'master_seed':MASTER_SEED,
            'alpha':'un-calibrated IID formula, NOT frozen fitted threshold',
            'qual_test_seeds_disjoint':True,
            'per_CPI_false_alarm_counts':counts.tolist(),
            'mean_alarm_count':mean,'sample_variance_alarm_count':variance,
            'iid_binomial_variance_at_observed_rate':variance_iid,
            'count_overdispersion_ratio':float(variance/variance_iid) if variance_iid>0 else None,
            'adjacent_alarmed_range_pairs_total':sum(adjacent_pairs),
            'total_alarm_cells':int(counts.sum()),
            'location':'CFAR fully processed output of synthetic Gaussian input with active static reference pipeline',
            'not_population_Pfa_result':True,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (folder/'S03_exploratory_spatial_diagnostic_128CPI.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print('N',N_CPI,'mean_alarm_count',mean,'variance',variance,'iid_equiv_variance',variance_iid,'overdispersion_ratio',result['count_overdispersion_ratio'])
    return result

if __name__=='__main__':run(sys.argv[1])

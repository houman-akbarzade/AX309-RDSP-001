"""S03 independent full NumPy radar-chain spatial + CA-CFAR numeric diagnostics.
This is NOT an alpha-calibration dataset, not CI calibration or qualification,
and NOT main Pfa acceptance. Uses only frozen analytic initializer alpha0.
"""
from pathlib import Path
import sys,hashlib,json,time
import numpy as np
from . import model as m

N_CPI=2048
SEED_SPATIAL=311091603
SEED_TARGET=311091606
ALPHA0=float(40*(.001**(-1/40)-1))
M_CUT=2782

def run(dest):
    dest=Path(dest);dest.mkdir(exist_ok=True,parents=True)
    start=time.perf_counter()
    counts=np.empty(N_CPI,dtype=int)
    neighbor_range=neighbor_doppler=0
    masks=[]
    for i in range(N_CPI):
        # Independent stream per CPI, disjoint from synthetic CI CAL/QUAL and main Pfa
        rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([SEED_SPATIAL,i,191])))
        w=(rng.standard_normal((33,128))+1j*rng.standard_normal((33,128)))/np.sqrt(2)
        pc=m.pulse_compress(w)
        rd=m.rd_power(m.doppler(m.mti(pc)))
        alarm,valid,z=m.cfar_2d(rd,alpha=ALPHA0)
        core=alarm[3:110,3:29]
        counts[i]=int(core.sum())
        neighbor_range+=int(np.sum(core[:-1,:]&core[1:,:]))
        neighbor_doppler+=int(np.sum(core[:,:-1]&core[:,1:]))
        if i in (0,1,100,2047):
            masks.append({'i':i,'valid_mask_sha256':hashlib.sha256(core.tobytes()).hexdigest()})
    mean=float(counts.mean());v=float(counts.var(ddof=1));p=mean/M_CUT
    # Simple model count variance for exchangeable independent CUT binomial at same p.
    iidvar=M_CUT*p*(1-p)
    rho_eff=(v/iidvar-1)/(M_CUT-1) if iidvar>0 else None
    acf1=float(np.corrcoef(counts[:-1],counts[1:])[0,1])
    spatial={'scope':'DIAGNOSTIC_NOMINAL_ALPHA0_NOT_VALIDATION',
             'CPI_independent':N_CPI,'CPI_seed_master':SEED_SPATIAL,
             'sample_generation':'PCG64 SeedSequence([SEED_SPATIAL,i,191]), standard normal real/imag separately',
             'alpha':'analytic IID initializer UNCALIBRATED','alpha_value':ALPHA0,
             'count_mean':mean,'count_variance':v,'observed_rate_NOT_Pfa_acceptance':p,
             'mean_count_iid_expected_variance':iidvar,
             'count_dispersion_ratio':v/iidvar,
             'beta_binomial_exchangeable_rho_equivalent_MOM_only':rho_eff,
             'acf_lag1':acf1,
             'count_quantiles':{str(a):float(np.quantile(counts,a)) for a in [0,.25,.5,.75,.9,.95,.99,1.]},
             'count_zero_rate':float(np.mean(counts==0)),
             'count_tail_ge8':float(np.mean(counts>=8)),
             'adjacent_range_alarm_pairs':neighbor_range,
             'adjacent_doppler_alarm_pairs':neighbor_doppler,
             'sample_masks_sha256':masks,'counts':counts.tolist(),
             'elapsed_seconds_monotonic':time.perf_counter()-start,
             'limitations':['Actual radar model output, but threshold not independently calibrated. NOT main Pfa test.',
                            'Exchangeable-rho moment matching does not prove any beta-binomial spatial equivalence.',
                            'Autocorrelation at one CPI lag is not proof of independence of all temporal structure.',
                            'Qualification on surrogate models does not itself certify this CA-CFAR chain.'],
             'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    sf=dest/'S03_v11_2048CPI_radar_chain_spatial_DIAGNOSTIC.json'
    sf.write_text(json.dumps(spatial,indent=2,sort_keys=True)+'\n')
    print('SPATIAL_DIAGNOSTIC',N_CPI,'mean',mean,'var',v,'ratio',v/iidvar,'rho_mom',rho_eff,'runtime',spatial['elapsed_seconds_monotonic'],flush=True)
    # Deterministic isolated and 3-target zero-noise scenarios.
    targets=[m.Target(20,-3,.18),m.Target(40,1.5,.18),m.Target(60,5,.18)]
    rows=[]
    for name,tar in [('single_20',[targets[0]]),('single_40',[targets[1]]),('single_60',[targets[2]]),('three_clean',targets)]:
        iq=m.generate_cpi(tar)
        pc=m.pulse_compress(iq)
        power=m.rd_power(m.doppler(m.mti(pc)))
        alarm,valid,training=m.cfar_2d(power,alpha=ALPHA0)
        clusters=m.clusters_8(alarm,power)
        out=[]
        for item in clusters:
            k=item['range_bin'];b=item['doppler_bin']
            sample=float(power[k,b]);noise=float(training[k,b]);threshold=float(ALPHA0*noise)
            # Examine the exact local CUT and training powers at each cluster peak.
            T=[float(power[k+dr,b+db]) for dr,db in m.TRAIN_OFFSETS]
            assert np.isclose(noise,sum(T)/40,atol=1e-8,rtol=1e-12)
            out.append({'selected_range_bin':k,'selected_doppler_bin':b,'power_CUT':sample,'training_sum':float(sum(T)),
                        'mean_training_power':noise,'alpha_times_training_mean':threshold,
                        'power_minus_threshold':sample-threshold,'strictly_above_threshold':bool(sample>threshold),
                        'training_min':min(T),'training_max':max(T),
                        'cluster_size':item['cluster_cells'],
                        'numeric_zero_relative':sample/(max(float(power.max()),1e-300))})
        rows.append({'scene':name,'target_count':len(tar),'clusters':len(clusters),'alarm_cells':int(alarm.sum()),
                     'cluster_peaks_CFAR_numeric':out})
        print('CLUSTER',name,'clusters',len(clusters),'minrel',min([e['numeric_zero_relative'] for e in out],default=None),flush=True)
    cf={'scope':'EXPLORATORY_FLOAT_REFERENCE_CA_CFAR_NUMERIC_STAGE_ISOLATION',
        'alpha_initializer_NOT_CALIBRATED':ALPHA0,
        'noise_free_scenes':rows,
        'warning':'Training cells/threshold may be exactly or numerically near zero; a small positive FFT residue can meet strict P>alpha*training even when theoretical power is zero. This does NOT justify changing alpha or adding floors without approved change.',
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (dest/'S03_v11_extra_clusters_CUT_training_thresholds_DIAGNOSTIC.json').write_text(json.dumps(cf,indent=2,sort_keys=True)+'\n')
    return spatial,cf

if __name__=='__main__':run(sys.argv[1])

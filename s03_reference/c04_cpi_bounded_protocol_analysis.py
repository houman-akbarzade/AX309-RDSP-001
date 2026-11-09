"""Read-only analytical design of C04 candidate. NO NEW CPI/FINAL Pfa GENERATED.
Uses previously preserved post-alpha Python spatial diagnostic only for observed
CPI mean/variance; distribution-free coverage does not rely on those estimates.
"""
from pathlib import Path
import json,math,hashlib,platform
import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parents[1]
ALPHA=.05
TARGET=.001
LIMIT=.0015
MCUT=2782
INPUT='engineering/S03-C04-post-alpha-spatial-diagnostic-v0.1.json'
N_PROPOSED=20000
N_ANALYTIC=[4096,8192,12000,16000,18000,20000,22000,24000,32768,50000]
def kl(a,b):
    assert 0<=a<=1 and 0<b<1
    return ((a*math.log(a/b)) if a>0 else 0)+((1-a)*math.log((1-a)/(1-b)) if a<1 else 0)
def eb(n,mean,var):
    assert n>1 and 0<=mean<=1 and var>=0
    return min(1.,mean+math.sqrt(2*var*math.log(2/ALPHA)/n)+7*math.log(2/ALPHA)/(3*(n-1)))
def kl_bound(n,observed):
    if observed>=1:return 1.
    if observed==0:return 1-math.exp(math.log(ALPHA)/n)
    return brentq(lambda u:n*kl(observed,u)-math.log(1/ALPHA),observed+1e-14,1-1e-12)
def kl_threshold(n):
    # maximal observed Xbar such that the upper KL inversion <= LIMIT
    if n*kl(0.,LIMIT)<math.log(1/ALPHA):return None
    return brentq(lambda x:n*kl(x,LIMIT)-math.log(1/ALPHA),0.,LIMIT-1e-13)
def normal_proxy_power_eb(n,v,mult=1.):
    vv=v*mult
    upper_at_mean=eb(n,TARGET,vv)
    threshold=LIMIT-(upper_at_mean-TARGET)
    return float(norm.cdf((threshold-TARGET)/math.sqrt(vv/n)))
def normal_proxy_power_kl(n,v,mult=1.):
    x=kl_threshold(n)
    if x is None:return 0.
    return float(norm.cdf((x-TARGET)/math.sqrt(v*mult/n)))
def main():
    raw=json.loads((ROOT/INPUT).read_text())
    assert raw['status']=='FAIL_SPATIAL_TRANSFER_GATE'
    assert raw['CPI']==4096 and raw['CUT_per_CPI']==MCUT
    variance_count=float(raw['sample_variance'])
    historic_mean=float(raw['mean'])/MCUT
    variance_x=variance_count/(MCUT*MCUT)
    rows=[]
    for n in N_ANALYTIC:
        base={
            'N_CPI':n,
            'eb_U_at_population_p001_and_historical_sample_variance':eb(n,TARGET,variance_x),
            'eb_U_at_population_p001_and_4x_historical_variance':eb(n,TARGET,4*variance_x),
            'KL_U_at_observed_mean_p001':kl_bound(n,TARGET),
            'KL_critical_max_observed_mean_for_PASS':kl_threshold(n),
            'hoeffding_additive_95':math.sqrt(math.log(1/ALPHA)/(2*n)),
            'EB_distribution_free_additive_term_alone':7*math.log(2/ALPHA)/(3*(n-1)),
            'normal_proxy_probability_EB_Pass_at_true_p001':normal_proxy_power_eb(n,variance_x),
            'normal_proxy_probability_EB_Pass_at_true_p001_var4x':normal_proxy_power_eb(n,variance_x,4),
            'normal_proxy_probability_KL_Pass_at_true_p001':normal_proxy_power_kl(n,variance_x),
            'reference_model_seconds_linear_extrapolation':n/4096*float(raw['elapsed_monotonic_seconds']),
            'minimum_UART_8N1_one_way_hours_if_full_CPI_uploaded':n*16896*10/(115200*3600),
            'full_input_IQ_bytes':n*16896,
            'CPI_fraction_buffer_bytes_float64':n*8}
        rows.append(base)
    testnum=next(n for n in range(4096,100001) if eb(n,TARGET,variance_x)<=LIMIT)
    cross_power=next(n for n in range(4096,100001) if normal_proxy_power_eb(n,variance_x)>=.95)
    cross_power4=next(n for n in range(4096,100001) if normal_proxy_power_eb(n,variance_x,4)>=.95)
    min_kl=math.ceil(math.log(1/ALPHA)/kl(TARGET,LIMIT))
    assert testnum<cross_power<20000
    assert min_kl>20000
    d={
      'stage':'S03','status':'ANALYTICAL_PROTOCOL_DESIGN_ONLY_DO_NOT_EXECUTE_FINAL_PFA',
      'script_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'source_diagnostic_file':INPUT,'source_diagnostic_SHA256':hashlib.sha256((ROOT/INPUT).read_bytes()).hexdigest(),
      'source_diagnostic_was_not_an_independent_final_test':True,
      'source_diagnostic_failed_spatial_gate':True,
      'reference_CPI_count_variance':variance_count,
      'reference_CPI_alarm_fraction_sample_variance':variance_x,
      'reference_raw_rate':historic_mean,
      'Pfa_goal':TARGET,'U_limit':LIMIT,'confidence':.95,
      'CUT_per_CPI':MCUT,'recommended_fixed_future_main_CPI':N_PROPOSED,
      'proposed_inference':'fixed-sample empirical Bernstein with CPI as independent bounded units',
      'formula':'U=min(1,mean(X)+sqrt(2*S2*ln(40)/N)+7*ln(40)/(3*(N-1))), S2 with ddof=1',
      'other_comparators':['fixed-sample Hoeffding','bounded Bernoulli-KL Chernoff inverted upper','existing approved Studentized v1.1'],
      'numerical_analytic_grid':rows,
      'min_N_EB_at_true_p_and_historical_variance_NO_POWER':testnum,
      'min_N_EB_normal_approx_95percent_power_historical_variance':cross_power,
      'min_N_EB_normal_approx_95percent_power_4x_variance':cross_power4,
      'min_N_KL_at_observed_mean_p001_NO_POWER':min_kl,
      'statistical_coverage_guarantee':'For independent identically distributed CPI counts with 0<=F<=2782, EB one-sided has >=95% finite-sample coverage at a single FIXED N, regardless of within-CPI CUT spatial dependence',
      'normal_power_model_is_only_approximation_not_guarantee':True,
      'no_simulation_new_samples':True,'no_delta_or_alpha_changed':True,
      'runtime_basis_source_measured_4096_CPI_seconds':float(raw['elapsed_monotonic_seconds']),
      'original_failed_student_t_7_of_15_preserved':True,
      'prospective_approval_required_before_any_change':True,'python_version':platform.python_version(),'numpy_version':np.__version__}
    out=ROOT/'engineering/S03-C04-CPI-bounded-analytical-cost-and-power-v0.1.json'
    assert not out.exists()
    out.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    for r in rows:
        print('N',r['N_CPI'],'EB',round(r['eb_U_at_population_p001_and_historical_sample_variance'],9),'EB4x',round(r['eb_U_at_population_p001_and_4x_historical_variance'],9),'KL',round(r['KL_U_at_observed_mean_p001'],9),'EBpower',r['normal_proxy_probability_EB_Pass_at_true_p001'],'UART_h',round(r['minimum_UART_8N1_one_way_hours_if_full_CPI_uploaded'],2))
    print('DECISION_N',N_PROPOSED,'CROSS_EB',testnum,'CROSS_EB_P95',cross_power,'CROSS_EB_P95_4X',cross_power4,'CROSS_KL',min_kl)
    print('OUTPUT',out)
if __name__=='__main__':main()

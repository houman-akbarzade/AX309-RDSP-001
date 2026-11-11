"""S04-C03 all eight primitive sections, independent integer/Fraction oracles.

Tests marked C03-P01..P08 are NEW C03 qualification, not renamed C02
regression. DUT remains unchanged v0.5 selected C / v0.6 diagnostic capture.
"""
import json,sys,math,hashlib,struct,unittest
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'engineering/s04_numeric'))
import s04_c03_independent_oracle_v1 as OR
import s04_c03_fulltrace_v1 as TR
import s04_c02_integer_bittrue_v05 as DUT
import s04_c02_integer_maps_v06 as MAP
from s03_reference import model as S03
C=OR.CONTRACT
TRACE=json.loads((ROOT/'engineering/s04_numeric/S04-C03-complete-overflow-replay-v1.0.json').read_text())
CASES={r['vector_id']:r for r in TRACE['cases']}
TAPS=[tuple(z) for z in C['MF']['mf16_stored_pairs']]
TW=[[tuple(z) for z in stage['twiddle_stage_stored_pairs']] for stage in C['FFT']['stages']]
class P01_IQ_Independent(unittest.TestCase):
 def test_both_scales_exact_thresholds_signed_and_reconstruction(self):
  values=[(Fraction(0),0,False),(Fraction(1,65536),0,False),
     (Fraction(3,65536),2,False),(Fraction(-3,65536),-2,False),
     (Fraction(32767,32768),32767,False),(Fraction(-1),-32768,False),
     (Fraction(65535,65536),32767,True),
     (Fraction(-65537,65536),-32768,False),
     (Fraction(1),32767,True),
     (Fraction(-6,5),-32768,True)]
  for g in (1,5):
   for normalized,expected,clip in values:
    q,sat=OR.input_pack(g*normalized,g)
    self.assertEqual((q,sat),(expected,clip),(g,normalized))
    if not sat:
     self.assertLessEqual(abs(OR.unpack_input(q,g)-g*normalized),Fraction(g,65536))
 def test_IQ_interleave_little_endian_and_model_consistency(self):
  packed=[(-32768,32767),(1,-2),(0,42)]
  self.assertEqual(OR.interleaved_iq_bytes(packed),struct.pack('<hhhhhh',-32768,32767,1,-2,0,42))
  for g in (1,5):
   for pattern in ('zero','half_lsb_pos_neg','near_clip','overrange_stress'):
    _,arr,tel=DUT.source_vector(pattern,g)
    for p,r in ((0,0),(8,40),(15,127),(32,63)):
     re,im=DUT.vector_value(pattern,p,r)
     self.assertEqual(arr[p][r],(OR.input_pack(g*re,g)[0],OR.input_pack(g*im,g)[0]))

class P02_Coefficients_Independent(unittest.TestCase):
 def test_chirp_rederived_without_DUT_helpers(self):
  self.assertEqual(OR.independent_mf_taps(),TAPS)
  actual=S03.matched_filter()
  self.assertEqual(len(actual),16)
  for k,(i,q) in enumerate(TAPS):
   self.assertLessEqual(abs(float(actual[k].real)-i/32768),1/65536+1e-12)
   self.assertLessEqual(abs(float(actual[k].imag)-q/32768),1/65536+1e-12)
  self.assertEqual(TAPS[0],TAPS[15])
 def test_fft_forward_twiddle_sign_order_and_hash(self):
  self.assertEqual(OR.independent_twiddles(),TW)
  self.assertEqual([len(s) for s in TW],[1,2,4,8,16])
  self.assertEqual(TW[2][1],(23170,-23170))
  self.assertEqual(TW[0][0],(32767,0))
  self.assertEqual(C['FFT']['bit_reversal'],[int(f'{i:05b}'[::-1],2) for i in range(32)])
  source=ROOT/'engineering/s04_numeric/S04-C02-coeff-shift-quant-analysis-v0.3.json'
  self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
        C['evidence_SHA256']['source_coefficients_v03'])

class P03_Complex_MF_Independent(unittest.TestCase):
 def test_manual_gaussian_integer_products(self):
  self.assertEqual(OR.integer_complex((3,-5),(-7,11)),(34,68))
  self.assertEqual(OR.integer_complex((-32768,32767),(32767,-32768)),(0,2147418113))
  # reference from symbolic (a+jb)*(c+jd), not DUT candidate rne.
  for a,b in [((0,1),(1,0)),((-1,0),(0,-1)),((22,-33),(-6,-5))]:
   expected=(a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
   self.assertEqual(OR.integer_complex(a,b),expected)
 def test_16tap_accumulator_independent_signed_range(self):
  sample=[(32767,-32768)]*16
  sum_r,sum_i=OR.mf_full_accumulator(sample,TAPS)
  self.assertTrue(all(-(1<<36)<=x<1<<36 for x in (sum_r,sum_i)))
  self.assertEqual(OR.mf_full_accumulator([(0,0)]*16,TAPS),(0,0))
  self.assertEqual((C['MF']['four_exact_signed_products_W'],C['MF']['complex_pair_signed_W'],C['MF']['raw_16tap_accumulator_signed_W']),(32,33,37))
 def test_independent_MF_at_range_against_selected_FFT_map(self):
  for g in (1,5):
   src,iq,tel=DUT.source_vector('impulse',g)
   candidate=MAP.run_one(src,iq,tel,'C_hypothetical',(0,1,0,1,1),g,capture_maps=True)
   for r in (25,30,38,40,41):
    mf=[OR.mf_at(iq,p,r,TAPS) for p in range(33)]
    mti=[OR.mti(mf[p],mf[p+1]) for p in range(32)]
    oracle_fft=OR.fft32_oracle(mti,TW)
    actual=[tuple(x) for x in candidate['captured']['rd_iq_integer'][r]]
    self.assertEqual(oracle_fft[-1],actual,(g,r))
   self.assertEqual(candidate['overflow']['total'],0)

class P04_MTI_FFT_Independent(unittest.TestCase):
 def test_MTI_endpoints_and_raw_difference(self):
  self.assertEqual(OR.mti((0,0),(4194303,-4194304)),(4194303,-4194304))
  self.assertEqual(OR.mti((4194303,-4194304),(-4194304,4194303)),(-4194304,4194303))
  self.assertEqual(C['MTI']['raw_subtract_signed_W'],23)
 def test_five_stage_fullwidth_and_rounding_divisor(self):
  self.assertEqual([stage['shift'] for stage in C['FFT']['stages']],[0,1,0,1,1])
  for i,stage in enumerate(C['FFT']['stages']):
   self.assertEqual(stage['signed_real_product_W'],39 if i==0 else 41)
   self.assertEqual(stage['signed_real_complex_pair_W'],40 if i==0 else 42)
   self.assertEqual(stage['pre_shift_butterfly_signed_W'],41 if i==0 else 43)
   self.assertEqual(stage['rounding_denom_power_of_two'],15+OR.SCHED[i])
   self.assertEqual(OR.butterfly((0,0),(0,0),(32767,0),i),((0,0),(0,0)))
 def test_fft_negative_tie_boundary_differs_from_arithmetic_shift(self):
  # t=-32768 at F30, exact FFT stage0 output=-1 code, stage1 half=-0.5 ties->0.
  plus,minus=OR.butterfly((0,0),(-1,0),(32767,0),1)
  self.assertEqual(plus[0],0)
  self.assertEqual(minus[0],0)

class P05_RNE_SignedEdges(unittest.TestCase):
 def test_ties_both_signs_and_fractional(self):
  table={Fraction(1,2):0,Fraction(3,2):2,Fraction(5,2):2,
         Fraction(-1,2):0,Fraction(-3,2):-2,Fraction(-5,2):-2,
         Fraction(7,2):4,Fraction(-7,2):-4,Fraction(9,4):2,Fraction(-9,4):-2}
  for x,y in table.items():
   self.assertEqual(OR.ref_round(x),y)
   self.assertEqual(DUT.rne(x.numerator,x.denominator),y)
 def test_exhaust_small_denominators_against_fraction_oracle(self):
  for den in (2,4,8,32768,65536):
   for v in range(-33,34):
    self.assertEqual(DUT.rne(v,den),OR.ref_round(Fraction(v,den)))
 def test_signed_extremes_and_saturations(self):
  for w in (16,22,23,25,32,33,37,39,40,41,42,43):
   low,high=OR.limits(w)
   self.assertEqual(OR.checked(low,w),(low,False))
   self.assertEqual(OR.checked(high,w),(high,False))
   self.assertEqual(OR.checked(low-1,w),(low,True))
   self.assertEqual(OR.checked(high+1,w),(high,True))
  self.assertNotEqual((-1)>>1,OR.ref_round(Fraction(-1,2)))
  self.assertNotEqual((-5)>>1,OR.ref_round(Fraction(-5,2)))

class P06_Power_SUM40_CFAR(unittest.TestCase):
 def test_signed_extrema_full_power_and_unsigned_narrowing(self):
  extreme=-(1<<24)
  raw=2*extreme*extreme
  self.assertEqual(raw,1<<49)
  self.assertEqual(OR.oracle_power(extreme,extreme),((1<<46)-1,True))
  self.assertEqual(OR.oracle_power(0,0),(0,False))
  self.assertEqual(OR.oracle_power(1,-1),(2,False))
  self.assertEqual(C['power']['raw_I_squared_plus_Q_squared_unsigned_W'],51)
 def test_entire_4096_power_map_and_all_2782_CUT_against_fraction_oracle(self):
  src,iq,trace=DUT.source_vector('phase_interference',1)
  captured=MAP.run_one(src,iq,trace,'C_hypothetical',(0,1,0,1,1),1,capture_maps=True)['captured']
  rd=captured['rd_iq_integer']
  full=[]
  for row in rd:
   full.append([OR.oracle_power(i,q)[0] for i,q in row])
  self.assertEqual(full,captured['power_integer'])
  decisions={(r,b):d for r,b,d,_,_,_ in captured['cut_records']}
  checks=[]
  for r in range(3,110):
   for b in range(3,29):
    train=[]
    for dr in range(-3,4):
     for db in range(-3,4):
      if abs(dr)>1 or abs(db)>1:
       train.append(full[r+dr][b+db])
    self.assertEqual(len(train),40)
    total,sat=OR.oracle_sum40(train)
    self.assertFalse(sat)
    self.assertEqual(OR.oracle_cfar(full[r][b],total),bool(decisions[(r,b)]))
    checks.append((r,b))
  self.assertEqual(len(checks),2782)
 def test_sum40_exhaust_extrema(self):
  self.assertEqual(OR.oracle_sum40([0]*40),(0,False))
  hi=(1<<46)-1
  summ=40*hi
  self.assertEqual(OR.oracle_sum40([hi]*40),(summ,False))
  self.assertLess(summ,1<<52)
  self.assertEqual(C['SUM40']['raw_sum_unsigned_W'],52)
 def test_strict_Cfar_exact_tie_neighbors_and_full_products(self):
  n=490007;den=65536
  training=40*den
  for cut,expect in [(n-1,False),(n,False),(n+1,True)]:
   self.assertEqual(OR.oracle_cfar(cut,training),expect)
   self.assertEqual(40*cut*den>n*training,expect)
  left=40*((1<<46)-1)*den
  right=n*((1<<52)-1)
  self.assertLess(left,1<<68)
  self.assertLess(right,1<<72)
  self.assertEqual((C['CFAR']['left_unsigned_fullproduct_conservative_W'],
    C['CFAR']['right_unsigned_fullproduct_conservative_W']),(68,72))

class P07_FullOverflowTrace(unittest.TestCase):
 def test_complete_stress_and_no24_cap(self):
  self.assertEqual(TRACE['event_count'],16896)
  self.assertEqual(TRACE['total_cases'],6)
  for g in (1,5):
   case=CASES[f'S04-C03-g{g}-overrange_stress']
   self.assertEqual(case['retained_records'],8448)
   self.assertEqual(case['per_scope_counts'],{'input':8448,'processing':0})
   path=ROOT/case['full_file']
   lines=path.read_bytes().splitlines()
   self.assertEqual(len(lines),8448)
   self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),case['full_file_SHA256'])
   self.assertEqual(len({json.loads(line)['event_id'] for line in lines}),8448)
   self.assertTrue(all(json.loads(line)['pre_narrow_integer'] for line in lines))
   self.assertEqual(case['full_re_read_and_uniqueness'],'PASS')
   self.assertTrue(case['no_truncation'])
 def test_forced_internal_overflow_and_all_event_positions(self):
  TR.CompleteEventRecorder.instances=[]
  TR.CompleteEventRecorder.current_vector='C03-forced-unit-vector'
  tel=TR.CompleteEventRecorder()
  for i in range(77):
   if i%2:
    v=-(1<<25)-i
   else:
    v=(1<<25)+i
   bounded=DUT.bounded(v,25,tel,'FFT5',(5,i%32),'I')
   self.assertEqual(bounded,OR.checked(v,25)[0])
  self.assertEqual(len(tel.events),77)
  self.assertEqual(tel.summary()['total'],77)
  self.assertEqual(len(tel.summary()['first_24']),24) # legacy summary only
  self.assertEqual(len({e['event_id'] for e in tel.events}),77)
  self.assertEqual([e['ordinal_in_stream'] for e in tel.events],list(range(77)))
  self.assertEqual(tel.events[-1]['pre_narrow_integer'],str((1<<25)+76))
 def test_all_forced_internal_FFT_power_SUM_events_saved_and_readable(self):
  p=ROOT/'engineering/s04_numeric/S04-C03-forced-internal-overflow-evidence-v1.0.json'
  m=json.loads(p.read_text())
  self.assertEqual(m['events'],159)
  self.assertEqual(m['new_complete_trace_retained'],159)
  raw=(ROOT/m['source_file']).read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),m['source_SHA256'])
  self.assertEqual(len(raw.splitlines()),159)
  items=[json.loads(row) for row in raw.splitlines()]
  self.assertEqual([item['ordinal_in_stream'] for item in items],list(range(159)))
  self.assertEqual(len(set(e['event_id'] for e in items)),159)
  self.assertEqual({e['site'] for e in items},{'FFT5','POWER','SUM40'})
 def test_input_vs_processing_saturation_event_replay(self):
  for g in (1,5):
   for kind in ('zero','near_clip'):
    self.assertEqual(CASES[f'S04-C03-g{g}-{kind}']['retained_records'],0)
  self.assertEqual({k['vector_id'] for k in TRACE['cases']},set(CASES))

class P08_ReproAndIndependence(unittest.TestCase):
 def test_independent_expected_constants_and_source(self):
  body=(ROOT/'engineering/s04_numeric/s04_c03_independent_oracle_v1.py').read_text()
  for bad in ('DUT.rne','DUT.bounded','DUT.shifted_round','import s04_c02_integer_bittrue_v05'):
   self.assertNotIn(bad,body)
  self.assertEqual(OR.integer_complex((3,-5),(-7,11)),(34,68))
  self.assertEqual(OR.ref_round(Fraction(-5,2)),-2)
  self.assertEqual(OR.oracle_cfar(490007,40*65536),False)
 def test_stable_contract_and_historic_commit_not_modified(self):
  self.assertEqual(C['architecture'],'C')
  self.assertEqual(C['schedule'],[0,1,0,1,1])
  state=json.loads((ROOT/'engineering/S04-progress.json').read_text())
  self.assertEqual(state['completed_count'],2)
  self.assertEqual(state['stage_percent'],25.0)
  self.assertFalse(state['criteria'][2]['completed'])
  self.assertEqual(state['criteria'][2]['id'],'S04-C03')
  self.assertEqual(json.loads((ROOT/'project.yaml').read_text())['progress']['s04_completed_criteria'],2)
 def test_no_stochastic_CPI_or_hardware_commands(self):
  for f in ('s04_c03_independent_oracle_v1.py','s04_c03_fulltrace_v1.py'):
   code=(ROOT/'engineering/s04_numeric'/f).read_text()
   for bad in ('np.random','default_rng(','generate_cpi(','noise_only_cpi(','SeedSequence('):
    self.assertNotIn(bad,code)
if __name__=='__main__':
 unittest.main(verbosity=2)

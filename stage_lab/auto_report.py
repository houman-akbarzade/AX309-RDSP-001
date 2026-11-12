"""Human reports and deterministic SVGs, built only from captured hardware arrays."""
import html,json
from pathlib import Path
import numpy as np
from .models import decode,reference
from .visuals import svg_start as _svg_start,text
def svg_start(w,h):return _svg_start(w,h).replace('width="100%" height="100%"',f'width="{w}" height="{h}"')
from desktop_app.scenarios import RANGE_STEP,VELOCITY_STEP
from s03_reference import model as M
FA={0:'IQ خام',1:'فیلتر منطبق MF',2:'فیلتر MTI',3:'FFT',4:'Power',5:'CFAR',6:'کلاسترینگ'}
def fmt(x):
 return 'تعریف‌نشده' if x is None else f'{x:.6g}' if isinstance(x,(int,float)) else str(x)
def esc(x):return html.escape(str(x))
def page(title,body):
 return '<!doctype html><html dir="rtl"><meta charset="UTF-8"><style>body{font-family:"B Nazanin","DejaVu Sans";font-size:18px;line-height:1.7;background:#142338;color:#ecf2fa;margin:26px}h1,h2,h3,a{color:#75d8fa}article{background:#20354c;padding:18px;margin:16px 0;border-right:4px solid #75d8fa}table{border-collapse:collapse;width:100%;margin:14px 0}td,th{border:1px solid #567088;padding:7px}img{max-width:100%;height:auto}small{color:#b9cbdd}.ok{color:#72e0b2}.warn{color:#ffca68}</style><title>'+esc(title)+'</title><h1>'+esc(title)+'</h1>'+body+'</html>'
def table(headers,rows):
 return '<table><tr>'+''.join('<th>'+esc(v)+'</th>' for v in headers)+'</tr>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</table>'
def target_sentence(targets):
 if not targets:return 'سناریوی نویز بدون هدف'
 ranges=[t['delay']*RANGE_STEP for t in targets];vel=[t['velocity'] for t in targets]
 s=f"{len(targets)} هدف در بردهای "+'، '.join(fmt(v) for v in ranges)+' متر و با سرعت‌های '+ '، '.join(fmt(v) for v in vel)+' متر بر ثانیه'
 if len(targets)==2:s+='؛ فاصله بردی دو هدف '+fmt(abs(ranges[1]-ranges[0]))+' متر و اختلاف سرعت '+fmt(abs(vel[1]-vel[0]))+' متر بر ثانیه'
 return s
def metric_text(metrics):
 statements=[]
 for label,m in metrics.items():
  if 'Fixed' not in label:continue
  if 'RMSE' in m:out='RMSE برابر '+fmt(m['RMSE'])+' و بیشینه اختلاف '+fmt(m['max_abs_error'])+' بود؛ '+('همه کدهای خروجی برابر بودند' if m.get('exact_integer') else 'اختلاف کد عددی وجود داشت')
  elif 'decision_mismatches' in m:out=fmt(m['decision_mismatches'])+' تصمیم CFAR متفاوت، '+fmt(m['extra_alarms_vs_reference'])+' تصمیم اضافی و '+fmt(m['missing_alarms_vs_reference'])+' تصمیم گمشده ثبت شد'
  else:out=fmt(m['hardware_clusters'])+' کلاستر سخت‌افزاری در برابر '+fmt(m['reference_clusters'])+' کلاستر مرجع ثبت شد؛ '+('امضای رکوردها برابر بود' if m['record_signatures_exact'] else 'رکوردها اختلاف داشتند')
  statements.append('با مرجع '+label+' مقایسه شد: '+out+'.')
 return ' '.join(statements)
def sentence(job):
 s=target_sentence(job['targets'])+f" با RMS نویز {fmt(job['noise_rms'])}"
 if job['scope']=='accumulated':s+=' از IQ خام وارد زنجیره سخت‌افزاری شد؛ در این آزمون خروجی '+FA[job['stage']]+' برداشت شد. '+metric_text(job['full_chain_metrics'])
 else:s+=' برای آزمون از خروجی '+FA[job['entry']]+' تزریق و خروجی '+FA[job['stage']]+' برداشت شد. '+metric_text(job['metrics'])
 rows=job['status']['input_words']//128
 s+=' ورودی شامل '+str(rows)+(' ردیف PRI بود.' if job['entry']<3 else ' ردیف بین داپلر بود.')
 return s
def function_text(fun):
 out=[]
 for r in fun.get('mti_target_response',[]):
  result='خروجی دقیقاً صفر شد' if r['exact_zero_output'] else 'بهره دامنه خروجی نسبت به ورودی '+fmt(r['gain_db'])+' dB بود'
  out.append('هدف '+r['target']+' با سرعت '+fmt(r['velocity_m_s'])+' m/s: '+result+'.')
 for key in ['range_resolution','velocity_resolution']:
  if key in fun:
   r=fun[key];out.append(('تفکیک برد' if key=='range_resolution' else 'تفکیک سرعت')+': '+('دو قله با معیار افت دره حداقل ۳ dB تفکیک شدند' if r['resolved'] else 'دو قله با معیار افت دره حداقل ۳ dB تفکیک نشدند')+('؛ مقدار دره در کد خروجی دقیقاً صفر بود.' if r.get('valley_exact_zero') else '؛ افت دره '+fmt(r['valley_depth_db'])+' dB.'))
 if 'association' in fun:
  a=fun['association'];out.append(fmt(a['matched_targets'])+' هدف از '+fmt(a['defined_targets'])+' هدف با کلاسترها تطبیق یافت؛ '+fmt(a['unassociated_clusters'])+' کلاستر بدون تطبیق باقی ماند.')
 return ' '.join(out)
def normalized(a,stage,fixed=True):
 if stage<=3:return np.asarray(a)/(32768 if fixed else 1)
 if stage==4:return np.asarray(a,float)/((1<<30) if fixed else 1)
 if stage==5:return np.asarray(a[0],float)/((1<<30) if fixed else 1),np.asarray(a[1],bool)
 return a
def map_array(a,stage,fixed=True):
 z=normalized(a,stage,fixed)
 if stage<=3:p=np.abs(z)**2
 elif stage==4:p=z
 elif stage==5:p=z[1].astype(float)
 else:
  p=np.zeros((32,128))
  for r in a:p[int(r['doppler_bin']),int(r['range_bin'])]+=1
 return np.fft.fftshift(p,axes=0) if stage>=3 else p
def heat_svg(title,a,stage,limits=None):
 p=np.nan_to_num(np.asarray(a,float));lo,hi=limits or (float(p.min()),float(p.max()));den=max(hi-lo,1e-30)
 w=920;h=400;left=90;top=65;pw=790;ph=260;s=svg_start(w,h)+text(18,27,title,20)+text(90,52,f'Color: {lo:.5g} .. {hi:.5g}',13)
 for r in range(p.shape[0]):
  for c in range(p.shape[1]):
   q=float(np.clip((p[r,c]-lo)/den,0,1));color=f'rgb({int(255*q)},{int(235*np.sqrt(q))},{int(100+120*(1-q))})'
   s+=f'<rect x="{left+c*pw/p.shape[1]:.2f}" y="{top+(p.shape[0]-1-r)*ph/p.shape[0]:.2f}" width="{pw/p.shape[1]+.1:.2f}" height="{ph/p.shape[0]+.1:.2f}" fill="{color}"/>'
 for k in range(5):
  f=k/4;xx=left+(.5+f*(p.shape[1]-1))*pw/p.shape[1];yy=top+ph-(.5+f*(p.shape[0]-1))*ph/p.shape[0]
  s+=text(xx-20,top+ph+22,f'{f*127*RANGE_STEP:.5g}',12)
  y=(-16+f*31)*VELOCITY_STEP if stage>=3 else f*(p.shape[0]-1)
  s+=text(10,yy+4,f'{y:.5g}',12)
 s+=text(400,385,'Range (m)',15)+text(10,365,'Radial velocity (m/s)' if stage>=3 else 'PRI / slow-time index',14)
 return s+'</g></svg>'
def line_svg(title,x,curves,xlabel,ylabel):
 x=np.asarray(x,float);ys=[np.asarray(v,float) for v in curves.values()];lo=min(float(v.min()) for v in ys);hi=max(float(v.max()) for v in ys)
 if hi==lo:hi=lo+max(abs(lo)*.1,1e-20)
 w=920;h=400;l=85;top=105;pw=790;ph=230;s=svg_start(w,h)+text(15,26,title,19)
 colors=['#ffca68','#75d8fa','#72e0b2','#e099fa','#ff8585']
 for k in range(5):
  f=k/4;xx=l+f*pw;yy=top+(1-f)*ph;s+=f'<path d="M{xx},{top} V{top+ph} M{l},{yy} H{l+pw}" stroke="#30465b"/>'
  s+=text(xx-22,top+ph+23,f'{x.min()+f*np.ptp(x):.5g}',12)+text(5,yy+4,f'{lo+f*(hi-lo):.4g}',12)
 for i,(name,v) in enumerate(curves.items()):
  v=np.asarray(v,float);points=' '.join(f'{l+(xx-x.min())/max(np.ptp(x),1e-30)*pw:.3f},{top+ph-(yy-lo)/(hi-lo)*ph:.3f}' for xx,yy in zip(x,v))
  s+=f'<polyline points="{points}" fill="none" stroke="{colors[i%5]}" stroke-width="2"/>'+text(90+(i%3)*260,50+(i//3)*22,name,13,colors[i%5])
 s+=text(350,390,xlabel,14)+text(5,83,ylabel,13)
 return s+'</g></svg>'
def job_details(job,d):
 z=np.load(d/job['artifact']);t=job['stage'];entry=job['entry'];rows=z['input_words'].size//128
 inp=decode(z['input_words'],entry,rows);out=decode(z['output_words'],t,rows-1 if t==2 else rows);refs={}
 for label in job['metrics']:
  key='ref_'+label.replace(' ','_')
  if t<=4:refs[label]=z[key]
  elif t==5:refs[label]=(z[key+'_power'],z[key+'_mask'])
  else:refs[label]=job['record_references']['ref '+label]
 if job['scope']=='accumulated':
  refs={}
  for label in job['full_chain_metrics']:
   key='chain_'+label.replace(' ','_')
   if t<=4:refs[label]=z[key]
   elif t==5:refs[label]=(z[key+'_power'],z[key+'_mask'])
   else:refs[label]=job['record_references']['chain '+label]
 label=next((k for k in refs if 'Fixed' in k),next(iter(refs)));ref=refs[label]
 a=map_array(out,t);b=map_array(ref,t,'Fixed' in label);limits=(min(a.min(),b.min()),max(a.max(),b.max()));body='<p><a href="index.html">بازگشت به جمع‌بندی</a></p><article>'+esc(sentence(job))+'</article><p>'+esc(function_text(job['functional']))+'</p>'
 for name,data,lim in [('FPGA',a,limits),(label,b,limits),('FPGA minus reference',a-b,None)]:
  f=job['id']+'-'+name.replace(' ','_')+'.svg';(d/f).write_text(heat_svg(name+' | '+('normalized power' if t<=4 else 'CFAR decision' if t==5 else 'cluster peak count'),data,t,lim));body+=f'<p><img src="{f}" width="920"></p>'
 from .visuals import architecture_svg,scenario_svg
 from desktop_app.scenarios import Flight
 file=job['id']+'-path.svg';(d/file).write_text(architecture_svg(0 if job['scope']=='accumulated' else entry,t,job['scope']=='accumulated',job['origin']['origin'],rows));body='<img src="'+file+'" width="920">'+body
 file=job['id']+'-input-map.svg';(d/file).write_text(heat_svg('Actual echoed input | normalized power / mask',map_array(inp,entry),entry));body+='<h2>ورودی واقعی بازخوانی‌شده از FPGA</h2><img src="'+file+'" width="920">'
 if entry<=2:
  ainput=normalized(inp,entry)
  for row in sorted({0,ainput.shape[0]//2,ainput.shape[0]-1}):
   file=job['id']+f'-input-pri-{row}.svg';(d/file).write_text(line_svg('Actual input PRI index '+str(row),np.arange(128)*RANGE_STEP,{'FPGA input echo':abs(ainput[row])},'Range (m)','Normalized amplitude'));body+='<img src="'+file+'" width="920">'
 # Multiple range profiles use the SAME PRI/bin for FPGA and every reference.
 if t<=4:
  aa=normalized(out,t);rr={k:normalized(v,t,'Fixed' in k) for k,v in refs.items()}
  indices=sorted({0,aa.shape[0]//2,aa.shape[0]-1}) if t<3 else sorted({int(np.rint(v['velocity']/VELOCITY_STEP))%32 for v in job['targets']}) or [int(np.argmax(np.sum(abs(aa)**2,axis=1)))]
  for row in indices[:3]:
   curves={'FPGA':np.abs(aa[row]) if t<=3 else aa[row]};curves.update({k:np.abs(v[row]) if t<=3 else v[row] for k,v in rr.items()})
   f=job['id']+f'-profile-{row}.svg';(d/f).write_text(line_svg(('PRI index ' if t<3 else 'Natural Doppler bin ')+str(row),np.arange(128)*RANGE_STEP,curves,'Range (m)','Normalized amplitude' if t<=3 else 'Normalized power'));body+=f'<img src="{f}" width="920">'
  if t>=3:
   for cell in sorted({v['delay'] for v in job['targets']})[:3] or [40]:
    curves={'FPGA':np.fft.fftshift(np.abs(aa[:,cell]) if t==3 else aa[:,cell])};curves.update({k:np.fft.fftshift(abs(v[:,cell]) if t==3 else v[:,cell]) for k,v in rr.items()})
    f=job['id']+f'-spectrum-{cell}.svg';(d/f).write_text(line_svg(f'Range cell {cell}',np.arange(-16,16)*VELOCITY_STEP,curves,'Radial velocity (m/s)','Normalized amplitude' if t==3 else 'Normalized power'));body+=f'<img src="{f}" width="920">'
 if t==5:
  power=normalized(out,5)[0];bin=int(np.rint(job['targets'][0]['velocity']/VELOCITY_STEP))%32 if job['targets'] else 6
  _,_,avg=M.cfar_2d(power.T,alpha=490007/65536);threshold=avg.T*(490007/65536)
  f=job['id']+'-power-threshold.svg';(d/f).write_text(line_svg(f'Natural bin {bin}: derived threshold, actual Power',np.arange(3,110)*RANGE_STEP,{'FPGA Power':power[bin,3:110],'Derived CA-CFAR threshold':threshold[bin,3:110]},'Range (m)','Normalized power'));body+='<p>آستانه زیر از نقشه توان و ضریب ثابت CFAR بازسازی شده است؛ رجیستر آستانه از FPGA خوانده نشده است. ماسک بالا واقعاً از FPGA دریافت شده است.</p>'+f'<img src="{f}" width="920">'
 if t==6:
  body+=table(['منبع','شناسه','سلول برد','bin داپلر','سرعت m/s','سلول‌های کلاستر'],[[name,r['record_id'],r['range_bin'],r['doppler_bin'],fmt(r['signed_doppler_bin']*VELOCITY_STEP),r['cluster_cells']] for name,records in [('FPGA',out),*refs.items()] for r in records])
 body+='<h2>'+('مقایسه تجمعی از IQ خام؛ نمودارهای بالا همین مقایسه را نشان می‌دهند' if job['scope']=='accumulated' else 'مقایسه مستقل با همان ورودی تزریق‌شده')+'</h2>'
 body+=table(['مرجع','معیار','مقدار'],[[k,m,fmt(v)] for k,vals in (job['full_chain_metrics'] if job['scope']=='accumulated' else job['metrics']).items() for m,v in vals.items()])
 if job['scope']=='accumulated':
  body+='<h3>تفکیک سهم بلوک آخر با ورودی سخت‌افزاری یکسان</h3>'+table(['مرجع','معیار','مقدار'],[[k,m,fmt(v)] for k,vals in job['metrics'].items() for m,v in vals.items()])
 (d/(job['id']+'.html')).write_text(page(job['case']+' / '+FA[t],body))
def summary_chart(job,d):
 z=np.load(d/job['artifact']);stage=job['stage'];entry=job['entry'];rows=z['input_words'].size//128
 inp=decode(z['input_words'],entry,rows);out=decode(z['output_words'],stage,rows-1 if stage==2 else rows)
 prefix='chain_' if job['scope']=='accumulated' else 'ref_'
 metrics=job['full_chain_metrics'] if job['scope']=='accumulated' else job['metrics'];refs={}
 for label in metrics:
  key=prefix+label.replace(' ','_')
  if stage<=4:refs[label]=z[key]
  elif stage==5:refs[label]=(z[key+'_power'],z[key+'_mask'])
  else:refs[label]=job['record_references'][('chain ' if prefix=='chain_' else 'ref ')+label]
 label=next(k for k in refs if 'Fixed' in k)
 if stage in (5,6):
  a=map_array(out,stage)>0;b=map_array(refs[label],stage,'Fixed' in label)>0
  combined=np.where(a&b,1,np.where(a,2,np.where(b,3,0)))
  svg=heat_svg(('CFAR decisions' if stage==5 else 'Cluster peaks')+' vs '+label+' | 0 none; 1 common; 2 FPGA-only; 3 ref-only',combined,stage,(0,3))
  caption='نقشه مقایسه '+('ماسک CFAR' if stage==5 else 'قله کلاسترها')+' با '+label+'؛ کد ۱ مشترک، ۲ فقط FPGA و ۳ فقط مرجع است.'
 else:
  a=normalized(out,stage);rr={k:normalized(v,stage,'Fixed' in k) for k,v in refs.items()}
  if stage<=2:
   curves={'FPGA output RMS':np.sqrt(np.mean(abs(a)**2,axis=0))}
   curves.update({k:np.sqrt(np.mean(abs(v)**2,axis=0)) for k,v in rr.items()})
   if stage==2:curves={'Actual MF input RMS':np.sqrt(np.mean(abs(normalized(inp,entry))**2,axis=0)),**curves}
   svg=line_svg('MTI before / after' if stage==2 else 'Matched-filter range response',np.arange(128)*RANGE_STEP,curves,'Range (m)','RMS normalized amplitude')
   caption='پروفایل RMS دامنه روی PRIها؛ '+('ورودی MF و خروجی MTI همراه مراجع روی محور برد.' if stage==2 else 'خروجی فیلتر منطبق FPGA و مراجع روی محور برد.')
  else:
   cell=job['targets'][0]['delay'] if job['targets'] else int(np.argmax(np.sum(abs(a),axis=0)))
   curves={'FPGA':np.fft.fftshift(abs(a[:,cell]) if stage==3 else a[:,cell])};curves.update({k:np.fft.fftshift(abs(v[:,cell]) if stage==3 else v[:,cell]) for k,v in rr.items()})
   svg=line_svg('Spectrum at shared range cell '+str(cell),np.arange(-16,16)*VELOCITY_STEP,curves,'Radial velocity (m/s)','Normalized amplitude' if stage==3 else 'Normalized power')
   caption='طیف '+('دامنه FFT' if stage==3 else 'توان')+' FPGA و مراجع در سلول برد مشترک '+str(cell)+'؛ محل برش از حقیقت هدف انتخاب شده است.'
 if stage>=3:
  label=next((k for k in refs if k=='MATLAB Fixed'),next(k for k in refs if 'Fixed' in k))
  a=map_array(out,stage);b=map_array(refs[label],stage,'Fixed' in label)
  if stage==3:a=np.sqrt(a);b=np.sqrt(b)
  hi=max(float(a.max()),float(b.max()));hi=hi if hi>0 else 1.
  if stage in (5,6):hi=1.
  unit='normalized amplitude' if stage==3 else 'normalized power' if stage==4 else 'decision 0/1' if stage==5 else 'cluster peak 0/1'
  panels=[]
  for title,data in [('FPGA',a),(label,b)]:
   panel=heat_svg(title+' | '+unit,data,stage,(0,hi))
   bar=''
   for k in range(100):
    q=k/99;color=f'rgb({int(255*q)},{int(235*np.sqrt(q))},{int(100+120*(1-q))})'
    bar+=f'<rect x="895" y="{65+(99-k)*2.6}" width="14" height="2.7" fill="{color}"/>'
   panel=panel.replace('</g></svg>',bar+text(800,355,'Color scale: 0 .. '+fmt(hi),12)+'</g></svg>');panels.append(panel)
  contents=[panel.split('>',1)[1].rsplit('</svg>',1)[0] for panel in panels]
  svg='<svg xmlns="http://www.w3.org/2000/svg" width="1840" height="400" viewBox="0 0 1840 400"><g>'+contents[0]+'</g><g transform="translate(920 0)">'+contents[1]+'</g></svg>'
  caption='خروجی FPGA و '+label+' در صفحه برد–سرعت؛ '+unit+' با مقیاس رنگ مشترک و راهنمای رنگی. دامنه و توان در مقیاس عددی نرمال‌شده سامانه هستند.'
  if stage in (3,4):
   # Shared normalization preserves FPGA/reference gain differences.
   pass
 file=job['id']+'-summary.svg';(d/file).write_text(svg)
 return '<p>'+esc(caption)+'</p><p align="center"><img src="'+file+'" width="920"></p>'
def render_report(state,d):
 body='<p>گزارش بر پایه ورودی بازخوانی‌شده و خروجی واقعی UART تهیه شده است. هیچ خروجی نرم‌افزاری جای خروجی FPGA قرار نگرفته است.</p>'
 body+=table(['وضعیت اجرا','آزمون تکمیل‌شده / برنامه','زمان اجرا s'],[[state['status'],str(len(state['jobs']))+' / '+str(state['planned_jobs']),fmt(state.get('elapsed_s'))]])
 fixed=[]
 for job in state['jobs']:
  for label,m in (job['full_chain_metrics'] if job['scope']=='accumulated' else job['metrics']).items():
   if 'Fixed' in label:fixed.append(bool(m.get('exact_integer',m.get('exact_decisions',m.get('record_signatures_exact',False)))))
 body+='<article>جمع‌بندی مقایسه عددی: '+str(sum(fixed))+' مقایسه Fixed از '+str(len(fixed))+' مقایسه انجام‌شده، برابری کامل داشت. وضعیت اجرای مجموعه: '+esc(state['status'])+'.</article>'
 body+='<p>نتیجه برابری با مرجع Fixed، عملکرد تفکیک دو هدف و پذیرش آماری سه موضوع جدا هستند. عدم تفکیک دو هدف در هر دو مسیر، خطای پیاده‌سازی معرفی نمی‌شود.</p>'
 if state.get('error'):body+='<article class="warn">آزمون متوقف شد: '+esc(state['error'])+'</article>'
 if 'statistics' in state:
  stats=state['statistics'];body+='<h2>بررسی آماری توسعه‌ای CFAR و کلاسترینگ</h2><p>تزریق این بخش: Power حاصل از FFT نرم‌افزاری Float. کلاسترینگ از ماسک واقعی CFAR سخت‌افزاری تغذیه می‌شود. این اعداد Pd/Pfa کل زنجیره خام نیستند.</p>'
  def ci(v):return 'ناموجود' if v is None else '['+fmt(v[0])+', '+fmt(v[1])+']'
  body+='<article>در '+str(stats['noise_CPIs'])+' CPI مستقل بدون هدف و '+str(stats['target_CPIs'])+' CPI دارای یک هدف، تصمیم واقعی CFAR و رکوردهای واقعی کلاسترینگ دریافت و مقایسه شدند. RMS نویز '+fmt(stats.get('noise_RMS'))+' و SNR بر پایه اکو فعال '+fmt(stats.get('active_echo_SNR_dB'))+' dB بود.</article>'
  body+=table(['معیار','برآورد','فاصله اطمینان ۹۵٪ / توضیح'],[
   ['Pfa سلولی CFAR',fmt(stats['cell_Pfa']),ci(stats['cell_Pfa_95pct_CPI_Hoeffding'])+'؛ کران محافظه‌کارانه بر پایه CPI'],
   ['احتمال وجود حداقل یک هشدار در CPI بدون هدف',fmt(stats['CPI_any_false_alarm_probability']),ci(stats['CPI_any_false_alarm_95pct'])],
   ['میانگین کلاستر کاذب در هر CPI',fmt(stats['false_clusters_per_CPI']),'این کمیت احتمال سلولی نیست'],
   ['Pd هدف تعریف‌شده در CFAR',fmt(stats['CFAR_Pd']),ci(stats['CFAR_Pd_95pct'])],
   ['Pd پس از کلاسترینگ',fmt(stats['Grouping_Pd']),ci(stats['Grouping_Pd_95pct'])],
   ['تعداد سلول معتبر در هر CPI',2782,'سلول‌های هم‌بسته، آزمایش مستقل شمرده نشدند']])
  obs=stats.get('observations',{})
  if obs.get('noise'):
   n=len(obs['noise']);x=np.arange(1,n+1);pfa=np.cumsum([v['false_alarm_cells'] for v in obs['noise']])/(2782*x)
   name='statistics-pfa-summary.svg';(d/name).write_text(line_svg('CFAR cell false-alarm fraction | independent CPIs',x,{'Cumulative cell Pfa':pfa},'Independent noise CPI count','Cell fraction'));body+='<img src="'+name+'" width="920">'
  if obs.get('target'):
   n=len(obs['target']);x=np.arange(1,n+1);curves={key:np.cumsum([v[field] for v in obs['target']])/x for key,field in [('CFAR','cfar_detected_targets'),('Grouping','grouping_detected_targets')]}
   name='statistics-pd-summary.svg';(d/name).write_text(line_svg('Defined-target detection fraction | independent CPIs',x,curves,'Independent target CPI count','Detected target fraction'));body+='<img src="'+name+'" width="920">'
  body+='<p>هر CPI نویز مستقل دارد؛ سلول‌های یک CPI مستقل فرض نشده‌اند. بازه Pfa سلولی از کران محافظه‌کارانه CPIهای مستقل محاسبه شده و ممکن است بسیار باز باشد. یک مقدار کم بدون فاصله اطمینان کافی، پذیرش آماری نیست.</p>'
 for scope,title in [('accumulated','رفتار تجمعی زنجیره از IQ خام'),('isolated','آزمون مستقل بلوک‌ها و تفکیک برد و سرعت'),('statistics','تکرارهای مستقل آماری')]:
  subset=[j for j in state['jobs'] if j['scope']==scope]
  if not subset:continue
  body+='<h2>'+title+'</h2>'
  for job in subset:
   job_details(job,d);body+='<article><b>'+esc(job['case']+' / '+FA[job['stage']])+'</b><p>'+esc(sentence(job))+'</p><p>'+esc(function_text(job['functional']))+'</p>'+summary_chart(job,d)+'<p><a href="'+job['id']+'.html">مشاهده نمودارها، داده‌ها و مقایسه مراجع</a></p></article>'
 body+='<h2>شرایط و حدود آزمون</h2><p>دامنه‌ها نرمال‌شده‌اند، توان وات نیست. هدف‌ها در مدل stop-and-hop هستند. پنجره CFAR معتبر 107×26 سلول و ناحیه داپلر طبیعی 3..28 است؛ هدف ساکن و بسیار کند الزاماً در این ناحیه قرار نمی‌گیرد. آزمون MTI ساکن برای اندازه‌گیری تضعیف است، نه انتظار آشکارسازی نهایی. فایل‌های JSON/NPZ کنار گزارش، داده و شواهد دقیق را نگه می‌دارند.</p>'
 (d/'index.html').write_text(page('گزارش آزمون خودکار AX309',body));return d/'index.html'
def render_normal(state,d,power,codes,truth,refs):
 from .auto_metrics import association
 description='فایل IQ با حقیقت هدف نامشخص' if state['metadata'].get('truth')=='Not supplied' else target_sentence(state['metadata'].get('targets',[]))
 body='<article>'+esc(description)+' از IQ خام به نسخه کامل پایدار سخت‌افزار تزریق و خروجی نهایی کلاسترینگ دریافت شد. '+esc(metric_text(state['metrics']))+'</article>'
 body+='<p>ورودی بایت‌به‌بایت کنترل شد؛ COMMIT دریافت و CPI آزاد شد. معیار تطبیق یک‌به‌یک: ±2 سلول برد و ±1 بین داپلر.</p>'
 body+=table(['منبع','هدف تطبیق‌یافته','هدف تعریف‌شده','کلاستر بدون تطبیق'],[[name,a['matched_targets'],a['defined_targets'],a['unassociated_clusters']] for name,a in [('FPGA',state['association']),*state['reference_association'].items()]])
 for name,records in [('FPGA',state['hardware_records']),*refs.items()]:
  arr=map_array(records,6);file=name.replace(' ','_')+'-clusters.svg';(d/file).write_text(heat_svg(name+' cluster peaks',arr,6));body+='<h2>'+esc(name)+'</h2>'+f'<img src="{file}" width="920">'
  body+=table(['شناسه','برد m','سرعت m/s','سلول‌های کلاستر'],[[r['record_id'],fmt(r['range_bin']*RANGE_STEP),fmt(r['signed_doppler_bin']*VELOCITY_STEP),r['cluster_cells']] for r in records])
 file='actual-power.svg';(d/file).write_text(heat_svg('Actual FPGA Power | normalized power',np.fft.fftshift(power/(1<<30),axes=0),4));body+='<h2>توان واقعی دریافت‌شده</h2>'+f'<img src="{file}" width="920">'
 body+=table(['مرجع','معیار','نتیجه'],[[k,m,fmt(v)] for k,a in state['metrics'].items() for m,v in a.items()]);body+='<p>این اجرای سناریو، برآورد آماری Pd/Pfa نیست. فایل ورودی بدون مشخصات حقیقت هدف، فقط برای مقایسه FPGA و مراجع قابل استفاده است.</p>'
 (d/'index.html').write_text(page('مقایسه خروجی نهایی کلاسترینگ AX309',body));return d/'index.html'

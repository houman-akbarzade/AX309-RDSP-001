function stage_lab_ref(inputfile,outputfile,entry,target,fixed)
% Independent MATLAB stage arithmetic; FFT fixed invokes official vendor C model.
s=load(inputfile);a=s.input_a;
if entry==5,a={a,logical(s.input_mask)};end
if ~fixed
 if entry<=3,a=double(a)/32768;
 elseif entry==4,a=double(a)/2^30;
 else,a={double(a{1})/2^30,a{2}};end
end
for stage=entry+1:target
 switch stage
 case 1
  if fixed
   taps=complex([30425 15800 -2811 -17869 -27020 -31238 -32568 -32766 -32766 -32568 -31238 -27020 -17869 -2811 15800 30425],[12167 28707 32647 27467 18538 9896 3612 402 402 3612 9896 18538 27467 32647 28707 12167]);out=zeros(size(a));
   for p=1:size(a,1)
    for r=1:128
     ar=int64(0);ai=int64(0);
     for k=0:15
      idx=r+15-k;
      if idx>128,continue;end
      ir=int64(real(a(p,idx)));ii=int64(imag(a(p,idx)));
      hr=int64(real(taps(k+1)));hi=int64(imag(taps(k+1)));
      ar=ar+ir*hr-ii*hi;ai=ai+ir*hi+ii*hr;
     end
     qr=rne(double(ar),32768);qi=rne(double(ai),32768);
     out(p,r)=complex(max(-2^21,min(2^21-1,qr)),max(-2^21,min(2^21-1,qi)));
    end
   end
   a=out;
  else
   t=((0:15)+.5)/1e6;phase=2*pi*(-125e3*t+.5*250e3/(16/1e6)*t.^2);
   h=conj(fliplr(exp(1i*phase)));out=zeros(size(a));
   for p=1:size(a,1),z=conv(a(p,:),h);out(p,:)=z(16:143);end
   a=out;
  end
 case 2
  a=a(2:end,:)-a(1:end-1,:);
 case 3
  if fixed
   if exist('stage_fft_fixed_mex','file')~=3
    root=fileparts(mfilename('fullpath'));mex('-R2017b','-outdir',root,fullfile(root,'stage_fft_fixed_mex.cpp'),'-ldl');
   end
   a=stage_fft_fixed_mex(complex(double(real(a)),double(imag(a))));
  else,a=fft(a,32,1)/8;end
 case 4
  if fixed
   re=int64(real(a));im=int64(imag(a));a=min(uint64(re.*re+im.*im),uint64(2^46-1));
  else,a=abs(a).^2;end
 case 5
  power=a;mask=false(32,128);
  for r=4:110
   for b=4:29
    if fixed,train=uint64(0);else,train=0;end
    for dr=-3:3
     for db=-3:3
      if abs(dr)<=1 && abs(db)<=1,continue;end
      train=train+power(b+db,r+dr);
     end
    end
    if fixed
     % 72-bit exact comparison. Never cast the wide products through double.
     cut=fi(power(b,r),0,46,0,'OverflowAction','Saturate','RoundingMethod','Floor');
     sm=fi(train,0,52,0,'OverflowAction','Saturate','RoundingMethod','Floor');
     left=fi(fi(cut*fi(uint64(40*65536),0,22,0),0,72,0),0,72,0);
     right=fi(fi(sm*fi(uint64(490007),0,19,0),0,72,0),0,72,0);
     mask(b,r)=left>right;
    else,mask(b,r)=power(b,r)>7.476912055027923*train/40;end
   end
  end
  a={power,mask};
 case 6
  power=a{1};mask=a{2};seen=false(size(mask));records=struct([]);
  for r=1:128
   for b=1:32
    if ~mask(b,r)||seen(b,r),continue;end
    queue=zeros(4096,2);queue(1,:)=[b r];seen(b,r)=true;head=1;tail=1;
    while head<=tail
     bb=queue(head,1);rr=queue(head,2);head=head+1;
     for dr=-1:1
      for db=-1:1
       nr=rr+dr;nb=bb+db;
       if nr>=1&&nr<=128&&nb>=1&&nb<=32&&mask(nb,nr)&&~seen(nb,nr)
        tail=tail+1;queue(tail,:)=[nb nr];seen(nb,nr)=true;
       end
      end
     end
    end
    cells=queue(1:tail,:);vals=zeros(tail,1,'like',power);
    for k=1:tail,vals(k)=power(cells(k,1),cells(k,2));end
    peak=max(vals);choices=cells(vals==peak,:);sb=choices(:,1)-1;sb(sb>=16)=sb(sb>=16)-32;
    [~,order]=sortrows([sb choices(:,2)-1 choices(:,1)-1],[1 2 3]);chosen=choices(order(1),:);
    rr=chosen(2)-1;bb=chosen(1)-1;signed=bb;if signed>=16,signed=signed-32;end
    rec=struct('record_id',0,'range_bin',rr,'doppler_bin',bb,'signed_doppler_bin',signed,'cluster_cells',tail,'tie_flag',sum(vals==peak)>1,'max_equal_power_cells',sum(vals==peak));
    if fixed,rec.power_stored_integer=peak;else,rec.power_linear=peak;end
    records=[records rec];
   end
  end
  if ~isempty(records)
   [~,ord]=sortrows([[records.range_bin]' [records.signed_doppler_bin]'],[1 2]);records=records(ord);
   for k=1:numel(records),records(k).record_id=k-1;end
  end
  a=records;
 end
end
if target==5
 result_power=a{1};result_mask=a{2};save(outputfile,'result_power','result_mask','-v7');
else,result=a;save(outputfile,'result','-v7');end
end
function q=rne(x,d)
 ax=abs(x);q=floor(ax/d);r=rem(ax,d);q=sign(x).*(q+(r>d/2 | (r==d/2 & mod(q,2)==1)));
end

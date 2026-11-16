function out = ax309_fixed(iq, gain)
% مدل Fixed-Point منتخب برای AX309؛ با Xilinx FFT v7.1 واقعی
% ورودی: آرایه مختلط Float 33x128 یا int16 با ابعاد 33x128x2
% اگر ورودی مختلط باشد: ابتدا بر gain تقسیم و سپس Q1.15 با RNE کوانتیزه می‌شود.
% بخش MF/MTI و Power/CFAR/Grouping در MATLAB از محاسبات صحیح استفاده می‌کند.
% FFT با فراخوانی کتابخانه بیت‌دقیق Xilinx از طریق رابط Python اجرا می‌شود.
% این کد بدون محیط Xilinx و Python قابل اجرای مستقل نیست.
if nargin<2 || isempty(gain);gain=1;end
if isreal(iq) && ndims(iq)==3 && isequal(size(iq),[33,128,2])
    q=int64(iq); assert(all(q(:)>=-32768 & q(:)<=32767));
    input_clips=0;
else
    assert(isequal(size(iq),[33,128]) && isfinite(gain) && gain>0);
    a=zeros(33,128,2);
    a(:,:,1)=real(iq)/gain; a(:,:,2)=imag(iq)/gain;
    rounded=ax309_rne_float(a*32768);
    input_clips=nnz(rounded < -32768 | rounded > 32767);
    q=int64(min(32767,max(-32768,rounded)));
end
here=fileparts(mfilename('fullpath'));root=fileparts(here);
c=jsondecode(fileread(fullfile(root,'engineering','s04_numeric', ...
    'S04-C02-coeff-shift-quant-analysis-v0.3.json')));
taps=c.formats.C_hypothetical.mf16;
coeff=zeros(16,2,'int64');
for k=1:16;coeff(k,:)=int64(taps(k).stored_integer);end
mf=zeros(33,128,2,'int64');mfclip=0;
for p=1:33
 for r=1:128
  re=int64(0);im=int64(0);
  for k=1:16
   idx=r+16-k; % هم‌ترازی کانولوشن با تأخیر r-1
   if idx>128;continue;end
   ir=q(p,idx,1);ii=q(p,idx,2);
   hr=coeff(k,1);hi=coeff(k,2);
   re=re + ir*hr - ii*hi;
   im=im + ir*hi + ii*hr;
  end
  y=[ax309_rne_int(re,int64(32768)),ax309_rne_int(im,int64(32768))];
  mfclip=mfclip+nnz(y<-(2^21) | y>(2^21-1));
  mf(p,r,1)=min(int64(2^21-1),max(int64(-2^21),y(1)));
  mf(p,r,2)=min(int64(2^21-1),max(int64(-2^21),y(2)));
 end
end
mt=mf(2:end,:,:)-mf(1:end-1,:,:);
mtclip=nnz(mt<-(2^22) | mt>2^22-1);
mt=min(int64(2^22-1),max(int64(-2^22),mt));

% رابط فایل دودویی MATLAB/Python؛ ساختارها کاملاً مشخص و قابل بررسی‌اند.
infile=[tempname,'.bin'];outfile=[tempname,'.bin'];overfile=[tempname,'.txt'];
cleanup=onCleanup(@() cleanup_files({infile,outfile,overfile}));
fid=fopen(infile,'w','ieee-le');assert(fid~=-1,'Cannot create FFT input');
cnt=fwrite(fid,permute(mt,[3,2,1]),'int64');fclose(fid);
assert(cnt==32*128*2);
bridge=fullfile(here,'fft_vendor_bridge.py');
cmd=sprintf('env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 "%s" --input "%s" --output "%s" --overflow "%s"', ...
    bridge,infile,outfile,overfile);
[status,msg]=system(cmd);
if status~=0;error('Xilinx C-model FFT bridge failed: %s',msg);end
fid=fopen(outfile,'r','ieee-le');assert(fid~=-1);
v=fread(fid,128*32*2,'*int64');fclose(fid);
assert(numel(v)==128*32*2,'Bad FFT output');
fftcode=permute(reshape(v,[2,32,128]),[3,2,1]);
fft_overflow=str2double(strtrim(fileread(overfile)));
assert(isfinite(fft_overflow) && fft_overflow>=0);

% توان صحیح U46: مربع‌های 25بیتی در int64 جا می‌شوند.
power=zeros(128,32,'uint64');powerclip=0;
hi=int64(2^46-1);
for r=1:128
 for b=1:32
  vr=fftcode(r,b,1);vi=fftcode(r,b,2);
  assert(abs(vr)<2^24 && abs(vi)<2^24);
  total=vr*vr+vi*vi;
  powerclip=powerclip+double(total>hi);
  power(r,b)=uint64(min(total,hi));
 end
end

% مقایسه دقیق CA-CFAR بدون تبدیل محصول 72بیتی به double
mask=false(128,32); valid=false(128,32);
training=zeros(128,32,'uint64');
for r=4:110
 for b=4:29
  total=uint64(0);
  for dr=-3:3
   for db=-3:3
    if abs(dr)>1 || abs(db)>1
     total=total+power(r+dr,b+db);
    end
   end
  end
  valid(r,b)=true;
  training(r,b)=total;
  % 40*CUT*65536 > 490007*SUM40 ؛ مساوی بودن هشدار نیست
  mask(r,b)=ax309_widemul_greater(uint64(40)*power(r,b),uint64(65536), ...
                                  total,uint64(490007));
 end
end
records=ax309_grouping(mask,power);
out=struct('iq_codes',q,'mf_codes',mf,'mti_codes',mt,'fft_codes',fftcode, ...
 'power_codes',power,'cfar_mask',mask,'valid_mask',valid, ...
 'train_sum40',training,'records',records,'cfar_alarm_count',nnz(mask), ...
 'input_clips',input_clips,'mf_clips',mfclip,'mti_clips',mtclip, ...
 'fft_overflows',fft_overflow,'power_clips',powerclip, ...
 'input_gain',gain,'model','MATLAB integer MF/MTI/CFAR + actual Xilinx FFT C-model');
end

function y=ax309_rne_float(x)
% گردکردن به نزدیک‌ترین عدد زوج در نیمه‌ها، پیش از اشباع
a=abs(x);q=floor(a);fraction=a-q;
y=sign(x).*(q + double(fraction>0.5 | (fraction==0.5 & mod(q,2)==1)));
end

function y=ax309_rne_int(x,d)
% RNE صحیح؛ در مقادیر منفی نیز تقارن حفظ می‌شود.
assert(isa(x,'int64') && isa(d,'int64') && d>0);
a=abs(x);q=idivide(a,d,'floor');r=rem(a,d);
q=q+int64(2*r>d || (2*r==d && bitand(q,int64(1))~=0));
if x<0;q=-q;end
y=q;
end

function greater=ax309_widemul_greater(a,b,c,d)
% ضرب دقیق 64×20 بیت با دو کلمه 32بیتی. هیچ تبدیل float رخ نمی‌دهد.
% برای چهار ورودی نامنفی و در بازه‌های قراردادی CFAR تعریف شده است.
mask=uint64(2^32-1);
x=a; y=b; lowpart=bitand(x,mask)*y;
left_hi=bitshift(x,-32)*y + bitshift(lowpart,-32);
left_lo=bitand(lowpart,mask);
x=c; y=d; lowpart=bitand(x,mask)*y;
right_hi=bitshift(x,-32)*y + bitshift(lowpart,-32);
right_lo=bitand(lowpart,mask);
greater=left_hi>right_hi || (left_hi==right_hi && left_lo>right_lo);
end

function cleanup_files(paths)
for i=1:numel(paths)
 if isfile(paths{i});delete(paths{i});end
end
end

% نمایش آموزشی زنجیره Float و Fixed-Point در MATLAB R2024a
% بدون بازنویسی سناریو یا استفاده از Seed متفاوت، همان IQ ذخیره‌شده بازپخش می‌شود.
here=fileparts(mfilename('fullpath'));addpath(here);
f=fullfile(here,'testvectors','target_float_iq.f64');
fid=fopen(f,'r','ieee-le');assert(fid>0,'Missing saved reference IQ');
v=fread(fid,33*128*2,'*double');fclose(fid);
a=permute(reshape(v,[2,128,33]),[3,2,1]);
x=complex(a(:,:,1),a(:,:,2));
disp('Running S03 Float model...');
F=ax309_float(x);
disp('Running S04 selected FFT-IP fixed model...');
Q=ax309_fixed(x,1);
fprintf('Float CFAR alarms: %d, clusters: %d\n',F.cfar_alarm_count,numel(F.records));
fprintf('Fixed CFAR alarms: %d, clusters: %d\n',Q.cfar_alarm_count,numel(Q.records));
fprintf('Fixed clips/overflows: input=%d MF=%d MTI=%d FFT=%d Power=%d\n', ...
 Q.input_clips,Q.mf_clips,Q.mti_clips,Q.fft_overflows,Q.power_clips);
figure('Name','AX309 Float reference','NumberTitle','off');
imagesc(0:31,0:127,10*log10(F.power+1));axis xy;
xlabel('Doppler bin (0-based)');ylabel('Range bin (0-based)');
title('S03 Floating-point range-Doppler Power (dB)');colorbar;
figure('Name','AX309 Fixed FFT-IP','NumberTitle','off');
imagesc(0:31,0:127,10*log10(double(Q.power_codes)+1));axis xy;
xlabel('Doppler bin (0-based)');ylabel('Range bin (0-based)');
title('S04 Fixed-point integer Power (dB, integer storage)');colorbar;

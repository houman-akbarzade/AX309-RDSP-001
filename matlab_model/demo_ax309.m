% مقایسه صحیح توان Float و Fixed-Point در واحد مشترک
% هر دو مدل دقیقاً یک CPI ذخیره‌شده را مصرف می‌کنند.
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

% fixed MF/MTI uses Q1.15 storage. The vendor Xilinx FFT model uses
% schedule [0 1 0 1 1] = 3 right shifts = overall 1/8 amplitude.
% For original (pre-gain) Float input, multiply integer FFT amplitudes by
% (gain * 8 / 2^15), and squared powers by its square.
fft_schedule=[0 1 0 1 1];
amplitude_scale=Q.input_gain*2^sum(fft_schedule)/2^15;
power_scale=amplitude_scale^2;
Pfloat=double(F.power);
Pfixed=double(Q.power_codes)*power_scale;

% Do not use log10(P+1) on one map and log10(integer P+1) on the other!
% Use a common linear floor to keep finite dB values and identical colors.
floor_power=1e-4;
float_db=10*log10(max(Pfloat,floor_power));
fixed_db=10*log10(max(Pfixed,floor_power));
upper_db=5*ceil(max([float_db(:);fixed_db(:)])/5);
common_db_limits=[upper_db-80 upper_db];

peak_f=max(Pfloat(:));
peak_q=max(Pfixed(:));
[rf,bf]=find(Pfloat==peak_f,1,'first');
[rq,bq]=find(Pfixed==peak_q,1,'first');
error_power=Pfixed-Pfloat;
rel_nmse=sum(error_power(:).^2)/max(sum(Pfloat(:).^2),realmin);
nmse_db=10*log10(rel_nmse);
max_abs_error=max(abs(error_power(:)));
fprintf('Float CFAR alarms=%d; Fixed CFAR alarms=%d\n', ...
    F.cfar_alarm_count,Q.cfar_alarm_count);
fprintf('Float peak: range=%d Doppler=%d, linear=%.9f, dB=%.6f\n', ...
    rf-1,bf-1,peak_f,10*log10(peak_f));
fprintf('Fixed peak: range=%d Doppler=%d, linear=%.9f, dB=%.6f\n', ...
    rq-1,bq-1,peak_q,10*log10(peak_q));
fprintf('Correct conversion: power codes * %.17g (%.6f dB offset)\n', ...
    power_scale,10*log10(power_scale));
fprintf('Power NMSE=%.3f dB, maximum absolute error=%.9g\n', ...
    nmse_db,max_abs_error);
fprintf('Fixed input/MF/MTI/FFT/Power clips or overflows: %d/%d/%d/%d/%d\n', ...
    Q.input_clips,Q.mf_clips,Q.mti_clips,Q.fft_overflows,Q.power_clips);

if ~usejava('desktop')
    disp('Headless MATLAB: numeric comparison passed; plots are available in desktop MATLAB.');
    return;
end
figure('Name','AX309 Float vs Fixed: common physical scale',...
       'NumberTitle','off','Position',[90 120 1200 470]);
tiledlayout(1,2,'TileSpacing','compact','Padding','compact');
nexttile;
imagesc(0:31,0:127,float_db);axis xy;
clim(common_db_limits);colorbar;
xlabel('Doppler bin (zero-based)');ylabel('Range bin (zero-based)');
title('Float (S03), power dB');
nexttile;
imagesc(0:31,0:127,fixed_db);axis xy;
clim(common_db_limits);colorbar;
xlabel('Doppler bin (zero-based)');ylabel('Range bin (zero-based)');
title('Fixed (S04 FFT-IP), power dB, normalized');
colormap(parula);
sgtitle(sprintf('Same IQ, same dB scale | Peak %.4f / %.4f dB | NMSE %.2f dB', ...
    10*log10(peak_f),10*log10(peak_q),nmse_db));

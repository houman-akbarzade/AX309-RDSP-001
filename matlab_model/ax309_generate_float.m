function iq = ax309_generate_float(targets,snr_db,seed,clutter)
% تولید سیگنال Float آموزشی مشابه S03 با مشخصات فیزیکی ثابت پروژه
% هر سطر targets: [delay_sample, velocity_m_s, amplitude_real, amplitude_imag, phase_rad]
% تولید تصادفی MATLAB از نظر نمونه‌به‌نمونه با NumPy PCG64 برابر نیست.
if nargin<1 || isempty(targets);targets=zeros(0,5);end
if nargin<2;snr_db=[];end
if nargin<3 || isempty(seed);seed=12345;end
if nargin<4;clutter=[];end
assert(size(targets,2)==5);
fs=1e6;fc=10e9;c_nominal=3e8;PRI=.001;L=16;N=128;P=33;B=250e3;
t=((0:L-1)+.5)/fs;
chirp=exp(1i*2*pi*((-B/2)*t+.5*(B/(L/fs))*t.^2));
iq=complex(zeros(P,N));
for j=1:size(targets,1)
 delay=targets(j,1);v=targets(j,2);
 amp=complex(targets(j,3),targets(j,4));phase=targets(j,5);
 assert(delay>=0 && delay<=N-L && fix(delay)==delay);
 fd=2*v*fc/c_nominal;
 slow=(0:P-1).';
 factor=amp.*exp(1i*(2*pi*fd*PRI*slow+phase));
 iq(:,delay+(1:L))=iq(:,delay+(1:L))+factor*chirp;
end
if ~isempty(clutter)
 assert(isequal(size(clutter),[1,N]));
 iq=iq+repmat(clutter,P,1);
end
if ~isempty(snr_db)
 assert(~isempty(targets),'SNR noise requires a target');
 amps=hypot(targets(:,3),targets(:,4));
 assert(max(abs(amps-amps(1)))<1e-12,'Common SNR requires equal target amplitudes');
 sigma2=amps(1)^2/10^(snr_db/10);
 stream=RandStream('mt19937ar','Seed',seed);
 iq=iq+sqrt(sigma2/2)*(randn(stream,P,N)+1i*randn(stream,P,N));
end
end

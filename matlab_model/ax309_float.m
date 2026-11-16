function out = ax309_float(iq, alpha)
% مرجع Float برای زنجیره S03، مطابق s03_reference/model.py
% ورودی: ماتریس مختلط 33x128 به ترتیب پالس × سلول فاصله
% خروجی: MF، MTI، FFT، Power، CFAR، رکوردهای Grouping
% این مدل بیت‌دقیق RTL یا Xilinx FFT-IP نیست.
if nargin < 2 || isempty(alpha)
    alpha = 7.476912055027923; % آلفای کالیبره‌شده S03، نه مقدار اولیه تحلیلی
end
assert(isequal(size(iq), [33,128]), 'Input must be complex 33x128');
assert(all(isfinite(real(iq(:))) & isfinite(imag(iq(:)))));
fs = 1e6; B = 250e3; L = 16; N = 128; c = 299792458;
t = ((0:L-1)+0.5)/fs;
chirp = exp(1i*2*pi*((-B/2).*t + 0.5*(B/(L/fs)).*t.^2));
h = conj(chirp(end:-1:1));
pc = complex(zeros(33,N));
for p = 1:33
    z = conv(double(iq(p,:)),h,'full');
    pc(p,:) = z(L:L+N-1);
end
mt = pc(2:end,:) - pc(1:end-1,:);
rd = fft(mt,32,1).'; % 128×32؛ بین‌ها به ترتیب طبیعی، بدون fftshift
power = abs(rd).^2;
mask = false(128,32);valid = false(128,32); noise = zeros(128,32);
drs = -3:3; dbs = -3:3;
% هندسه CFAR: پنجره 7×7 با حذف 3×3 مرکزی
for r = 4:110
    for b = 4:29
        train = 0;
        for dr = drs
            for db = dbs
                if abs(dr)>1 || abs(db)>1
                    train = train + power(r+dr,b+db);
                end
            end
        end
        valid(r,b)=true;
        noise(r,b) = train/40;
        mask(r,b) = power(r,b) > alpha*noise(r,b);
    end
end
records = ax309_grouping(mask,power);
% اندیس رکوردها در خروجی صفرمبنا هستند؛ در ماتریس MATLAB یک‌مبنا
for k=1:numel(records)
    records(k).range_m_exact = records(k).range_bin*c/(2*fs);
    records(k).power_linear = power(records(k).range_bin+1,records(k).doppler_bin+1);
end
out=struct('iq',iq,'mf',pc,'mti',mt,'fft',rd,'power',power, ...
    'cfar_mask',mask,'valid_mask',valid,'noise_estimate',noise, ...
    'records',records,'alpha',alpha,'cfar_alarm_count',nnz(mask), ...
    'model','S03 Float reference (not bit-true)');
end

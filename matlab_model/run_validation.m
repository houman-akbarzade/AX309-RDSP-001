function run_validation()
% مقایسه خروجی MATLAB با بردارهای مرجع تولیدشده از کد اصلی پروژه
here=fileparts(mfilename('fullpath'));
v=fullfile(here,'testvectors');
for name={'zero','target','noise'}
    stem=name{1};
    iq=load_float_iq(fullfile(v,[stem '_float_iq.f64']));
    floating=ax309_float(iq);
    expected_float=load_map_f64(fullfile(v,[stem '_float_power.f64']));
    err=max(abs(floating.power(:)-expected_float(:)));
    tolerance=1e-11*max(1,max(abs(expected_float(:))));
    assert(err<=tolerance,'Float Power mismatch in %s: %g',stem,err);
    q=load_iq_i16(fullfile(v,[stem '_iq.i16']));
    fixed=ax309_fixed(q);
    expected_mt=load_i64(fullfile(v,[stem '_mti.i64']),[2,128,32],[3,2,1]);
    expected_fft=load_i64(fullfile(v,[stem '_fft.i64']),[2,32,128],[3,2,1]);
    expected_power=load_power_u64(fullfile(v,[stem '_power.u64']));
    expected_mask=load_cfar(fullfile(v,[stem '_cfar.u8']));
    assert(isequal(fixed.mti_codes,expected_mt),'MTI mismatch');
    assert(isequal(fixed.fft_codes,expected_fft),'FFT mismatch');
    assert(isequal(fixed.power_codes,expected_power),'Power mismatch');
    assert(isequal(fixed.cfar_mask,expected_mask),'CFAR mismatch');
    expected_records=jsondecode(fileread(fullfile(v,[stem '_records.json'])));
    assert(numel(expected_records)==numel(fixed.records),'Grouping count mismatch');
    for k=1:numel(fixed.records)
        a=fixed.records(k);b=expected_records(k);
        assert(a.range_bin==b.range_bin && a.doppler_bin==b.doppler_bin ...
            && a.cluster_cells==b.cluster_cells && a.record_id==b.record_id, ...
            'Grouping record mismatch');
    end
    assert(fixed.input_clips==0 && fixed.mf_clips==0 ...
         && fixed.mti_clips==0 && fixed.fft_overflows==0 ...
         && fixed.power_clips==0,'Clipping or overflow');
    fprintf('PASS MATLAB %s: FLOAT_ERR=%g FIXED_CFAR=%d CLUSTERS=%d\n', ...
        stem,err,fixed.cfar_alarm_count,numel(fixed.records));
end
fprintf('PASS MATLAB FLOAT/FIXED: all retained validation vectors matched\n');
end

function x=load_float_iq(path)
fid=fopen(path,'r','ieee-le');assert(fid>0);
v=fread(fid,33*128*2,'*double');fclose(fid);assert(numel(v)==8448);
z=permute(reshape(v,[2,128,33]),[3,2,1]);
x=complex(z(:,:,1),z(:,:,2));
end
function x=load_iq_i16(path)
fid=fopen(path,'r','ieee-le');assert(fid>0);
v=fread(fid,33*128*2,'*int16');fclose(fid);assert(numel(v)==8448);
x=permute(reshape(v,[2,128,33]),[3,2,1]);
end
function y=load_i64(path,shape,order)
fid=fopen(path,'r','ieee-le');assert(fid>0);
v=fread(fid,prod(shape),'*int64');fclose(fid);assert(numel(v)==prod(shape));
y=permute(reshape(v,shape),order);
end
function y=load_power_u64(path)
fid=fopen(path,'r','ieee-le');assert(fid>0);
v=fread(fid,128*32,'*uint64');fclose(fid);
y=reshape(v,[32,128]).';
end
function y=load_map_f64(path)
fid=fopen(path,'r','ieee-le');assert(fid>0);
v=fread(fid,128*32,'*double');fclose(fid);
y=reshape(v,[32,128]).';
end
function y=load_cfar(path)
fid=fopen(path,'r');assert(fid>0);
v=fread(fid,128*32,'*uint8');fclose(fid);
y=logical(reshape(v,[32,128]).');
end

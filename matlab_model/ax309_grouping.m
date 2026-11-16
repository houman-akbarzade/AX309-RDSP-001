function records = ax309_grouping(mask,power)
% خوشه‌بندی 8-همسایه با مرزهای غیرچرخشی داپلر
% رکوردهای فاصله/داپلر با اندیس صفرمبنا ساخته می‌شوند.
assert(isequal(size(mask),[128,32]) && isequal(size(power),[128,32]));
seen = false(128,32);
tmpl=struct('range_bin',0,'doppler_bin',0,'signed_doppler_bin',0, ...
            'velocity_m_s_nominal',0,'cluster_cells',0,'tie_flag',false, ...
            'max_equal_power_cells',0,'record_id',0);
records=repmat(tmpl,1,0);
for r0=1:128
 for d0=1:32
  if ~mask(r0,d0) || seen(r0,d0);continue;end
  queue=zeros(4096,2); head=1;tail=1;
  queue(1,:)=[r0,d0]; seen(r0,d0)=true;
  while head<=tail
   r=queue(head,1);b=queue(head,2);head=head+1;
   for rr=max(1,r-1):min(128,r+1)
    for bb=max(1,b-1):min(32,b+1)
     if mask(rr,bb) && ~seen(rr,bb)
      seen(rr,bb)=true;tail=tail+1;queue(tail,:)=[rr,bb];
     end
    end
   end
  end
  members=queue(1:tail,:);
  inds=sub2ind([128,32],members(:,1),members(:,2));
  pp=double(power(inds));
  mx=max(pp); ties=find(pp==mx);
  sb=members(ties,2)-1;
  sb(sb>15)=sb(sb>15)-32;
  % تقدم: توان بیشینه؛ سپس داپلر علامت‌دار کمینه؛ سپس فاصله و بین
  candidates=[sb, members(ties,1)-1, members(ties,2)-1];
  [~,idx]=sortrows(candidates,[1,2,3]);
  peak=members(ties(idx(1)),:);
  b0=peak(2)-1;bs=b0;if bs>15;bs=bs-32;end
  x=tmpl;
  x.range_bin=peak(1)-1;x.doppler_bin=b0;x.signed_doppler_bin=bs;
  x.velocity_m_s_nominal=bs*0.46875;
  x.cluster_cells=tail;
  x.tie_flag=numel(ties)>1;
  x.max_equal_power_cells=numel(ties);
  records(end+1)=x; %#ok<AGROW>
 end
end
if ~isempty(records)
 indices=vertcat(records.range_bin);
 signed=vertcat(records.signed_doppler_bin);
 [~,order]=sortrows([indices,signed],[1,2]);
 records=records(order);
 for i=1:numel(records);records(i).record_id=i-1;end
end
end

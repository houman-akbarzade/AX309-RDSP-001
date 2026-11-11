"""Append-only conversation archive with source and completeness controls.

It cannot intercept ChatGPT messages. Call explicitly in each project turn,
then readback/verify; never rewrite historical lines.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import uuid

ROOT=Path(__file__).resolve().parent.parent
ARCHIVE=ROOT/'replay/conversations.jsonl'

def canonical(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')

def sha_text(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def parse_archive():
    original=ARCHIVE.read_bytes()
    rows=[]
    for n,line in enumerate(original.splitlines(),1):
        if not line.strip():
            raise ValueError('blank archived row '+str(n))
        d=json.loads(line.decode('utf-8'))
        if not isinstance(d,dict):
            raise ValueError('not a JSON object row '+str(n))
        rows.append(d)
    return original,rows

def append_many(entries):
    before,existing=parse_archive()
    used_refs={r.get('message_ref') for r in existing}
    used_full={(r.get('role'),r.get('content_sha256')) for r in existing
                  if r.get('completeness')=='FULL'}
    used_refs.discard(None)
    added=[]
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for e in entries:
        role=e['role']
        level=e['completeness']
        if role not in ('user','assistant') or level not in ('FULL','EXCERPT','SUMMARY'):
            raise ValueError('bad role/completeness')
        body=e['text']
        if not isinstance(body,str) or not body.strip():raise ValueError('empty text')
        if level=='FULL' and e['source_type'] not in ('current_chat_visible','user_provided_text','assistant_prepared_final'):
            raise ValueError('FULL requires directly available exact text')
        source_id=e['source_id']
        key=e['source_type']+'|'+source_id+'|'+role+'|'+level
        message_ref='s04-'+str(uuid.uuid5(uuid.NAMESPACE_URL,'AX309-RDSP-001|'+key))
        digest=sha_text(body)
        if message_ref in used_refs or (level=='FULL' and (role,digest) in used_full):
            continue
        row={
         'message_ref':message_ref,'role':role,'text':body,
         'completeness':level,'is_full_message':level=='FULL',
         'content_sha256':digest,'source_type':e['source_type'],
         'source_id':source_id,'source_note':e.get('source_note',''),
         'project_event_refs':e.get('project_event_refs',[]),
         'historical_time_utc':e.get('historical_time_utc'),
         'recorded_at_utc':now,
         'archive_schema_version':'s04-append-only-v1',
        }
        if level !='FULL':
            row['reconstructed_or_partial']=True
        added.append(row)
        used_refs.add(message_ref)
        if level=='FULL':used_full.add((role,digest))
    with ARCHIVE.open('ab',buffering=0) as f:
        for row in added:
            f.write(canonical(row)+b'\n')
        os.fsync(f.fileno())
    after,allrows=parse_archive()
    if not after.startswith(before):raise AssertionError('historical bytes mutated')
    if len(allrows)!=len(existing)+len(added):raise AssertionError('row count mismatch')
    for left,right in zip(added,allrows[len(existing):]):
        if canonical(left)!=canonical(right):raise AssertionError('readback changed content')
        if left['content_sha256']!=sha_text(right['text']):
            raise AssertionError('content sha mismatch')
    return {'prior_rows':len(existing),'added_rows':len(added),
            'total_rows':len(allrows),'added_by_completeness':{
             level:sum(x['completeness']==level for x in added)
             for level in ('FULL','EXCERPT','SUMMARY')},
            'archive_sha256':hashlib.sha256(after).hexdigest(),
            'prior_prefix_sha256':hashlib.sha256(before).hexdigest(),
            'all_added_refs':[x['message_ref'] for x in added]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--batch-json',required=True)
    args=ap.parse_args()
    data=json.loads(Path(args.batch_json).read_text())
    if not isinstance(data,list):raise ValueError('batch should be list')
    print(json.dumps(append_many(data),ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()

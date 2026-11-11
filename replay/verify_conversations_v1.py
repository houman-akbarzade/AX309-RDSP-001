"""Read-only integrity and coverage checker, understands legacy excerpt rows."""
import collections
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
CHAT=ROOT/'replay/conversations.jsonl'
EVENTS=ROOT/'replay/events.jsonl'

def inspect():
    data=CHAT.read_bytes()
    messages=[json.loads(s) for s in data.decode('utf-8').splitlines() if s.strip()]
    events=[json.loads(s) for s in EVENTS.read_text().splitlines() if s.strip()]
    event_ids={str(z.get('event_id')) for z in events}
    seen_refs=set()
    kinds=collections.Counter()
    roles=collections.Counter()
    missing_event_links=[]
    seen_keys=set()
    for idx,m in enumerate(messages,1):
        ref=m.get('message_ref')
        if not ref or ref in seen_refs:raise AssertionError('duplicate/missing message_ref '+str(idx))
        seen_refs.add(ref)
        roles[m.get('role')]+=1
        level=m.get('completeness','EXCERPT' if m.get('is_full_message') is False else 'UNKNOWN')
        kinds[level]+=1
        if 'text' in m:
            assert m.get('content_sha256')==hashlib.sha256(m['text'].encode('utf-8')).hexdigest()
            assert bool(m.get('is_full_message'))==(level=='FULL')
            assert m.get('source_type') and m.get('source_id')
            assert m.get('recorded_at_utc')
            for eid in m.get('project_event_refs',[]):
                if eid not in event_ids:
                    missing_event_links.append([ref,eid])
            if level=='FULL':
                key=(m['role'],m['content_sha256'])
                assert key not in seen_keys,'duplicate FULL text'
                seen_keys.add(key)
        else:
            assert m.get('is_full_message') is False
            assert 'verbatim_excerpt' in m
    assert not missing_event_links,missing_event_links
    return {'total_records':len(messages),'completeness_counts':dict(kinds),
            'role_counts':dict(roles),'full_sha_verified':kinds['FULL'],
            'project_event_links_all_valid':True,
            'jsonl_sha256':hashlib.sha256(data).hexdigest(),
            'legacy_excerpt_count':sum('verbatim_excerpt' in m for m in messages)}

if __name__=='__main__':
    print(json.dumps(inspect(),ensure_ascii=False,indent=2))

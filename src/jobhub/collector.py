from datetime import datetime, timezone
from pathlib import Path
from .core import normalize_job,score_job,deduplicate_jobs
from .classifier import classify_job, score_job_v2
from .sources import SourceAdapter, fetch_with_resilience
from .verifier import verify_job, deduplicate_jobs_v2, fingerprint

TARGET=('torino','turin','collegno','rivoli','remote','italy','italia')

def collect_jobs(fetchers,profile,existing=None):
    jobs=[]; run={'sources':{},'processed':0}
    for name,fetch in fetchers:
        try:
            raw=fetch(); run['sources'][name]={'ok':True,'count':len(raw)}
            for r in raw:
                j=normalize_job(r,name); loc=(j['location']+' '+j['work_mode']).lower(); score,why,gaps=score_job(j,profile)
                if score>=55 and (not loc or any(x in loc for x in TARGET)):
                    j.update(score=score,why=why,gaps=gaps,verification='PLAUSIBILE'); jobs.append(j)
        except Exception as e: run['sources'][name]={'ok':False,'error':type(e).__name__}
    jobs=deduplicate_jobs(jobs); jobs.sort(key=lambda x:x['score'],reverse=True); run['processed']=len(jobs)
    return jobs,run


def collect_jobs_v2(adapters, profile, previous_jobs=None, cache_dir=None, now=None):
    previous_jobs=list(previous_jobs or [])
    now=now or datetime.now(timezone.utc)
    cache_dir=Path(cache_dir or '.cache/jobhub')
    candidates=[]
    run={'sources':{},'fetched':0,'rejected_irrelevant':0,'rejected_expired':0,'deduplicated':0,'published':0,'stale_data':False}
    any_network_source_ok=False
    for adapter in adapters:
        if not isinstance(adapter,SourceAdapter):
            raise TypeError('collect_jobs_v2 requires SourceAdapter instances')
        raw,meta=fetch_with_resilience(adapter,cache_dir,now=now)
        run['sources'][adapter.name]=meta
        any_network_source_ok = any_network_source_ok or bool(adapter.network and meta.get('ok'))
        run['fetched'] += len(raw)
        for item in raw:
            j=normalize_job(item,adapter.name)
            j['source_kind']=item.get('source_kind') or adapter.source_kind
            attribution_url=item.get('source_url') or adapter.attribution_url or j.get('url')
            j['source_attribution']={'name':adapter.name,'url':attribution_url}
            classified=classify_job(j,profile)
            score,label,why,gaps,blockers=score_job_v2(classified,profile)
            classified.update(score=score,match_label=label,why=why,gaps=gaps,blockers=blockers)
            checked=verify_job(classified)
            if checked.get('verification')=='SCARTATO':
                run['rejected_expired']+=1; continue
            if label=='NON_PERTINENTE':
                run['rejected_irrelevant']+=1; continue
            candidates.append(checked)
    if not any_network_source_ok and not candidates and previous_jobs:
        run['stale_data']=True; run['published']=len(previous_jobs)
        return previous_jobs,run
    before=len(candidates)
    jobs=deduplicate_jobs_v2(candidates)
    run['deduplicated']=before-len(jobs)
    prev_by_fp={fingerprint(x):x for x in previous_jobs}
    ts=now.isoformat()
    for j in jobs:
        prev=prev_by_fp.get(fingerprint(j),{})
        j['first_seen_at']=prev.get('first_seen_at') or ts
        j['last_seen_at']=ts
        j['canonical_source']=j.get('source_attribution',{}).get('url') or j.get('url')
    jobs.sort(key=lambda x:(x.get('match_label')=='MATCH_FORTE',x.get('score',0)),reverse=True)
    run['published']=len(jobs)
    return jobs,run

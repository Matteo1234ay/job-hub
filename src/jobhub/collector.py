from .core import normalize_job,score_job,deduplicate_jobs
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

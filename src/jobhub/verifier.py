import re
from urllib.parse import urlsplit
from .core import canonical_url

CLOSED_SIGNALS=(
    'no longer accepting applications','position has been filled','job is closed','vacancy closed',
    'non accetta più candidature','non accettiamo più candidature','offerta scaduta','annuncio scaduto','posizione chiusa',
)
PRIORITY={'official':4,'ats':3,'aggregator':2,'discovery':1,'unknown':0}


def verify_job(job):
    out=dict(job)
    out['url']=canonical_url(out.get('url',''))
    text=f"{out.get('title','')} {out.get('description','')}".lower()
    parsed=urlsplit(out.get('url',''))
    if any(x in text for x in CLOSED_SIGNALS):
        out.update(verification='SCARTATO',active_status='closed')
        return out
    if parsed.scheme not in ('http','https') or not parsed.netloc or not out.get('company'):
        out.update(verification='DA_VERIFICARE',active_status='unknown')
        return out
    kind=out.get('source_kind') or 'unknown'
    verification='VERIFICATO' if kind in ('official','ats') else ('PLAUSIBILE' if kind in ('aggregator','discovery') else 'DA_VERIFICARE')
    out.update(verification=verification,active_status='active' if verification!='DA_VERIFICARE' else 'unknown')
    return out


def _norm(s):
    s=re.sub(r'\b(junior|jr\.?|senior|sr\.?)\b',' ',str(s or '').lower())
    return re.sub(r'[^a-z0-9]+',' ',s).strip()


def fingerprint(job):
    return f"{_norm(job.get('company'))}|{_norm(job.get('title'))}"


def deduplicate_jobs_v2(jobs):
    groups={}
    for j in jobs:
        key=fingerprint(j) or canonical_url(j.get('url',''))
        current=groups.get(key)
        if current is None:
            groups[key]=dict(j); continue
        curp=PRIORITY.get(current.get('source_kind','unknown'),0)
        newp=PRIORITY.get(j.get('source_kind','unknown'),0)
        if newp>curp:
            winner=dict(j); loser=current
        else:
            winner=current; loser=j
        alts=list(winner.get('alternate_sources') or [])
        alt={'source':loser.get('source'),'url':loser.get('url')}
        if alt not in alts: alts.append(alt)
        winner['alternate_sources']=alts
        groups[key]=winner
    return list(groups.values())

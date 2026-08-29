import hashlib, math, re
from urllib.parse import urlsplit, urlunsplit

def canonical_url(url):
    p=urlsplit((url or '').strip()); return urlunsplit((p.scheme,p.netloc,p.path.rstrip('/'),'',''))

def normalize_job(raw,source):
    title=str(raw.get('title') or '').strip(); company=str(raw.get('company') or raw.get('company_name') or '').strip(); url=canonical_url(raw.get('url') or raw.get('link') or '')
    key='|'.join([company.lower(),title.lower(),url.lower()]); jid=hashlib.sha256(key.encode()).hexdigest()[:16]
    return {'id':jid,'title':title,'company':company,'url':url,'location':str(raw.get('location') or '').strip(),'description':re.sub(r'<[^>]+>',' ',str(raw.get('description') or '')).strip(),'source':source,'published_at':raw.get('published_at') or raw.get('date') or '', 'work_mode':raw.get('work_mode') or ('remote' if raw.get('remote') else '')}

def haversine_km(lat1,lon1,lat2,lon2):
    if lat1==lat2 and lon1==lon2:return 0
    r=6371; p1,p2=map(math.radians,[lat1,lat2]); dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1); a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return r*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

def score_job(job,profile):
    text=' '.join(str(job.get(k,'')) for k in ('title','description')).lower(); hits=[k for k in profile.get('keywords',[]) if k.lower() in text]; bad=[k for k in profile.get('negative',[]) if k.lower() in text]
    score=min(100,35+len(hits)*18-len(bad)*35) if hits else max(0,20-len(bad)*20)
    return score,[f'Competenza richiesta: {x}' for x in hits[:4]],[f'Segnale penalizzante: {x}' for x in bad[:3]]

def deduplicate_jobs(jobs):
    seen=set(); out=[]
    for j in jobs:
        key=canonical_url(j.get('url','')).lower() or f"{j.get('company','').lower()}|{j.get('title','').lower()}"
        if key not in seen: seen.add(key); out.append(j)
    return out

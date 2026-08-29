from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import re
import time
import xml.etree.ElementTree as ET
import requests

UA={'User-Agent':'JobHub/2.0 (+personal job discovery; low-rate; contact via repository)'}

@dataclass
class SourceAdapter:
    name: str
    fetcher: callable
    max_requests_per_run: int = 1
    cache_ttl_hours: int = 24
    retry_count: int = 1
    backoff_seconds: float = 0.25
    source_kind: str = 'aggregator'
    attribution_url: str = ''
    network: bool = True

    def fetch(self):
        return self.fetcher()


def _cache_path(cache_dir, name):
    safe = re.sub(r'[^a-z0-9._-]+','-',name.lower()).strip('-') or 'source'
    return Path(cache_dir) / f'{safe}.json'


def _read_cache(path):
    try:
        data=json.loads(Path(path).read_text())
        return data if isinstance(data,dict) and isinstance(data.get('jobs'),list) else None
    except Exception:
        return None


def _write_cache(path, jobs, now):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps({'saved_at':now.isoformat(),'jobs':jobs},ensure_ascii=False,indent=2))


def _cache_is_fresh(cached, now, ttl_hours):
    if not cached or not cached.get('saved_at') or ttl_hours <= 0:
        return False
    try:
        saved=datetime.fromisoformat(str(cached['saved_at']).replace('Z','+00:00'))
        if saved.tzinfo is None: saved=saved.replace(tzinfo=timezone.utc)
        age=(now-saved).total_seconds()
        return 0 <= age < ttl_hours*3600
    except Exception:
        return False


def _status_code(exc):
    code=getattr(exc,'status_code',None)
    if code: return code
    response=getattr(exc,'response',None)
    return getattr(response,'status_code',None)


def fetch_with_resilience(adapter, cache_dir, now=None):
    now=now or datetime.now(timezone.utc)
    path=_cache_path(cache_dir,adapter.name)
    cached=_read_cache(path)
    if adapter.network and _cache_is_fresh(cached,now,adapter.cache_ttl_hours):
        return cached['jobs'],{'ok':True,'count':len(cached['jobs']),'requests':0,'cache_used':True,'cache_fresh':True,'source_kind':adapter.source_kind}
    requests_made=0
    last_error=None
    attempts=min(adapter.max_requests_per_run, adapter.retry_count+1)
    for attempt in range(max(0,attempts)):
        try:
            requests_made+=1
            jobs=adapter.fetch() or []
            if not isinstance(jobs,list): raise ValueError('source must return a list')
            _write_cache(path,jobs,now)
            return jobs,{'ok':True,'count':len(jobs),'requests':requests_made,'cache_used':False,'source_kind':adapter.source_kind}
        except Exception as exc:
            last_error=exc
            if _status_code(exc)==429:
                break
            if attempt+1 < attempts and adapter.backoff_seconds:
                time.sleep(adapter.backoff_seconds*(2**attempt))
    cached=_read_cache(path)
    if cached is not None:
        return cached['jobs'],{'ok':False,'count':len(cached['jobs']),'requests':requests_made,'cache_used':True,'cache_fresh':False,'error':type(last_error).__name__ if last_error else 'Unavailable','source_kind':adapter.source_kind}
    return [],{'ok':False,'count':0,'requests':requests_made,'cache_used':False,'error':type(last_error).__name__ if last_error else 'Unavailable','source_kind':adapter.source_kind}


def _get_json(url, timeout=20):
    r=requests.get(url,headers=UA,timeout=timeout)
    r.raise_for_status()
    return r.json()


def arbeitnow():
    data=_get_json('https://www.arbeitnow.com/api/job-board-api').get('data',[])
    return [{'title':x.get('title'),'company':x.get('company_name'),'url':x.get('url'),'location':x.get('location'),'description':x.get('description'),'remote':x.get('remote'),'published_at':x.get('created_at'),'source_kind':'aggregator','source_url':'https://www.arbeitnow.com/'} for x in data]


def remoteok():
    data=_get_json('https://remoteok.com/api')
    return [{'title':x.get('position'),'company':x.get('company'),'url':x.get('url'),'location':x.get('location') or 'Remote','description':x.get('description'),'remote':True,'published_at':x.get('date'),'source_kind':'aggregator','source_url':'https://remoteok.com/'} for x in data if isinstance(x,dict) and x.get('position')]


def lever_fetch(site):
    data=_get_json(f'https://api.lever.co/v0/postings/{site}?mode=json')
    out=[]
    for x in data:
        cats=x.get('categories') or {}
        out.append({'title':x.get('text'),'company':site,'url':x.get('hostedUrl') or x.get('applyUrl'),'location':cats.get('location'),'description':x.get('descriptionPlain') or x.get('description'),'published_at':'','source_kind':'ats','source_url':f'https://jobs.lever.co/{site}'})
    return out


def personio_fetch(url, company=''):
    r=requests.get(url,headers=UA,timeout=20); r.raise_for_status()
    root=ET.fromstring(r.text)
    out=[]
    for pos in root.findall('.//position'):
        def txt(tag):
            node=pos.find(tag); return (node.text or '').strip() if node is not None else ''
        title=txt('name') or txt('title')
        office=txt('office') or txt('location')
        pid=txt('id')
        job_url=txt('url') or txt('jobUrl') or url
        desc=' '.join((e.text or '') for e in pos.iter() if e.text)
        out.append({'title':title,'company':company,'url':job_url,'location':office,'description':desc,'external_id':pid,'source_kind':'ats','source_url':url})
    return out


def discovery_file_fetch(path):
    p=Path(path)
    if not p.exists(): return []
    data=json.loads(p.read_text())
    if isinstance(data,dict): data=data.get('jobs',[])
    return data if isinstance(data,list) else []


def build_adapters(root, config=None):
    config=config or {}
    adapters=[
        SourceAdapter('Arbeitnow',arbeitnow,max_requests_per_run=1,retry_count=1,cache_ttl_hours=24,source_kind='aggregator',attribution_url='https://www.arbeitnow.com/'),
        SourceAdapter('RemoteOK',remoteok,max_requests_per_run=1,retry_count=1,cache_ttl_hours=24,source_kind='aggregator',attribution_url='https://remoteok.com/'),
    ]
    discovery=config.get('discovery_file','public/data/discovery.json')
    if discovery:
        path=Path(root)/discovery
        adapters.append(SourceAdapter('Web discovery',lambda p=path: discovery_file_fetch(p),max_requests_per_run=1,retry_count=0,source_kind='discovery',network=False))
    for item in config.get('lever',[]):
        site=item['site'] if isinstance(item,dict) else str(item)
        name=item.get('name',site) if isinstance(item,dict) else site
        adapters.append(SourceAdapter(f'Lever · {name}',lambda s=site: lever_fetch(s),max_requests_per_run=1,retry_count=1,source_kind='ats',attribution_url=f'https://jobs.lever.co/{site}'))
    for item in config.get('personio',[]):
        if not isinstance(item,dict) or not item.get('url'): continue
        url=item['url']; name=item.get('name','Personio')
        adapters.append(SourceAdapter(f'Personio · {name}',lambda u=url,n=name: personio_fetch(u,n),max_requests_per_run=1,retry_count=1,source_kind='ats',attribution_url=url))
    return adapters

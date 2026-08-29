import json
from datetime import datetime, timezone
from pathlib import Path
from .collector import collect_jobs_v2
from .sources import build_adapters
from .privacy import sanitize_public_job,assert_public_payload_safe

ROOT=Path(__file__).resolve().parents[2]

def _load_json(path,default):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return default

def _atomic_json(path,payload):
    path=Path(path); tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    tmp.replace(path)

def main():
    profile=_load_json(ROOT/'config/profile.json',{})
    source_config=_load_json(ROOT/'config/sources.json',{})
    out=ROOT/'public/data'; out.mkdir(parents=True,exist_ok=True)
    previous=_load_json(out/'jobs.json',[])
    if not isinstance(previous,list): previous=[]
    adapters=build_adapters(ROOT,source_config)
    jobs,run=collect_jobs_v2(adapters,profile,previous_jobs=previous,cache_dir=ROOT/'.cache/jobhub')
    public=[sanitize_public_job(x) for x in jobs]
    run['generated_at']=datetime.now(timezone.utc).isoformat()
    run['pipeline']='v2'
    assert_public_payload_safe({'jobs':public,'run':run})
    _atomic_json(out/'jobs.json',public)
    _atomic_json(out/'run.json',run)

if __name__=='__main__': main()

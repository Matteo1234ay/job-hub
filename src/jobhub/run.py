import json
from pathlib import Path
from .collector import collect_jobs
from .sources import arbeitnow,remoteok
from .privacy import sanitize_public_job,assert_public_payload_safe
ROOT=Path(__file__).resolve().parents[2]
def main():
    profile=json.loads((ROOT/'config/profile.json').read_text()); jobs,run=collect_jobs([('Arbeitnow',arbeitnow),('RemoteOK',remoteok)],profile)
    public=[sanitize_public_job(x) for x in jobs]; assert_public_payload_safe(public); out=ROOT/'public/data'; out.mkdir(parents=True,exist_ok=True)
    (out/'jobs.json').write_text(json.dumps(public,ensure_ascii=False,indent=2)); (out/'run.json').write_text(json.dumps(run,ensure_ascii=False,indent=2))
if __name__=='__main__': main()

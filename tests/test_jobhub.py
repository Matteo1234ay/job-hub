from pathlib import Path
import pytest
from src.jobhub.core import normalize_job,haversine_km,score_job,deduplicate_jobs
from src.jobhub.collector import collect_jobs
from src.jobhub.privacy import sanitize_public_job,assert_public_payload_safe

def test_core_matching_distance_and_dedupe():
    assert haversine_km(45.07,7.69,45.07,7.69)==0
    j=normalize_job({'title':'Social Media Manager','company':'Acme','url':'https://x/a','location':'Torino','description':'content video social canva'},'test')
    score,why,_=score_job(j,{'keywords':['social media','content','video','canva'],'negative':['senior director']})
    assert score>=70 and why and len(deduplicate_jobs([j,j]))==1

def test_source_failure_isolated():
    def good(): return [{'title':'Content Creator','company':'A','url':'https://a/1','location':'Torino','description':'social video content'}]
    def bad(): raise RuntimeError('boom')
    jobs,run=collect_jobs([('good',good),('bad',bad)],{'keywords':['content','social','video'],'negative':['senior']})
    assert len(jobs)==1 and run['sources']['bad']['ok'] is False

def test_sensitive_data_never_public():
    x=sanitize_public_job({'id':'1','title':'X','company':'Y','url':'https://x','email':'private@example.invalid','notes':'private','score':80})
    assert 'email' not in x and 'notes' not in x
    assert_public_payload_safe([x])
    with pytest.raises(ValueError): assert_public_payload_safe({'token':'secret'})

def test_frontend_private_state_contract():
    js=Path('public/app.js').read_text(); html=Path('public/index.html').read_text()
    assert 'jobhub.applicationState.v1' in js and 'localStorage' in js and 'data/jobs.json' in js
    assert 'Esporta' in html and 'Importa' in html

def test_workflow_contract():
    daily=Path('.github/workflows/daily-jobs.yml').read_text(); pages=Path('.github/workflows/pages.yml').read_text()
    assert "cron: '15 6 * * *'" in daily and 'python -m src.jobhub.run' in daily and 'path: public' in pages

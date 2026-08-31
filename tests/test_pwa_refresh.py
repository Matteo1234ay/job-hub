import json
from pathlib import Path


def test_pwa_files_and_ios_metadata_exist():
    html = Path('public/index.html').read_text()
    manifest = json.loads(Path('public/manifest.webmanifest').read_text())
    assert 'rel="manifest" href="manifest.webmanifest"' in html
    assert 'apple-mobile-web-app-capable' in html
    assert 'apple-mobile-web-app-status-bar-style' in html
    assert manifest['display'] == 'standalone'
    assert manifest['start_url'] == './'
    assert manifest['name'] == 'Job Hub Torino'
    assert Path('public/sw.js').exists()


def test_dashboard_exposes_last_refresh_status():
    html = Path('public/index.html').read_text()
    js = Path('public/app.js').read_text()
    assert 'id="refreshStatus"' in html
    assert 'data/run.json${fresh()}' in js
    assert "cache:'no-store'" in js
    assert 'generated_at' in js


def test_daily_workflow_has_free_redundant_schedule():
    workflow = Path('.github/workflows/daily-jobs.yml').read_text()
    assert "cron: '15 6 * * *'" in workflow
    assert "cron: '15 7 * * *'" in workflow

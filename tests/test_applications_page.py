from pathlib import Path


def test_home_links_to_applications_page():
    html = Path('public/index.html').read_text()
    assert 'href="candidature.html"' in html
    assert 'Le mie candidature' in html


def test_applications_page_exists_and_uses_private_local_state():
    html = Path('public/candidature.html').read_text()
    js = Path('public/candidature.js').read_text()
    assert 'Le mie candidature' in html
    assert "jobhub.applicationState.v1" in js
    assert 'data/jobs.json${fresh()}' in js
    assert "cache:'no-store'" in js


def test_home_moves_applied_jobs_out_of_feed():
    js = Path('public/app.js').read_text()
    assert 'APPLICATION_STATUSES' in js
    assert '!APPLICATION_STATUSES.has(state[j.id]?.status)' in js


def test_service_worker_never_caches_app_shell_or_data():
    sw = Path('public/sw.js').read_text()
    assert "cache:'no-store'" in sw
    assert 'caches.open' not in sw
    assert 'caches.match' not in sw
    assert 'self.skipWaiting()' in sw
    assert 'self.clients.claim()' in sw

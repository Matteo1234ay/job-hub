from pathlib import Path


def test_pages_build_emits_version_marker():
    workflow = Path('.github/workflows/pages.yml').read_text()
    assert 'version.json' in workflow
    assert 'github.event.workflow_run.head_sha' in workflow


def test_both_pages_load_mobile_freshness_guard():
    for path in ('public/index.html', 'public/candidature.html'):
        html = Path(path).read_text()
        assert 'freshness.js' in html


def test_mobile_freshness_checks_on_resume_and_forces_reload():
    js = Path('public/freshness.js').read_text()
    assert "fetch(`version.json?t=${Date.now()}`" in js
    assert "cache:'no-store'" in js
    assert "document.addEventListener('visibilitychange'" in js
    assert "window.addEventListener('pageshow'" in js
    assert 'location.replace(' in js
    assert 'registration.update()' in js

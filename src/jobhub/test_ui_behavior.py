from pathlib import Path


def test_home_uses_csp_safe_event_delegation_for_status_changes():
    js = Path('public/app.js').read_text()
    assert 'onchange=' not in js
    assert 'onclick=' not in js
    assert "addEventListener('change'" in js
    assert "data-job-status" in js
    assert "setStatus(select.dataset.jobStatus,select.value)" in js


def test_application_page_uses_csp_safe_event_delegation_and_updates_immediately():
    js = Path('public/candidature.js').read_text()
    assert 'onchange=' not in js
    assert "addEventListener('change'" in js
    assert "data-job-status" in js
    assert "setStatus(select.dataset.jobStatus,select.value)" in js


def test_job_links_are_opened_without_replacing_job_hub():
    app = Path('public/app.js').read_text()
    applications = Path('public/candidature.js').read_text()
    for js in (app, applications):
        assert "data-external-job" in js
        assert "window.open(link.href,'_blank','noopener,noreferrer')" in js
        assert 'event.preventDefault()' in js


def test_applications_page_has_clear_back_navigation():
    html = Path('public/candidature.html').read_text()
    assert 'class="back-link"' in html
    assert '← Torna agli annunci' in html

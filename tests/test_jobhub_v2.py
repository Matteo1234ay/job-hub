from pathlib import Path
import json
import pytest

from src.jobhub.classifier import classify_job, score_job_v2
from src.jobhub.sources import SourceAdapter, fetch_with_resilience
from src.jobhub.verifier import verify_job, deduplicate_jobs_v2
from src.jobhub.collector import collect_jobs_v2
from src.jobhub.privacy import sanitize_public_job, assert_public_payload_safe

PROFILE = {
    "role_terms": ["social media", "content creator", "content specialist", "video editor", "videomaker", "digital content"],
    "task_terms": ["editorial plan", "social strategy", "content creation", "video editing", "reels", "tiktok", "instagram", "youtube", "community management", "analytics", "storytelling"],
    "tool_terms": ["davinci", "premiere", "canva", "figma", "capcut"],
}


def job(title, description, location="Torino", **extra):
    base = {
        "id": "x",
        "title": title,
        "company": "Acme",
        "url": "https://acme.example/jobs/1",
        "location": location,
        "description": description,
        "source": "official",
        "published_at": "2026-08-28",
        "work_mode": "hybrid",
    }
    base.update(extra)
    return base


def test_strong_social_video_role_scores_high():
    result = classify_job(job(
        "Video Editor / Social Media Manager",
        "Piano editoriale, social strategy, riprese, video editing, Reels, TikTok, Instagram, YouTube, analytics e storytelling. 1-3 years experience."
    ), PROFILE)
    score, label, why, gaps, blockers = score_job_v2(result, PROFILE)
    assert score >= 75
    assert label == "MATCH_FORTE"
    assert not blockers
    assert any("video" in x.lower() for x in why)


def test_misleading_social_title_that_is_sales_is_rejected():
    result = classify_job(job(
        "Social Media Manager",
        "Primary responsibility: outbound sales, cold calling, lead generation, account closing and sales targets. Social posting is occasional."
    ), PROFILE)
    score, label, _, _, blockers = score_job_v2(result, PROFILE)
    assert label == "NON_PERTINENTE"
    assert score < 60
    assert any("sales" in x.lower() for x in blockers)


def test_non_obvious_title_is_retained_when_tasks_match():
    result = classify_job(job(
        "Junior Communication Specialist",
        "Create Instagram and TikTok content, shoot and edit short-form video, manage editorial calendar, community and performance analytics."
    ), PROFILE)
    score, label, why, _, blockers = score_job_v2(result, PROFILE)
    assert score >= 60
    assert label in {"MATCH_FORTE", "DA_VALUTARE"}
    assert not blockers
    assert why


def test_mandatory_senior_requirement_is_hard_blocker():
    result = classify_job(job(
        "Senior Content Lead",
        "Lead a team of creators. Minimum 7+ years mandatory and 4 years people management."
    ), PROFILE)
    score, label, _, _, blockers = score_job_v2(result, PROFILE)
    assert label == "NON_PERTINENTE"
    assert any("senior" in x.lower() or "years" in x.lower() for x in blockers)


@pytest.mark.parametrize("location,expected", [
    ("Torino", "LOCAL_STRONG"),
    ("Collegno", "LOCAL_STRONG"),
    ("Rivoli", "LOCAL_STRONG"),
    ("Moncalieri", "LOCAL_NEARBY"),
    ("Avigliana", "LOCAL_NEARBY"),
    ("Rosta", "LOCAL_NEARBY"),
    ("Remote - Italy", "REMOTE_ITALY"),
    ("Milano onsite", "OUTSIDE_SCOPE"),
])
def test_geography_classification(location, expected):
    result = classify_job(job("Content Creator", "Instagram content and video editing", location=location), PROFILE)
    assert result["geo_class"] == expected


def test_official_duplicate_wins_over_linkedin_discovery():
    linkedin = job("Content Creator", "video social", source="LinkedIn", url="https://it.linkedin.com/jobs/view/123", source_kind="discovery")
    official = job("Content Creator", "video social", source="Acme Careers", url="https://acme.example/jobs/content-creator", source_kind="official")
    out = deduplicate_jobs_v2([linkedin, official])
    assert len(out) == 1
    assert out[0]["source_kind"] == "official"
    assert "acme.example" in out[0]["url"]


def test_closed_job_is_rejected_by_verifier():
    checked = verify_job(job("Content Creator", "This job is no longer accepting applications", source_kind="discovery"))
    assert checked["verification"] == "SCARTATO"
    assert checked["active_status"] == "closed"


def test_source_429_uses_cache_and_does_not_raise(tmp_path):
    calls = {"n": 0}
    def fetch():
        calls["n"] += 1
        err = RuntimeError("429 Too Many Requests")
        err.status_code = 429
        raise err
    adapter = SourceAdapter("test", fetch, max_requests_per_run=1, cache_ttl_hours=24, retry_count=0)
    cache_file = tmp_path / "test.json"
    cache_file.write_text(json.dumps({"saved_at":"2099-01-01T00:00:00+00:00","jobs":[{"title":"Cached"}]}))
    jobs, meta = fetch_with_resilience(adapter, tmp_path)
    assert jobs == [{"title":"Cached"}]
    assert meta["ok"] is False
    assert meta["cache_used"] is True
    assert calls["n"] == 1


def test_total_source_failure_preserves_previous_dataset(tmp_path):
    previous = [job("Content Creator", "video editing reels")]
    def bad():
        raise TimeoutError("network")
    jobs, run = collect_jobs_v2([SourceAdapter("bad", bad, retry_count=0)], PROFILE, previous_jobs=previous, cache_dir=tmp_path)
    assert jobs == previous
    assert run["stale_data"] is True


def test_privacy_guard_rejects_sensitive_v2_fields():
    safe = sanitize_public_job({**job("Content Creator", "video"), "match_label":"MATCH_FORTE", "first_seen_at":"2026-08-29", "source_attribution":{"name":"Acme","url":"https://acme.example"}})
    assert "match_label" in safe and "source_attribution" in safe
    assert_public_payload_safe([safe])
    with pytest.raises(ValueError):
        assert_public_payload_safe({"jobs": safe, "email": "private@example.invalid"})


def test_frontend_v2_contract():
    js = Path("public/app.js").read_text()
    html = Path("public/index.html").read_text()
    assert "MATCH_FORTE" in js
    assert "VERIFICATO" in js
    assert "Candidato" in js
    assert "source_attribution" in js
    assert "jobhub.applicationState.v1" in js
    assert "localStorage" in js
    assert "analytics" not in html.lower()

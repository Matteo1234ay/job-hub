from src.jobhub.classifier import classify_job, score_job_v2

PROFILE = {
    "role_terms": ["content creator", "video editor"],
    "task_terms": ["video editing", "reels"],
    "tool_terms": [],
}


def make_job(location, work_mode="remote", description="video editing reels"):
    return {
        "title": "Video Editor",
        "company": "Acme",
        "url": "https://example.com/job",
        "location": location,
        "work_mode": work_mode,
        "description": description,
        "source_kind": "aggregator",
    }


def test_remote_flag_does_not_override_explicit_foreign_location():
    result = classify_job(make_job("Nagpur, India", description="Full-time on-site role based in Nagpur with video editing and reels."), PROFILE)
    score, label, _, _, blockers = score_job_v2(result, PROFILE)
    assert result["geo_class"] == "OUTSIDE_SCOPE"
    assert label == "NON_PERTINENTE"
    assert score < 60
    assert blockers


def test_generic_or_europe_remote_is_allowed_but_us_only_remote_is_not():
    generic = classify_job(make_job("Remote"), PROFILE)
    europe = classify_job(make_job("Europe"), PROFILE)
    us_only = classify_job(make_job("United States"), PROFILE)
    assert generic["geo_class"] == "REMOTE_ITALY"
    assert europe["geo_class"] == "REMOTE_ITALY"
    assert us_only["geo_class"] == "OUTSIDE_SCOPE"

from src.jobhub.classifier import classify_job, score_job_v2

PROFILE = {
    "role_terms": ["social media manager", "content creator", "video editor"],
    "task_terms": ["reels", "tiktok", "video editing"],
    "tool_terms": ["capcut", "canva"],
}


def test_direct_local_social_role_is_at_least_reviewable_when_description_is_sparse():
    job = {
        "title": "Tirocinante Social Media Manager",
        "company": "Studio",
        "url": "https://example.com/job",
        "location": "Avigliana",
        "description": "Inventare format, scrivere e registrare video, editare con CapCut e pubblicare contenuti social.",
        "source_kind": "discovery",
    }
    classified = classify_job(job, PROFILE)
    score, label, _, _, blockers = score_job_v2(classified, PROFILE)
    assert not blockers
    assert score >= 60
    assert label in {"DA_VALUTARE", "MATCH_FORTE"}
    assert classified["seniority_class"] == "JUNIOR_ACCESSIBLE"

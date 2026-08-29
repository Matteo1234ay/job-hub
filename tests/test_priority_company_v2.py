from src.jobhub.collector import collect_jobs_v2
from src.jobhub.sources import SourceAdapter

PROFILE = {
    "role_terms": ["social media manager", "content creator", "video editor"],
    "task_terms": ["reels", "tiktok", "video editing"],
    "tool_terms": ["capcut", "canva"],
    "priority_companies": ["nam studio"],
}


def test_priority_company_keeps_active_jobs_even_when_role_is_not_a_normal_match(tmp_path):
    def fetch():
        return [{
            "title": "Office Coordinator",
            "company": "Nam Studio",
            "url": "https://example.com/nam-office",
            "location": "Avigliana",
            "description": "Gestione operativa dello studio e organizzazione interna.",
            "source_kind": "discovery",
        }]

    jobs, _ = collect_jobs_v2(
        [SourceAdapter("discovery", fetch, retry_count=0, network=False, source_kind="discovery")],
        PROFILE,
        previous_jobs=[],
        cache_dir=tmp_path,
    )

    assert len(jobs) == 1
    assert jobs[0]["company"] == "Nam Studio"
    assert jobs[0]["match_label"] in {"DA_VALUTARE", "MATCH_FORTE"}
    assert any("azienda prioritaria" in reason.lower() for reason in jobs[0]["why"])


def test_priority_company_does_not_keep_closed_jobs(tmp_path):
    def fetch():
        return [{
            "title": "Old Role",
            "company": "Nam Studio",
            "url": "https://example.com/nam-old",
            "location": "Avigliana",
            "description": "Posizione chiusa. Non accetta più candidature.",
            "source_kind": "discovery",
        }]

    jobs, _ = collect_jobs_v2(
        [SourceAdapter("discovery", fetch, retry_count=0, network=False, source_kind="discovery")],
        PROFILE,
        previous_jobs=[],
        cache_dir=tmp_path,
    )

    assert jobs == []

from src.jobhub.collector import collect_jobs_v2
from src.jobhub.sources import SourceAdapter

PROFILE = {
    "role_terms": ["content creator"],
    "task_terms": ["video editing", "reels"],
    "tool_terms": [],
}


def test_canonical_source_points_to_specific_job_not_aggregator_homepage(tmp_path):
    def fetch():
        return [{
            "title": "Content Creator",
            "company": "Acme",
            "url": "https://jobs.example.com/jobs/123",
            "location": "Torino",
            "description": "Content creator with video editing and reels",
            "source_kind": "aggregator",
            "source_url": "https://jobs.example.com/",
        }]
    adapter = SourceAdapter("Jobs", fetch, retry_count=0, source_kind="aggregator", attribution_url="https://jobs.example.com/", network=False)
    jobs, _ = collect_jobs_v2([adapter], PROFILE, cache_dir=tmp_path)
    assert len(jobs) == 1
    assert jobs[0]["canonical_source"] == "https://jobs.example.com/jobs/123"

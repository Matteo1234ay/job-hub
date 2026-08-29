import json
from datetime import datetime, timezone
from src.jobhub.sources import SourceAdapter, fetch_with_resilience


def test_fresh_network_cache_skips_request(tmp_path):
    calls = {"n": 0}
    def fetch():
        calls["n"] += 1
        return [{"title": "Live"}]
    adapter = SourceAdapter("fresh", fetch, max_requests_per_run=1, cache_ttl_hours=24, retry_count=0, network=True)
    (tmp_path / "fresh.json").write_text(json.dumps({
        "saved_at": "2026-08-29T10:00:00+00:00",
        "jobs": [{"title": "Cached"}]
    }))
    jobs, meta = fetch_with_resilience(adapter, tmp_path, now=datetime(2026,8,29,11,0,0,tzinfo=timezone.utc))
    assert jobs == [{"title": "Cached"}]
    assert calls["n"] == 0
    assert meta["cache_used"] is True
    assert meta["cache_fresh"] is True

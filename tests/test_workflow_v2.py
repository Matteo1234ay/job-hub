from pathlib import Path


def test_discovery_feed_push_triggers_daily_collection():
    workflow = Path('.github/workflows/daily-jobs.yml').read_text()
    assert 'push:' in workflow
    assert 'public/data/discovery.json' in workflow
    assert 'python -m pytest -q' in workflow
    assert 'python -m src.jobhub.run' in workflow

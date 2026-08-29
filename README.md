# Job Hub

Personal, zero-mandatory-cost job discovery dashboard for social/content/video roles around Torino and relevant remote opportunities.

## Search V2

Job Hub combines low-request public sources with a curated web-discovery feed. LinkedIn is used only as a public discovery signal: the automated collector does not log in, bypass protections, or scrape an account. When an official company/ATS posting is available, it is preferred as the canonical source.

The ranking evaluates the real job content instead of only the title: role family, social/content/video tasks, tools, seniority, geography, source quality and hard blockers such as sales-heavy roles, pure SEO/SEM, unrelated IT, mandatory senior requirements or expired jobs.

The collector uses bounded requests, retries only transient failures, stops on rate limits, keeps per-source cache in GitHub Actions, and preserves the last valid public dataset if all live sources fail.

## Privacy

The public feed contains job metadata only. Application tracking lives in browser localStorage. No analytics, cookies, account system, CV, email, Gmail content, OAuth tokens, private notes or application history are published.

## Run

`pip install -r requirements.txt && python -m src.jobhub.run`

## Tests

`python -m pytest -q`

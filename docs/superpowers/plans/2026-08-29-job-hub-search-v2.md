# Job Hub Search V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Job Hub to a resilient, privacy-safe, zero-paid-dependency job discovery and ranking system that finds genuinely relevant social media, content and video roles around Torino and remote Italy.

**Architecture:** Split the V2 into focused modules: classification/scoring, resilient source adapters with bounded requests and cache, verification/canonicalization, history/privacy publication, and dashboard rendering. The collector keeps the last valid public dataset when live collection fails, and every published job carries explainable match/verification/source metadata.

**Tech Stack:** Python 3.12, requests, pytest, static HTML/CSS/JavaScript, GitHub Actions, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-08-29-job-hub-search-v2-design.md`

## Global Constraints

- No mandatory paid APIs or SaaS dependencies.
- No scraping of logged-in LinkedIn pages, login automation, CAPTCHA bypass or anti-bot evasion.
- LinkedIn is discovery-only; prefer official company/ATS canonical URLs.
- No CV, email, name, application notes, Gmail data, OAuth tokens, API keys or exact home location in public artifacts.
- Application state remains browser-local.
- Current public Job Hub URL remains unchanged.
- Study Hub must not be touched.
- Each source must have a bounded request budget and failures must not abort the whole run.
- If every live source fails, preserve the last known valid dataset and mark it stale.

---

### Task 1: V2 classification and scoring

**Files:**
- Create: `src/jobhub/classifier.py`
- Modify: `src/jobhub/core.py`
- Modify: `config/profile.json`
- Test: `tests/test_jobhub_v2.py`

**Interfaces:**
- Produces: `classify_job(job: dict, profile: dict) -> dict`
- Produces: `score_job_v2(job: dict, profile: dict) -> tuple[int, str, list[str], list[str], list[str]]`

- [ ] Write failing tests for strong social/video roles, misleading sales-heavy social titles, non-obvious content/video titles, seniority penalties, Torino/nearby/remote geography and hard exclusions.
- [ ] Run `python -m pytest -q` and verify the new V2 tests fail before implementation.
- [ ] Implement role-family, task, tool, seniority, geography and exclusion classifiers.
- [ ] Implement explainable weighted scoring with labels `MATCH_FORTE`, `DA_VALUTARE`, `NON_PERTINENTE`.
- [ ] Run the complete suite and verify all scoring/classification tests pass.

### Task 2: Resilient source adapters and cache

**Files:**
- Create: `src/jobhub/cache.py`
- Rewrite: `src/jobhub/sources.py`
- Test: `tests/test_jobhub_sources_v2.py`

**Interfaces:**
- Produces: `SourceAdapter` with `name`, `fetch()`, `max_requests_per_run`, `cache_ttl_hours`, `retry_count`.
- Produces: `fetch_with_resilience(adapter, cache_dir, now=None) -> tuple[list[dict], dict]`.
- Adapters: Arbeitnow, RemoteOK, Lever public boards, Personio public feeds when configured.

- [ ] Write failing tests for timeout isolation, 429 handling, cache fallback and request-budget enforcement.
- [ ] Run the targeted tests and confirm failure.
- [ ] Implement JSON cache with timestamps and source-health metadata.
- [ ] Implement bounded retries/backoff and stop-on-429 behavior.
- [ ] Keep existing Arbeitnow/RemoteOK coverage and add configurable official ATS adapters without requiring secrets.
- [ ] Run source tests and then the full suite.

### Task 3: Verification, canonicalization and deduplication

**Files:**
- Create: `src/jobhub/verifier.py`
- Modify: `src/jobhub/core.py`
- Test: `tests/test_jobhub_verifier_v2.py`

**Interfaces:**
- Produces: `verify_job(job: dict) -> dict`.
- Produces: canonical-source priority `official > ATS > aggregator > discovery`.
- Produces: `deduplicate_jobs_v2(jobs: list[dict]) -> list[dict]`.

- [ ] Write failing tests for closed signals, canonical URL cleanup, official-vs-aggregator duplicate merging and verification labels.
- [ ] Run the tests and confirm they fail.
- [ ] Implement closure-signal detection and source confidence labels.
- [ ] Implement stronger fingerprinting over normalized company/title plus canonical URL.
- [ ] Prefer the strongest canonical source and preserve attribution metadata.
- [ ] Run verifier tests and full suite.

### Task 4: Collector/history/privacy publication

**Files:**
- Rewrite: `src/jobhub/collector.py`
- Modify: `src/jobhub/run.py`
- Modify: `src/jobhub/privacy.py`
- Test: `tests/test_jobhub_pipeline_v2.py`

**Interfaces:**
- Collector output jobs include `match_label`, `verification`, `first_seen_at`, `last_seen_at`, `active_status`, `source_attribution`.
- `run.json` includes source health, request counts, cache hits, rejection counts, publication count and `stale_data`.

- [ ] Write failing tests that a source failure does not stop the run, all-source failure preserves previous valid jobs, history fields are retained, and sensitive fields fail publication.
- [ ] Run the tests and confirm failure.
- [ ] Implement the V2 pipeline from source registry through privacy guard.
- [ ] Ensure invalid/empty new output never overwrites a valid previous dataset after total source failure.
- [ ] Run pipeline tests and full suite.

### Task 5: Dashboard V2 presentation

**Files:**
- Modify: `public/index.html`
- Modify: `public/app.js`
- Modify: `public/styles.css`
- Test: `tests/test_jobhub_frontend_v2.py`

**Interfaces:**
- Visible cards show Italian application statuses, match label, verification state, source attribution, publication/freshness and explainable reasons.
- Existing localStorage/export/import contract remains backward compatible.

- [ ] Write failing static-contract tests for Italian labels, source attribution links, match/verification rendering and local-only application persistence.
- [ ] Run tests and confirm failure.
- [ ] Update dashboard rendering without adding analytics, cookies or external scripts.
- [ ] Keep external links `noopener noreferrer` and source attribution visible.
- [ ] Run frontend tests and full suite.

### Task 6: Workflow, real dry run and release gate

**Files:**
- Modify: `.github/workflows/daily-jobs.yml`
- Modify: `README.md`
- Modify: `PRIVACY.md` only if needed to document V2 behavior.

**Interfaces:**
- Daily workflow remains one scheduled run and executes tests before collection/publication.
- No secrets are required for normal operation.

- [ ] Ensure the workflow runs `python -m pytest -q` before collection.
- [ ] Add bounded runtime/environment defaults for source request budgets and cache path.
- [ ] Run a real local/CI collection dry run where network is available; if live sources are unavailable, verify graceful fallback behavior instead of treating it as a code failure.
- [ ] Run `python -m pytest -q` as the final verification command.
- [ ] Inspect generated `public/data/jobs.json` and `public/data/run.json` with the privacy guard.
- [ ] Open a PR from `feature/job-search-v2` to `main` and merge only after verification passes.
- [ ] Verify the Pages deployment after merge and confirm the existing Job Hub URL still works.

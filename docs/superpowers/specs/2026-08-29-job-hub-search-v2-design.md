# Job Hub Search V2 — Design

Date: 2026-08-29

## Goal

Upgrade Job Hub from simple keyword filtering to a robust, privacy-safe, zero-paid-dependency job discovery and ranking pipeline focused on genuinely relevant social media, content, video and adjacent digital roles in the Torino area and remote Italy.

The system must remain useful if one source is unavailable, rate-limited, changes format, or temporarily blocks requests.

## Non-negotiable constraints

- No mandatory paid APIs or SaaS dependencies.
- No direct scraping of logged-in LinkedIn pages, no login automation, no CAPTCHA bypass, no anti-bot evasion.
- LinkedIn may be used as a public discovery signal, but the automated collector must prefer public/official sources that can be accessed without an account.
- No CV, email, name, application notes, Gmail data, OAuth tokens, API keys or other personal information in the public repository or published Pages data.
- Application state remains local to the browser unless the user explicitly chooses an export/import workflow.
- The current public Job Hub URL and existing privacy model remain unchanged.
- Study Hub is out of scope and must not be touched.

## Approaches considered

### A. Aggressive multi-site scraping

Search LinkedIn, Indeed and other job boards directly on every daily run.

Rejected: brittle, likely to trigger rate limits or anti-bot systems, can violate site terms, and would make the free pipeline unreliable.

### B. Single free job API

Use one free API and improve only the ranking logic.

Rejected: simple and cheap, but source coverage remains weak and a single outage or API policy change can break the whole product.

### C. Federated low-request collector with source adapters — selected

Use several low-cost/public sources, official ATS feeds where available, public company career pages, caching, source-specific request budgets, backoff and graceful fallback. Treat LinkedIn/public search results as discovery only and prefer the original company/ATS posting for verification.

This approach maximizes coverage while keeping request volume low and avoiding a single point of failure.

## Source strategy

### Tier 1 — official/public structured sources

Preferred because they are stable and easy to verify.

- Lever public Postings API for known company boards.
- Personio public career-site XML feeds for known company boards.
- Other official/public ATS feeds with documented anonymous access, added only after verification.
- Official company career pages with a lightweight adapter when no structured feed exists.

### Tier 2 — free public aggregators

- Arbeitnow.
- RemoteOK, mainly for remote roles.
- Additional free sources may be added only if their current terms permit the intended use and they do not create a mandatory paid dependency.

### Tier 3 — discovery signals

- Public LinkedIn job pages found through web search or externally surfaced links.
- Public search-engine results pointing to a company career page or ATS.

These signals are not treated as the canonical record when an official posting can be resolved.

## Request-budget and resilience model

Each source adapter declares:

- `max_requests_per_run`
- `timeout_seconds`
- `cache_ttl_hours`
- `retry_count`
- `backoff_seconds`
- `enabled`

Default policy:

- one daily scheduled run;
- no burst crawling;
- small per-source request budget;
- cached source results reused when still fresh;
- exponential backoff for transient failures;
- no retry loops for permanent 4xx responses except 429;
- 429 responses cause the adapter to stop for that run and use cached data if available;
- one failing source never aborts the whole run;
- source health is recorded in `run.json`.

If every live source fails, the dashboard keeps the last known valid dataset and marks it stale instead of publishing an empty feed.

## Query planner

The collector will not search only for `social media manager`.

It will use role families:

### Social / community

- social media manager
- junior social media manager
- social media specialist
- social media coordinator
- community manager
- community & social specialist

### Content

- content creator
- digital content creator
- social content creator
- content specialist
- content marketing specialist
- junior content marketing
- editorial/content specialist

### Video

- video editor
- social video editor
- videomaker
- video maker
- video content creator
- reels editor
- short-form video editor

### Adjacent digital roles

Included only when the description is content/social/video-heavy:

- digital marketing specialist
- communication specialist
- employer branding content
- junior creative
- creative content specialist

The role title is a signal, never sufficient on its own.

## Geographic model

Priority order:

1. Torino
2. Collegno
3. Rivoli
4. nearby Torino-area municipalities
5. remote Italy

No home address or precise user coordinates are stored.

Location classification returns:

- `LOCAL_STRONG`
- `LOCAL_NEARBY`
- `REMOTE_ITALY`
- `OUTSIDE_SCOPE`
- `UNKNOWN`

Outside-scope roles are normally excluded unless fully remote and otherwise a strong fit.

## Relevance engine V2

The score is based on independent dimensions instead of raw keyword count.

### 1. Role fit — 25 points

Checks whether the actual job function belongs to social, content, video or a closely related role family.

### 2. Task fit — 25 points

High-value task signals include:

- editorial planning
- social strategy
- content ideation
- copywriting
- filming/shooting
- video editing
- Reels / TikTok / Shorts
- Instagram / YouTube / TikTok management
- community management
- content performance analysis
- organic growth
- brand storytelling

### 3. Tool / execution fit — 15 points

Signals such as video-editing tools, Canva/Figma, analytics and content-production workflows.

### 4. Seniority accessibility — 15 points

Positive:

- junior
- entry level
- 0–2 years
- 1–3 years
- portfolio accepted in place of long experience

Negative:

- senior/lead/head/director
- 5+ years mandatory
- team-management requirements inconsistent with a junior/mid profile

### 5. Geography / work mode — 10 points

Torino-area on-site/hybrid and remote Italy score highest.

### 6. Opportunity quality — 10 points

Signals include clear employer identity, clear role description, active official posting and acceptable employment conditions.

## Hard exclusion rules

The job is hidden before ranking when strong evidence shows it is primarily:

- pure sales/business development;
- pure SEO/SEM/PPC;
- generic performance marketing with no meaningful content/social/video scope;
- graphic design requiring deep specialist design experience but little social/content work;
- senior leadership requiring 5+ years where the requirement is mandatory;
- unrelated software/IT roles;
- expired/closed jobs;
- duplicated jobs already represented by a better canonical source;
- unpaid volunteer work unless explicitly configured to show it.

## Match labels

- `MATCH_FORTE`: score >= 75 and no hard blocker.
- `DA_VALUTARE`: score 60–74 and no hard blocker.
- `NON_PERTINENTE`: score < 60 or hard blocker; not shown in the normal dashboard.

Each visible job must explain the score with positive and negative reasons, for example:

- `+ video editing`
- `+ Instagram/TikTok/Reels`
- `+ Torino`
- `+ junior / 1–3 years`
- `- paid acquisition dominant`
- `- 5+ years mandatory`

## Verification pipeline

Every candidate job passes through these checks:

1. URL is well-formed.
2. Source is known and allowed.
3. Posting appears active or has no closure signal.
4. Company/employer identity is present.
5. If a discovery link points to LinkedIn or an aggregator, try to resolve an official company/ATS posting.
6. Prefer the official URL as canonical when available.
7. Remove tracking query parameters.
8. Deduplicate by canonical URL plus normalized company/title fingerprint.

Verification labels:

- `VERIFICATO`: official/current source confirmed.
- `PLAUSIBILE`: credible public source but official canonical source not confirmed.
- `DA_VERIFICARE`: insufficient confidence; hidden by default or shown only in a secondary view.
- `SCARTATO`: closed, invalid, duplicate or irrelevant.

## Freshness and history

Each record stores only public metadata:

- `first_seen_at`
- `last_seen_at`
- `published_at`
- `active_status`
- `source`
- `canonical_source`

A job missing from a source is not immediately deleted. It enters a grace period to avoid false expiry caused by temporary source failures.

The dashboard differentiates:

- NUOVO
- GIÀ VISTO
- SALVATO
- CANDIDATO
- SCADUTO

Personal state remains browser-local.

## Public-data privacy boundary

Allowed in public JSON:

- job title
- company
- public job URL
- public location
- public description/snippet
- source
- publication/freshness dates
- match score and generic reasons
- verification state

Forbidden in public JSON/repository:

- user identity
- email address
- CV/resume
- phone
- personal portfolio URLs if they identify the user
- application notes/history
- Gmail messages
- tokens/secrets/passwords
- OAuth material
- exact home location

A recursive privacy validator must fail the build if forbidden keys appear in public artifacts.

## Source attribution and terms compliance

The dashboard must visibly attribute sources where their terms require attribution.

- Arbeitnow entries must provide a link back to Arbeitnow.
- RemoteOK entries must preserve required source attribution/linking.
- Official ATS/company postings link directly to the canonical source.

No source adapter is enabled until its current terms have been checked for the intended use.

## Data flow

1. `source registry` selects enabled adapters.
2. Each adapter returns normalized public job candidates.
3. `source cache` prevents unnecessary repeated requests.
4. `normalizer` standardizes title/company/location/content.
5. `verifier` resolves canonical source and activity confidence.
6. `classifier` detects role family, tasks, seniority, geography and exclusions.
7. `scorer` produces score, label, reasons and blockers.
8. `deduper` merges equivalent postings and keeps the best source.
9. `history` compares against the previous public dataset.
10. `privacy guard` validates the outgoing payload.
11. Only then are `public/data/jobs.json` and `public/data/run.json` replaced.

If validation fails, the previous valid public dataset remains untouched.

## Observability

`run.json` contains non-sensitive operational metadata:

- run timestamp
- source status
- requests made per source
- cache hits
- jobs fetched
- jobs rejected as irrelevant
- jobs rejected as expired
- jobs deduplicated
- jobs published
- stale-data flag

This allows diagnosing a degraded source without exposing personal data.

## Testing strategy

Tests are required before implementation for:

- strong social/video role scores highly;
- misleading `Social Media Manager` role that is actually sales is rejected;
- relevant non-obvious title is retained when description is strongly social/video;
- mandatory senior requirement penalizes/excludes correctly;
- Torino and nearby geography classify correctly;
- remote Italy works;
- duplicate LinkedIn/official ATS posting collapses to the official canonical record;
- closed/expired posting is excluded;
- 429 from one source does not fail the run;
- network timeout from one source does not fail the run;
- cached results are used when a source fails;
- all-source failure preserves the last valid dataset;
- request budgets are respected;
- public payload rejects sensitive fields;
- source attribution fields are present where required;
- browser-local application state continues to work.

## Rollout

Implementation will be incremental so the live dashboard never loses the working V1 path:

1. Add V2 tests and scoring/classification modules.
2. Add resilient source registry/cache.
3. Add official ATS adapters and source attribution.
4. Add canonical verification/deduplication.
5. Update public schema and dashboard labels.
6. Run full test suite and a real collection dry run.
7. Publish only after tests and privacy validation pass.

## Success criteria

The V2 is considered successful when:

- a daily run can complete even if one or more sources fail;
- no single source is required for the dashboard to remain usable;
- request volume stays deliberately low and bounded;
- clearly irrelevant search-result noise is filtered out;
- relevant content/video roles with non-obvious titles are retained;
- official active postings are preferred over aggregator duplicates;
- no personal data enters the public repository or Pages payload;
- no paid API is necessary for normal operation.

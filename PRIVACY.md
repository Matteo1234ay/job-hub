# Privacy

Job Hub publishes only public job-listing metadata intended for recruitment: role, company, public URL, location, public description/snippet, source, dates, verification state and generic match reasons.

Application status/history is stored in browser `localStorage` and is never sent to GitHub by the application. The V2 source cache is excluded from the repository and is used only as operational fallback during automated collection.

Do not commit CVs, email content, tokens, credentials, private notes, OAuth data, Gmail messages, exact home location, or application history. The repository and GitHub Pages site are public: treat every committed file as internet-public.

The frontend uses no analytics, ad trackers, cookies, remote persistence API, or third-party JavaScript. A Content Security Policy restricts network access to the same origin. The publication pipeline runs a recursive privacy guard before replacing the public feed.

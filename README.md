# Build Log

The companion repository to the SignalRoads Build Log series. Every Friday I publish a new go-to-market workflow I built that week, with the actual scripts, prompts, and configs alongside the writeup.

Each numbered folder = one workflow. Each workflow has its own README that walks through how to fork it.

## What's in here today

```
build-log/
├── 01-content-pipeline/          # Build Log #1 — content pipeline
│   ├── brief/                    # Brief template + intelligence layer outputs
│   ├── research/                 # Link library, SERP gap analysis, GSC/GA4 pulls
│   ├── writing/                  # CMS push, widget HTML examples
│   └── review/                   # Post-publish lint / audit
```

## What this is not

- **Not a SaaS.** No hosted service, no auth, no UI. Scripts you run locally.
- **Not turnkey.** It assumes you can read Python, set env vars, and wire your own API keys.
- **Not a content factory.** The pipeline is built to ship *good* content with leverage, not to mass-produce filler.

## What you need

- Python 3.11+
- An LLM API key (Anthropic or OpenAI)
- Optional, depending on the workflow: Google Search Console + Analytics access, Webflow API token, a CMS to push to

See [SETUP.md](SETUP.md) for the bootstrap walkthrough.

## How to fork

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in your values
3. Pick the workflow you want to run (e.g. `01-content-pipeline/`)
4. Read that folder's README
5. Run the scripts against your own site

## How to read the code

- Anything in a numbered folder root (`01-...`, `02-...`) is a workflow.
- A workflow is structured: `brief/` (intelligence layer), `research/` (data pulls), `writing/` (drafting + CMS push), `review/` (post-publish checks).
- Some scripts are fully built and runnable today.
- Some scripts are **stubs**, marked with `TODO` headers, pointing at where the implementation lives in the next Build Log. This is intentional — each weekly post extracts one component fully.

## Status table

| File | Status | Notes |
|---|---|---|
| `01-content-pipeline/research/build_link_library.py` | Built | Scrapes a blog category, generates SEO anchors via LLM |
| `01-content-pipeline/research/suggest_inbound_links.py` | Built | Given a draft + link library, proposes contextual inserts |
| `01-content-pipeline/research/gsc_pull.py` | Stub | GSC auth + query skeleton |
| `01-content-pipeline/research/ga4_pull.py` | Stub | GA4 blog-page pull skeleton |
| `01-content-pipeline/research/serp_check.py` | Stub | SERP gap analysis skeleton |
| `01-content-pipeline/writing/push_webflow.py` | Stub | Asset upload + bulk-create + locale handling skeleton |
| `01-content-pipeline/review/post_publish_audit.py` | Stub | 5-lint live-page audit skeleton |

Stubs ship cleanly and run with explanatory errors, so a downstream agent (or human) can see what each one does and where it's going.

## Working with this repo via an AI agent

If you point Claude Code, Codex, or a similar agent at this repo: read [CLAUDE.md](CLAUDE.md) first. It's the operating manual. Without it the agent will assume the stubs are complete implementations and confuse itself.

## License

MIT. See [LICENSE](LICENSE).

## Where the writeups live

Build Log archive: see SignalRoads.

---

This repository is intentionally written so a fresh AI agent or a human stranger can fork and run it without context from me. If anything is unclear, that's a bug — file an issue or send a PR.

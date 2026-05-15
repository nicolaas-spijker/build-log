# SETUP

Bootstrap walkthrough for a fresh clone. ~15 minutes if you have your API keys handy.

## 1. Clone and install

```bash
git clone https://github.com/<your-fork-or-source>/build-log.git
cd build-log
python3 -m venv .venv
source .venv/bin/activate
pip install -r 01-content-pipeline/requirements.txt
```

Python 3.11+ is required.

## 2. Set environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

- `LLM_PROVIDER` — `anthropic` or `openai`
- The matching API key (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`)
- `SITE_BASE_URL`, `SITE_BLOG_PATH`, `SITE_HOST` — your site, no trailing slash on the base URL
- `SCRAPER_USER_AGENT` — keep the default or set your own polite UA

Everything else (Webflow, GSC, GA4) is optional and only needed for the specific scripts that use those services.

## 3. Build your link library

The link library is the foundation of the inbound-linking flow. It's a JSON file of all your blog articles + the SEO anchor texts that should link to each.

```bash
python 01-content-pipeline/research/build_link_library.py \
  --category "$SITE_BASE_URL$SITE_BLOG_PATH" \
  --output 01-content-pipeline/data/link_library.json \
  --validate-with-llm
```

Notes:

- The scraper paginates the category page automatically, up to 10 pages
- Each article it finds gets up to 5 anchor texts derived from URL slug, title, and H2s
- `--validate-with-llm` runs the candidate anchors through your LLM provider for relevance filtering
- Output is gitignored by default — your live library is local-only

Expect the run to take 1-3 minutes per 50 articles. Bigger blogs longer.

## 4. Try an inbound link suggestion

Once you have `link_library.json`, you can ask the suggester to propose contextual inserts for a draft:

```bash
python 01-content-pipeline/research/suggest_inbound_links.py \
  --library 01-content-pipeline/data/link_library.json \
  --draft path/to/your/draft.md \
  --max-suggestions 5
```

The script outputs proposed `(find, replace)` pairs as JSON. It does not edit your draft file. Apply suggestions manually, or wire your own `apply` step.

## 5. The rest

The other scripts in `research/`, `writing/`, and `review/` are stubs as of this release. Their headers describe what they do and what's missing. Each will be promoted to "Built" status in a future Build Log post.

If you want to extend a stub yourself, read [CLAUDE.md](CLAUDE.md) for conventions before you start. The patterns matter more than the individual file.

## Troubleshooting

**`LLM_API_KEY missing`** — set the right env var for your provider. The script reads provider-specific keys first, then falls back to `LLM_API_KEY`.

**Scraper returns 0 links** — your `SITE_BLOG_PATH` may be wrong, or the category page uses client-side rendering. Inspect the page source manually; if articles are loaded by JS, this scraper won't see them and you'll need a headless-browser approach.

**Anchor validation fails with JSON parse error** — the LLM occasionally returns malformed JSON when batches are too large. Lower `--batch-size` (default 10) and re-run.

**OAuth-based scripts (GSC, GA4)** — these are stubs in this release. When you fill them in, place your `client_secret*.json` and `*_token.pickle` files in a directory OUTSIDE this repo, and point to them via env vars. The `.gitignore` already blocks them but external storage is the safer default.

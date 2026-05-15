# CLAUDE.md — operating manual for AI agents working in this repo

This file exists so a fresh agent (Claude Code, Codex, any LLM with file access) can be productive in this repository without context from the human owner. If you are that agent, read this end to end before editing anything.

## What this repository is

A collection of go-to-market workflow components. Each numbered folder (`01-*`, `02-*`, ...) is one workflow. Inside each workflow, the structure is the same:

```
NN-workflow-name/
├── README.md          # Workflow-specific intro
├── brief/             # Intelligence-layer inputs that go into a draft
├── research/          # Scripts that pull data (link library, SERP, GSC, GA4)
├── writing/           # CMS push, widget HTML, draft helpers
└── review/            # Post-publish lint / audit
```

## What this repository is NOT

- A turnkey product. There is no UI, no installer, no managed service.
- Backend code with persistence. Every script is one-shot; state lives in env vars and input files.
- A monorepo for a SaaS. Treat folders as independent runnable examples.

## Status legend (read this before assuming any script works end to end)

Each script's header docstring states one of:

- **Built.** Runs as-is once env vars are set. Tested.
- **Stub.** Skeleton with `TODO` comments. Documents the design + intended flow. Does not run to completion. Will be filled in a future Build Log post.
- **Example.** Static asset (HTML, JSON, markdown). Not executable.

If you cannot find a status header, treat the file as a stub and read it as design intent, not behaviour.

## Conventions

### Environment variables

All scripts load `.env` from the repo root (not from the numbered subfolder). Use `python-dotenv` or equivalent.

Required variables are listed in `.env.example`. If a script's required variable is missing, fail loudly with a clear message:

```python
key = os.environ.get("WEBFLOW_API_TOKEN")
if not key:
    raise SystemExit("WEBFLOW_API_TOKEN missing. See .env.example.")
```

Never hardcode tokens, site IDs, collection IDs, or domain names. If you find one hardcoded, refactor it to an env var before doing anything else.

### LLM provider abstraction

Scripts read `LLM_PROVIDER` (`anthropic` or `openai`) and call the matching client. Default to `anthropic`. Anthropic uses Claude Haiku for cheap utility calls (anchor validation, link suggestion); reserve larger models for drafting. Never call an LLM if `LLM_API_KEY` (or the provider-specific key) is unset — print a clear skip message and exit.

### File paths

- Inputs and outputs default to relative paths under the workflow folder (e.g. `01-content-pipeline/data/link_library.json`)
- Never reference `~/...` absolute paths in scripts
- Treat the repo root as the working directory

### Output files

Anything generated locally (link library JSON, scraped CSVs, draft markdown, draft HTML) is gitignored. Real outputs may contain crawl results that include third-party content. Keep them local.

## What was deliberately left out

The companion writeup at SignalRoads explains design choices. This repo holds the code. If you find the code's intent unclear, the design rationale is in the article, not in code comments. Do not over-document inside Python files.

## Webflow CMS — known quirks (universal, not specific to one site)

If you wire any of the writing/ helpers against a real Webflow CMS, expect these. They are not bugs in this repo — they are Webflow Designer / API behaviours that bit me repeatedly.

1. **Rich-text sanitizer strips raw `<button>`, `<input>`, `<form>`, `<select>`, `<textarea>` from embeds.** Anything inside `<script>` tags survives. Always inject form elements at runtime via JS `createElement` or `innerHTML`, never write static interactive tags in an embed.

2. **Rich-text sanitizer strips raw `<table>` outside `data-rt-embed-type='true'` wrappers.** For comparison tables, wrap the entire table in `<div data-rt-embed-type='true'>...</div>` with a scoped `<style>` block.

3. **Interactive widgets containing an empty `<table>` shell in their initial HTML get stripped on Designer save.** If your widget needs a table layout, build the `<table>`, `<thead>`, `<tbody>` at runtime via `document.createElement`. Confirmed across multiple incidents.

4. **Apostrophes inside `<script>` single-quoted JS strings silently kill the IIFE.** Symptom: the widget renders but clicks do nothing after a certain point. Fix: rewrite copy to avoid apostrophes (`do not`, `cannot`, `the user` instead of `don't`, `can't`, `user's`), or escape with `\'`.

5. **`<ul>`, `<ol>`, `<li>` outside `data-rt-embed-type` wrappers are silently stripped.** Sometimes on first publish, sometimes on the second Designer edit (non-deterministic). Convert lists to `<p><strong>Label.</strong> Description.</p>` blocks or table embeds. The only safe lists are those inside an embed wrapper.

6. **`update_collection_items` (or the v2 PATCH) does not publish to the live site even with `isDraft: false`.** You need a separate `publish_collection_items` call. Check `lastPublished` on the response — if it's stale, the change is not live.

7. **The image CDN URL filename does not update when you swap an asset.** If you replace a thumbnail through the API, the CDN URL stays the same but the bytes change. Fetch the actual bytes to verify, do not trust the filename.

8. **Multi-locale CMS items need a body field for locale IDs, not a query param.** A `PATCH /items/:id?cmsLocaleId=xxx` silently writes to the primary locale. Pass `cmsLocaleIds: [...]` in the body.

9. **`POST /items/bulk` with `cmsLocaleIds` in the field creates the same item across both locales under one item ID.** Useful for shipping EN + ES together. Separate PATCH calls per locale update language-specific copy.

10. **Webflow Designer can strip widget HTML on edit.** If someone opens a published widget article in Designer and clicks save, the entire widget can disappear. Verify the live page after any Designer touch and restore from a local copy if needed.

## Pre-publish gate (the 5-lint pattern)

If you wire the `review/post_publish_audit.py` skeleton against a real CMS, the gate has 5 lints. Run them all on every push.

1. **Editorial.** Intro length, sentence length cap (~25 words), no em dashes, paragraph length, header length, quote attribution, no bare bold-wrapped Quick Answer paragraphs.
2. **SEO.** Meta description length, primary keyword frequency, internal links present and contextual, external links return 200, alt text length, thumbnail not duplicated as first body figure.
3. **GEO (LLM search).** Tables for comparison content, Quick Answer block near top, first-person "what we do" experience signal, named quotes with attribution, scannable H2 cadence.
4. **Reader.** Jargon scan, idiom swap to literal phrasing, no unexplained brand drops in the intro, no passive skim-stoppers.
5. **Render.** Fetch the live page; verify image content-types, widget scripts present, no leaked `[PLACEHOLDER]` text, **zero raw `<ul>`/`<ol>`/`<li>` outside embed wrappers**, no orphaned tags. This lint is run pre-push on local assembled body AND post-push on the live page.

The Render lint is the hard block: if a pre-push scan finds list tags outside embed wrappers, convert them before pushing. Otherwise Webflow will strip them silently and leave holes in the article.

## How to extend

To add a new workflow:

1. Create `NN-name/` at the repo root, where `NN` is the next two-digit number.
2. Copy the `01-content-pipeline/` structure (folders + READMEs).
3. Add the workflow status to the top-level README status table.
4. Write the brief template in `brief/`. Briefs are markdown, not code.
5. Decide which scripts are Built vs Stub. Stubs are fine; mark them clearly.

To deepen an existing workflow:

1. Pick one stub.
2. Promote it to Built by filling in the implementation.
3. Update the workflow's README status row.
4. Write the companion Build Log post explaining the design choices.

## What never goes in this repository

- API keys, tokens, OAuth credentials (`.env`, `*.pickle`, `client_secret*.json`, etc.)
- Customer or user data (CSV exports, email lists, account IDs)
- Proprietary client business strategy
- Real CMS site IDs, collection IDs, locale IDs (use env vars)
- Real domain names beyond `example.com` in defaults
- Any third-party content that was scraped (the scraper outputs are gitignored)

If you are unsure whether something belongs, default to leaving it out.

## When in doubt

The companion writeups at SignalRoads contain the why. The README explains the what. This file explains how an agent should operate. If the three contradict, the writeup wins.

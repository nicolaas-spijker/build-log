# Content brief — [Article working title]

> One markdown file per article. The drafter (LLM or human) consumes this; nothing else. If a section is empty, fix it before drafting.

## 1. Topic & intent

- **Primary keyword:** [e.g. "stakeholder mapping"]
- **Search intent:** [informational | navigational | transactional | commercial]
- **Reader profile:** [job title, seniority, what they already know, what they're searching for]
- **The promise:** [one sentence on what the reader will take away]

## 2. Search demand (from `research/gsc_pull.py` + keyword research)

- Primary keyword monthly search volume: [number]
- Top 3 related queries: [list]
- Queries this article should rank for but is not yet ranking for: [list]
- Refresh signal? [if existing article: current position, click trend, CTR vs SERP avg]

## 3. SERP gap (from `research/serp_check.py`)

- Top 10 ranking pages: [list with format type — listicle, guide, comparison, tool]
- Most common H2s across top 10: [list]
- AI Overview content present? [yes/no — if yes, what frame is Google using]
- **Angle nobody is covering:** [the differentiation, the reason this article exists]

## 3b. LLM-shaped queries (the alignment layer)

Per Discovered Labs research on 2M AI citations (`research.discoveredlabs.com`), prompt-content alignment is β=+0.37 — 5.3x stronger than any other signal. Readers type short queries into Google but ask LLMs full questions with context. Write 2-3 actual prompts a buyer would type into Claude/ChatGPT/Perplexity on this topic. Use literal buyer phrasing, not paraphrased.

- LLM-shaped query 1: [e.g. "best PM software for a 10-person marketing agency working with US clients"]
- LLM-shaped query 2: [e.g. "what to switch to from slack for a small team that also needs simple task management"]
- LLM-shaped query 3 (optional): [...]

Pick 1-2 of these and ensure either the Quick Answer block OR a dedicated H3 question block answers them directly. This is the difference between ranking on Google and getting cited by an answer engine.

Where to harvest buyer phrasings: Reddit threads on the topic, G2/Capterra/TrustRadius reviews of competitors, support tickets (if accessible), customer interview transcripts. Do not invent the phrasings — pull from real sources.

## 4. Structure

- Hook (≈100-150 words): [the opening promise]
- TOC: anchored H2 jump links, embedded near top
- Quick Answer / definition block (≈80-150 words): [direct answer to the query, plain prose, no full-paragraph bold wrap]
- H2 outline:
  - [H2 #1] — [purpose, key beats]
  - [H2 #2] — [purpose, key beats]
  - [H2 #3] — [purpose, key beats]
  - ...
- Closing CTA + related links

Total target word count: [1500-3500]

## 5. Widget / interactive element

- Type: [none | calculator | quiz | comparison table | step-by-step | pitfalls card]
- Why: [what decision/quantification it helps the reader make]
- Placement: [near top, after intro — readers decide in 5-10 seconds]
- Notes: [content of widget if non-trivial]

## 6. Visuals

- Hero / thumbnail: [concept, source]
- In-body figures: [list with concept per H2 section]
- Rule: thumbnail must differ from first in-body figure

## 7. Internal linking (from `research/suggest_inbound_links.py`)

- Inbound links INTO this article from existing posts: [list of candidate sources + anchors]
- Outbound links FROM this article: [list of sibling/related articles to link to in body]
- Closing related-reads: [max 2-3 curated, only if body could not absorb inline]

## 8. External sources

- 2-3 credible external links (research orgs, established publications, named industry studies)
- Every statistic must link to its original source inline

## 9. Quotes

- 2-3 named industry quotes with full attribution: "Name, Title, Company"
- Pull from research interviews, published articles, books, or industry studies
- Place inside `<blockquote>` for native CMS rendering

## 10. SEO meta

- Meta title (max 60 chars): [...]
- Meta description (max 160 chars): [...]
- URL slug: [...]

## 11. Pre-publish gate

Before pushing to CMS, run the 5 lints (see `review/post_publish_audit.py` design + repo `CLAUDE.md`):

- [ ] Editorial — intro, sentence length, em dashes, paragraph length, header length, quotes
- [ ] SEO — meta length, keyword frequency, internal/external links 200-status
- [ ] GEO — tables for comparison content, Quick Answer block, named quotes
- [ ] Reader — jargon scan, idiom swap, no unexplained brand drops in intro
- [ ] Render — no raw `<ul>`/`<ol>`/`<li>` outside embed wrappers, widget scripts present, image content-types correct

## 12. After publish

- Re-run Render lint against the live page
- Update link library JSON to include this new article
- Add this article as an outbound link from 3-5 sibling articles (close the mesh)

#!/usr/bin/env python3
"""
Status: Built.

Scrape a blog category and produce a link library JSON file.

For every article found on the category (and its paginated pages), this writes
an entry with:
  - title
  - canonical URL
  - excerpt
  - 3-5 SEO anchor texts that should link TO this article from elsewhere on
    the same blog

Anchors are derived from URL slug, title, and H2 headers, then optionally
validated and refined by an LLM (Anthropic or OpenAI).

Usage:
    python build_link_library.py \
        --category "https://example.com/blog" \
        --output ../data/link_library.json \
        --validate-with-llm
"""
import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)

DEFAULT_USER_AGENT = os.environ.get(
    "SCRAPER_USER_AGENT", "build-log-scraper/1.0 (+https://example.com)"
)


# ---------------------------------------------------------------------------
# LLM client abstraction
# ---------------------------------------------------------------------------

def _llm_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "anthropic").lower()


def _llm_api_key(provider: str) -> str | None:
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("LLM_API_KEY")
    if provider == "openai":
        return os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    return None


def _llm_complete(prompt: str, system: str = "", max_tokens: int = 1000) -> str | None:
    """Provider-agnostic single-turn completion. Returns None if no key."""
    provider = _llm_provider()
    key = _llm_api_key(provider)
    if not key:
        return None

    if provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            logging.warning("anthropic package not installed. Skipping LLM call.")
            return None
        client = anthropic.Anthropic(api_key=key)
        model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if hasattr(b, "text")).strip()

    if provider == "openai":
        try:
            from openai import OpenAI
        except ImportError:
            logging.warning("openai package not installed. Skipping LLM call.")
            return None
        client = OpenAI(api_key=key)
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=0,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content.strip()

    logging.warning("Unknown LLM_PROVIDER=%s. Skipping LLM call.", provider)
    return None


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def normalize_url(raw: str) -> str:
    try:
        p = urlparse(raw)
    except Exception:
        return raw
    scheme = p.scheme or "https"
    netloc = p.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = p.path.rstrip("/")
    if path == "":
        path = "/"
    return urlunparse((scheme, netloc, path, "", "", ""))


def is_valid_url(url: str, timeout: int = 8) -> bool:
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        return resp.status_code == 200
    except Exception:
        try:
            resp = requests.get(url, allow_redirects=True, timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Pagination / link extraction
# ---------------------------------------------------------------------------

def fetch_category_links(
    category_url: str,
    session: requests.Session,
    blog_path_segment: str = "/blog",
    skip_path_patterns: tuple[str, ...] = (),
    max_pages: int = 10,
) -> list[str]:
    all_links: list[str] = []
    seen: set[str] = set()
    base_netloc = urlparse(category_url).netloc.lower().lstrip("www.")

    def extract_links_from_soup(soup: BeautifulSoup, base_url: str) -> list[str]:
        out: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#"):
                continue
            full = urljoin(base_url, href)
            p = urlparse(full)
            if p.netloc.lower().lstrip("www.") != base_netloc:
                continue
            if p.scheme not in ("http", "https"):
                continue
            path = p.path.rstrip("/")
            if path in ("", blog_path_segment):
                continue
            if blog_path_segment and blog_path_segment not in path:
                continue
            if any(pat in path for pat in skip_path_patterns):
                continue
            if p.path.lower().endswith((".pdf", ".zip", ".jpg", ".png", ".gif", ".svg")):
                continue
            norm = normalize_url(full)
            if norm not in seen:
                seen.add(norm)
                out.append(full)
        return out

    def find_next_page_url(soup: BeautifulSoup, current_url: str, current_page: int):
        next_page_num = current_page + 1
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "_page=" in href:
                m = re.search(r"_page=(\d+)", href)
                if m and int(m.group(1)) == next_page_num:
                    return urljoin(current_url, href), next_page_num
        return None, None

    current_url = category_url
    page_num = 1
    while current_url and page_num <= max_pages:
        logging.info("Fetching page %d: %s", page_num, current_url)
        r = session.get(current_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        page_links = extract_links_from_soup(soup, current_url)
        all_links.extend(page_links)
        logging.info("Found %d links on page %d", len(page_links), page_num)
        next_url, next_page_num = find_next_page_url(soup, current_url, page_num)
        if next_url:
            current_url, page_num = next_url, next_page_num
        else:
            break
    return all_links


# ---------------------------------------------------------------------------
# Anchor extraction
# ---------------------------------------------------------------------------

JUNK_PHRASES = {
    "accept all cookies", "reject all", "always active", "cookie settings",
    "read more", "click here", "learn more", "sign up", "get started",
    "privacy policy", "terms of service", "subscribe now", "contact us",
    "share this", "related posts", "table of contents", "free trial",
    "free plan", "pro plan", "enterprise plan", "basic plan",
    "finally", "however", "therefore", "moreover", "furthermore",
    "conclusion", "summary", "overview", "introduction", "example",
    "best practices", "what is", "how to", "ways to",
}


def _is_valid_anchor(text: str, allow_single_word: bool = False) -> bool:
    text = text.strip()
    norm = text.lower().strip()
    if norm in JUNK_PHRASES or any(j in norm for j in JUNK_PHRASES):
        return False
    if text.endswith((":", "!", "?")) or ":" in text or "@" in text:
        return False
    words = text.split()
    if not words:
        return False
    if len(words) > 5 or len(text) > 40:
        return False
    if len(words) == 1:
        if not allow_single_word:
            return False
        if len(text) < 7:
            return False
    if any(c in text for c in ['"', "→", "←", "✓", "©", "®", "™", "🎁", "📌"]):
        return False
    if any(c in text for c in ["$", "€", "£", "(", ")"]):
        return False
    if re.search(r"\d+/month|\d+/year|\d+ users", text, re.IGNORECASE):
        return False
    if text and ord(text[0]) > 127:
        return False
    return True


def extract_anchors(
    soup: BeautifulSoup,
    article_url: str,
    title: str,
    max_anchors: int = 5,
    global_anchors: set | None = None,
) -> list[dict]:
    anchors: list[dict] = []
    seen_local: set[str] = set()

    def add(text: str, allow_single_word: bool = False) -> bool:
        t = text.strip()
        if not _is_valid_anchor(t, allow_single_word=allow_single_word):
            return False
        norm = t.lower()
        if norm in seen_local:
            return False
        if global_anchors is not None and norm in global_anchors:
            return False
        seen_local.add(norm)
        if global_anchors is not None:
            global_anchors.add(norm)
        anchors.append({"text": t, "href": article_url})
        return True

    # 1. Core topic from URL slug
    slug = article_url.rstrip("/").split("/")[-1]
    core_topic = slug.replace("-", " ").strip()
    if core_topic:
        add(core_topic, allow_single_word=True)

    # 2. Title (cleaned)
    if title:
        clean = title.split("|")[0].split(" - ")[0].strip()
        clean = re.sub(r"\s*[\[\(]\d{4}[\]\)]\s*", "", clean)
        clean = re.sub(r"^\d+\+?\s*", "", clean)
        clean = re.sub(
            r"\s+(for|and|with|to|in|on|of|the|your|our|a)\s+.*$",
            "",
            clean,
            flags=re.IGNORECASE,
        )
        clean = clean.strip()
        if clean:
            add(clean, allow_single_word=True)

    # 3. H2s that share a word with the core topic
    core_words = {w.lower() for w in core_topic.split() if len(w) > 3}
    skip_h2 = ("table of contents", "conclusion", "summary", "introduction",
               "related", "faq", "frequently asked", "final thoughts",
               "key takeaways", "wrapping up")
    for h2 in soup.find_all("h2"):
        if len(anchors) >= max_anchors:
            break
        text = h2.get_text(" ", strip=True)
        if any(s in text.lower() for s in skip_h2):
            continue
        text_clean = re.sub(r"^\d+[\.\)]\s*", "", text).strip()
        if not text_clean:
            continue
        text_words = {w.lower() for w in text_clean.split() if len(w) > 3}
        if not (core_words & text_words):
            continue
        add(text_clean)

    # 4. Modifier variations (best/top/good) for plural-noun topics
    if len(anchors) < max_anchors and core_topic:
        first = core_topic.split()[0].lower() if core_topic.split() else ""
        existing_mods = {"best", "top", "good", "effective", "simple", "easy", "free"}
        if first not in existing_mods and re.search(
            r"(s|es|ies|tips|tools|apps|examples|questions|strategies|practices)$",
            core_topic,
            re.IGNORECASE,
        ):
            for mod in ("best", "top", "good"):
                if len(anchors) >= max_anchors:
                    break
                add(f"{mod} {core_topic}")

    return anchors


# ---------------------------------------------------------------------------
# Per-article metadata fetch
# ---------------------------------------------------------------------------

def fetch_article_metadata(
    url: str,
    session: requests.Session,
    allowed_host: str,
    max_excerpt_chars: int = 800,
    global_anchors: set | None = None,
    skip_path_patterns: tuple[str, ...] = (),
) -> dict | None:
    if not is_valid_url(url):
        logging.info("Skipping unreachable URL: %s", url)
        return None
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        title = None
        og = soup.find("meta", attrs={"property": "og:title"})
        if og and og.get("content"):
            title = og.get("content").strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()

        excerpt = None
        ogd = soup.find("meta", attrs={"property": "og:description"})
        if ogd and ogd.get("content"):
            excerpt = ogd.get("content").strip()
        else:
            md = soup.find("meta", attrs={"name": "description"})
            if md and md.get("content"):
                excerpt = md.get("content").strip()
            else:
                p = soup.find("p")
                if p:
                    excerpt = p.get_text(" ", strip=True)
        if excerpt:
            excerpt = excerpt[:max_excerpt_chars]
        if not excerpt or len(excerpt.strip()) < 30:
            return None

        canonical = None
        lc = soup.find("link", rel=lambda v: v and "canonical" in v)
        if lc and lc.get("href"):
            canonical = normalize_url(urljoin(url, lc.get("href")))
        else:
            canonical = normalize_url(url)

        try:
            can_netloc = urlparse(canonical).netloc.lower().lstrip("www.")
        except Exception:
            can_netloc = ""
        if allowed_host and can_netloc != allowed_host:
            return None

        can_path = urlparse(canonical).path.lower()
        if any(pat in can_path for pat in skip_path_patterns):
            return None
        if not is_valid_url(canonical):
            return None
        if not title or title.strip().startswith("http") or title.strip() == canonical:
            return None

        article_link = canonical or url
        anchors = extract_anchors(soup, article_link, title, global_anchors=global_anchors)
        return {
            "title": title,
            "url": article_link,
            "excerpt": excerpt or "",
            "anchors": anchors,
        }
    except Exception as e:
        logging.warning("Failed metadata fetch for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Optional LLM refinement of anchor sets
# ---------------------------------------------------------------------------

LLM_SYSTEM = (
    "You are an SEO expert. Validate anchor texts for internal blog linking. "
    "Reject filler, generic, or promotional anchors. Approve only topically "
    "specific, search-intent-aligned phrases. Return strict JSON."
)

LLM_PROMPT_TEMPLATE = """For each article below, return 3-5 SEO anchor texts.

Rules:
- KEEP relevant anchors from the candidates
- ADD new anchors if fewer than 3 candidates are usable (derive from title/URL)
- Good: short niche terms (1-3 words), main topic keyword, queries someone
  would actually search to find the article
- Bad: generic filler ("best practices", "how to"), promotional ("click here"),
  partial phrases that do not stand alone
- Return exactly 3-5 anchors per article

Articles:
{articles}

Respond ONLY with JSON in this exact shape, no prose:
{{
  "1": ["anchor1", "anchor2", "anchor3"],
  "2": ["anchor1", "anchor2", "anchor3", "anchor4"]
}}
"""


def validate_anchors_with_llm(articles: list[dict], batch_size: int = 10) -> list[dict]:
    if _llm_api_key(_llm_provider()) is None:
        logging.warning("LLM key missing. Skipping anchor validation.")
        return articles

    out: list[dict] = []
    for i in range(0, len(articles), batch_size):
        batch = articles[i : i + batch_size]
        logging.info("Validating anchors batch %d-%d", i + 1, i + len(batch))
        articles_block = "\n\n".join(
            f"Article {idx+1}:\nTitle: {a['title']}\nURL: {a['url']}\n"
            f"Candidate anchors: {', '.join(x['text'] for x in a.get('anchors', []))}"
            for idx, a in enumerate(batch)
        )
        prompt = LLM_PROMPT_TEMPLATE.format(articles=articles_block)
        raw = _llm_complete(prompt, system=LLM_SYSTEM, max_tokens=1500)
        if raw is None:
            out.extend(batch)
            continue
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        try:
            mapping = json.loads(raw)
        except json.JSONDecodeError:
            logging.warning("LLM returned non-JSON for batch. Keeping original anchors.")
            out.extend(batch)
            continue
        for idx, art in enumerate(batch):
            new = mapping.get(str(idx + 1))
            if isinstance(new, list) and new:
                art["anchors"] = [
                    {"text": str(x).strip(), "href": art["url"]}
                    for x in new
                    if str(x).strip()
                ]
            out.append(art)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 2)[1])
    parser.add_argument("--category", required=True,
                        help="Blog category URL to scrape (e.g. https://example.com/blog)")
    parser.add_argument("--output", default="link_library.json",
                        help="Path to write the JSON output")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max number of articles to process (0 = no limit)")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--blog-path", default=os.environ.get("SITE_BLOG_PATH", "/blog"),
                        help="Path segment that must appear in article URLs")
    parser.add_argument("--skip-path", action="append", default=[],
                        help="Path substrings to exclude (repeatable)")
    parser.add_argument("--validate-with-llm", action="store_true",
                        help="Refine anchor sets with the configured LLM")
    parser.add_argument("--batch-size", type=int, default=10,
                        help="LLM validation batch size")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent})

    skip_patterns = tuple(args.skip_path)

    logging.info("Fetching category links from %s", args.category)
    links = fetch_category_links(
        args.category,
        session,
        blog_path_segment=args.blog_path,
        skip_path_patterns=skip_patterns,
    )
    logging.info("Found %d candidate links", len(links))

    if args.limit > 0:
        links = links[: args.limit]

    posts: list[dict] = []
    seen_canon: set[str] = set()
    global_anchors: set[str] = set()
    allowed_host = urlparse(args.category).netloc.lower().lstrip("www.")

    for i, link in enumerate(links, start=1):
        logging.info("(%d/%d) Processing %s", i, len(links), link)
        meta = fetch_article_metadata(
            link,
            session,
            allowed_host,
            global_anchors=global_anchors,
            skip_path_patterns=skip_patterns,
        )
        if not meta:
            continue
        key = normalize_url(meta["url"])
        if key in seen_canon:
            continue
        seen_canon.add(key)
        posts.append(meta)

    if args.validate_with_llm:
        logging.info("Validating anchors with LLM (%d articles)...", len(posts))
        posts = validate_anchors_with_llm(posts, batch_size=args.batch_size)
        total = sum(len(p.get("anchors", [])) for p in posts)
        logging.info("Validation complete. Total anchors: %d", total)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("Wrote %d articles to %s", len(posts), out_path)


if __name__ == "__main__":
    main()

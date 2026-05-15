#!/usr/bin/env python3
"""
Status: Built.

Suggest contextual inbound links for a draft article, using a pre-built link
library.

Given a draft (markdown or HTML) and a link library JSON (from
build_link_library.py), this script:

  1. Walks every article in the library
  2. For each article, looks for any of its anchor texts inside the draft body
     (case-insensitive, word-boundary, not already inside an <a> tag)
  3. Scores each candidate by relevance (LLM) + position (earlier is better) +
     anchor specificity
  4. Returns the top N proposed (find_text, replacement_html) pairs as JSON

The script does NOT modify the draft file. It outputs proposals you apply
manually or via a downstream tool.

Usage:
    python suggest_inbound_links.py \
        --library ../data/link_library.json \
        --draft path/to/draft.md \
        --max-suggestions 5 \
        --output proposals.json
"""
import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


# ---------------------------------------------------------------------------
# LLM client abstraction (mirrors build_link_library.py for self-containment)
# ---------------------------------------------------------------------------

def _llm_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "anthropic").lower()


def _llm_api_key(provider: str) -> str | None:
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("LLM_API_KEY")
    if provider == "openai":
        return os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    return None


def _llm_complete(prompt: str, system: str = "", max_tokens: int = 1500) -> str | None:
    provider = _llm_provider()
    key = _llm_api_key(provider)
    if not key:
        return None
    if provider == "anthropic":
        try:
            import anthropic
        except ImportError:
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
    return None


# ---------------------------------------------------------------------------
# Candidate detection
# ---------------------------------------------------------------------------

def _strip_existing_links(body: str) -> str:
    """Replace existing <a>...</a> with a sentinel so we do not propose links
    inside content that is already linked."""
    return re.sub(r"<a\b[^>]*>.*?</a>", " [[LINKED]] ", body, flags=re.IGNORECASE | re.DOTALL)


def _word_boundary_pattern(anchor: str) -> re.Pattern:
    """Match anchor text on word boundaries, case-insensitive."""
    escaped = re.escape(anchor.strip())
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def find_candidates(
    draft_body: str,
    library: list[dict],
    self_url: str | None = None,
) -> list[dict]:
    """Return a list of candidate (article, anchor, position, snippet) tuples.

    A candidate is one occurrence of one anchor text in the draft body, not
    overlapping with an existing <a> tag, and not linking back to the draft
    itself.
    """
    stripped = _strip_existing_links(draft_body)
    candidates: list[dict] = []
    seen_anchors_in_draft: set[str] = set()  # cap one anchor text per draft

    for entry in library:
        target_url = entry.get("url")
        if not target_url:
            continue
        if self_url and target_url == self_url:
            continue
        title = entry.get("title", "")
        for anchor in entry.get("anchors", []):
            text = anchor.get("text", "").strip()
            if not text or len(text) < 4:
                continue
            norm = text.lower()
            if norm in seen_anchors_in_draft:
                continue
            pattern = _word_boundary_pattern(text)
            match = pattern.search(stripped)
            if not match:
                continue
            if "[[LINKED]]" in stripped[max(0, match.start() - 20) : match.end() + 20]:
                continue
            seen_anchors_in_draft.add(norm)
            # Capture a snippet for LLM scoring
            start = max(0, match.start() - 120)
            end = min(len(stripped), match.end() + 120)
            snippet = stripped[start:end].replace("\n", " ").strip()
            candidates.append({
                "target_url": target_url,
                "target_title": title,
                "anchor_text": text,
                "position": match.start(),
                "snippet": snippet,
            })
    candidates.sort(key=lambda c: c["position"])
    return candidates


# ---------------------------------------------------------------------------
# LLM relevance scoring
# ---------------------------------------------------------------------------

LLM_SYSTEM = (
    "You evaluate whether an internal link is contextually a good fit. "
    "Approve only when the anchor's surrounding sentence genuinely benefits "
    "from the link's destination topic. Reject forced or tangential matches. "
    "Return strict JSON."
)

LLM_PROMPT = """For each candidate, decide whether the proposed link adds value.

A good candidate:
- The anchor phrase is being used in the same topical sense as the target article's title
- The surrounding sentence is talking about the topic the link points to (not just sharing a word)
- The link would meaningfully help the reader (clarification, definition, deeper dive)

A bad candidate:
- The anchor is being used in a different sense than the target article covers
- The surrounding sentence is about something unrelated
- The link would be a generic see-our-other-article tag-on

Candidates:
{candidates}

Respond ONLY with JSON of this exact shape:
{{
  "1": {{"approve": true, "reason": "..."}},
  "2": {{"approve": false, "reason": "..."}}
}}
"""


def score_candidates(candidates: list[dict]) -> list[dict]:
    """Adds 'approve' and 'reason' fields via LLM. Falls back to approve=True
    if LLM is unavailable (caller should review manually in that case)."""
    if not candidates:
        return []
    if _llm_api_key(_llm_provider()) is None:
        logging.warning("LLM key missing. Returning candidates unscored.")
        for c in candidates:
            c["approve"] = True
            c["reason"] = "unscored (LLM key not set)"
        return candidates

    block = "\n\n".join(
        f"Candidate {i+1}:\n"
        f"  Anchor: \"{c['anchor_text']}\"\n"
        f"  Target: {c['target_title']} ({c['target_url']})\n"
        f"  Context: ...{c['snippet']}..."
        for i, c in enumerate(candidates)
    )
    raw = _llm_complete(LLM_PROMPT.format(candidates=block), system=LLM_SYSTEM)
    if raw is None:
        for c in candidates:
            c["approve"] = True
            c["reason"] = "unscored (LLM call returned None)"
        return candidates
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError:
        logging.warning("LLM returned non-JSON. Marking candidates unscored.")
        for c in candidates:
            c["approve"] = True
            c["reason"] = "unscored (LLM parse error)"
        return candidates

    for idx, c in enumerate(candidates):
        entry = mapping.get(str(idx + 1), {})
        c["approve"] = bool(entry.get("approve", False))
        c["reason"] = str(entry.get("reason", ""))
    return candidates


# ---------------------------------------------------------------------------
# Proposal output
# ---------------------------------------------------------------------------

def build_proposals(
    candidates: list[dict],
    max_suggestions: int,
) -> list[dict]:
    approved = [c for c in candidates if c.get("approve")]
    approved = approved[:max_suggestions]
    proposals = []
    for c in approved:
        anchor = c["anchor_text"]
        url = c["target_url"]
        # Build a find/replace pair the caller can apply
        find_text = anchor
        replace_text = f'<a href="{url}">{anchor}</a>'
        proposals.append({
            "anchor_text": anchor,
            "target_url": url,
            "target_title": c["target_title"],
            "reason": c.get("reason", ""),
            "find": find_text,
            "replace": replace_text,
            "approx_position": c["position"],
            "snippet": c["snippet"],
        })
    return proposals


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 2)[1])
    parser.add_argument("--library", required=True,
                        help="Path to link_library.json (from build_link_library.py)")
    parser.add_argument("--draft", required=True,
                        help="Path to the draft article (markdown or HTML)")
    parser.add_argument("--self-url", default=None,
                        help="Canonical URL of the draft, to avoid linking to itself")
    parser.add_argument("--max-suggestions", type=int, default=5)
    parser.add_argument("--output", default=None,
                        help="Path to write JSON proposals (defaults to stdout)")
    parser.add_argument("--no-llm-score", action="store_true",
                        help="Skip LLM relevance scoring (returns all positional candidates)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    library_path = Path(args.library)
    if not library_path.exists():
        sys.exit(f"Link library not found: {library_path}")
    library = json.loads(library_path.read_text(encoding="utf-8"))

    draft_path = Path(args.draft)
    if not draft_path.exists():
        sys.exit(f"Draft file not found: {draft_path}")
    draft = draft_path.read_text(encoding="utf-8")

    candidates = find_candidates(draft, library, self_url=args.self_url)
    logging.info("Found %d positional candidates", len(candidates))

    if not args.no_llm_score:
        candidates = score_candidates(candidates)
        approved = sum(1 for c in candidates if c.get("approve"))
        logging.info("%d candidates approved by LLM", approved)
    else:
        for c in candidates:
            c["approve"] = True
            c["reason"] = "LLM scoring skipped"

    proposals = build_proposals(candidates, max_suggestions=args.max_suggestions)
    out_json = json.dumps(proposals, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(out_json, encoding="utf-8")
        logging.info("Wrote %d proposals to %s", len(proposals), args.output)
    else:
        print(out_json)


if __name__ == "__main__":
    main()

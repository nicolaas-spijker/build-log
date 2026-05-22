#!/usr/bin/env python3
"""
Status: Stub.

Select images for a draft from a metadata-tagged image library.

Design intent: take the cost of image choice off the writer. A human
picking from a 500+ image library reuses the same handful and forgets
what was used where. This script does the bandwidth part; the final
call can still be a human eye, or fully automated, to your tolerance.

  1. Build (or load) a metadata index of the image library: for every
     image, a filename or URL, a short description, and use-case tags.
     Cache it as data/image_index.json (gitignored).
  2. For each image slot in the draft (thumbnail, plus one figure every
     400-500 words), take the surrounding section copy as context and
     score library images for relevance — embeddings or an LLM call.
  3. Propose a shortlist per slot. Enforce two rules: the thumbnail and
     the first body figure must differ, and no image repeats within one
     article.
  4. Output the chosen filename or URL per slot for the writing step to
     insert, or write the shortlist for a human to pick from.

The image library itself is NOT in this repo — it is your own asset
collection (and, on a client project, theirs). This script only ever
needs the metadata index, never the image binaries.

Required env (when implemented):
  IMAGE_INDEX_PATH=        path to the metadata index JSON
  LLM_PROVIDER=            anthropic | openai (see repo CLAUDE.md)
  LLM_API_KEY=             provider key; if unset, scoring is skipped

Implementation lands in a future Build Log post.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


def main() -> None:
    index = os.environ.get("IMAGE_INDEX_PATH", "")
    if not index:
        sys.exit("Missing env var: IMAGE_INDEX_PATH. See .env.example.")
    print("[stub] Image library index would load here.")
    print("[stub] Per-slot relevance scoring lands in a future Build Log post.")
    print("[stub] The image library itself is never committed to this repo.")


if __name__ == "__main__":
    main()

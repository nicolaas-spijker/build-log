#!/usr/bin/env python3
"""
Status: Stub.

Pull query-level Google Search Console data for the configured site.

Design intent: this script will produce a CSV (or JSON) of
queries x clicks/impressions/position for the last N days, optionally
clustered by topical seed terms so the output is consumable by the brief
template's "search demand" section.

The skeleton below shows the OAuth flow and the request shape. To finish:

  1. Run the OAuth handshake once locally, save the token to a path
     referenced by GOOGLE_APPLICATION_CREDENTIALS or a local pickle path
     OUTSIDE this repo. The .gitignore already blocks common credential
     filenames, but keeping them outside the repo is safer.
  2. Wire the searchanalytics().query() call against your GSC_PROPERTY env var.
  3. Add seed-cluster bucketing (see Build Log #2 — coming).

Until then this script prints what it would do and exits 0.

Required env:
  GSC_PROPERTY=sc-domain:example.com
  GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/outside/repo/credentials.json
"""
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


def main() -> None:
    prop = os.environ.get("GSC_PROPERTY", "")
    cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not prop:
        sys.exit("GSC_PROPERTY missing. See .env.example.")
    if not cred:
        sys.exit("GOOGLE_APPLICATION_CREDENTIALS missing. Point it at a JSON or pickle path OUTSIDE this repo.")

    end = datetime.now(timezone.utc).date() - timedelta(days=3)  # GSC lag
    start = end - timedelta(days=90)
    print(f"[stub] Would pull GSC data for {prop} from {start} to {end}")
    print("[stub] Implementation lands in a future Build Log post.")
    print("[stub] Design reference: see repo CLAUDE.md and the brief template's section 2.")


if __name__ == "__main__":
    main()

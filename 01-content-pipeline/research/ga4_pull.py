#!/usr/bin/env python3
"""
Status: Stub.

Pull GA4 engagement signals scoped to your blog landing pages.

Design intent: produce a list of top blog landing pages over the last N days
with sessions, engaged sessions, engagement rate, avg session duration. The
output feeds the brief's "refresh signal" decision: pages with falling clicks
but holding engagement are refresh candidates; pages with low engagement are
either intent mismatches or quality issues.

The skeleton below shows the request shape. To finish:

  1. Create a Google Cloud service account, download its JSON key, save the
     key OUTSIDE this repo. Point GOOGLE_APPLICATION_CREDENTIALS at it.
  2. Grant the service account read access to your GA4 property.
  3. Wire the BetaAnalyticsDataClient().run_report() call below with a filter
     scoped to your blog landing path.

Required env:
  GA4_PROPERTY_ID=123456789
  GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/outside/repo/credentials.json
  SITE_BLOG_PATH=/blog
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


def main() -> None:
    prop_id = os.environ.get("GA4_PROPERTY_ID", "")
    cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    blog_path = os.environ.get("SITE_BLOG_PATH", "/blog")
    if not prop_id:
        sys.exit("GA4_PROPERTY_ID missing. See .env.example.")
    if not cred:
        sys.exit("GOOGLE_APPLICATION_CREDENTIALS missing. Point it at a JSON path OUTSIDE this repo.")

    print(f"[stub] Would pull GA4 data for property {prop_id}, blog path {blog_path}")
    print("[stub] Implementation lands in a future Build Log post.")
    print("[stub] Design reference: see repo CLAUDE.md and the brief template's section 2.")


if __name__ == "__main__":
    main()

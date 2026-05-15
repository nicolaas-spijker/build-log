#!/usr/bin/env python3
"""
Status: Stub.

Live SERP gap analysis for a target query.

Design intent: given a target query, this script will (1) fetch the top 10
ranking pages, (2) extract their H2 outlines and primary content frames,
(3) capture any AI Overview text if present, (4) ask an LLM to identify the
angle space nobody is covering. Output is appended to the brief's section 3
("SERP gap").

Two implementation paths:

  A. Use a SERP API service (DataForSEO, SerpAPI, Bright Data, ScaleSerp).
     Cleanest. Requires a paid key. Add SERP_API_KEY to .env.

  B. Headless browser (Playwright) against Google directly. Brittle, slow,
     against TOS at scale. Useful for one-offs only.

Skeleton uses (A) shape. Replace _fetch_serp() with your provider of choice.

Required env (when implemented):
  SERP_API_KEY=
  LLM_PROVIDER + key (for gap analysis)
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env", override=False)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: serp_check.py 'your target query'")
    query = sys.argv[1]
    api_key = os.environ.get("SERP_API_KEY", "")
    if not api_key:
        print(f"[stub] SERP_API_KEY missing. Would query top 10 for: {query!r}")
    else:
        print(f"[stub] Would fetch top 10 for: {query!r}")
    print("[stub] Implementation lands in a future Build Log post.")
    print("[stub] Design reference: see repo CLAUDE.md and the brief template's section 3.")


if __name__ == "__main__":
    main()

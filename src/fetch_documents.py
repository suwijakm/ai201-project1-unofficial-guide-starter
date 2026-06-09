"""Milestone 3 — Document loader (ingestion, step 1).

Downloads the raw HTML for every Bruinwalk professor-course source listed in
`documents/sources.md` and saves it verbatim to `documents/raw/`. We save the
RAW HTML first, before any cleaning, so the pipeline has a consistent,
reproducible starting format (per the Milestone 3 instructions: "Save the raw
text to a consistent format before you start cleaning").

Why raw HTML instead of WebFetch/an LLM scrape: Bruinwalk's review text is
server-rendered and present in the page source, so we can parse the *verbatim*
student reviews ourselves in the cleaning step (src/ingest.py). Passing pages
through a summarizing model would paraphrase the reviews and corrupt the corpus.

Reviews are paginated; we follow ?page=2, ?page=3, ... until a page contains no
review cards (or MAX_PAGES is reached).
"""

from __future__ import annotations

import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from sources import SOURCES

RAW_DIR = Path(__file__).resolve().parent.parent / "documents" / "raw"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

MAX_PAGES = 3          # cap pages per source so we don't over-collect
REQUEST_DELAY = 1.0    # seconds between requests — be polite to the server


def count_reviews(html: str) -> int:
    """Number of review cards in a page — used to know when to stop paginating."""
    return len(BeautifulSoup(html, "html.parser").select("div.review.reviewcard"))


def fetch_source(slug: str, base_url: str) -> int:
    """Download all pages for one source. Returns the total review count saved."""
    total = 0
    for page in range(1, MAX_PAGES + 1):
        url = base_url if page == 1 else f"{base_url}?page={page}"
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        n = count_reviews(resp.text)
        if n == 0:
            break  # no more reviews — stop paginating
        out = RAW_DIR / f"{slug}_p{page}.html"
        out.write_text(resp.text, encoding="utf-8")
        total += n
        print(f"  page {page}: {n:3d} reviews  -> {out.name}")
        time.sleep(REQUEST_DELAY)
    return total


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    grand_total = 0
    for slug, prof, course, base_url in SOURCES:
        print(f"{prof} — {course}")
        try:
            grand_total += fetch_source(slug, base_url)
        except requests.RequestException as exc:
            print(f"  ERROR: {exc}")
    print(f"\nDone. Saved raw HTML for {len(SOURCES)} sources, "
          f"{grand_total} total reviews, into {RAW_DIR}")


if __name__ == "__main__":
    main()

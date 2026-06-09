"""Milestone 3 — Document cleaning (ingestion, step 2).

Reads the raw Bruinwalk HTML saved by fetch_documents.py and turns it into
clean, structured review records ready for chunking.

What "cleaning" means for this corpus:
  - Keep ONLY the student-written review text (the <p> tags inside
    div.expand-area.review-paragraph). Everything else on the card —
    "Helpful? / vote counts / Please log in to provide feedback", flag
    buttons, nav — is boilerplate and is dropped by construction (we never
    read it).
  - Keep the metadata needed for attribution and filtering: professor, course,
    source_url (from sources.py), plus the per-review quarter, grade, date, and
    up/down votes.
  - Dedup the desktop + mobile copies of each card by data-id (Bruinwalk
    renders every review twice in the page source).
  - HTML entities (&#x27; &amp; &nbsp; ...) are decoded for free by
    BeautifulSoup's get_text().

Outputs:
  documents/clean/reviews.jsonl   one JSON record per review (the chunking input)
  documents/clean/<slug>.txt      human-readable cleaned text, one file per source
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from sources import BY_SLUG, SOURCES

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "documents" / "raw"
CLEAN_DIR = ROOT / "documents" / "clean"


def _norm(text: str) -> str:
    """Collapse runs of whitespace while preserving paragraph breaks."""
    # Normalize within lines, keep blank-line paragraph separation.
    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in text.split("\n\n")]
    return "\n\n".join(p for p in paragraphs if p)


def _cell_value(card, label: str) -> str:
    """Pull the value following a 'Quarter:' / 'Grade:' label in the term row.

    Only look at the direct children of the term-row flex container, so we don't
    match the outer wrapper div (whose text concatenates Quarter AND Grade).
    Returns "" for missing or "N/A" values (treated as unknown).
    """
    for div in card.select("div.qtaken-flex-container > div"):
        txt = re.sub(r"\s+", " ", div.get_text(" ", strip=True)).strip()
        if txt.lower().startswith(label.lower()):
            # e.g. "Quarter: Fall 2018" -> "Fall 2018"
            value = txt.split(":", 1)[1].strip() if ":" in txt else ""
            return "" if value.upper() == "N/A" else value
    return ""


def parse_card(card, src) -> dict | None:
    """Turn one review card into a structured record, or None if it has no text."""
    body = card.select_one("div.expand-area.review-paragraph")
    if body is None:
        return None
    # Join the <p> paragraphs with blank lines; this is the verbatim review.
    paras = [p.get_text(" ", strip=True) for p in body.find_all("p")]
    text = _norm("\n\n".join(paras)) if paras else _norm(body.get_text("\n", strip=True))
    if not text:
        return None

    def vote(cls: str) -> int:
        el = card.select_one(f"span.{cls}")
        try:
            return int(el.get_text(strip=True)) if el else 0
        except ValueError:
            return 0

    return {
        "id": card.get("data-id"),
        "professor": src.professor,
        "course": src.course,
        "source": src.slug,
        "source_url": src.url,
        "quarter": _cell_value(card, "Quarter") or None,
        "grade": (_cell_value(card, "Grade") or None),
        "date": (card.select_one("span.date").get_text(strip=True)
                 if card.select_one("span.date") else None),
        "upvotes": vote("upvote-value"),
        "downvotes": vote("downvote-value"),
        "text": text,
    }


def reviews_for_source(slug: str) -> list[dict]:
    """All deduped reviews for one source, across its paginated HTML files."""
    src = BY_SLUG[slug]
    seen: set[str] = set()
    reviews: list[dict] = []
    for path in sorted(RAW_DIR.glob(f"{slug}_p*.html")):
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for card in soup.select("div.review.reviewcard"):
            rid = card.get("data-id")
            if rid in seen:            # desktop/mobile duplicate, or repeat across pages
                continue
            rec = parse_card(card, src)
            if rec is None:            # empty / no review text — skip
                continue
            seen.add(rid)
            reviews.append(rec)
    return reviews


def write_source_txt(slug: str, reviews: list[dict]) -> None:
    """Human-readable cleaned text for one source — for eyeballing the output."""
    src = BY_SLUG[slug]
    lines = [f"# {src.professor} — {src.course}", f"# {src.url}",
             f"# {len(reviews)} reviews", ""]
    for r in reviews:
        meta = " | ".join(filter(None, [r["quarter"], f"Grade: {r['grade']}" if r["grade"] else None, r["date"]]))
        lines.append(f"--- review {r['id']} ({meta}) ---")
        lines.append(r["text"])
        lines.append("")
    (CLEAN_DIR / f"{slug}.txt").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    all_reviews: list[dict] = []
    per_source_counts: list[tuple[str, int]] = []

    for src in SOURCES:
        reviews = reviews_for_source(src.slug)
        write_source_txt(src.slug, reviews)
        all_reviews.extend(reviews)
        per_source_counts.append((src.slug, len(reviews)))

    # Structured output for the chunking step.
    with (CLEAN_DIR / "reviews.jsonl").open("w", encoding="utf-8") as f:
        for r in all_reviews:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # --- Report -----------------------------------------------------------
    print("Cleaned reviews per source:")
    for slug, n in per_source_counts:
        print(f"  {slug:22s} {n:3d}")
    print(f"\nTotal cleaned reviews: {len(all_reviews)}")
    lengths = [len(r["text"]) for r in all_reviews]
    print(f"Review length (chars): min {min(lengths)}, "
          f"median {sorted(lengths)[len(lengths)//2]}, max {max(lengths)}")
    print(f"Wrote {CLEAN_DIR / 'reviews.jsonl'} and {len(SOURCES)} per-source .txt files")

    # Print ONE fully-cleaned document so we can read it (Milestone 3 step 3).
    sample_slug = "eggert-cs33"
    print(f"\n===== SAMPLE CLEANED DOCUMENT: {sample_slug}.txt (first ~1200 chars) =====")
    print((CLEAN_DIR / f"{sample_slug}.txt").read_text(encoding="utf-8")[:1200])


if __name__ == "__main__":
    main()

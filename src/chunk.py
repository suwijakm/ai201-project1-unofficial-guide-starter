"""Milestone 3 — Chunking (ingestion, step 3).

Turns the cleaned review records (documents/clean/reviews.jsonl) into the chunks
the embedding step will index, following the Chunking Strategy in planning.md:

  - One student review per chunk. A Bruinwalk review is already a complete,
    self-contained opinion, so the review boundary IS the natural semantic
    boundary — that maximizes how cleanly a query matches a single sentiment.
  - No overlap BETWEEN reviews: separate reviews don't continue into each other,
    so there is nothing to bridge.
  - Long reviews (> MAX_CHARS) are split at sentence boundaries so no single
    chunk becomes a diluted, multi-topic blob. A ~1-sentence (OVERLAP_CHARS)
    overlap is applied ONLY across these intra-review splits, so the split
    halves stay coherent.

Every chunk carries metadata for attribution and filtering (Milestone 4 needs
source metadata): professor, course, source, source_url, the review id, the
review's position on its page, and — for split reviews — the sub-chunk index.

Output:
  documents/clean/chunks.jsonl   one JSON record per chunk (the embedding input)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLEAN_DIR = ROOT / "documents" / "clean"
REVIEWS_PATH = CLEAN_DIR / "reviews.jsonl"
CHUNKS_PATH = CLEAN_DIR / "chunks.jsonl"

MAX_CHARS = 800      # split a review only when it exceeds this
OVERLAP_CHARS = 80   # ~1 sentence carried across an intra-review split

# Split on sentence-ending punctuation followed by whitespace. Kept deliberately
# simple (no NLTK dependency); reviews are casual prose where this is accurate
# enough, and a missed boundary only means a slightly longer/shorter chunk.
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def chunk_text(text: str) -> list[str]:
    """Split one review's text into <= MAX_CHARS pieces at sentence boundaries.

    Short reviews (the common case) return a single chunk unchanged. Long
    reviews are packed greedily; each new piece after the first repeats the
    trailing ~OVERLAP_CHARS of the previous piece so a fact straddling the split
    stays retrievable from either side.
    """
    if len(text) <= MAX_CHARS:
        return [text]

    sentences = split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    length = 0

    for sent in sentences:
        # +1 for the joining space.
        if current and length + len(sent) + 1 > MAX_CHARS:
            chunks.append(" ".join(current))
            # Seed the next chunk with the tail of this one for overlap.
            overlap: list[str] = []
            olen = 0
            for prev in reversed(current):
                if olen + len(prev) > OVERLAP_CHARS and overlap:
                    break
                overlap.insert(0, prev)
                olen += len(prev) + 1
            current = overlap
            length = sum(len(s) + 1 for s in current)
        current.append(sent)
        length += len(sent) + 1

    if current:
        chunks.append(" ".join(current))
    return chunks


def load_reviews() -> list[dict]:
    return [json.loads(line) for line in REVIEWS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def chunk_reviews(reviews: list[dict]) -> list[dict]:
    """Yield one chunk record per review (or per split-piece of a long review)."""
    chunks: list[dict] = []
    for position, r in enumerate(reviews):
        pieces = chunk_text(r["text"])
        for sub_index, piece in enumerate(pieces):
            chunk_id = f"{r['source']}-{r['id']}"
            if len(pieces) > 1:
                chunk_id += f"-{sub_index}"
            chunks.append({
                "chunk_id": chunk_id,
                "text": piece,
                # --- metadata (carried into ChromaDB in Milestone 4) ---
                "professor": r["professor"],
                "course": r["course"],
                "source": r["source"],
                "source_url": r["source_url"],
                "review_id": r["id"],
                "position": position,       # review's position in its source doc
                "sub_index": sub_index,     # 0 unless a long review was split
                "n_pieces": len(pieces),    # >1 means this review was split
                "quarter": r.get("quarter"),
                "grade": r.get("grade"),
                "date": r.get("date"),
            })
    return chunks


def write_chunks(chunks: list[dict]) -> None:
    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def main() -> None:
    reviews = load_reviews()
    chunks = chunk_reviews(reviews)
    write_chunks(chunks)

    # --- Report (Milestone 3 checkpoint) ---------------------------------
    lengths = [len(c["text"]) for c in chunks]
    split = sum(1 for c in chunks if c["n_pieces"] > 1)
    print(f"Loaded {len(reviews)} cleaned reviews")
    print(f"Produced {len(chunks)} chunks "
          f"({len(reviews)} reviews, {split} chunks came from split long reviews)")
    print(f"Chunk length (chars): min {min(lengths)}, "
          f"median {sorted(lengths)[len(lengths)//2]}, max {max(lengths)}")
    print(f"Wrote {CHUNKS_PATH}")

    # Sanity guardrails from the instructions.
    if len(chunks) < 50:
        print("WARNING: <50 chunks — chunks may be too large.")
    if len(chunks) > 2000:
        print("WARNING: >2000 chunks — chunks may be too small.")

    # Print 5 representative chunks spread across the corpus so we can confirm
    # each is readable, substantive, and self-contained (Milestone 3 checkpoint).
    print("\n===== 5 REPRESENTATIVE CHUNKS =====")
    step = max(1, len(chunks) // 5)
    for c in chunks[::step][:5]:
        tag = f"{c['professor']} — {c['course']} (chunk {c['chunk_id']}"
        if c["n_pieces"] > 1:
            tag += f", piece {c['sub_index'] + 1}/{c['n_pieces']}"
        tag += f", {len(c['text'])} chars)"
        print(f"\n--- {tag} ---")
        print(f"source: {c['source']}.txt")
        print(c["text"])


if __name__ == "__main__":
    main()

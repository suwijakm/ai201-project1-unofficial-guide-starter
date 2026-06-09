"""Milestone 4 — Semantic retrieval over the ChromaDB store (step 2).

Provides retrieve(query, k) — the function Milestone 5's generation step will
call — and a test harness (run this file directly) that queries the store with
the evaluation-plan questions and prints the returned chunks + distance scores,
so retrieval can be judged BEFORE generation is wired in.

The embedding model is loaded once and reused. Queries are embedded with the
SAME model and normalization used at index time (embed.py), and the collection
is configured for cosine distance, so a smaller distance = a closer match
(roughly 0 = identical, ~1 = unrelated; the checkpoint wants top hits < ~0.5).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from embed import COLLECTION_NAME, DB_DIR, MODEL_NAME

ROOT = Path(__file__).resolve().parent.parent

# The 5 evaluation-plan questions (planning.md) used to sanity-check retrieval.
# Q3 (Hsieh) is a known, documented weakness: students rarely name him in their
# reviews and CS 180 is shared with Burgin, so a name-anchored query collides
# with the more name-matchable Burgin chunks. See README evaluation report.
TEST_QUERIES = [
    "How difficult are Paul Eggert's exams in CS 33, and what do students recommend to prepare?",
    "For CS 33, do students recommend Nowatzki or Eggert?",
    "Is CS 35L with Eggert a heavy-workload class?",
    "What do students say about Cho-Jui Hsieh's lecturing style in CS 180?",
    "Which professor is more recommended for CS 181 — Sahai or Meka?",
]


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


@lru_cache(maxsize=1)
def _collection():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_collection(COLLECTION_NAME)


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Return the top-k chunks for a query, closest first.

    Each result: {text, distance, professor, course, source, source_url, ...}.
    """
    embedding = _model().encode([query], normalize_embeddings=True).tolist()
    res = _collection().query(
        query_embeddings=embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    results = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        results.append({"text": text, "distance": dist, **meta})
    return results


def _preview(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n] + " ..."


def main(k: int = 5) -> None:
    print(f"Testing retrieval (top-k={k}) against the store at {DB_DIR}\n")
    for query in TEST_QUERIES:
        print("=" * 80)
        print(f"QUERY: {query}")
        for rank, hit in enumerate(retrieve(query, k=k), 1):
            print(f"\n  [{rank}] distance={hit['distance']:.3f}  "
                  f"{hit['professor']} — {hit['course']}  ({hit['source']})")
            print(f"      {_preview(hit['text'])}")
        print()


if __name__ == "__main__":
    main()

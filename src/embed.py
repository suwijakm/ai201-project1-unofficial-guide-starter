"""Milestone 4 — Embed chunks and load them into ChromaDB (step 1).

Reads the chunks produced by chunk.py (documents/clean/chunks.jsonl), embeds
each chunk's text with all-MiniLM-L6-v2 (sentence-transformers, runs locally),
and stores the vectors + metadata in a persistent ChromaDB collection.

Design choices (from planning.md Retrieval Approach):
  - Model: all-MiniLM-L6-v2 — 384-dim, fast on CPU, no API key. Well-suited to
    a corpus of short reviews.
  - Distance: cosine. Configured on the collection (hnsw:space=cosine) so the
    distances retrieve.py reports are comparable to the spec's 0-1 scale
    (the Milestone 4 checkpoint wants top results below ~0.5).
  - We compute embeddings ourselves and hand them to Chroma (rather than letting
    Chroma pick a default embedding function) so the SAME model is used at index
    time and query time, and the choice is explicit.

Each chunk's metadata (professor, course, source, source_url, position, ...) is
carried into the store for source attribution in Milestone 5. Chroma metadata
values must be str/int/float/bool — None values are dropped.

Run:  python src/embed.py   (re-run any time chunks.jsonl changes; the collection
is reset so it always matches the current chunks).
"""

from __future__ import annotations

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
CHUNKS_PATH = ROOT / "documents" / "clean" / "chunks.jsonl"
DB_DIR = ROOT / "chroma_db"

MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "reviews"

# Metadata fields carried into Chroma (the chunk text is stored as the document,
# not duplicated here). None values are dropped — Chroma rejects them.
META_FIELDS = (
    "professor", "course", "source", "source_url",
    "review_id", "position", "sub_index", "n_pieces",
    "quarter", "grade", "date",
)


def load_chunks() -> list[dict]:
    return [json.loads(line) for line in CHUNKS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def metadata_for(chunk: dict) -> dict:
    """Flat, Chroma-safe metadata (drop None; everything else is str/int)."""
    return {k: chunk[k] for k in META_FIELDS if chunk.get(k) is not None}


def build() -> None:
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_PATH.name}")

    print(f"Loading embedding model: {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)

    texts = [c["text"] for c in chunks]
    print("Embedding chunks ...")
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True,
                              normalize_embeddings=True)

    client = chromadb.PersistentClient(path=str(DB_DIR))
    # Reset so the collection always matches the current chunks.jsonl.
    if COLLECTION_NAME in {c.name for c in client.list_collections()}:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=[metadata_for(c) for c in chunks],
    )

    print(f"Stored {collection.count()} chunks in ChromaDB collection "
          f"'{COLLECTION_NAME}' at {DB_DIR}")


if __name__ == "__main__":
    build()

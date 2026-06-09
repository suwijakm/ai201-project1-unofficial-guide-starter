"""Milestone 5 — Grounded answer generation (the end-to-end query function).

ask(question) ties the whole pipeline together:
    retrieve top-k chunks  ->  build a grounded prompt  ->  Groq LLM  ->  answer
and attaches source attribution PROGRAMMATICALLY (from the retrieved chunks'
metadata) rather than trusting the model to cite correctly.

Grounding is enforced two ways, not merely suggested:
  1. The system prompt instructs the model to answer ONLY from the numbered
     context blocks and to output the exact refusal sentence when the context
     is insufficient. Temperature is 0 to minimize improvisation.
  2. Sources are derived from the retrieved metadata in code (build_sources),
     so attribution can't drift from what was actually retrieved. When the model
     refuses, we return no sources — attributing documents to a non-answer would
     be misleading.

Used by app.py (the Gradio UI) and runnable directly for a quick smoke test.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL = "llama-3.3-70b-versatile"
REFUSAL = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You answer questions about UCLA computer-science professors and courses "
    "using ONLY the student reviews provided in the context below. Follow these "
    "rules strictly:\n"
    "- Use only facts stated in the numbered context blocks. Do not add outside "
    "knowledge about these professors, courses, or UCLA.\n"
    "- If the context does not contain enough information to answer the "
    f"question, reply with exactly this sentence and nothing else: \"{REFUSAL}\"\n"
    "- When reviews disagree, summarize the range of opinion rather than picking "
    "one side.\n"
    "- Be concise (2-5 sentences). Do not invent professor names, grades, or "
    "statistics that are not in the context."
)


def _client() -> Groq:
    key = os.environ.get("GROQ_API_KEY")
    if not key or key == "your_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
            "free Groq key from https://console.groq.com"
        )
    return Groq(api_key=key)


def build_context(chunks: list[dict]) -> str:
    """Render retrieved chunks as numbered, source-labeled blocks for the prompt."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(
            f"[{i}] Source: {c['source']}.txt — {c['professor']}, {c['course']}\n"
            f"{c['text']}"
        )
    return "\n\n".join(blocks)


def build_sources(chunks: list[dict]) -> list[dict]:
    """Unique source documents among the retrieved chunks, in rank order.

    This is the programmatic attribution: it reflects exactly what retrieval
    surfaced, independent of what the model writes.
    """
    seen: set[str] = set()
    sources: list[dict] = []
    for c in chunks:
        if c["source"] in seen:
            continue
        seen.add(c["source"])
        sources.append({
            "source": c["source"],
            "professor": c["professor"],
            "course": c["course"],
            "url": c.get("source_url", ""),
        })
    return sources


def format_source(s: dict) -> str:
    """One-line human-readable citation, e.g. for the Gradio 'Retrieved from' box."""
    return f"{s['source']}.txt — {s['professor']}, {s['course']} ({s['url']})"


def ask(question: str, k: int = 5) -> dict:
    """Answer a question grounded in retrieved reviews.

    Returns {answer, sources, chunks}: the grounded answer text, the list of
    source documents it could draw from (empty if the model refused), and the
    raw retrieved chunks (useful for debugging / the eval report).
    """
    chunks = retrieve(question, k=k)
    context = build_context(chunks)

    user_prompt = (
        f"Context (student reviews):\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above."
    )

    resp = _client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # Don't attribute sources to a refusal.
    refused = REFUSAL.rstrip(".").lower() in answer.lower()
    sources = [] if refused else build_sources(chunks)

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    # Quick smoke test: one in-corpus question and one out-of-scope question.
    for q in [
        "How difficult are Paul Eggert's exams in CS 33, and how should I prepare?",
        "What are the best dorms for freshmen at UCLA?",  # out of scope
    ]:
        print("=" * 80)
        print("Q:", q)
        out = ask(q)
        print("\nANSWER:\n", out["answer"])
        print("\nSOURCES:")
        for s in out["sources"]:
            print("  •", format_source(s))
        if not out["sources"]:
            print("  (none — system declined to answer)")
        print()

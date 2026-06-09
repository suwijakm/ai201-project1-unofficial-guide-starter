"""Milestone 5 — Gradio query interface for The Unofficial Guide.

A minimal web UI over the end-to-end pipeline: type a question about a UCLA CS
professor or course, get a grounded answer plus the source documents it drew
from and the actual chunks that were retrieved (with distance scores, useful for
the demo and for spotting retrieval issues).

Run:  python src/app.py   then open http://localhost:7860
"""

from __future__ import annotations

import gradio as gr

from query import ask, format_source

EXAMPLES = [
    "How difficult are Paul Eggert's exams in CS 33, and how should I prepare?",
    "For CS 33, do students recommend Nowatzki or Eggert?",
    "Is CS 35L with Eggert a heavy-workload class?",
    "Which professor is more recommended for CS 181 — Sahai or Meka?",
]


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", "", ""

    result = ask(question)

    sources = "\n".join(f"• {format_source(s)}" for s in result["sources"])
    if not sources:
        sources = "(no sources — the system declined to answer this question)"

    # Show the retrieved chunks + distances so a viewer can see the grounding.
    retrieved = "\n\n".join(
        f"[{i}] distance={c['distance']:.3f} — {c['professor']}, {c['course']} "
        f"({c['source']}.txt)\n{c['text']}"
        for i, c in enumerate(result["chunks"], 1)
    )
    return result["answer"], sources, retrieved


with gr.Blocks(title="The Unofficial Guide — UCLA CS Reviews") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about UCLA computer-science professors and courses. Answers are "
        "grounded **only** in real student reviews from Bruinwalk — if the "
        "reviews don't cover your question, the system says so instead of guessing."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. Is CS 35L with Eggert a heavy-workload class?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=6)
    sources = gr.Textbox(label="Sources (documents the answer can draw from)", lines=4)
    with gr.Accordion("Retrieved chunks (with distance scores)", open=False):
        retrieved = gr.Textbox(label="", lines=14, show_label=False)

    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources, retrieved])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources, retrieved])


if __name__ == "__main__":
    demo.launch()

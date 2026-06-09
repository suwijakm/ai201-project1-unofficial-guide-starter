"""Milestone 6 — Evaluation harness.

Runs all 5 evaluation-plan questions (planning.md) end-to-end through the
system and prints, for each: the question, the grounded answer, the source
documents attributed, and the top retrieved chunks with distance scores and the
professor/course they came from. The output is what populates the README
Evaluation Report and Failure Case Analysis sections.

Accuracy judgments are made by hand against the expected answers in planning.md
(an LLM grading its own pipeline isn't a trustworthy judge here) — this script
just gathers the evidence consistently.

Run:  python src/evaluate.py
"""

from __future__ import annotations

from query import ask, format_source

# (question, expected-answer summary from planning.md) for side-by-side reading.
EVAL = [
    ("How difficult are Paul Eggert's exams in CS 33, and what do students recommend to prepare?",
     "Extremely difficult; open-note yet very low averages; test lecture + textbook. "
     "Advice: read the textbook before lectures, use office hours."),
    ("For CS 33, do students recommend Nowatzki or Eggert?",
     "Overwhelmingly Nowatzki (clear teaching, generous curve); Eggert seen as brilliant but punishing."),
    ("Is CS 35L (with Eggert) a heavy-workload class?",
     "Yes — among the heaviest; 'most workload of any class by far.' Advice: start early."),
    ("What do students say about Cho-Jui Hsieh's lecturing style in CS 180?",
     "Mixed-to-negative: covers material and states expectations clearly, but lectures "
     "are often called messy / hard to follow, needing heavy independent study."),
    ("Which professor is more recommended for CS 181 — Sahai or Meka?",
     "Both well-regarded; Meka rates higher / more universally recommended; "
     "Sahai excellent for theory-oriented students but harder and polarizing."),
]


def run() -> None:
    for i, (question, expected) in enumerate(EVAL, 1):
        result = ask(question)
        print("=" * 90)
        print(f"Q{i}: {question}")
        print(f"\nEXPECTED (planning.md): {expected}")
        print(f"\nSYSTEM ANSWER:\n{result['answer']}")
        print("\nSOURCES ATTRIBUTED:")
        for s in result["sources"]:
            print(f"  • {format_source(s)}")
        if not result["sources"]:
            print("  (none — system declined)")
        print("\nTOP RETRIEVED CHUNKS:")
        for rank, c in enumerate(result["chunks"], 1):
            preview = " ".join(c["text"].split())[:140]
            print(f"  [{rank}] d={c['distance']:.3f}  {c['professor']}, {c['course']} "
                  f"({c['source']})\n        {preview} ...")
        print()


if __name__ == "__main__":
    run()

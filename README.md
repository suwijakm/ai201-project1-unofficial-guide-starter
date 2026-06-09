# The Unofficial Guide — Project 1

A RAG system that answers plain-language questions about UCLA computer-science
professors and courses, grounded in real student reviews collected from
[Bruinwalk](https://www.bruinwalk.com).

**Pipeline:** Bruinwalk pages → clean → chunk (one review each) → embed
(all-MiniLM-L6-v2) → ChromaDB → retrieve top-5 → Groq `llama-3.3-70b-versatile`
(grounded) → Gradio UI.

**Run it:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add your free Groq key from console.groq.com

python src/fetch_documents.py # download raw Bruinwalk HTML  -> documents/raw/
python src/ingest.py          # clean into reviews          -> documents/clean/reviews.jsonl
python src/chunk.py           # chunk reviews               -> documents/clean/chunks.jsonl
python src/embed.py           # embed + load into ChromaDB  -> chroma_db/
python src/retrieve.py        # (optional) test retrieval only
python src/evaluate.py        # (optional) run the 5 eval questions end-to-end
python src/app.py             # launch the Gradio UI at http://localhost:7860
```

---

## Domain

Student reviews of **UCLA computer-science professors and the courses they
teach**. This is exactly the knowledge official channels don't capture: the
course catalog and registrar describe *what* a class covers, but not which
professor teaches CS 33 well, how brutal the exams actually are, whether the
workload is survivable, or whether a class's difficulty comes from the material
or the grading. That knowledge lives scattered across hundreds of anonymous
Bruinwalk reviews; this system makes it answerable in one plain-language query
instead of forcing a student to read dozens of professor pages.

---

## Document Sources

12 Bruinwalk professor-course review pages (each page = one professor teaching
one course, holding many short student reviews). Chosen for variety across the
CS curriculum **and** across sentiment — beloved, polarizing, and disliked
professors — so the corpus answers a range of questions rather than repeating
the same praise. Reviews are paginated; the loader follows `?page=2`, `?page=3`,
… up to 3 pages per source.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Smallberg — CS 31 (well-liked) | Bruinwalk reviews | https://www.bruinwalk.com/professors/david-a-smallberg/com-sci-31/ |
| 2 | Nachenberg — CS 32 ("one of the best") | Bruinwalk reviews | https://www.bruinwalk.com/professors/carey-nachenberg/com-sci-32/ |
| 3 | Nowatzki — CS 33 (beloved, generous curve) | Bruinwalk reviews | https://www.bruinwalk.com/professors/anthony-nowatzki/com-sci-33/ |
| 4 | Eggert — CS 33 (polarizing, brutal exams) | Bruinwalk reviews | https://www.bruinwalk.com/professors/paul-r-eggert/com-sci-33/ |
| 5 | Eggert — CS 35L (heavy workload, mixed) | Bruinwalk reviews | https://www.bruinwalk.com/professors/paul-r-eggert/com-sci-35l/ |
| 6 | Sahai — CS 181 (theory, polarizing) | Bruinwalk reviews | https://www.bruinwalk.com/professors/amit-sahai/com-sci-181/ |
| 7 | Meka — CS 181 (theory, positive) | Bruinwalk reviews | https://www.bruinwalk.com/professors/raghu-meka/com-sci-181/ |
| 8 | Hsieh — CS 180 (algorithms, mixed/negative) | Bruinwalk reviews | https://www.bruinwalk.com/professors/cho-jui-hsieh/com-sci-180/ |
| 9 | Burgin — CS 180 (algorithms, divided) | Bruinwalk reviews | https://www.bruinwalk.com/professors/mark-burgin/com-sci-180/ |
| 10 | Darwiche — CS 161 (AI, positive) | Bruinwalk reviews | https://www.bruinwalk.com/professors/adnan-darwiche/com-sci-161/ |
| 11 | Mirzasoleiman — CS 188 (ML, positive) | Bruinwalk reviews | https://www.bruinwalk.com/professors/baharan-mirzasoleiman/com-sci-188-7/ |
| 12 | Ercegovac — CS M51A (logic design) | Bruinwalk reviews | https://www.bruinwalk.com/professors/milos-d-ercegovac/com-sci-m51a/ |

**Cleaning ([src/ingest.py](src/ingest.py)):** Bruinwalk review text is
server-rendered, so the loader saves the raw HTML
([src/fetch_documents.py](src/fetch_documents.py)) and the cleaner extracts
*only* the student-written review paragraphs (`div.expand-area.review-paragraph`).
Everything else on the card — vote counts, "Please log in to provide feedback,"
flag buttons, nav — is dropped by construction. Each review's duplicate
desktop/mobile copy is deduped by `data-id`, HTML entities are decoded, and the
professor / course / source URL / quarter / grade / date are kept as metadata.
This yields **274 clean reviews** in `documents/clean/reviews.jsonl`.

---

## Chunking Strategy

**Chunk size:** One student review per chunk (variable length, typically
~150–800 characters). Reviews longer than **800 characters** are split at
sentence boundaries so no single chunk becomes a diluted, multi-topic blob.

**Overlap:** **None between separate reviews** — each review is an independent,
self-contained opinion, so there is nothing to bridge. A ~**80-character**
(~1 sentence) overlap is applied **only** when a single long review must be
split, so the split halves stay coherent.

**Why these choices fit your documents:** This is a review-style corpus, not
long-form prose. Each Bruinwalk review is already a complete thought ("Eggert's
exams are brutal but the curve is generous"), so the review boundary *is* the
natural semantic boundary. Splitting on a fixed character count would cut
reviews mid-sentence and merge two students' opinions into one chunk, blurring
the sentiment an embedding should capture. Keeping one review per chunk
maximizes how cleanly a query matches a specific opinion. Overlap, which exists
to stop a key fact from being orphaned across a split, is unnecessary between
reviews because reviews don't continue into each other.

**Preprocessing before chunking:** HTML stripping, entity decoding, and
desktop/mobile dedup all happen in the cleaning stage (see Document Sources);
the chunker consumes already-clean review text from `reviews.jsonl`.

**Final chunk count:** **541 chunks** from 274 reviews (119 long reviews were
split into multiple pieces). Chunk length: min 4, median 674, max 865
characters. This sits comfortably inside the 50–2,000 guardrail — coarse enough
to carry real semantic signal, fine enough to match specific queries.

### Sample chunks (5, each labeled with its source document)

1. **`nowatzki-cs33.txt` — Anthony Nowatzki, COM SCI 33:**
   *"Nowatzki is an amazing professor (and an even better Overwatch player). He
   is super kind and made this class much more bearable. … Nowatzki is also very
   VERY generous with grading and curves the class and tests a ridiculous
   amount. It is nearly impossible to fail this class … TLDR: take Nowatzki
   because he is the best 33 professor to ever exist."*

2. **`eggert-cs35l.txt` — Paul R. Eggert, COM SCI 35L (piece 2/2 of a split review):**
   *"If you have to take this course, I would recommend you start to study the
   content, such as python and bash, before the quarter you are gonna take the
   course. … some people may be smart enough to be a very good graduate student,
   but they may not be competent to be a TA, and this is a TA based course."*

3. **`meka-cs181.txt` — Raghu Meka, COM SCI 181:**
   *"Meka is a great professor. 181 is definitely a hard class but somehow Meka
   made this class extremely enjoyable. His OHs are great and he explains
   everything really well. … The 1 hr OH is somehow the most productive studying
   sesh ever."*

4. **`burgin-cs180.txt` — Mark Burgin, COM SCI 180 (piece 1/4 of a split review):**
   *"This is the WORST professor and the WORST experience I've ever had. … To be
   honest, this professor welcomes questions and loves helping students, and he
   knows his stuff … However, he is a slow person and this causes a lot of
   confusions and annoyance."*

5. **`smallberg-cs31.txt` — David A. Smallberg, COM SCI 31 (piece 1/2 of a split review):**
   *"1) He does an excellent job of teaching the material … 2) His lectures can
   get very dry, especially since they are almost two hours long. 3) He does not
   use slides … 5) Final was more difficult than the midterm but still
   manageable. Average was around an 80."*

Each chunk is readable and self-contained. **Known low-signal tail:** 13 of 541
chunks are very short reviews (e.g. *"yyds"*, *"berg is the best <3"*). These
were deliberately kept rather than dropped — they're real reviews — but they
embed to weak, generic vectors and are a known noise source (see Anticipated
Challenges in [planning.md](planning.md)).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` — 384-dimensional
embeddings, runs locally with no API key or rate limits, fast on CPU. Vectors
are L2-normalized and stored in a ChromaDB collection configured for **cosine**
distance ([src/embed.py](src/embed.py)). It's well-suited to a corpus of short
reviews where each chunk is small, and it kept the whole pipeline free and
offline.

**Production tradeoff reflection:** If this served real students and cost
weren't a constraint, I'd weigh:

- **Accuracy on domain-specific text** *(the big one)*. MiniLM is a strong
  general model but isn't tuned for slangy, abbreviation-heavy student reviews
  ("psets," "the curve," "CS33," professor nicknames). A larger or
  instruction-tuned embedding model (OpenAI `text-embedding-3-large`, Voyage,
  Cohere embed) would likely separate fine-grained sentiment ("hard but fair" vs.
  "hard and unfair") better — and might mitigate the name-anchoring failure
  documented below.
- **Context length:** Mostly irrelevant here — reviews are short, so MiniLM's
  ~256-token window is plenty. It would matter only if I added long-form docs
  (syllabi, guides).
- **Latency vs. local control:** MiniLM running locally has zero network latency
  and no data leaving the machine — a privacy plus for anonymous reviews. An API
  model adds per-query latency and cost but offloads compute and usually improves
  quality.
- **Multilingual support:** Not needed for an English-only UCLA corpus, but a
  multilingual model would matter for an international campus.

Net: MiniLM is the right call for this project; for production I'd most likely
upgrade the embedding model for domain accuracy and benchmark it against MiniLM
on this same eval set before paying for it.

---

## Grounded Generation

Grounding is enforced **two ways**, not merely suggested
([src/query.py](src/query.py)):

**System prompt grounding instruction.** The model is told to answer *only* from
the numbered context blocks and to emit an exact refusal otherwise; decoding is
`temperature=0`. The actual instruction:

> You answer questions about UCLA computer-science professors and courses using
> ONLY the student reviews provided in the context below. … Use only facts
> stated in the numbered context blocks. Do not add outside knowledge about
> these professors, courses, or UCLA. If the context does not contain enough
> information to answer the question, reply with exactly this sentence and
> nothing else: "I don't have enough information on that." When reviews
> disagree, summarize the range of opinion rather than picking one side. …

Retrieved chunks are formatted as numbered, source-labeled blocks
(`[1] Source: eggert-cs33.txt — Paul R. Eggert, COM SCI 33\n<review text>`) so
the context is unambiguous and traceable.

**How source attribution is surfaced.** Attribution is computed
**programmatically** from the retrieved chunks' metadata (`build_sources()`),
*not* written by the LLM — so the cited documents can never drift from what was
actually retrieved. When the model returns the refusal sentence, the system
returns **no** sources (attributing documents to a non-answer would mislead).
The Gradio UI shows the answer, the source list, and the raw retrieved chunks
with distance scores.

This is why an out-of-scope query behaves correctly:

> **Q:** "What are the best dorms for freshmen at UCLA?"
> **A:** "I don't have enough information on that." — *(no sources)*

---

## Evaluation Report

All 5 questions from [planning.md](planning.md), run end-to-end via
[src/evaluate.py](src/evaluate.py).

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | How difficult are Eggert's CS 33 exams, and how to prepare? | Extremely difficult; very low averages; test lecture + textbook; advice: read textbook early, use OH | "Ridiculously difficult," F averages, 32%/52% midterm averages; advises reading textbook, going through notes, office hours | Relevant (4/5 Eggert CS 33; top d=0.249) | **Accurate** |
| 2 | For CS 33, Nowatzki or Eggert? | Overwhelmingly Nowatzki; Eggert brilliant but punishing | Recommends Nowatzki (engaging, generous grading); advises against Eggert (very difficult, few A's) | Relevant & **balanced** (3 Nowatzki + 2 Eggert) | **Accurate** |
| 3 | Is CS 35L (Eggert) heavy-workload? | Yes — among the heaviest; advice: start early | "Yes… workload is insane," "change your life," don't pair with other hard courses | Relevant (top 4 = Eggert CS 35L; 5th = Smallberg CS 31, off-source) | **Accurate** |
| 4 | What do students say about Hsieh's CS 180 lecturing style? | Mixed-to-negative: clear expectations but lectures messy/hard to follow | "Did a great job… willing to answer questions… enjoyable" — **one-sided positive** | **Off-target** (top 4 are the wrong professors; top d=0.490) | **Inaccurate** |
| 5 | CS 181 — Sahai or Meka? | Both good; Meka more universally recommended; Sahai harder/polarizing | "Both highly recommended… depends on personal preference" | Relevant & **balanced** (2 Sahai + 3 Meka) | **Partially accurate** |

**Scoreboard:** 3 accurate, 1 partially accurate, 1 inaccurate.

**Q5 nuance (why "partially accurate"):** Retrieval was on-target and balanced,
but generation **flattened the sentiment** to "both good, your choice." It
missed the real distinction in the reviews — Meka is more *universally*
recommended while Sahai is excellent-but-polarizing and harder. This is the
"mixed sentiment getting flattened" risk anticipated in planning.md materializing
mildly: a `temperature=0`, "summarize the range of opinion" prompt produces a
safe, symmetric answer that under-commits.

---

## Failure Case Analysis

**Question that failed:** Q4 — *"What do students say about Cho-Jui Hsieh's
lecturing style in CS 180?"*

**What the system returned:** A confidently **positive** answer — "Hsieh did a
great job of teaching the material… always willing to spend time answering
questions… enjoyable." The expected answer is **mixed-to-negative** (students
frequently call his lectures messy and hard to follow). Worse, the attributed
sources were mostly the *wrong professors*: `burgin-cs180.txt`,
`darwiche-cs161.txt`, `sahai-cs181.txt`, and only then `hsieh-cs180.txt`.

**Root cause (tied to the retrieval stage).** This is a **name-anchoring +
shared-course collision** in embedding/retrieval, not a generation bug. Two
facts combine:

1. **Only 7 of 42 Hsieh chunks actually contain his name** — students write
   "this professor," "this guy," "the lectures." So the query embedding for
   "Cho-Jui **Hsieh**'s lecturing style" has little to latch onto in his own
   reviews.
2. **CS 180 is shared with Burgin**, whose reviews express strong, explicitly
   *lecture-focused* opinions ("This guy doesn't know how to teach CS 180…
   Everything is a mess"). Those embed closer to "lecturing style" than Hsieh's
   own reviews do.

The result: the top 4 retrieved chunks (distances 0.490–0.511) are Burgin,
Darwiche, and Sahai; the only Hsieh chunk in the top 5 (rank 5, d=0.512) happens
to be one of his *positive* reviews. Generation then did its job faithfully — it
grounded its answer in the retrieved text — but the retrieved text was the wrong
professor's, so the answer is wrong. (Confirming the diagnosis: a name-light
query, `"Hsieh CS 180 lectures hard to follow messy"`, pulls 4 Hsieh chunks at
d=0.387 — the content *is* well-embedded; the professor's name just isn't.)

A secondary, milder version of the same retrieval imprecision shows up in Q3,
where a Smallberg CS 31 "workload is INSANE" chunk leaks into the retrieved set
(and thus into the programmatic source list) for a question about Eggert's CS 35L
— harmless to the answer here, but the same off-target mechanism.

**What I would change to fix it:**
- **Metadata filtering (the direct fix):** every chunk already stores
  `professor` and `course`; detect the named professor/course in the query and
  pass a ChromaDB `where` filter so retrieval is scoped to that professor. This
  is listed as a stretch feature and would require updating planning.md first.
- **Embed the professor/course into the chunk text** (e.g. prepend
  "Cho-Jui Hsieh, CS 180:" to each review before embedding) so the name anchors
  every chunk, not just the 7 that happen to mention it.
- **Upgrade the embedding model** to one with stronger entity sensitivity (see
  Embedding Model reflection).

---

## Spec Reflection

**One way the spec helped you during implementation.** Writing the **Chunking
Strategy** section *after* skimming the documents (Milestone 1) settled the
single most important design decision before any code existed: one review per
chunk, no inter-review overlap. Because that rule was explicit, `chunk_reviews()`
was a near-direct translation of the spec, and the resulting chunks retrieved
cleanly — most eval queries returned on-topic chunks at distances of 0.25–0.43.
The **Anticipated Challenges** section also paid off directly: it named the
"lopsided comparison" and "flattened sentiment" risks in advance, which is
exactly what shaped the evaluation questions (Q2, Q4, Q5 are comparison/mixed
questions chosen to stress those risks) and gave the failure analysis a head
start.

**One way your implementation diverged from the spec, and why.** planning.md
predicted the **comparison questions (Q2 Nowatzki/Eggert, Q5 Sahai/Meka) would
be "the most likely source of a documented failure case"** due to lopsided
retrieval. In practice those retrieved *balanced* both-professor context and
came back accurate/partially-accurate — the prediction was wrong. The real
failure was Q4 (Hsieh), a **name-anchoring/shared-course collision the spec did
not anticipate at all**. I let the implementation follow the evidence rather than
the prediction: instead of engineering around the risk the spec feared, I kept
top-k=5 semantic search as specified and documented the failure the system
*actually* produced. (A smaller divergence: I added a `chunks.jsonl` intermediate
artifact and `n_pieces`/`sub_index` chunk metadata that the spec didn't call out,
to make the pipeline stages independently runnable and debuggable.)

---

## AI Usage

I used **Claude (Claude Code)** throughout, directing it section-by-section from
planning.md and reviewing/overriding its output at each stage.

**Instance 1 — Chunking implementation**

- *What I gave the AI:* The **Chunking Strategy** and **Documents** sections of
  planning.md (one review per chunk, ~800-char split cap, ~80-char overlap only
  on intra-review splits), plus the cleaned `reviews.jsonl` schema.
- *What it produced:* `chunk.py` with a `chunk_text()` sentence-boundary splitter
  and a `chunk_reviews()` that emits one chunk per review with full metadata.
- *What I changed or directed:* I directed that overlap apply **only** across
  splits of a single long review and **never** between separate reviews (the
  default instinct is to apply uniform overlap everywhere) — that's the whole
  point of a review-style corpus. I also verified the output myself: printed the
  length distribution and confirmed 541 chunks fell in the 50–2,000 range, and
  chose to **keep** the 13 tiny "yyds"-style chunks as a documented noise source
  rather than auto-merging them.

**Instance 2 — Enforcing grounding programmatically**

- *What I gave the AI:* The grounding requirement (answer only from retrieved
  context; refuse otherwise) and the desired output format (answer + source
  list).
- *What it produced:* `query.py` wiring retrieval → Groq `llama-3.3-70b-versatile`
  with a grounded system prompt.
- *What I changed or directed:* The instructions allow attribution *either* by
  asking the LLM to cite sources *or* by appending them programmatically. I
  directed the stricter option — **source attribution derived in code from the
  retrieved chunks' metadata**, never written by the model — and added the rule
  that a refusal returns **zero** sources. This makes attribution impossible to
  hallucinate and was what surfaced the Q4 failure so clearly (the source list
  showed the wrong professors).

**Instance 3 — Diagnosing the retrieval failure instead of hiding it**

- *What I gave the AI:* The Milestone 4 retrieval output showing Q4 (Hsieh)
  returning wrong-professor chunks.
- *What it produced:* A diagnostic comparing name-anchored vs. name-light queries
  and a count of how many Hsieh reviews actually name him (7 of 42).
- *What I changed or directed:* I directed it **not** to "fix" the failure with
  metadata filtering (a stretch feature) and instead to preserve it as the
  honest, fully-explained failure case for this report — the project explicitly
  values a well-explained failure over a suspiciously perfect system.

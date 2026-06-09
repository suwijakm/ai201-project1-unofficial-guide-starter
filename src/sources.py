"""Single source of truth for the Bruinwalk sources in this corpus.

Both the loader (fetch_documents.py) and the cleaner (ingest.py) import from
here so professor/course/URL metadata is defined in exactly one place. The
`slug` is used as the filename stem for saved HTML (e.g. "eggert-cs33_p1.html")
and as the key to recover a review's metadata during cleaning.
"""

from __future__ import annotations

from typing import NamedTuple


class Source(NamedTuple):
    slug: str
    professor: str
    course: str
    url: str


SOURCES: list[Source] = [
    Source("smallberg-cs31",      "David A. Smallberg",      "COM SCI 31",   "https://www.bruinwalk.com/professors/david-a-smallberg/com-sci-31/"),
    Source("nachenberg-cs32",     "Carey Nachenberg",        "COM SCI 32",   "https://www.bruinwalk.com/professors/carey-nachenberg/com-sci-32/"),
    Source("nowatzki-cs33",       "Anthony Nowatzki",        "COM SCI 33",   "https://www.bruinwalk.com/professors/anthony-nowatzki/com-sci-33/"),
    Source("eggert-cs33",         "Paul R. Eggert",          "COM SCI 33",   "https://www.bruinwalk.com/professors/paul-r-eggert/com-sci-33/"),
    Source("eggert-cs35l",        "Paul R. Eggert",          "COM SCI 35L",  "https://www.bruinwalk.com/professors/paul-r-eggert/com-sci-35l/"),
    Source("sahai-cs181",         "Amit Sahai",              "COM SCI 181",  "https://www.bruinwalk.com/professors/amit-sahai/com-sci-181/"),
    Source("meka-cs181",          "Raghu Meka",              "COM SCI 181",  "https://www.bruinwalk.com/professors/raghu-meka/com-sci-181/"),
    Source("hsieh-cs180",         "Cho-Jui Hsieh",           "COM SCI 180",  "https://www.bruinwalk.com/professors/cho-jui-hsieh/com-sci-180/"),
    Source("burgin-cs180",        "Mark Burgin",             "COM SCI 180",  "https://www.bruinwalk.com/professors/mark-burgin/com-sci-180/"),
    Source("darwiche-cs161",      "Adnan Darwiche",          "COM SCI 161",  "https://www.bruinwalk.com/professors/adnan-darwiche/com-sci-161/"),
    Source("mirzasoleiman-cs188", "Baharan Mirzasoleiman",   "COM SCI 188",  "https://www.bruinwalk.com/professors/baharan-mirzasoleiman/com-sci-188-7/"),
    Source("ercegovac-csm51a",    "Milos D. Ercegovac",      "COM SCI M51A", "https://www.bruinwalk.com/professors/milos-d-ercegovac/com-sci-m51a/"),
]

BY_SLUG: dict[str, Source] = {s.slug: s for s in SOURCES}

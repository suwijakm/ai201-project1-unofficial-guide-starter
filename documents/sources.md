# Domain & Source Documents (Milestone 1)

## Domain Summary

Student reviews of **UCLA Computer Science professors and the courses they teach**, collected
from [Bruinwalk](https://www.bruinwalk.com) — a student-run review site. This knowledge — which
professor to take for CS 33, how heavy a class's workload really is, and whether a course's
difficulty comes from the material or the grading — lives in scattered, anonymous reviews and is
not captured anywhere official like the course catalog or the registrar's class descriptions. A
retrieval system makes it answerable in plain language instead of forcing a student to read
hundreds of individual reviews across dozens of professor pages.

## Sources (≥10 identified)

Each page is one professor teaching one course, holding many short student reviews. Selected for
variety across the CS curriculum and across sentiment (beloved, polarizing, and disliked
professors). Reviews are paginated; append `?page=2`, `?page=3`, etc. to collect more.

| #  | Source            | Description                                              | URL |
|----|-------------------|----------------------------------------------------------|-----|
| 1  | Smallberg — CS 31 | Intro to CS I; flipped classroom, ~154 reviews, well-liked | https://www.bruinwalk.com/professors/david-a-smallberg/com-sci-31/ |
| 2  | Nachenberg — CS 32| Intro to CS II; "one of the best at UCLA"                | https://www.bruinwalk.com/professors/carey-nachenberg/com-sci-32/ |
| 3  | Nowatzki — CS 33  | Computer organization; beloved, generous curve          | https://www.bruinwalk.com/professors/anthony-nowatzki/com-sci-33/ |
| 4  | Eggert — CS 33    | Computer organization; polarizing, brutal exams         | https://www.bruinwalk.com/professors/paul-r-eggert/com-sci-33/ |
| 5  | Eggert — CS 35L   | Software construction; heavy workload, mixed            | https://www.bruinwalk.com/professors/paul-r-eggert/com-sci-35l/ |
| 6  | Sahai — CS 181    | Theory of computing; "best CS class at UCLA"            | https://www.bruinwalk.com/professors/amit-sahai/com-sci-181/ |
| 7  | Meka — CS 181     | Theory of computing; whiteboard style, positive         | https://www.bruinwalk.com/professors/raghu-meka/com-sci-181/ |
| 8  | Hsieh — CS 180    | Algorithms; "messy, hard to follow" (negative)          | https://www.bruinwalk.com/professors/cho-jui-hsieh/com-sci-180/ |
| 9  | Burgin — CS 180   | Algorithms; detailed proofs, positive                   | https://www.bruinwalk.com/professors/mark-burgin/com-sci-180/ |
| 10 | Darwiche — CS 161 | Artificial intelligence; positive                       | https://www.bruinwalk.com/professors/adnan-darwiche/com-sci-161/ |
| 11 | Mirzasoleiman — CS 188 | ML special topics; clear pace, positive            | https://www.bruinwalk.com/professors/baharan-mirzasoleiman/com-sci-188-7/ |
| 12 | Ercegovac — CS M51A | Logic design of digital systems                       | https://www.bruinwalk.com/professors/milos-d-ercegovac/com-sci-m51a/ |

## Example questions the system should answer

1. How difficult are Paul Eggert's exams in CS 33, and what do students recommend to prepare?
2. For CS 33, do students recommend Nowatzki or Eggert?
3. Is CS 35L (with Eggert) a heavy-workload class?
4. What do students say about Cho-Jui Hsieh's lecturing style in CS 180?
5. Which professor is more recommended for CS 181 — Sahai or Meka?

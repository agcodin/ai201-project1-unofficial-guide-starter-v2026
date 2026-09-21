# Acceptance criteria: The Unofficial Guide

Written in unit 1, before any results existed.

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
In four of my questions, the answer is one sentence in one post, which is the easy case for this corpus. The housing lottery question is the likely miss. `advising_registration.txt` also says registration is "staggered by credit hours, same as the housing lottery," so a similar post could push the real answer out. Asking for 5 of 5 would assume that never happens.

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
The grounding instruction tells the model to name the file, and each chunk in the prompt is labeled with its filename, so the model has no material without a name on it. A miss here would mean the model ignored a direct instruction, and I'd rather catch that than allow one.

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that",
in at least 4 of 5 tries.

**Why this target:**
The questions about Mongolia, diesel engines, and ibuprofen share almost no words with posts about dining halls and dorms, so they should land far from everything in the store. I allow one miss for the Rust for-loop question, which could loosely match course posts about weekly problem sets.

## 4. Chunks stand on their own

At least 4 of 5 chunks printed by `python app.py chunks -n 5` can answer one specific question on their own (without the rest of the post), and no chunk in the whole index is shorter than 60 characters.

**Why this target:**
In Milestone 1, most posts had two or three facts in separate paragraphs (wait time in one, hours and price in another), so each paragraph chunk should answer something by itself. 60 characters is about the length of a title line alone. Anything shorter is a fragment, like the 2-character tail the starter produced on `advice_threads`. I allow one weak chunk in five because some posts end with a filler line that carries no fact.

## 5. The cited source is the right one

For my 5 test questions, the file named in the answer's `Source:` line is the one that actually contains the `expects` phrase in at least 4 of 5 answers.

**Why this target:**
Criterion 2 only checks that some source is named. This corpus is full of near-duplicates (each dining hall has a `_followup` post, each course has `_exams` and `_workload` posts), and I expect the model to sometimes cite a similar file that doesn't have the answer. Citing the original or its follow-up counts if that file contains the phrase. I allow one miss because the dining follow-ups repeat the original's numbers almost word for word.

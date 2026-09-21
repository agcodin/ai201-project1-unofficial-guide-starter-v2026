# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
Four of my five questions have their answer stated in a single sentence in one post, which is the easy case for this corpus. The housing-lottery question is the one I'd expect to miss: "credit hours" also shows up in `advising_registration.txt` ("staggered by credit hours, same as the housing lottery"), so a near-duplicate could crowd out the real answer. 5 of 5 would assume no crowding at all.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
All five, because the grounding instruction tells the model to name the file and every chunk is labelled with its filename in the prompt, so there's no chunk the model could draw on without a name attached. If this misses, it means the model ignored an explicit instruction, which I want to know about rather than tolerate one of.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
The out-of-scope questions (Mongolia, diesel engines, ibuprofen) share almost no vocabulary with dining halls and dorms, so I expect them to land far from anything in the store. I allow one miss because a question like the Rust for-loop could loosely match course posts about workload and "loops" of weekly assignments.

---

## 4. Chunks stand on their own

At least 4 of 5 chunks printed by `python app.py chunks -n 5` can answer one specific question on their own (without the rest of the post), and no chunk in the whole index is shorter than 60 characters.

**Why this target:**
In Milestone 1 I saw posts that each hold two or three separate facts in separate paragraphs (wait time, then hours and price), so if I split by paragraph each piece should still answer something. 60 characters is roughly the length of a post's title line alone; anything shorter is a fragment like the 2-character tail the starter produced on `advice_threads`. I allow one weak chunk out of five because some posts are one-liners of filler ("Nobody tells you this at orientation").

---

## 5. The cited source is the right one

For my 5 test questions, the file named in the answer's `Source:` line is the one that actually contains the `expects` phrase in at least 4 of 5 answers — not just any retrieved file.

**Why this target:**
Criterion 2 only checks that *a* source is named. This corpus has a lot of near-duplicates (every dining hall has a `_followup` post, every course has `_exams` and `_workload` spin-offs), so the model citing the wrong-but-similar file is the failure I actually expect. Citing either the original or its follow-up counts as correct if that file contains the phrase. One miss allowed because the dining follow-ups repeat the original's numbers almost word for word.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         
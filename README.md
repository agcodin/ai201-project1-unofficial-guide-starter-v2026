# The Unofficial Guide

Aryan Gaur, using the `campus_life` corpus.

# Unit 1

## What This Does

This system answers questions about student life from the `campus_life` corpus, 88 short posts students wrote about dining halls, dorms, courses, and admin rules like the housing lottery, dining dollars, add/drop, and parking permits. Ask it "how long is the lunch line at Kestrel Commons?" and it pulls the closest posts, answers from them alone, and names the file it used. If nothing in the corpus comes close to the question, it replies "I don't have enough information about that" and never calls the model. You run it from the command line with `python app.py ask "your question"`.

## Chunking Strategy

**Chunk size:** Whole paragraphs, merged up to 450 characters (`PARA_MAX_CHARS`). A paragraph under 60 characters (`PARA_MIN_CHARS`) joins its neighbor. That gives 168 chunks averaging 170 characters, with the shortest at 79 and the longest at 397.

**Overlap:** No character overlap. Every chunk starts with its post's title line ("Kestrel Commons", "BIOL 160 Cell Biology") instead.

With the starter's 800-character windows, 88 posts became 88 chunks, because almost no post is that long. So the decision I actually had to make was whether a post should ever be split. Most posts are a title and one to three short paragraphs, and each paragraph holds a different fact. In the dining posts, one paragraph covers wait times and what to order and the next covers hours and price. Splitting on blank lines keeps sentences whole, and a question about hours can match the hours paragraph directly.

A paragraph like "Hours are 7:00am to 9:00pm weekdays" is useless alone, though, since a dozen halls have a sentence in that exact format. Putting the title on every chunk fixes this. The title is the only thing a paragraph needs from the rest of its post, so I dropped character overlap. The floor started at 120 characters, and I lowered it to 60 after watching a question fail. Verrill Street Grill is open until 1:00am, but its hours paragraph is short, so it merged into the paragraph about wait times and burgers. The combined chunk no longer looked like a chunk about opening hours to the embedder, and it never came back for "which dining hall is open the latest", even at top-k of 16. Since every chunk already carries its post's title, a short paragraph doesn't need a neighbor for context. At 60 the shortest chunk in the index is 79 characters, still clear of the floor in criterion 4.

I changed the cleaning step after reading the first chunks. Lots of posts open with a line about the writer, like "Second-year here." or "Transferred in last year, so take this with a grain of salt." `course_biol_160.txt` even opens with "I lived here my sophomore year.", which makes no sense in a course review. These lines have no facts in them, so `clean_text` in `ingest.py` removes a fixed list of them (`FILLER_SENTENCES`), plus the "Nobody tells you this at orientation." line on the follow-up posts. Between that cleaning and the 60-character floor, 88 posts became 168 chunks.

## Sample Chunks

Printed with `python app.py chunks -n 5`.

**Chunk 1** | source: `admin_add_drop_deadline.txt` (chunk #0) | produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** | source: `course_cs_340_exams.txt` (chunk #0) | produced by: `chunker.py::split_documents`

```
CS 340 Databases — assessment

One midterm and a final, both open-book. Lightly curved, usually two or three points.
```

**Chunk 3** | source: `course_stat_150.txt` (chunk #0) | produced by: `chunker.py::split_documents`

```
STAT 150 Applied Statistics

Format is flipped: watch the recordings, class time is problem sets. Assessment: three equally weighted midterms, no final. No curve, but the lowest midterm is dropped.

Expect 5 to 6 hours a week outside class.
```

**Chunk 4** | source: `health_center.txt` (chunk #0) | produced by: `chunker.py::split_documents`

```
The health centre

Walk-in hours are 8am to 11am; everything after that is by appointment and appointments run about a week out. If something is urgent, go at 8am and wait rather than booking.
```

**Chunk 5** | source: `housing_morrow_house.txt` (chunk #2) | produced by: `chunker.py::split_documents`

```
Morrow House — what it's actually like

The bad: known damp problem on the ground floor; two rooms were taken offline in 2024.
```

## Sample Answer

**Question:** How long is the lunchtime wait at Kestrel Commons between 12:15 and 1:00?

**Answer:**

```
$ python app.py ask "How long is the lunchtime wait at Kestrel Commons between 12:15 and 1:00?"

The wait time at Kestrel Commons between 12:15 and 1:00 is 20 to 25 minutes.

Source: dining_kestrel_commons.txt

Sources retrieved: dining_halden_hall_followup.txt, dining_kestrel_commons.txt, dining_kestrel_commons_followup.txt, dining_north_kitchen_followup.txt, dining_the_ridgeway_cafe_followup.txt
```

An out-of-scope question gets stopped before the model runs:

```
$ python app.py ask "Who won the 1994 World Cup?"

I don't have enough information about that.

0 model calls this session
```

**My relevance cutoff:** 0.6 (`THRESHOLD` in `config.py`), with `TOP_K = 5`.

I ran my five test questions and the five `OUT_OF_SCOPE` questions through `python app.py retrieve` and recorded the best distance for each. My questions landed between 0.18 and 0.44. The out-of-scope ones landed between 0.81 and 0.92. Nothing fell between 0.44 and 0.81, and 0.6 sits 0.16 above my hardest question and 0.21 below the nearest out-of-scope one.

The gap is wide, but my margin on the in-corpus side is thin, and that is deliberate. My two comparison questions ("which dining hall is cheapest if I pay cash", "which is open the latest") are answerable from the corpus, yet no single post answers either one, so their best match sits furthest out at 0.431 and 0.440. I would rather see a wrong comparison than a refusal, because a wrong answer tells me retrieval handed the model an incomplete set. ECON 101 sits at 0.419, asking two things at once. Of the out-of-scope questions, Mongolia got closest at 0.82, matching the HIST 118 world history posts on vocabulary.

Each dining hall and course has two or three near-duplicate posts (the original, a `_followup`, and `_exams` or `_workload` versions), and they tend to fill the top two or three results together. Top-k of 5 leaves room for a couple of other posts after them.

| Question | In corpus? | Best distance |
|---|---|---|
| Which dining hall is cheapest if I pay cash? | Yes | 0.4310 |
| Which dining hall is open the latest? | Yes | 0.4400 |
| Do dining dollars roll over from spring semester to the next autumn? | Yes | 0.1849 |
| How are juniors and seniors ordered in the housing lottery? | Yes | 0.2250 |
| Is ECON 101 curved, and what kind of exams does it have? | Yes | 0.4190 |
| What is the capital of Mongolia? | No | 0.8120 |
| How do I change the oil in a diesel engine? | No | 0.9230 |
| Who won the 1994 World Cup? | No | 0.8859 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.8490 |
| How do I write a for loop in Rust? | No | 0.8640 |

I added two rules to `GROUNDING_INSTRUCTION` in `generate.py`. The model may only use documents about the hall, building, or course the question names, because every dining post follows the same template and Halden Hall's wait time could easily end up in an answer about Kestrel Commons. It also has to end with a `Source: <filename>` line, so criteria 2 and 5 are easy to check.

## How I Used AI

**1.** I used Claude to break the project into chunks I could work through one at a time, one per milestone: get the starter running, write the questions and criteria, replace the chunker, set the cutoff, then write up the README. For each step I asked it what "done" looked like, then checked the output myself before committing. When it planned the chunker, I had it print sample chunks so I could read them and decide whether each one held up on its own.

**2.** I also used Claude to track down bugs. `python test.py` failed at the start because my system Python was 3.9 and the course needs 3.11 or newer, so it helped me rebuild the virtual environment on Python 3.12. Later, after I stripped filler lines like "People keep asking so:" out of the posts, one chunk began with a lowercase "a lot of reading". Claude explained that removing the lead-in left the rest of the line untouched. Deleting the whole line would have lost real content, so I kept the targeted removal and added a step that capitalizes the first letter of each line.


**3.** In unit 2 I pasted the failing question, the chunks that came back, and the distances into Claude and asked for three possible causes at different pipeline stages, without ranking them. It gave me an embedding mismatch, top-k being too small, and the short-paragraph merge in my chunker. I tested them rather than picking one: raising top-k to 16 and printing every result ruled out the second, because Verrill's chunk never appeared at any depth.
---

# Unit 2

## Run Log — Before

`python run_eval.py --label before`, three runs per question, cache off. Raw file: `results/run_2026-09-23_2023_before.md`, written by `run_eval.py::main`. Scored by `scorer.py::judge`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 3/5 | 3/5 | 3/5 | MISSED |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks stand alone, none under 60 chars | 4 of 5 sampled, min 60 | 5/5, min 150 | same | same | MET |
| 5. The cited file contains the answer | 4 of 5 | 3/5 | 3/5 | 3/5 | MISSED |

Criteria 1, 3 and 4 are deterministic, so one measurement goes in all three columns. Criteria 2 and 5 were scored from each run's answer text.

Real output, run 1, generated by `generate.py::answer_from_chunks` over chunks from `chunker.py::split_documents`:

Criterion 1 and 5, "Which dining hall is cheapest if I pay cash?" (retrieved: `admin_dining_dollars.txt`, `dining_pellew_dining_hall.txt`, `housing_fenwick_court.txt`, `housing_innisfree_hall.txt`, `housing_morrow_house.txt`):

```
Based on the provided documents, there is no mention of the cash cost for any other dining hall to make a comparison, only the cost for Pellew Dining Hall, which is $11.75 cash.

Source: dining_pellew_dining_hall.txt
```

Criterion 1 and 5, "Which dining hall is open the latest?":

```
Pellew Dining Hall has hours from 7:00am to 8:00pm daily, making it open later than Halden Hall, which closes at 7:00pm.

Source: dining_pellew_dining_hall.txt, dining_halden_hall_followup.txt
```

Criterion 2, a passing answer that still names its file:

```
Juniors and seniors are ordered by accumulated credit hours first in the housing lottery, with ties broken randomly.

Source: admin_housing_lottery.txt
```

Criterion 3, from `run_eval.py::check_out_of_scope`: all five out-of-corpus questions were refused, best distances 0.825, 0.928, 0.886, 0.849 and 0.872, all above the 0.6 cutoff.

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer, 4 of 5 | MISSED | 3 of 5 on all three runs. Both comparison questions failed every time, so this is not a near miss or an unlucky pass. |
| 2 | Every answer names a source, 5 of 5 | MET | Every answer in all 15 runs ended with a `Source:` line naming a `.txt` file. `scorer.py::judge` requires a filename, so any answer without one would have failed. |
| 3 | Gate stops out-of-corpus questions, 4 of 5 | MET | 5 of 5 refused. The closest out-of-corpus question was 0.825 against a cutoff of 0.6, so the margin is wide. |
| 4 | Chunks stand alone, 4 of 5 sampled, none under 60 chars | MET | All five sampled chunks answered a question on their own, and the shortest chunk in the index was 150 characters. This is the criterion I trust least, for reasons in What I'd Do Differently. |
| 5 | The cited file contains the answer, 4 of 5 | MISSED | 3 of 5. Both comparison answers cited `dining_pellew_dining_hall.txt`, which holds neither the cheapest price nor the latest closing time. |

## Diagnoses

Both misses are the same failure, and it is one pattern rather than two. Criterion 5 is criterion 1 seen one stage later: the model cited the wrong file because the right file was never in front of it.

**Stage: retrieval, with a cause in chunking.** Both comparison questions need facts that are spread over seven dining posts, and top-k is 5. For "cheapest if I pay cash", retrieval returned one dining hall with a cash price (Pellew at $11.75) plus three housing posts, so the model compared a set of one and said so. That answer is honest about its own ignorance and still wrong, which makes it worse than a refusal, not better.

"Open the latest" has a second cause underneath the first. Verrill Street Grill closes at 1:00am, and its hours sit in a short paragraph. My chunker merged any paragraph under 120 characters into its neighbour, so that paragraph was absorbed into the one about wait times and burgers. The merged chunk reads as a chunk about queueing, and the embedder scored it accordingly. I checked by raising top-k to 16 and printing every result: Verrill's chunk did not appear at any depth. The problem was not that 5 was too few.

Not generation. For the housing lottery, dining dollars and ECON 101 questions, the answer was in the retrieved chunks and the model used it and cited it correctly, three times each. The prompt is doing its job.

## The Improvement

**What I changed:** `PARA_MIN_CHARS` in `config.py`, from 120 to 60, then re-indexed. That is the only change. Short paragraphs now stay their own chunk instead of being merged into the paragraph above. The index went from 99 chunks to 168, average length from 268 to 170 characters, shortest from 150 to 79.

**Why I picked it:** The diagnosis said Verrill's opening hours were invisible because they had been merged into a chunk about wait times, so the fix is to stop merging them. Every chunk already carries its post's title, so a short paragraph has the context it needs without a neighbour.

I tested the obvious alternative first and rejected it. Raising top-k to 8, 12 or 16 also fixed the cheapest question, but it never fixed the latest one, and it costs more of the context window on every question. The chunking fix repaired the cheapest question at the original top-k of 5.

### Run Log — After

`python run_eval.py --label after`. Raw file: `results/run_2026-09-23_2112_after.md`.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks stand alone, none under 60 chars | 4 of 5 sampled, min 60 | 5/5, min 79 | same | same | MET |
| 5. The cited file contains the answer | 4 of 5 | 4/5 | 4/5 | 4/5 | MET |

Real output, run 1, the question that changed:

```
Halden Hall is the cheapest if you pay cash, costing $10.00 per meal.

Source: dining_halden_hall.txt
```

The question that did not change:

```
Pellew Dining Hall is open until 8:00pm daily.

Source: dining_pellew_dining_hall.txt
```

**Did it help?** Yes, and less than the table suggests. Criteria 1 and 5 each went from 3 of 5 to 4 of 5 and both now meet their targets, stable across three runs. But one of the two broken questions is still broken, and it is the one the fix was aimed at. The cheapest question was collateral: with 168 smaller chunks, several dining posts now fit in the top 5 instead of three housing posts crowding them out, so the model finally had prices to compare.

Verrill Street Grill still never gets retrieved for "which dining hall is open the latest", now at 0.440 for the wrong post. Splitting its hours into their own chunk was necessary and not sufficient.

## What's Still Broken

**Criterion 1 and 5, the "open the latest" question.** The hours paragraph is now its own chunk and still does not match the question. "11:00am to 1:00am daily during term" and "open the latest" share no words, and the embedding model does not know that 1:00am is later than 8:00pm. This is an embedding failure, one stage past where I fixed things.

What I would do next is hybrid search from the Milestone 4 menu. BM25 would match "open" and "latest" against the literal hours text, and `rank-bm25` is already in `requirements.txt`. I stopped here because the unit allows one improvement and I had already used it, and because a second change made in the same pass would make it impossible to say which one moved the number.

Even hybrid search may not be enough, since nothing in the corpus says "latest". The honest fix might be that a superlative over 7 documents is not a retrieval problem at all, and top-k of 5 can never be the right tool for it.

**A quieter problem my test did not catch.** The comparison answers sound confident while comparing an incomplete set. "Pellew is open until 8:00pm daily" is true, and as an answer to "which is open the latest" it is wrong. My criteria catch that only because I happened to write `expects` phrases naming the right hall.

## What I'd Do Differently

**Criterion 4 is the one I would rewrite.** It says at least 4 of 5 sampled chunks "can answer one specific question on their own", and I cannot score that the same way twice. On the before run I counted 5 of 5. Reading the same chunks again, I would argue that a chunk reading "The bad: known damp problem on the ground floor; two rooms were taken offline in 2024" only answers a question if you already know it is about Morrow House, which the title line tells you. That is a judgment call, not a measurement, and two people would split on it. The character floor in the same criterion is fine, since 79 is either above 60 or it isn't. Next time I would drop the "stands on its own" half and measure something countable instead, like the share of chunks that contain a complete sentence from start to finish.

**Criterion 1 measured less than I thought.** "The retrieved chunks include one that contains the answer" is a substring test, and `scorer.py::judge` showed me both ways it lies. My `expects` for the latest question was originally "1:00am", which is a substring of "11:00am" in North Kitchen's hours, so a chunk about the wrong hall would have scored as a hit. I changed the phrase to "Verrill" before the before run. In the other direction, an answer saying "closes at 1am" would score as a miss while being correct. Next unit I would write `expects` as something that cannot appear by accident, like a hall name.

**I would also write one criterion about comparison questions specifically.** Four of my five criteria are satisfied by single-fact lookups, and the two questions that actually stress this system are only visible through criterion 1's count. A criterion naming cross-document questions would have pointed at the weakness directly instead of averaging it away.


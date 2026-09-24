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

---

# Unit 2

## Run Log: Before

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

## The Improvement

**What I changed:**

**Why I picked it:**

### Run Log: After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

## What's Still Broken

## What I'd Do Differently


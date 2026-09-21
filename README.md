# The Unofficial Guide

Aryan Gaur — corpus: `campus_life`


---

# Unit 1

## What This Does

The Unofficial Guide answers plain-English questions about student life using the `campus_life` corpus: 88 short posts students wrote about dining halls, dorms, courses, and the admin rules nobody explains (housing lottery, dining dollars, add/drop, parking). You ask something like "how long is the lunch line at Kestrel Commons?" and it retrieves the closest posts, answers only from them, and names the file the answer came from. If nothing in the corpus is close enough to the question, it says "I don't have enough information about that" instead of calling the model. It runs from the command line: `python app.py ask "your question"`.

## Chunking Strategy

**Chunk size:** whole paragraphs, merged up to a cap of 450 characters (`PARA_MAX_CHARS`); a paragraph under 120 characters (`PARA_MIN_CHARS`) gets merged into its neighbour. Result: 99 chunks, 268 characters on average, shortest 150, longest 422.
**Overlap:** no character overlap. Instead, the post's title line ("Kestrel Commons", "BIOL 160 Cell Biology") is repeated at the top of every chunk from that post.

The starter's 800-character windows turned 88 posts into 88 chunks, since almost no post reaches 800 characters. So the question wasn't really "what size" but "should a post ever come apart?" Reading the posts, most are a title plus one to three short paragraphs, and each paragraph is its own fact: one paragraph on wait times and what's good, another on hours and price. Splitting on blank lines keeps every sentence whole and lets a question about hours match the hours paragraph instead of the whole post. The catch is that a paragraph like "Hours are 7:00am to 9:00pm weekdays" means nothing on its own, since a dozen halls have a sentence in exactly that format. Repeating the title fixes that, and it's the only context a paragraph needs from the rest of its post, which is why I dropped character overlap. The 120-character floor exists because some paragraphs are a single throwaway line, and those read better attached to the paragraph next to them.

I also changed my mind about cleaning once I looked at the chunks. Many posts open with a lead-in like "Second-year here." or "Transferred in last year, so take this with a grain of salt.", and `course_biol_160.txt` opens with "I lived here my sophomore year.", which makes no sense in a course review. None of these carry facts, so `clean_text` in `ingest.py` now strips a fixed list of them (`FILLER_SENTENCES`), along with the "Nobody tells you this at orientation." tag on the follow-up posts. That is why the chunk count only went from 88 to 99: once the filler was gone, a lot of posts were short enough that their paragraphs merged back together.

## Sample Chunks

Printed with `python app.py chunks -n 5`.

**Chunk 1** — source: `admin_add_drop_deadline.txt` (chunk #0) — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

**Chunk 2** — source: `course_biol_160.txt` (chunk #1) — produced by: `chunker.py::split_documents`

```
BIOL 160 Cell Biology

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

**Chunk 3** — source: `course_hist_118_workload.txt` (chunk #0) — produced by: `chunker.py::split_documents`

```
Workload for HIST 118 Modern World History

A lot of reading, about 120 pages a week, but no problem sets. That's real time, not optimistic time.

It's front-loaded — the first month is heavier than the rest, partly because you're learning the format.
```

**Chunk 4** — source: `dining_the_atrium_followup.txt` (chunk #0) — produced by: `chunker.py::split_documents`

```
Re: The Atrium

Adding to what people have said about The Atrium. The wait figure of no queue matches what I've seen. If you're trying to eat between classes, go before 11:45 and it's a different building entirely.

Also worth saying: picked clean by 1:15 and not restocked again until the next morning.
```

**Chunk 5** — source: `housing_innisfree_hall_laundry.txt` (chunk #0) — produced by: `chunker.py::split_documents`

```
Laundry in Innisfree Hall

Machines take $1.75 wash, $1.75 dry, app-based. There are eight washers and six dryers for the building, which is the wrong ratio and means the dryers back up on Sunday evenings.

Best time to do laundry here is Tuesday or Wednesday morning. Sunday after 6pm you will wait.
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

An out-of-scope question is stopped by the gate before the model runs:

```
$ python app.py ask "Who won the 1994 World Cup?"

I don't have enough information about that.

0 model calls this session
```

**My relevance cutoff:** 0.6 (`THRESHOLD` in `config.py`), with `TOP_K = 5`.

I ran my five test questions and the five `OUT_OF_SCOPE` questions through `python app.py retrieve` and wrote down the best distance for each. The in-corpus group landed between 0.18 and 0.40, and the out-of-corpus group between 0.82 and 0.93, so there's a wide gap from 0.40 to 0.82 with nothing in it. I kept 0.6 because it sits roughly in the middle, about 0.2 clear of each group. The question closest to the edge is the ECON 101 one (0.403). It's phrased as two questions at once ("is it curved, and what kind of exams"), and that pulls its best match further away than the single-fact questions. If I'd set the cutoff at 0.4, the gate would have refused it even though the answer is sitting in `course_econ_101_exams.txt`. The out-of-scope question that got closest was Mongolia (0.82), which matched the HIST 118 world-history posts on vocabulary alone.

I kept top-k at 5 because each dining hall and course has two or three near-duplicate posts (the original, a `_followup`, an `_exams`/`_workload` spin-off). They tend to take the top two or three slots together, and 5 leaves room for something else behind them.

| Question | In corpus? | Best distance |
|---|---|---|
| How long is the lunchtime wait at Kestrel Commons between 12:15 and 1:00? | Yes | 0.1929 |
| Do dining dollars roll over from spring semester to the next autumn? | Yes | 0.1849 |
| How are juniors and seniors ordered in the housing lottery? | Yes | 0.2250 |
| When is the best time to do laundry at Fenwick Court? | Yes | 0.2989 |
| Is ECON 101 curved, and what kind of exams does it have? | Yes | 0.4028 |
| What is the capital of Mongolia? | No | 0.8246 |
| How do I change the oil in a diesel engine? | No | 0.9280 |
| Who won the 1994 World Cup? | No | 0.8859 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.8487 |
| How do I write a for loop in Rust? | No | 0.8717 |

I also tightened `GROUNDING_INSTRUCTION` in `generate.py` with two rules. First, only use a document about the exact hall, building or course the question names, because the dining posts all share one template and it would be easy to lift Halden Hall's wait time into an answer about Kestrel Commons. Second, end with a `Source: <filename>` line, so the source is always in the same place when I check criteria 2 and 5.

## How I Used AI

**1.** I had Claude Code (Opus 5) write `split_documents` and the filler-stripping in `clean_text`. When it printed sample chunks, `course_hist_118_workload.txt` began with a lowercase "a lot of reading, about 120 pages a week", because the lead-in it had removed was "People keep asking so:". Deleting the whole line would have lost the real content on that line, so the fix was one step that re-capitalises the first letter of each line after cleaning.

**2.** Claude kept the starter's 0.6 cutoff after measuring the distances (in-corpus 0.18–0.40, out-of-corpus 0.82–0.93). I checked the choice against the edges: the two-part ECON 101 question sits at 0.403, so any cutoff near 0.4 would have refused a question the corpus answers. That's why the cutoff stays in the middle of the gap rather than hugging the in-corpus group.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->

# Results

The experimental record: what was tested, on what, how it was scored, what came out, and
what the results do not support. The counts on this page come from the files in
[`results/`](../results/); [`results/README.md`](../results/README.md) says which can be
recomputed from scratch there and which rest on a stored summary.

## 1. Questions

1. Given a scanned statement, how often does the method reach the right conclusion, and
   when a statement has been altered, does it name the altered row?
2. How do the two models it uses perform when each is asked to do the whole job alone?
3. What does the second reader contribute?
4. If the reading is already perfect, does it matter whether a model or code decides?

## 2. Materials

### 2.1 Documents

Source: [AgamiAI/Indian-Bank-Statements](https://huggingface.co/datasets/AgamiAI/Indian-Bank-Statements)
(Apache 2.0), a public corpus of synthetic bank statements in two layouts, six pages and
about 160 transactions each, in Indian rupees. "Type 1" has separate debit and credit
columns. "Type 2" has one amount column and a `Cr/Dr` column.

As published, none of the corpus's digital statements ties to its own balance column:
3,901 of 32,349 rows break the running balance, with at least six breaks in each of the
200 documents. So the corpus contains no statement that should be confirmed and no
alteration of known origin. Both were built from it
([`benchmark/external/agami_patch.py`](../benchmark/external/agami_patch.py)):

- **Clean** documents: the amounts are corrected to agree with the printed balances.
  The printed closing balance equals the last row's balance in all 200 documents, while
  the chain recomputed from the published amounts ends below the closing balance in 184
  of them, on it in 16, and above it in none. A one-sided error points at the amounts,
  which is why they are treated as the faulty field.
- **Altered** documents: a clean document in which one amount is then changed by a
  known quantity, with every balance left as it was. The row, the old value and the new
  value are recorded.

Every built file is read back through its text layer and compared, amount by amount and
date by date, with its answer key before it is used. 191 of the 200 could be built and
all 191 read back exactly; the other 9 are excluded. The source audit, the build
manifest with the reason for each exclusion, and the answer keys of the documents used
here are in [`results/corpus/`](../results/corpus/) and
[`results/answer_keys/`](../results/answer_keys/).

Each page is then flattened to a greyscale image at 300 dpi with a slight blur, a smooth
lighting gradient, sensor noise and JPEG compression
([`benchmark/external/rasterise.py`](../benchmark/external/rasterise.py)), and the result
is checked to carry no text layer. No skew or rotation is applied.

### 2.2 The sample

20 documents, taken in the corpus's own order: numbers 1 to 11 of layout Type 1 and
numbers 1 to 9 of layout Type 2. The tenth Type 2 document could not be built, which is
why there are 9 of that layout. Groups alternate by position within each layout (odd
numbers clean, even numbers altered), which gives 11 clean and 9 altered. Assignment is
by position, not random.

| | Type 1 | Type 2 | total |
|---|---:|---:|---:|
| clean | 6 | 5 | 11 |
| altered | 5 | 4 | 9 |
| rows | | | 3,221 |

In file names and document ids the two groups appear as `repaired` (clean) and
`tampered` (altered).

**These are development documents.** They were used while the method was built, and
none was held out.

### 2.3 Models

| role | model | accessed through |
|---|---|---|
| first reader | `google/gemini-3.1-flash-lite` | OpenRouter |
| second reader | `qwen/qwen3.5-flash-02-23` | OpenRouter |

Temperature 0. Neither model returned identical output on every repetition (section
4.2).

## 3. Conditions and measures

### 3.1 Conditions

| condition | reads | checks | decides |
|---|---|---|---|
| **Probity** | Gemini; Qwen re-reads pages where a rule failed; Gemini once more, at higher resolution, where the two agree and a rule still fails | rules as code | code |
| **No second reader** | Gemini; Gemini re-reads at higher resolution | rules as code | code |
| **Gemini alone** | Gemini | Gemini | Gemini |
| **Qwen alone** | Qwen | Qwen | Qwen |

In the two "alone" conditions
([`benchmark/run_llm_alone.py`](../benchmark/run_llm_alone.py)) the model first
transcribes the statement one page per request, with the instruction the framework's
reader uses. It is then sent every page image together with that transcription and
asked to (1) correct any debit, credit or balance it misread, (2) check the running
balance on every row and the closing total exactly, (3) say whether the statement is
consistent, and (4) name the rows where the printed document does not add up. It is then
shown its own answer and asked to re-examine it. The full prompt is in the source file.

The answer format lets the model correct amounts and balances, not dates or header
fields. That does not affect the scores below: neither model's transcription has a
wrong row date or a wrong opening or closing balance in any of the 20 documents. Qwen
does misread the statement period in 8 documents; no condition can correct that field,
so it is scored separately and kept out of the main measure.

Three answers are scored for each model: the **first** answer; the **re-examined**
answer on its own; and the **final** answer, which is the re-examined one where the
model returned one and otherwise the first. "Final" is a fallback rule, not a choice of
the better answer, and is the one used in summary tables.

**This compares workflows.** Probity differs from a model working alone in more than who
decides: it re-reads one page at a time at a higher resolution (400 dpi against 170),
and it draws on a second model family. The comparison shows what each complete
arrangement achieves at about the same cost. The experiment that isolates the deciding
step is in section 4.5.

### 3.2 Measures

| measure | definition |
|---|---|
| **clean confirmed** | Probity: conclusion `CONFIRMED` on a clean document. Model alone: it answered `consistent: true` |
| **altered confirmed** | the same, on an altered document. The correct value is zero |
| **altered row named, and no other** | Probity: conclusion `DOCUMENT_INCONSISTENT` and the only failing row is the altered one. Model alone: it answered `consistent: false` and listed that row and no other. Either the 0-based index or the printed 1-based number is accepted |
| **altered row among those named** | as above, but other rows may be named too |
| **ledger exact** | on the final transcription, every row's date, debit, credit and balance, and the opening and closing balances, equal the answer key. Rows are compared as a multiset. A blank amount and a zero are treated alike. **Descriptions, the account number, the statement period, row order and page assignment are not part of this measure** |
| **period exact** | the period start and end dates in the header equal the answer key |
| **no usable answer** | model alone only: the reply was cut off at the token limit, the provider aborted it, or it was not a valid answer. Such a document stays in every denominator and counts as not confirmed |

For an altered document the answer key holds the altered figure, because that is what
is printed. Reading it faithfully and concluding correctly are separate measures.

Intervals are 95% Wilson intervals. With 9 and 11 documents they are wide, and because
the sample was neither random nor held out they describe the precision of the counts
more than they license a claim about other documents.

## 4. Results

### 4.1 Main comparison

| | Gemini alone | Qwen alone | Probity |
|---|---:|---:|---:|
| clean confirmed | 10 of 11 (62–98%) | 11 of 11 (74–100%) | 10 of 11 (62–98%) |
| altered confirmed (should be 0) | 8 of 9 (56–98%) | 7 of 9 (45–94%) | **0 of 9** (0–30%) |
| altered row named, and no other | 0 of 9 | 0 of 9 | **9 of 9** |
| altered row among those named | 0 of 9 | 0 of 9 | **9 of 9** |
| ledger exact | 3 of 20 | 17 of 20 | **19 of 20** |
| period exact | 20 of 20 | 12 of 20 | 20 of 20 |
| no usable answer | 0 of 20 | 1 of 20 | n/a |
| cost per document | $0.047 | $0.040 | $0.045 |

Model-alone figures are for the final answer. Probity's are identical in both samples
of section 4.2.

Reading the table:

- Each model, working alone and asked explicitly to find inconsistencies, declared most
  of the altered statements consistent (8 of 9 and 7 of 9), and neither identified the
  altered row in any document, alone or among others.
- Reading well is not the same as judging well. Qwen's final transcription is exact on
  17 of 20 documents, far better than Gemini's 3, and it still declared 7 of the 9
  altered statements consistent.
- With the same two models and a similar cost, Probity confirmed no altered statement
  and named the altered row in each.
- On clean statements all three conditions are close (10, 11 and 10 of 11). Confirming
  a clean statement is the easy direction for a model that seldom objects. Probity's
  one miss is an `UNRESOLVED`, examined in section 4.3.
- Probity's result of 0 of 9 is compatible with a true rate anywhere up to about 30%.

### 4.2 Two samples of the same experiment

The models do not return the same transcription every time, so one run is one sample.
The Probity condition was run twice with independent model replies.

| | sample A | sample B |
|---|---:|---:|
| clean confirmed | 10 of 11 | 10 of 11 |
| altered confirmed | 0 of 9 | 0 of 9 |
| altered row named, and no other | 9 of 9 | 9 of 9 |
| ledger exact | 19 of 20 | 19 of 20 |
| rows corrected | 65 | 65 |
| second-reader page requests | 28 | 27 |
| documents that needed the second reader | 16 | 15 |
| third readings requested (the two models agreed, the rule failed) | 9 | 9 |
| third readings that changed a row | 0 | 0 |

The two samples are independent sets of model replies for the same 20 documents. The
conclusions agree on all 20. The corrections differ in detail (for instance, one
document needed one correction in A and none in B), which is the run-to-run variation
showing through.

In both samples a third reading was requested exactly once per altered document, for
the altered row, and each time it had the same figures as the other two readings. So
the tie-break changed nothing in the benchmark, and did not turn any altered row into
one that ties.

**The third reading at work.** The benchmark never needed it to change a row. The worked
example in [`examples/scanned/`](../examples/scanned/) does. In that run of
`Type2_00002` the second reader made the same debit/credit mistake as the first reader
on row 148, so the two models agreed on a wrong reading. The first reader's
higher-resolution transcription has that amount as a credit; with it the row ties and
is corrected, and the document is reported as inconsistent at row 127, the alteration,
and nowhere else. That is one case, so it shows what the step does and not how often it
succeeds.

### 4.3 What the first reader gets wrong

Rows whose values were replaced, by type, in sample A (sample B in brackets):

| error in the first reading | rows |
|---|---:|
| amount missing: a page transcribed without its amount column | 34 (34) |
| amount in the wrong column, debit for credit or the reverse | 25 (26) |
| a digit misread in an amount | 4 (3) |
| a digit misread in a balance | 2 (2) |
| **total corrected** | **65 (65)** of 3,221 rows |

The missing amounts are one page of one clean document (`Type2_00007`), 35 rows. 34 were
recovered and one was not, in both samples: on that row the first reader had also
dropped a digit from the reference number in the description
(`IMPS-78918018766-…` for `IMPS-789186018766-…`), so the two transcriptions of the row
no longer carried the same number and guard 3 refused to treat them as the same line.
The document ended `UNRESOLVED` with that single row reported. This is the guard working
as specified and costing a confirmation: it refuses to pair two transcriptions whose
reference numbers differ, because that is also how a value from a look-alike
neighbouring line would present.

The other 19 documents match the answer key on the ledger in both samples.

Descriptions are a different matter. They are transcribed by the first reader and
checked by nothing. At least 140 of 3,221 (4.3%) differ from the answer key in sample A
and 141 (4.4%) in sample B. This is a lower bound: descriptions are compared as a
multiset after normalising case, spacing and slashes, so two descriptions exchanged
between rows are not counted.

### 4.4 What the second reader contributes

The Probity condition with the second reader removed. When a rule fails, the first
reader is asked to transcribe that page again at a higher resolution, and its second
transcription goes through exactly the same comparison and guards as a second reader's
would. The one difference is by design: a model agreeing with itself confirms nothing,
so this arrangement can correct a row but can never report a document as inconsistent.

| | Gemini re-reading its own pages | Probity (Gemini, then Qwen) |
|---|---:|---:|
| clean confirmed | 8 of 11 (43–90%) | 10 of 11 |
| altered confirmed | 0 of 9 | 0 of 9 |
| altered documents ending `DOCUMENT_INCONSISTENT` | 0 of 9 | 9 of 9 |
| altered documents ending `UNRESOLVED` | 9 of 9 | 0 of 9 |
| altered row is the only row still failing | 3 of 9 | 9 of 9 |
| rows corrected | 53 | 65 |
| ledger exact | 11 of 20 | 19 of 20 |

A same-model re-read at higher resolution recovers most misreadings: 53 rows, against
65 with a second model. What it cannot do is separate the two cases that matter. All 9
altered documents end unresolved, as do 3 clean ones, and a reviewer cannot tell which
is which. The second reader's contribution is partly more corrections and mainly the
ability to say "two different models read this the same way, and it does not add up".

### 4.5 Does it matter who decides?

A separate experiment that holds the reading fixed
([`benchmark/ablate_decider.py`](../benchmark/ablate_decider.py)). 191 digital
statements, 97 clean and 94 altered, are read from their text layer; all 191 readings
match the answer key on every amount and date. The same reading is then judged three
ways.

| who decides | clean accepted | altered accepted |
|---|---:|---:|
| the rules, as code | 97 of 97 (96–100%) | 0 of 94 (0–4%) |
| `gemini-3.1-flash-lite`, shown the rules' results | 91 of 97 (87–97%) | 0 of 94 (0–4%) |
| `gemini-3.1-flash-lite`, shown only the reading | 88 of 97 (83–95%) | 84 of 94 (82–94%) |

Given a perfect transcription and nothing else, the model accepted 84 of 94 altered
statements. Given the rules' findings it accepted none, and rejected six clean ones.

### 4.6 Each model alone, in detail

| | Gemini first | Gemini re-examined | Gemini final | Qwen first | Qwen re-examined | Qwen final |
|---|---:|---:|---:|---:|---:|---:|
| clean confirmed | 10/11 | 10/11 | 10/11 | 11/11 | 11/11 | 11/11 |
| altered confirmed | 9/9 | 8/9 | 8/9 | 8/9 | 7/9 | 7/9 |
| altered row named, and no other | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| altered row among those named | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| ledger exact | 4/20 | 3/20 | 3/20 | 16/20 | 17/20 | 17/20 |
| period exact | 20/20 | 20/20 | 20/20 | 12/20 | 12/20 | 12/20 |
| no usable answer | 0 | 0 | 0 | 1 | 1 | 1 |

**Gemini** always answered, and nearly always said the statement was consistent. On the
one altered statement it refused after re-examination, it named five rows (125 to 129);
the altered row is 108. A typical final answer on an altered statement (the altered row is 6): *"The statement
is consistent after correcting the transcription error in row 48, where a blank credit
field was incorrectly transcribed as having a value."* Its corrections did not improve
its transcription: 4 documents were ledger-exact after its first answer and 3 after
re-examination.

**Qwen** transcribes much better than Gemini and reasons at length before answering. Its
verification requests were given the largest reply the model allows (65,536 tokens). It
gave a usable answer on 19 of the 20 statements; on the remaining one, an altered
statement, its reply ran past that limit and was cut off. Of the 8 altered statements it
did answer, it declared all 8 consistent at first and 7 after re-examination. On the
eighth it then refused and named row 154; the altered row is 108. Three of its requests
were aborted by the provider and were sent again, successfully.

### 4.7 Choosing the second reader

Before the experiments, candidate second readers each transcribed one 167-row scanned
statement in full. This is a single-document probe, recorded in
[`results/second_reader_probe/`](../results/second_reader_probe/), and is the reason
Qwen was chosen, not a result.

| model | rows returned | field accuracy score | cost |
|---|---:|---:|---:|
| `qwen/qwen3.5-flash-02-23` | 167 | 98.8% | $0.016 |
| `meta-llama/llama-4-scout` | 168 | 95.3% | $0.010 |
| `bytedance-seed/seed-2.0-mini` | 167 | 92.0% | $0.023 |
| `mistralai/mistral-small-3.2-24b-instruct` | 86 | 50.9% | $0.007 |

The score counts every unmatched row as four wrong cells, so it is harsher than a
cell-by-cell comparison; it is used here only to rank the candidates.

### 4.8 Cost and time

Measured on sample B, in which every request was paid for.

| | requests | cost | per document | time per request |
|---|---:|---:|---:|---:|
| first reader, 6 pages per document | 120 | $0.752 | $0.0376 | 10 s |
| second reader, pages where a rule failed | 27 | $0.090 | $0.0045 | 141 s |
| third reading, where the two models agree | 9 | $0.063 | $0.0031 | 13 s |
| **total** | 156 | **$0.905** | **$0.0452** | |

The second reader accounts for about 10% of the cost and most of the time, and the
third readings for about 7%. A document that needs no second look takes about a minute;
one that needs two pages re-read takes about six minutes when run on its own.

Model-alone costs: Gemini $0.038 to transcribe plus $0.009 to verify and re-examine,
$0.047 per document; Qwen $0.018 plus $0.022, $0.040 per document, including requests
that had to be sent again.

What the whole set costs to run from scratch, about four dollars:

| | cost | basis |
|---|---:|---|
| Probity, one sample | $0.91 | ledgers of sample B |
| Gemini alone | $0.93 | $0.75 transcription (as sample B's first reader) + $0.18 verification ledger |
| Qwen alone | $0.80 | transcription and verification ledgers |
| no second reader | about $0.95 | estimate: the first reading plus 28 page re-reads; not ledgered separately |
| who decides, 191 statements | $0.63 | total recorded by the original run; its ledger is not in `results/` |

Result files produced by replaying cached replies show a cost of zero; the ledgers of
the paid runs are in [`results/ledgers/`](../results/ledgers/).

## 5. Threats to validity

**No held-out data.** All 20 documents were used during development. The figures are an
upper estimate of what to expect on new documents.

**The alteration is the kind the main rule tests.** One amount is changed and the
balances are left alone, which is exactly what the row-balance rule detects on a perfect
reading. The experiment therefore measures whether reading and correction preserve that
signal through a degraded scan. It does not measure detection of fraud in general, and
an alteration that also adjusts the later balances would pass every rule.

**One corpus.** Two layouts from one synthetic source, one currency, one locale, no
skew or rotation, no handwriting, no stamps, no real documents.

**Small sample, not random.** 11 clean and 9 altered, assigned by position.

**The comparison is between workflows.** Section 3.1. A model working alone might do
better with page-by-page verification, higher resolution, or a stronger model. Only two
low-cost models were tested, each in one configuration.

**The first reader is the weaker transcriber.** Qwen transcribes these documents more
accurately than Gemini. Probity was run with Gemini first because it is several times
faster; the reverse arrangement was not tested.

**Non-determinism.** Section 4.2. Two full samples agree. A separate run of one document
showed two models sharing a misreading; the tie-break added for it is the same model as
the first reader at a higher resolution, so a misreading that survives a sharper image
is not caught.

**The tie-break could be wrong in the unsafe direction.** A third transcription that
misread an altered figure as exactly the value that ties would be accepted. It agreed
with the other two readings on all 18 altered rows across the two samples.

**A correction is not a proof.** A value is taken from the second reader because it
makes the arithmetic close. In the two Probity samples every row that was corrected
then matched the answer key, which is evidence that the rule selects true values here.
It is not a guarantee, and [METHOD.md](METHOD.md) section 6 says why.

**Guards trade coverage for safety.** Each guard blocks some right corrections along
with the wrong ones it targets. The matching rule cost one clean confirmation in 11
here; on documents with noisier descriptions it would cost more.

**Only arithmetic fields are protected.** At least one description in twenty-three is
wrong and nothing notices; the statement period is transcribed once and checked only
against the row dates.

## 6. Reproducing

```bash
pip install -e ".[all]"

# build: correct the amounts, alter one, verify, flatten to images
python -m benchmark.external.agami_patch --dir <downloaded pdf/json pairs> --out data/built
python - <<'EOF'
import json
from benchmark.external.rasterise import build_scanned

# the 20 documents used here, by the id of their digital source
wanted = {d["doc_id"].replace("-scan-", "-") for d in json.load(open("results/corpus/sample_20.json"))}
built = json.load(open("data/built/manifest.json"))
built["documents"] = [d for d in built["documents"] if d["doc_id"] in wanted]
json.dump(built, open("data/built/manifest_20.json", "w"))
build_scanned("data/built/manifest_20.json", "data/scanned")
EOF

export OPENROUTER_API_KEY=...

# Probity
python -m benchmark.run_scanned --manifest data/scanned/manifest.json \
       --model google/gemini-3.1-flash-lite --second-model qwen/qwen3.5-flash-02-23 \
       --workers 8 --out benchmark/results/probity

# no second reader
python -m benchmark.run_scanned --manifest data/scanned/manifest.json \
       --model google/gemini-3.1-flash-lite --workers 8 --out benchmark/results/no_second_reader

# each model alone
python -m benchmark.run_llm_alone --manifest data/scanned/manifest.json \
       --model google/gemini-3.1-flash-lite --workers 4 --out benchmark/results/gemini_alone
python -m benchmark.run_llm_alone --manifest data/scanned/manifest.json \
       --model qwen/qwen3.5-flash-02-23 --json-hint --max-tokens 65536 --workers 8 \
       --out benchmark/results/qwen_alone

# who decides
python -m benchmark.ablate_decider --manifest data/built/manifest.json
```

A fresh run draws new model replies and will not reproduce these counts exactly. The
whole set costs about four dollars (section 4.8).

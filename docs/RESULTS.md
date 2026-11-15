# Results

The evaluation on documents the method had never seen: 120 scanned bank statements and
100 real scanned receipts. The protocol, the test split, the measures and the outcomes
that would count against the method were written and committed before any test document
was built ([`benchmark/protocol/PROTOCOL.md`](../benchmark/protocol/PROTOCOL.md)). The
code was then frozen at the tag `sealed-run-1`, the test set was built with it, and each
condition was run once. Everything is reported, including what went against the method.

Every count on this page can be recomputed from the scored outcomes in
[`results/sealed/`](../results/sealed/) with `python results/sealed/tables.py`.
Percentages in brackets are 95% Wilson intervals.

The 20 statements the method was developed on, and the experiment that isolates the
deciding step, are in [DEVELOPMENT_SAMPLE.md](DEVELOPMENT_SAMPLE.md).

## 1. Findings

1. **A low-cost model asked to check a statement confirms almost anything.** Gemini
   alone confirmed 50 of 52 statements with a detectable alteration and Qwen alone 22
   of 26. Neither located one. Rewording the instructions did not change this.
2. **The same models inside the state machine let one through in 52 and located 42.**
   Cost was about the same as the model working alone: $0.045 against $0.047 a
   statement.
3. **That one counts against the method.** The protocol said in advance that any
   detectable alteration confirmed would. A debit had been moved to the credit column,
   and the first reader transcribed it in the column it had come from. The reading was
   consistent, so no rule failed and no second look was taken (section 5.1).
4. **Giving the model a Python interpreter does not replace the state machine.** It
   stopped the model confirming altered statements (2 of 52), but the model then
   confirmed only 17 of 40 clean ones, located the altered row exactly in 9 of 52, and
   returned no answer for 13 statements.
5. **Conventional OCR with the same rules is not enough either.** It confirmed 9 of 40
   clean statements and none on the two harder scan tiers. The vision models are doing
   work the rules need.
6. **The method's central assumption holds on this material.** Where two different
   models transcribe an amount identically, it is what is printed 99.993% of the time
   (2 shared misreadings in 28,113 cells, both on one row).
7. **Safety is paid for in coverage.** 8 of 40 clean statements ended unresolved and
   went to a person. None was reported as inconsistent.
8. **It carries to a second document type with no new code.** On 100 real receipts
   described by one YAML file, Probity confirmed 50 of 50 clean and 0 of 50 altered;
   Gemini alone confirmed 24 of the 50 altered and Qwen alone 34.
9. **`CONFIRMED` protects the money, not the dates.** Of 55 confirmed statements, 54
   have every amount and balance right; the exception is the one in finding 3. Eleven
   carry at least one misread date that still falls in order.

## 2. Materials

### 2.1 Bank statements

Source: the digital split of AgamiAI/Indian-Bank-Statements, a synthetic corpus in two
layouts. Of its 200 statements, 191 can be built. They were split by source statement
with a fixed seed into 21 seen in development, 50 further development statements and
**120 sealed test statements**
([`split.json`](../benchmark/protocol/split.json)). Each test statement has six pages
and about 160 transactions.

Each test statement was assigned by a seeded draw to one group and one scan tier, and
then flattened to images with no text layer.

| group | statements | what was done | can arithmetic detect it? |
|---|---:|---|---|
| clean | 40 | nothing; the statement ties | n/a |
| amount | 16 | one amount changed, balances untouched | yes |
| balance | 12 | one balance changed | yes |
| row removed | 12 | one row whited out, balances untouched | yes |
| direction | 12 | one amount moved from debit to credit or the reverse | yes |
| amount, balances adjusted | 12 | one amount changed and every later balance recomputed | **no** |
| row removed, balances adjusted | 8 | one row whited out and every later balance recomputed | **no** |
| text | 8 | a description changed, no figure touched | **no** |

The 52 statements in the four "yes" groups are the *detectable* alterations. The 20 with
adjusted balances are internally exact, and the rules cannot object to them; they are in
the test so that this number is on the page. Each alteration was verified in the built
PDF before flattening: the text reads as intended, and an audit of the ledger breaks at
exactly the expected rows.

| tier | statements | rendering |
|---|---:|---|
| T1 | 40 | 300 dpi greyscale, blur, uneven lighting, sensor noise, JPEG |
| T2 | 40 | T1 plus rotation of up to 2 degrees and a shadow band |
| T3 | 40 | T1 plus perspective distortion, stronger blur and lower JPEG quality, as from a phone |

### 2.2 Receipts

Source: CORD, a public corpus of real scanned receipts with published transcriptions.
A receipt can serve only if its published transcription satisfies the receipt rules, has
at least two lines and has no discount or nested line. The test set is every such
receipt of the corpus's test split (35) topped up to 100 with a seeded draw from its
training split (65), which was not opened during development. Half were altered by
repainting one line amount or the total in the image. Every receipt, altered or not, was
repainted once, so that retouching does not mark the altered group.

The receipt document type is [one YAML file](../examples/specs/receipt_cord.yaml): its
fields, its table, and five rules written as formulas (the lines sum to the subtotal,
the subtotal and charges sum to the total, cash less total is the change, quantity times
unit price is the line amount).

### 2.3 Models

`google/gemini-3.1-flash-lite` and `qwen/qwen3.5-flash-02-23`, through OpenRouter, at
temperature 0. Both are low-cost models. Larger models were excluded by design: the
question is what can be made reliable cheaply. Replies are not deterministic.

## 3. Conditions and measures

| condition | what it is | statements | receipts |
|---|---|---:|---:|
| **Probity** | Gemini reads; rules check; Qwen reads again where a rule fails; a third reading breaks ties; code decides | 120 | 100 |
| Gemini alone | Gemini transcribes, then, with every page and its own transcription in front of it, corrects what it misread, checks every row and the total, says whether the document is consistent, names the rows that are not, and re-examines its answer | 120 | 100 |
| Qwen alone | the same, with Qwen | 60 | 100 |
| Gemini with an interpreter | as Gemini alone, and it may run Python on its transcription, up to six times, before answering | 120 | 100 |
| OCR and rules | a conventional OCR engine, a position-based table parser, the same rules, no language model | 120 | 100 |

Qwen alone ran on a seeded 60-statement subset, balanced over groups, because it is slow
and the budget was fixed. Gemini alone uses Probity's first reading as its transcription,
so the two start from the same reading of every page.

**Measures.** *Confirmed*: the final word is that the document is consistent.
*Located*: the document is reported as inconsistent and the altered row is among those
named. *Located exactly*: and no other row is named. For a changed balance, two rows
fail by construction and both are expected. *Amounts, balances and dates exact*: every
row's date, debit, credit and balance and the opening and closing balances match the
answer key. For receipts, a failed sum cannot say which line is wrong, so *located*
means a rule that should fail is among those named.

For OCR and rules there is no second reader, so a statement on which a rule fails is
scored as reported at the failing rows. That is the most favourable reading of it: it
can be credited with finding an alteration, at the price of false reports on clean
statements it misreads.

## 4. Results on bank statements

### 4.1 Main comparison

<p align="center">
  <img src="assets/results.svg" alt="Three panels of horizontal bars comparing five systems on 120 scanned statements. Altered statements confirmed, which should be zero: Probity 1 of 52, Gemini alone 50 of 52, Qwen alone 22 of 26, Gemini with a Python interpreter 2 of 52, OCR with the same rules 0 of 52. Altered row named and no other: Probity 42 of 52, Gemini alone 0 of 52, Qwen alone 0 of 26, Gemini with a Python interpreter 9 of 52, OCR with the same rules 15 of 52. Clean statements confirmed: Probity 32 of 40, Gemini alone 36 of 40, Qwen alone 20 of 20, Gemini with a Python interpreter 17 of 40, OCR with the same rules 9 of 40." width="100%">
</p>

| 120 sealed statements | **Probity** | Gemini alone | Gemini with interpreter | OCR and rules | Qwen alone (60) |
|---|---:|---:|---:|---:|---:|
| clean confirmed | **32 of 40** (65-90%) | 36 of 40 (77-96%) | 17 of 40 (29-58%) | 9 of 40 (12-38%) | 20 of 20 (84-100%) |
| detectable alterations confirmed (should be 0) | **1 of 52** (0-10%) | 50 of 52 (87-99%) | 2 of 52 (1-13%) | 0 of 52 (0-7%) | 22 of 26 (66-94%) |
| detectable alterations located exactly | **42 of 52** (68-89%) | 0 of 52 (0-7%) | 9 of 52 (9-30%) | 15 of 52 (18-42%) | 0 of 26 (0-13%) |
| detectable alterations located | 42 of 52 | 0 of 52 | 42 of 52 | 21 of 52 | 0 of 26 |
| clean statements reported as inconsistent | **0 of 40** | 4 of 40 | 20 of 40 | 11 of 40 | 0 of 20 |
| amounts, balances and dates exact | **84 of 120** (61-77%) | 22 of 120 (12-26%) | 26 of 120 (15-30%) | 31 of 120 (19-34%) | 39 of 60 (52-76%) |
| no usable answer | 0 | 0 | 13 | 0 | 3 |
| cost per statement | $0.045 | about $0.047 | about $0.064 | none | $0.041 |

On the same 60 statements as Qwen alone, Probity confirmed 15 of 20 clean and 0 of 26
detectable alterations, and located 22 of 26 exactly.

**Reading the table.** The first row is the easy direction: a system that says
"consistent" to everything scores 40 of 40. The second and third rows are the test. The
two models alone sit near the top of the first row for that reason, and it is why they
confirm almost every altered statement as well.

**The interpreter.** With Python available, the model computes the running balance and
sees that something fails. That is why it rarely confirms an altered statement and why
the altered row is among the rows it names in 42 of 52. But it is computing on its own
uncorrected transcription, and it has no way to tell a misread from an alteration. It
names every row that fails, so it locates the altered row exactly in 9 of 52, reports 20
of 40 clean statements as inconsistent, and on 13 statements runs out of reply length
before answering. A model that can compute still needs something to decide which
failures belong to the reading and which to the document.

**OCR and rules.** On the first scan tier it does respectably: 9 of 12 clean confirmed,
15 of 20 located exactly. On the two harder tiers it confirms no clean statement and
locates nothing exactly.

### 4.2 What Probity concluded

| group | statements | confirmed | inconsistent, altered row named exactly | unresolved |
|---|---:|---:|---:|---:|
| clean | 40 | 32 | 0 | 8 |
| amount | 16 | 0 | 12 | 4 |
| balance | 12 | 0 | 9 | 3 |
| row removed | 12 | 0 | 10 | 2 |
| direction | 12 | 1 | 11 | 0 |
| amount, balances adjusted | 12 | 10 | 0 | 2 |
| row removed, balances adjusted | 8 | 6 | 0 | 2 |
| text | 8 | 6 | 0 | 2 |

No statement was reported as inconsistent at a row that had not been altered. Every
`DOCUMENT_INCONSISTENT` conclusion in the run, 42 of 42, names exactly the altered row.

To reach these conclusions the machine corrected 546 misread rows. A second reading was
needed on 99 of the 120 statements; 21 passed every rule on the first reading.

### 4.3 By scan quality

| Probity | T1 | T2 | T3 |
|---|---:|---:|---:|
| clean confirmed | 11 of 12 | 12 of 16 | 9 of 12 |
| detectable alterations confirmed | 0 of 20 | 0 of 12 | 1 of 20 |
| detectable alterations located exactly | 17 of 20 | 8 of 12 | 17 of 20 |
| amounts, balances and dates exact | 32 of 40 | 25 of 40 | 27 of 40 |

Coverage falls on the harder tiers; the rate of wrong conclusions does not rise with it,
apart from the one statement of finding 3.

### 4.4 What the second model contributes

On a seeded 40-statement subset (13 clean, 17 detectable), with code deciding in every
arrangement:

| arrangement | clean confirmed | detectable confirmed | located exactly | amounts exact |
|---|---:|---:|---:|---:|
| Gemini reads, **Qwen** second (Probity) | 9 of 13 | 0 of 17 | 14 of 17 | 29 of 40 |
| Gemini reads, **Gemini** re-reads its own pages | 8 of 13 | 0 of 17 | 0 of 17 | 19 of 40 |
| **Qwen** reads, Gemini second | 7 of 13 | 0 of 17 | 15 of 17 | 39 of 40 |
| Gemini alone decides, same subset | 11 of 13 | 16 of 17 | 0 of 17 | 4 of 40 |

A model re-reading its own page corrects many misreads, but a model agreeing with
itself is not taken as confirmation of anything, so nothing is ever reported and every
altered statement ends unresolved. A different model is what makes a finding possible.

The reverse arrangement gives the most accurate transcriptions and the same safety. It
confirmed fewer clean statements for a reason unrelated to money: on several statements
Qwen wrote the statement period in a form the document type's declared date format does
not accept, and a header field that does not parse is never guessed. Qwen is also about
twelve times slower per page, which is why it is the second reader.

### 4.5 Is the models' failure a matter of wording?

Gemini alone under two rewordings of the instructions, on a seeded 30-statement subset:

| brief | clean confirmed | detectable alterations confirmed | located |
|---|---:|---:|---:|
| original, same 30 statements | 8 of 10 | 13 of 13 | 0 of 13 |
| paraphrase B | 8 of 10 | 13 of 13 | 0 of 13 |
| paraphrase C | 10 of 10 | 12 of 13 | 0 of 13 |

### 4.6 Variation between runs

Probity twice more from scratch on the same 30 statements, with new model replies:

| | clean confirmed | detectable confirmed | located exactly | amounts exact |
|---|---:|---:|---:|---:|
| sealed run, these 30 | 7 of 10 | 0 of 13 | 11 of 13 | 23 of 30 |
| replicate 1 | 8 of 10 | 0 of 13 | 10 of 13 | 22 of 30 |
| replicate 2 | 8 of 10 | 0 of 13 | 11 of 13 | 21 of 30 |

Individual documents move between a conclusion and unresolved from run to run. No run
moved a detectable alteration to confirmed.

### 4.7 The assumption the method rests on

The method treats agreement between two different models as evidence of what is printed.
This was measured directly on the 58 statements both models transcribed in full, by
comparing each model's raw first transcription with the answer key, cell by cell.

| cells | compared | one reader wrong | both wrong, differently | both wrong, the same way | correct when they agree |
|---|---:|---:|---:|---:|---:|
| amounts and balances | 28,113 | 284 | 0 | 2 (0.007%; interval 0.002-0.026%) | 99.993% |
| dates | 9,371 | | | 1 (0.011%) | 99.989% |
| opening and closing balances | 116 | | | 0 | 100% |
| account number | 58 | | | 0 | 100% |
| descriptions | 9,371 | | | 81 (0.86%) | 99.09% |

The two shared amount misreadings are one event: on one row of one clean statement both
models, in their first transcriptions, put a debit in the credit column. That breaks
the running balance, so the row is looked at again; in the sealed run the statement
ended confirmed with the row corrected.

Where one reader is wrong and the other right, the rules can tell which, because only
one of the two readings ties. That is 284 cells here. The exposure is the last column
but one, and on this material it is about one cell in fourteen thousand.

### 4.8 Cost and time

| | |
|---|---|
| Probity, 120 statements | $5.44, $0.045 a statement |
| of which first readings and third readings (Gemini) | $4.83 |
| of which second readings (Qwen, 185 pages) | $0.62 |
| time per statement, pages read side by side | median 5.3 minutes, 90th percentile 8.2 |

Time is dominated by the second reader, at roughly two minutes a page. A statement that
passes on the first reading takes about a minute.

The whole evaluation, with development, cost $19.0 against a fixed budget of $20.

## 5. Where the method failed

### 5.1 The altered statement that was confirmed

`Type1_00030-direction-T3`. One debit of 643,950.43 had been moved to the credit column,
leaving the printed balances as they were, so the printed row no longer ties. The first
reader transcribed the amount as a debit, where it had been before the alteration. That
transcription is consistent, every rule passed, no second look was requested, and the
statement was confirmed.

This is the failure the method cannot see from the inside: a misreading that happens to
agree with the arithmetic. A second look is triggered by a failed rule, and here no rule
failed. Amounts in these layouts sit in one of two adjacent columns, and under
perspective distortion the first reader placed this one in the wrong column. It did not
happen on the other 11 direction statements, and it is the same kind of error as the one shared misreading of section 4.7: a column, not a digit.

The rate is 1 in 52, with an interval of 0 to 10%. Nothing in this evaluation supports a
claim of zero.

### 5.2 Statements left unresolved

23 of 120 ended `UNRESOLVED`, 8 of them clean. In 19, a rule still failed on one or more
rows and the second reading did not settle it: the two readers disagreed and neither
reading tied, or the rows could not be shown to be the same printed line. In 2, the first
reader's reply for one page was not usable, and a statement with an unread page is not
checked at all. In 2, a header field did not parse. In 5 of the 23 the final
transcription was in fact exact; the machine could not establish that, so it did not say
so.

An unresolved statement is handed to a person with the rows still in question, and the
readings side by side.

### 5.3 What `CONFIRMED` covers

Of the 55 confirmed statements, 43 match the answer key on every amount, balance and
date. In 11, every amount and balance is right and between 1 and 14 dates are misread to
another date that still falls in order; the date rule checks order, and an in-order
wrong date passes it. The remaining one is the statement of section 5.1.

Descriptions are transcribed once and checked by nothing: 6.2% of them differ from the
answer key in Probity's output.

### 5.4 Alterations no rule can see

Of the 20 statements with an amount or a row changed and every later balance recomputed,
16 were confirmed and 4 ended unresolved for reading reasons. Of the 8 with only a
description changed, 6 were confirmed. This is by construction. A document that is
internally exact passes, whatever was done to it.

## 6. Results on receipts

100 real scanned receipts, 50 as scanned and 50 with one amount repainted.

| | **Probity** | Gemini alone | Qwen alone | Gemini with interpreter | OCR and rules |
|---|---:|---:|---:|---:|---:|
| clean confirmed | **50 of 50** (93-100%) | 50 of 50 | 48 of 50 | 47 of 50 | 8 of 50 |
| altered confirmed (should be 0) | **0 of 50** (0-7%) | 24 of 50 (35-61%) | 34 of 50 (54-79%) | 13 of 50 (16-40%) | 0 of 50 |
| altered reported | **37 of 50** (60-84%) | 26 of 50 | 14 of 50 | 32 of 50 | 28 of 50 |
| altered located | 36 of 50 | 22 of 50 | 8 of 50 | 32 of 50 | 22 of 50 |
| clean reported as inconsistent | 0 of 50 | 0 of 50 | 1 of 50 | 0 of 50 | 23 of 50 |
| reading exact | 90 of 100 | 65 of 100 | 75 of 100 | 79 of 100 | 13 of 100 |
| no usable answer | 0 | 0 | 3 | 8 | 0 |
| total cost, 100 receipts | $0.19 | $0.25 | $0.40 | $0.64 | none |

The 13 altered receipts Probity neither confirmed nor reported ended unresolved: a rule
failed and the two readers disagreed on a value it uses.

A receipt is a much shorter document than a statement, and the models alone do better
on it than on statements. They still confirmed between a quarter and two thirds of the
altered ones. Probity was also the cheapest of the conditions that use a model, because
a receipt that passes on the first reading costs one request.

## 7. Against the criteria set in advance

| stated before the run as counting against the method | outcome |
|---|---|
| any detectable alteration confirmed | **happened: 1 of 52** (section 5.1) |
| clean confirmed below 75% on tier T1 | did not happen: 11 of 12 |
| located exactly below 80% on detectable alterations | did not happen, narrowly: 42 of 52, 80.8% |
| Gemini with an interpreter matching Probity on clean confirmed, alterations confirmed and located exactly | did not happen: 17 of 40, 2 of 52, 9 of 52 |
| OCR with the same rules matching Probity | did not happen: 9 of 40, 0 of 52, 15 of 52 |
| the receipt document type needing Python | did not happen: the type is one YAML file, read by the generic form engine that is part of the frozen code |

## 8. Threats to validity

- **The statements are synthetic.** One corpus, two layouts, one currency, generated
  transactions. The scan degradation is simulated. No real bank statement was available.
  The receipts are real scans, and are the only real documents in the evaluation.
- **The alterations are synthetic and single.** One change per document, made in the
  PDF before scanning or repainted in the image. A person altering a document to
  deceive would also adjust the balances, which is the group no rule here can detect.
- **Two models, one configuration each.** A stronger model would do better alone. That
  comparison was excluded on purpose and is not answered here.
- **Small cells.** The factorial, paraphrase and replicate comparisons rest on 30 or 40
  statements, and their intervals are wide. They show direction, not size.
- **Qwen alone covers 60 statements, not 120**, and returned no answer on 3.
- **One sealed run.** The replicates suggest the conclusions are stable, on a quarter of
  the set.
- **The models will change.** These are hosted models behind names; the same name may
  not return the same behaviour later.

## 9. Reproducing

The frozen code is the tag `sealed-run-1`. An OpenRouter key is needed; a fresh run draws
new replies and will not reproduce the counts exactly.

```bash
# the test sets
python -m benchmark.build_test_set --sources data/agami --split sealed_test --out data/sealed
python -m benchmark.receipts build --splits test train --out data/sealed_receipts --limit 100

# statements
python -m benchmark.run_scanned   --manifest data/sealed/manifest.json \
       --model google/gemini-3.1-flash-lite --second-model qwen/qwen3.5-flash-02-23 \
       --workers 8 --out runs/probity
python -m benchmark.run_llm_alone --manifest data/sealed/manifest.json \
       --model google/gemini-3.1-flash-lite --out runs/gemini_alone
python -m benchmark.run_code_tool --manifest data/sealed/manifest.json \
       --model google/gemini-3.1-flash-lite --out runs/gemini_with_interpreter
python -m benchmark.run_ocr_rules --manifest data/sealed/manifest.json --out runs/ocr_rules

# receipts, one condition at a time
python -m benchmark.run_receipts --manifest data/sealed_receipts/manifest.json \
       --condition probity --out runs/receipts_probity

# the tables on this page, from the stored outcomes
python results/sealed/tables.py
```

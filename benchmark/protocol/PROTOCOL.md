# Evaluation protocol

Written and committed before any document of the sealed test set was built or read.
Nothing below is to be changed after the sealed run starts; anything that has to change
is recorded under "Deviations" with the date and the reason.

## 1. Question

Does a state machine with computable rules make low-cost vision models reliable for
checking scanned financial documents, at about the cost of running those models alone?
Frontier models are out of scope: the point is what can be done cheaply.

## 2. Constraints

- Total model spend for this protocol: **20 USD**.
- Models: `google/gemini-3.1-flash-lite` and `qwen/qwen3.5-flash-02-23`, as in the
  development work. No other reader.
- No real bank statements are available. Real scanned documents enter through public
  receipt data only (section 4.2), and that is stated wherever results are reported.

## 3. What is frozen, and when

1. **Development** uses only the documents listed as `development_seen` and
   `development_unseen` in [`split.json`](split.json), and the training split of the
   receipt corpus. The method may be changed freely here.
2. **Freeze.** When development ends, the code is tagged. From that tag on, the method,
   the rules, the prompts, the scoring and this protocol do not change.
3. **Sealed run.** The test documents are built with the frozen code and run once per
   condition. The results are reported whatever they are.

A scoring defect found after the sealed run may be corrected only by re-scoring the
stored model replies, and is recorded under "Deviations". Model replies are never
re-requested for a condition that has already run, except for requests the provider
aborted.

## 4. Documents

### 4.1 Bank statements

Source: AgamiAI/Indian-Bank-Statements, digital split, the 191 statements that can be
built. The split is at the level of source statement, drawn with a fixed seed and
stored in [`split.json`](split.json):

| set | statements | use |
|---|---:|---|
| development, seen | 21 | everything done so far |
| development, unseen | 50 | further development |
| **sealed test** | **120** | the sealed run |

For the sealed test, each source statement is assigned by a seeded draw to one group
and one scan tier.

| group | statements | what is done | expected of the method |
|---|---:|---|---|
| clean | 40 | amounts corrected so the statement ties | confirmed |
| A1 amount | 16 | one amount changed, balances untouched | not confirmed; row named |
| A2 balance | 12 | one balance changed | not confirmed; row named |
| A3 row removed | 12 | one row deleted, balances untouched | not confirmed; neighbouring row named |
| A4 row added | 12 | one row inserted, balances untouched | not confirmed; row named |
| A5 amount, balances adjusted | 12 | one amount changed and every later balance and the closing balance recomputed | **confirmed. The rules cannot detect this** |
| A6 row removed, balances adjusted | 8 | one row deleted and every later balance recomputed | **confirmed**, unless the statement prints a transaction count |
| A7 text | 8 | a payee or description changed, no figure touched | confirmed by the arithmetic; flagged only if the field-agreement check (section 6) catches it |

A5 and A6 are included so that the number is on the page. A method that only reported
the alterations it is built for would be reporting a tautology.

Scan tiers, one third each, assigned independently of group:

| tier | rendering |
|---|---|
| T1 | as in development: 300 dpi greyscale, blur, uneven lighting, sensor noise, JPEG |
| T2 | T1 plus rotation of up to 2 degrees and a shadow band |
| T3 | T1 plus perspective distortion, stronger blur and lower JPEG quality, as from a phone |

### 4.2 Receipts

Source: a public corpus of real scanned receipts with itemised lines and totals (CORD).
Development uses its training split only; the sealed test is **100 receipts from its
test split**, 50 as scanned and 50 with one line amount or the total altered in the
image. Rule: the line amounts sum to the subtotal, and subtotal, tax and other charges
sum to the total. The document type is added by configuration, with no Python written
for it; if that turns out not to be possible, it is reported as a failure of the
framework claim.

## 5. Conditions

| condition | statements | receipts |
|---|---:|---:|
| **Probity** (Gemini reads, Qwen second reader, third reading, rules decide) | 120 | 100 |
| Gemini alone (reads, checks, re-examines, decides) | 120 | 100 |
| Qwen alone | 60, a seeded subset balanced over groups | 100 |
| Gemini with a code tool (it may run Python on its own transcription) | 120 | 100 |
| conventional OCR + the same rules, no LLM | 120 | 100 |

Factorial on 40 sealed statements (seeded, balanced over groups): who decides (code,
model) × second look (none, same model, different model) × first reader (Gemini, Qwen).
Cells that reuse replies already paid for are computed from the cache.

Replicates: Probity twice more on 30 sealed statements, to report variation.

Prompt sensitivity: the model-alone conditions with two paraphrases of the brief, on 30
sealed statements.

## 6. Measures

Fixed here; computed by `benchmark/` scoring code frozen at the tag.

**Per document**

- *confirmed*: the final word is "consistent".
- *reported*: the final word is "inconsistent", with rows named.
- *unresolved* (Probity) / *no usable answer* (model alone).
- *located*: the altered row is among those named; *located exactly*: and no other row.
  For A3 the row immediately after the deletion counts as the altered row.
- *ledger exact*: every row's date, debit, credit and balance, and the opening and
  closing balances, match the answer key.

**Headline numbers, each with a 95% Wilson interval**

1. clean confirmed;
2. detectable alterations (A1–A4) confirmed: should be zero;
3. detectable alterations located exactly;
4. undetectable alterations (A5, A6) confirmed: expected to be all of them, reported as
   the method's blind spot;
5. A7 flagged;
6. the same, by scan tier.

**Non-arithmetic fields.** For account number, holder name and each description: the
share where two readers agree, and among those the share that matches the answer key.
A field is "confirmed by agreement" when both readers transcribe it identically.

**The method's assumptions, measured on the sealed set**

- shared misreadings: per amount cell, the rate at which both readers are wrong in the
  same way;
- chance ties: for each corrected row, how many other values within one digit of the
  correct one would also satisfy the rule;
- coverage lost to guards: clean documents ending unresolved, by cause;
- cost and latency per document, with second looks run in parallel.

## 7. What would count against the method

Stated before the run:

- any A1–A4 statement confirmed;
- clean confirmed below 75% on tier T1;
- located exactly below 80% on A1–A4;
- Gemini with a code tool matching Probity on rows 1–3 of the headline numbers, which
  would mean the state machine adds nothing over a model that can compute;
- conventional OCR with the same rules matching Probity, which would mean the models
  add nothing;
- the receipt document type needing Python.

## 8. Budget

| item | estimate (USD) |
|---|---:|
| Probity, 120 statements | 5.4 |
| Gemini alone, verification only (its transcription is Probity's first reading) | 1.1 |
| Qwen alone, 60 statements | 2.4 |
| Gemini with a code tool | 2.4 |
| receipts, all conditions | 1.5 |
| factorial, uncached cells | 2.0 |
| replicates | 2.7 |
| prompt sensitivity | 0.6 |
| reserve | 1.9 |
| **total** | **20.0** |

If a line overruns, the reserve absorbs it; after that, items are cut from the bottom of
this table upward and the cut is recorded.

## 9. Deviations

Recorded before the sealed run, while the method could still be changed on development
documents. None of these was decided with knowledge of any sealed result.

1. **A4 "row added" is replaced by "direction": one amount moved to the other side**
   (debit to credit or the reverse), balances untouched. Adding a row to these PDFs
   would mean re-typesetting the page, which the cell-level surgery used to build the
   corpus cannot do. The slot count (12) is unchanged.
2. **A3 and A6 remove a row by whiting it out**, leaving a blank band where it was, for
   the same reason. The rows below do not move up.
3. **For A2 (a balance changed), two rows fail by construction:** the altered row and
   the one after it. Both are the expected rows; "located exactly" means exactly those
   two.
4. **A statement that cannot take its assigned kind takes the next kind in the seeded
   list that it can.** Two things prevent a kind: adjusted balances would go negative
   (A5, A6), or the row band or description cannot be identified with certainty (A3,
   A6, A7). The assignment therefore depends on the seed and on those properties of the
   statement, and on nothing else.
5. **Receipts.** Development used the corpus's validation split, not its training
   split. Only receipts whose published transcription satisfies the receipt rules, with
   at least two lines and no discount or nested line, can serve (38 of the 100 in the
   validation split). The sealed receipt set is therefore every usable receipt of the
   test split, topped up to 100 with a seeded draw from the usable receipts of the
   training split, which was not opened during development. Alternate receipts are
   altered after shuffling.
6. **"Located" for receipts is at the level of the rule,** since a sum that does not
   hold cannot say which line is wrong: an altered receipt is located when a rule that
   should fail is among the rules named.
7. **The non-arithmetic fields measure is limited to pages that were read twice.** The
   second reader is only asked for pages on which a rule failed, so agreement on
   descriptions and header fields can be measured there and nowhere else. A text-only
   alteration (A7) leaves every rule passing, so no second reading is requested and the
   method cannot flag it; A7 is reported as confirmed.
8. **"Chance ties" is answered by argument, not simulation.** With the previous balance
   and the row's balance both held fixed, exactly one signed amount satisfies the
   running-balance rule. A wrong amount can only be accepted together with a wrong
   balance on the same row, taken from the same second reading.
9. **The factorial is reduced to the cells that are well defined.** With code deciding:
   first reader (Gemini, Qwen) × second look (the same model re-reading, a different
   model). With a model deciding: Gemini alone and Qwen alone. "A model decides, with a
   second look" has no natural definition and is not run.
11. **Non-arithmetic fields: what is measured.** Agreement between the two readers, and
    accuracy given agreement, are measured for amounts, dates, descriptions, the header
    balances and the account number, on the statements both models transcribed in full
    (`benchmark/analysis.py`). The holder's name is not among the fields the readers
    are asked for, so it is not measured.
12. **The interpreter given to the code-tool baseline is contained, not sandboxed.** It
    restricts builtins, imports and attribute names and runs in a separate process with
    limits. It is adequate for a cooperative model and is not a security boundary.
10. **A third reading** (the first reader again at a higher resolution, when the two
    models agree and a rule still fails) was added to the method during development and
    is part of the Probity condition.

## 10. Development record

Spend during development, before the freeze, counted against the 20 USD:

| run | documents | cost (USD) |
|---|---:|---:|
| Probity on development statements | 16 | 0.73 |
| model with a code tool, development statements | 6 | 0.16 |
| receipts, development, four conditions | 12 | 0.12 |

On the 16 development statements, after the changes made in response to them (a second
reading may now supply a date the first reader could not parse): 3 of 4 clean confirmed,
0 of 8 detectable alterations confirmed, 7 of 8 located exactly, 4 of 4 undetectable
alterations confirmed. These are development figures and are not reported as results.

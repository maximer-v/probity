# Method

This document states the procedure precisely: what is read, what is checked, when a
second reader is consulted, how a value comes to be changed, and what each conclusion
does and does not establish. The implementation is in
[`probity/second_opinion.py`](../probity/second_opinion.py),
[`probity/pipeline.py`](../probity/pipeline.py) and
[`probity/invariants.py`](../probity/invariants.py).

## 1. Terms

| term | meaning |
|---|---|
| **document** | a statement supplied as a PDF or as one or more images. Nothing is assumed about a text layer |
| **reading** | a transcription of the document: header fields (opening and closing balance, period, account) and one row per transaction (date, description, debit, credit, balance), each stored with the characters as transcribed and the value parsed from them |
| **first reader** | the vision model that produces the reading, one page per request |
| **second reader** | a different vision model, consulted only for a page on which a rule failed. It receives the page image and the transcription instruction, and nothing else |
| **rule** | a named check implemented as code and evaluated with exact integer arithmetic on minor units (cents). A rule either passes or fails at a *location*: a row, a page or the document |
| **correction** | a row whose date or amounts are replaced by the second reader's transcription of the same line |
| **conclusion** | one of `CONFIRMED`, `DOCUMENT_INCONSISTENT`, `UNRESOLVED` |

Rows are numbered from 0 throughout the code and its outputs. A statement that prints
its own line numbers usually starts at 1, so row 127 here is the line printed as 128.

## 2. The rules

| rule | statement | located to |
|---|---|---|
| `ROW_BAL` | `balance[i] = balance[i-1] + credit[i] - debit[i]`, with `balance[-1]` the opening balance | row *i* |
| `GLOBAL_BAL` | opening balance + all movements = closing balance | document |
| `LAST_ROW_EQ_CLOSING` | the last row's balance is the closing balance | row |
| `DATE_ORDER` | dates run in the order the document type declares | row |
| `NO_DUP_ROW` | no transaction appears twice | row |
| `PAGE_SUBTOTAL` | a page's carried-forward figure matches | page |
| `COUNT` | the number of rows equals the count the statement prints | document |

Comparison is equality of integers. There is no tolerance and no setting that
introduces one.

`ROW_BAL` is the rule that makes the rest possible. A total that does not close says
only that something is wrong somewhere. A row whose balance does not follow says where,
and by how much.

## 3. Procedure

```
read      R  <- first reader transcribes every page
parse     amounts and dates are parsed from the transcribed characters by code
check     F  <- the set of failing (rule, location) pairs for R
loop while F contains a row r that has not been examined:
    P   <- the page of r
    R2  <- second reader's transcription of P        (once per page, then cached)
    pair the rows of R on P with the rows of R2      (section 4, guard 3)
    if r is unpaired:                        finding(r) = UNALIGNED
    else if R and R2 agree on r:
        if they do not agree on the figures carried into r (guard 4):
                                             finding(r) = DISPUTED
        else:
            R3 <- first reader's transcription of P at higher resolution   (tie-break)
            if R3 differs on r and replacing r by its row in R3 satisfies guards 1-3:
                                             finding(r) = CORRECTED (third reading)
            else:                            finding(r) = DOCUMENT_INCONSISTENT
    else:
        try replacing r by its row in R2, alone, then with an adjacent failing row
        accept the first replacement that satisfies guards 1 and 2
        if one is accepted:                  finding(r) = CORRECTED
            then offer R2 to every other failing row of P, under the same guards
        else:                                finding(r) = DISPUTED
    recompute F
conclude  (section 5)
```

**The tie-break.** Two models reading the same image can make the same mistake, and
without this step a shared misreading that breaks a rule is reported as a fault in the
document. So when the readers agree, the first reader transcribes the page once more at
its higher re-read resolution, again without seeing any earlier transcription. That
third transcription can do one thing only: replace that one row, under the same guards
as any other correction. If it agrees with the other
two, cannot be matched to the row, is unavailable, or differs without satisfying the
rule, nothing changes and the finding of the two readers stands. It is a third
transcription, not a third reader: the same model as the first, looking at a sharper
image.

A second look can address a row that fails `ROW_BAL`, `DATE_ORDER` (dates out of
order) or `LAST_ROW_EQ_CLOSING`. Agreement between the readers can settle only the
first two. A date outside the statement period, a duplicate row and any failure located
on a page or on the document are left unresolved.

**Without a second reader configured**, the same loop runs with `R2` supplied by the
first reader transcribing the page again at a higher resolution. The pairing and the
guards are identical, and a value changed that way is recorded as a *same-reader*
correction. One branch differs: when the two transcriptions agree, the finding is
`REPEATED`, not `DOCUMENT_INCONSISTENT`, because a model agreeing with itself confirms
nothing. A document that still fails then ends `UNRESOLVED`.

**Nothing else changes a value.** Once a transcription exists, a failed check is
settled by a second look under the guards or is not settled. A stronger model
configured in the spec is used only when the first reader returned nothing at all, and
there is no other repair path. Every change, including an unreadable cell replaced by a
blank one, is appended to the corrections record.

## 4. The guards

Each guard closes one specific way a wrong value could be accepted or a wrong conclusion
reached. The case under each guard shows what would happen without it, and each case is
a test in [`tests/test_second_opinion.py`](../tests/test_second_opinion.py).

**1. Only a row that itself fails a rule may be replaced.**
A neighbouring row that passes is never edited in order to make a failing row pass.
*Without it:* printed rows `-/100`, `debit 10/90`, `debit 20/80`, where the last is
altered and both readers transcribe it alike. The second reader misreads the middle row
as `-/100`. Applying that to the (passing) middle row would make the altered row tie,
and the document would be confirmed.

**2. A replacement may not create a failure.**
The set of failing checks after a replacement must be a strict subset of the set before,
and every replaced row must pass every rule. Counting failures is insufficient.
*Without it:* opening 100, closing 70, rows `debit 30/90` and `debit 10/80`. Replacing
the first row with `debit 20/80` removes two failures and creates one on the second
row. Three failures become two, and counting alone would accept the replacement.

**3. A row is replaced only by the same line.**
The two transcriptions of a page are aligned on (date, balance), and a pair is used only
with positive evidence that it is the same printed line. If the row's (date, balance) is
unique on the page in both readings, the rows must share a date or a balance and their
descriptions must be closely similar *with identical digits*, because lines on a
statement differ from their neighbours mostly in a reference number. If the key is not
unique, position proves nothing, so the descriptions must be identical and themselves
unique on the page. This guard is strict on purpose and has a price: a row on which a
reader misread a digit of the reference number cannot be matched, and stays unresolved.
*Without it:* two rows with the same date and balance and near-identical descriptions
(`cheque 5512`, `cheque 5513`). The second reader drops the first and returns the
second twice, so the row counts still match. Its row would be paired with a different
transaction and its blank amount copied across, confirming an altered document. The
same would happen if each reader returned only a different one of the two lines.

**4. Agreement must cover the operands.**
`ROW_BAL` at a row depends on the balance of the row before it in time: the row above on
an oldest-first statement, the row below on a newest-first one, or the opening balance
for the earliest row. `DATE_ORDER` compares a row's date with the row printed above it.
Neighbours are taken by position in the transcription, not by row number. A row is
reported as inconsistent only when the readers agree on the row *and* on the date and
balance of each of those neighbours. If one is on another page, that page is read by
the second reader too.
*Without it:* the first reader misreads a row on page 1 consistently (`debit 5/95` for
`debit 10/90`), so the only failing row is on page 2, where both readers agree. A clean
document would be reported as inconsistent.

**5. Agreement is between the two readers.**
A row that has already taken the second reader's transcription and still fails is not
agreed upon; it is unresolved. The same holds for the balance carried into a row: if
the earlier row was corrected, what is compared is the balance the *first* reader
originally transcribed there against the second reader's. A balance only one of them
ever produced is not an agreed figure.
*Without it:* a clean statement on which the second reader's (wrong but consistent)
reading of one row is accepted. Both readers then agree on the next row, which no
longer follows, and the document would be reported as inconsistent.

**6. A finding is bound to the figures it was made on.**
A `DOCUMENT_INCONSISTENT` finding stores the row's date and amounts and the figure
carried into it. If any of them changes afterwards, the finding lapses.

Two further conditions:

- The second reader must be a different model from the first. The same model
  configured twice is refused.
- A cell that the first reader itself contradicts (it reports the column heading as
  "Debit" and puts the amount under credit) blocks `CONFIRMED`, even if the arithmetic
  ties.

## 5. Conclusions

| conclusion | condition |
|---|---|
| `CONFIRMED` | every selected rule passes on the final reading, and no cell is unreadable or self-contradicted. A spec whose acceptance policy tolerates failing rules cannot produce this conclusion while a rule fails |
| `DOCUMENT_INCONSISTENT` | at least one row fails; every failing row has a standing `DOCUMENT_INCONSISTENT` finding (two readers agree, and the tie-break did not produce a correction); and any failure not on a row is the closing total, off by exactly the sum of what those rows are off by |
| `UNRESOLVED` | anything else |

## 6. What the conclusions establish

This section matters more than the rest.

**`CONFIRMED` is a statement about a transcription, not about a document.** It says
that the reading satisfies every selected rule. It does not say that the reading is
what is printed, and it does not say that the document is authentic. Specifically:

- **A correction is selected by arithmetic.** A value is taken from the second reader
  because the rule then passes. That is strong evidence when the alternative is a
  misread digit or a swapped column, because a random wrong value almost never makes an
  exact integer equation close. It is not proof. A second reader that "repairs" an
  altered figure back to the value that ties would be accepted. The second reader is
  never shown the rule or the first reading, which removes the incentive, but not the
  possibility.
- **Readers can share a misreading.** Different model families do not have
  statistically independent errors, and the third transcription comes from the same
  model as the first. The tie-break catches a misreading shared at the reading
  resolution; it does not catch one that survives a sharper image. A shared misreading
  that happens to be internally consistent would be confirmed; one that is not would be
  reported as an inconsistent document.
- **The tie-break can itself be wrong.** A third transcription that misreads an altered
  figure as exactly the value that makes the row tie would be accepted over two readers
  who read it correctly. In the benchmark the third transcription agreed with the other
  two on every altered row, 18 times out of 18.
- **Fields outside the rules are not checked by anything.** Descriptions and the
  account number are transcribed by the first reader and confirmed by no rule and no
  second reading. The statement period is used by one rule (a row dated outside it
  fails `DATE_ORDER`) but is itself confirmed by nothing, so a misread period produces
  a failure that ends unresolved.
- **Rows that were never read are invisible** unless their absence breaks a balance.
  A set of omitted rows whose amounts cancel leaves every remaining balance consistent.

**`DOCUMENT_INCONSISTENT` says the transcription both readers agree on does not add
up** at the named row. It does not say why. An alteration, a bank error, a legitimate
adjustment printed elsewhere, and a shared misreading all look the same.

**An alteration that keeps the arithmetic intact is out of scope.** An amount changed
together with every later balance produces a document that satisfies every rule here.
Only a comparison with an external record can detect it.

## 7. Parsing

Amounts are converted from the transcribed characters to integer minor units under the
locale declared in the document spec, with no floating-point value at any step. A cell
that does not parse is recorded as unreadable with a reason code. An unreadable cell
blocks `CONFIRMED`; it is not treated as empty.

## 8. Bounds

Each reader has a call budget per document, and a run has a spend cap. The cap is
checked before each request against the amount already spent, so a run can exceed it by
the cost of requests already in flight; it is cumulative for a cache directory, not per
invocation. When a budget is exhausted the document ends `UNRESOLVED`.

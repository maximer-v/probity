# Verification report: Type2_00091-amount-T1

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:146.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 166 |
| Rule checks passed | 332 of 335 |
| Rows corrected | 3 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0521 |
| Document SHA-256 | `31aa4873819177bc` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 60 | 3 | credit | 49,856.96 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 60 | 3 | debit | (blank) | 49,856.96 | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | balance | 476,134.78 | 476,134.63 | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | credit | 77,373.34 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | debit | (blank) | 77,373.34 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 138, page 5

```
previous balance         1,745,961.43
movement                   108,716.17
should read              1,854,677.60
transcribed balance      1,853,777.60
difference                    -900.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 15/03/2024 | (blank) | 108,716.17 | 1,853,777.60 |
| `qwen/qwen3.5-flash-02-23` | 15/03/2024 | (blank) | 108,716.17 | 1,853,777.60 |
| third reading (first reader, higher resolution) | 15/03/2024 | (blank) | 108,716.17 | 1,853,777.60 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## For a person to check

- row 146, page 5, ROW_BAL: row 146: 130029093 + 16490469 = 146519562, but the balance column reads 113538624 (off by -32980938)
  - second look (UNALIGNED): the second reading of page 5 has 35 rows against 35, and no row in it could be shown to be the row in question
- document, GLOBAL_BAL: opening 61711409 + movements 111424403 = 173135812, closing balance reads 140064874

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 164 | 2 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 166 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

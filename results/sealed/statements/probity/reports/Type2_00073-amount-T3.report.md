# Verification report: Type2_00073-amount-T3

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:123, row:152.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 162 |
| Rule checks passed | 323 of 327 |
| Rows corrected | 16 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0520 |
| Document SHA-256 | `ff92a24118880a32` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 41 | 2 | credit | 90,465.89 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 41 | 2 | debit | (blank) | 90,465.89 | DATE_ORDER, ROW_BAL | second reader |
| 42 | 2 | credit | 10,094.56 | 10,094.97 | DATE_ORDER, ROW_BAL | second reader |
| 44 | 2 | credit | 65,690.28 | 65,690.07 | DATE_ORDER, ROW_BAL | second reader |
| 104 | 4 | balance | 741,386.66 | 741,386.86 | DATE_ORDER, ROW_BAL | second reader |
| 120 | 5 | credit | 94,842.81 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 120 | 5 | debit | (blank) | 94,842.81 | DATE_ORDER, ROW_BAL | second reader |
| 126 | 5 | credit | 15,658,770.58 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 126 | 5 | debit | (blank) | 15,658,770.58 | DATE_ORDER, ROW_BAL | second reader |
| 128 | 5 | credit | 1,851,384.41 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 128 | 5 | debit | (blank) | 1,851,384.41 | DATE_ORDER, ROW_BAL | second reader |
| 131 | 5 | credit | 2,626,002.05 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 131 | 5 | debit | (blank) | 2,626,002.05 | DATE_ORDER, ROW_BAL | second reader |
| 134 | 5 | credit | 411,526.41 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 134 | 5 | debit | (blank) | 411,526.41 | DATE_ORDER, ROW_BAL | second reader |
| 135 | 5 | credit | 1,134,687.22 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 135 | 5 | debit | (blank) | 1,134,687.22 | DATE_ORDER, ROW_BAL | second reader |
| 136 | 5 | credit | 555,261.52 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 136 | 5 | debit | (blank) | 555,261.52 | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | credit | 49,644.07 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 139 | 5 | debit | (blank) | 49,644.07 | DATE_ORDER, ROW_BAL | second reader |
| 142 | 5 | credit | 1,864,652.06 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 142 | 5 | debit | (blank) | 1,864,652.06 | DATE_ORDER, ROW_BAL | second reader |
| 145 | 5 | credit | 728,939.45 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 145 | 5 | debit | (blank) | 728,939.45 | DATE_ORDER, ROW_BAL | second reader |
| 148 | 5 | credit | 1,959,148.89 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 148 | 5 | debit | (blank) | 1,959,148.89 | DATE_ORDER, ROW_BAL | second reader |
| 151 | 5 | credit | 600,153.16 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 151 | 5 | debit | (blank) | 600,153.16 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 91, page 4

```
previous balance           287,171.80
movement                    28,035.14
should read                315,206.94
transcribed balance        308,006.94
difference                  -7,200.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 19/02/2024 | (blank) | 28,035.14 | 308,006.94 |
| `qwen/qwen3.5-flash-02-23` | 19/02/2024 | (blank) | 28,035.14 | 308,006.94 |
| third reading (first reader, higher resolution) | 19/02/2024 | (blank) | 28,035.14 | 308,006.94 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## For a person to check

- row 123, page 5, ROW_BAL: row 123: 846604290 + 124332173 = 970936463, but the balance column reads 722272117 (off by -248664346)
  - second look (UNALIGNED): the second reading of page 5 has 34 rows against 34, and no row in it could be shown to be the row in question
- row 152, page 5, ROW_BAL: row 152: 354399066 + 6968322 = 361367388, but the balance column reads 347430744 (off by -13936644)
  - second look (UNALIGNED): the second reading of page 5 has 34 rows against 34, and no row in it could be shown to be the row in question
- document, GLOBAL_BAL: opening 240213711 + movements 545763194 = 785976905, closing balance reads 522655915

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 3 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 162 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

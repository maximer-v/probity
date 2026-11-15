# Verification report: Type2_00043-row_removed-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:84, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 159 |
| Rule checks passed | 319 of 321 |
| Rows corrected | 17 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0481 |
| Document SHA-256 | `3662407a246fd3f9` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 0 | 1 | debit | (blank) | 118,186.32 | DATE_ORDER, ROW_BAL | second reader |
| 1 | 1 | credit | (blank) | 367,670.15 | DATE_ORDER, ROW_BAL | second reader |
| 2 | 1 | debit | (blank) | 250,026.10 | DATE_ORDER, ROW_BAL | second reader |
| 3 | 1 | credit | (blank) | 916,533.82 | DATE_ORDER, ROW_BAL | second reader |
| 4 | 1 | credit | (blank) | 220,639.53 | DATE_ORDER, ROW_BAL | second reader |
| 5 | 1 | credit | (blank) | 340,556.66 | DATE_ORDER, ROW_BAL | second reader |
| 6 | 1 | debit | (blank) | 316,947.30 | DATE_ORDER, ROW_BAL | second reader |
| 7 | 1 | credit | (blank) | 507,647.01 | DATE_ORDER, ROW_BAL | second reader |
| 8 | 1 | credit | (blank) | 1,007,479.34 | DATE_ORDER, ROW_BAL | second reader |
| 9 | 1 | debit | (blank) | 989,445.67 | DATE_ORDER, ROW_BAL | second reader |
| 10 | 1 | credit | (blank) | 665,485.69 | DATE_ORDER, ROW_BAL | second reader |
| 11 | 1 | debit | (blank) | 2,263,998.88 | DATE_ORDER, ROW_BAL | second reader |
| 12 | 1 | debit | (blank) | 4,920,646.20 | DATE_ORDER, ROW_BAL | second reader |
| 13 | 1 | credit | (blank) | 4,824,166.20 | DATE_ORDER, ROW_BAL | second reader |
| 14 | 1 | credit | (blank) | 1,498,196.70 | DATE_ORDER, ROW_BAL | second reader |
| 15 | 1 | debit | (blank) | 157.85 | DATE_ORDER, ROW_BAL | second reader |
| 80 | 3 | balance | 3,701,873.55 | 3,701,873.35 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 84, page 3

```
previous balance         3,885,444.66
movement                   -16,319.82
should read              3,869,124.84
transcribed balance      3,868,713.69
difference                    -411.15
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 17/02/2024 | 16,319.82 | (blank) | 3,868,713.69 |
| `qwen/qwen3.5-flash-02-23` | 17/02/2024 | 16,319.82 | (blank) | 3,868,713.69 |
| third reading (first reader, higher resolution) | 17/02/2024 | 16,319.82 | (blank) | 3,868,713.69 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 158 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 159 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

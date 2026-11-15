# Verification report: Type2_00049-amount-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:99, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 155 |
| Rule checks passed | 311 of 313 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0488 |
| Document SHA-256 | `59154cb5c2c8c24f` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 37 | 2 | balance | 5,804,344.40 | 5,804,344.32 | DATE_ORDER, ROW_BAL | second reader |
| 113 | 4 | credit | 1,306,753.08 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 113 | 4 | debit | (blank) | 1,306,753.08 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 99, page 4

```
previous balance         8,416,186.55
movement                   668,482.55
should read              9,084,669.10
transcribed balance      9,284,669.10
difference                 200,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 27/02/2024 | (blank) | 668,482.55 | 9,284,669.10 |
| `qwen/qwen3.5-flash-02-23` | 27/02/2024 | (blank) | 668,482.55 | 9,284,669.10 |
| third reading (first reader, higher resolution) | 27/02/2024 | (blank) | 668,482.55 | 9,284,669.10 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 154 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 155 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

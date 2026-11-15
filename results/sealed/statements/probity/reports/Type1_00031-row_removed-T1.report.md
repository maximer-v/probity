# Verification report: Type1_00031-row_removed-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:23, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 171 |
| Rule checks passed | 343 of 345 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0529 |
| Document SHA-256 | `1406b1373e6b7d43` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 13 | 2 | credit | (blank) | Rs. 810,840.84 | DATE_ORDER, ROW_BAL | second reader |
| 13 | 2 | debit | Rs. 810,840.84 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 23, page 2

```
previous balance            47,601.44
movement                   -13,410.34
should read                 34,191.10
transcribed balance         43,203.66
difference                   9,012.56
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 18-01-2024 16:23:17 | Rs. 13,410.34 | (blank) | Rs. 43,203.66 |
| `qwen/qwen3.5-flash-02-23` | 18-01-2024 16:23:17 | Rs. 13,410.34 | (blank) | Rs. 43,203.66 |
| third reading (first reader, higher resolution) | 18-01-2024 16:23:17 | Rs. 13,410.34 | (blank) | Rs. 43,203.66 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 170 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 171 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

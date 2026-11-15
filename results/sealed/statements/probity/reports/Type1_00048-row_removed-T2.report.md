# Verification report: Type1_00048-row_removed-T2

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:73, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 158 |
| Rule checks passed | 317 of 319 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0519 |
| Document SHA-256 | `39a6c9361bf7784a` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 110 | 4 | credit | (blank) | Rs. 20,715.81 | DATE_ORDER, ROW_BAL | second reader |
| 110 | 4 | debit | Rs. 20,715.81 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 73, page 3

```
previous balance           203,826.72
movement                    24,220.25
should read                228,046.97
transcribed balance        233,191.42
difference                   5,144.45
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12-02-2024 | (blank) | Rs. 24,220.25 | Rs. 233,191.42 |
| `qwen/qwen3.5-flash-02-23` | 12-02-2024 06:28:20 | (blank) | Rs. 24,220.25 | Rs. 233,191.42 |
| third reading (first reader, higher resolution) | 12-02-2024 | (blank) | Rs. 24,220.25 | Rs. 233,191.42 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 157 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 158 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

# Verification report: Type1_00021-direction-T2

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:28, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 170 |
| Rule checks passed | 341 of 343 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0582 |
| Document SHA-256 | `c1d2fe53afc42fc0` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 50 | 3 | balance | Rs. 137,229.52 | Rs. 137,229.72 | DATE_ORDER, ROW_BAL | second reader |
| 53 | 3 | balance | Rs. 448,518.12 | Rs. 448,538.12 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 28, page 2

```
previous balance         2,469,336.28
movement                 2,272,613.66
should read              4,741,949.94
transcribed balance        196,722.62
difference              -4,545,227.32
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 17-01-2024 10:20:37 | (blank) | Rs. 2,272,613.66 | Rs. 196,722.62 |
| `qwen/qwen3.5-flash-02-23` | 17-01-2024 10:20:37 | (blank) | Rs. 2,272,613.66 | Rs. 196,722.62 |
| third reading (first reader, higher resolution) | 17-01-2024 10:20:37 | (blank) | Rs. 2,272,613.66 | Rs. 196,722.62 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 169 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 170 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

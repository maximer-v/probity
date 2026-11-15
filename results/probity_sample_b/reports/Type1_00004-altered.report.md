# Verification report: agami-Digital_Type1_00004-scan-tampered

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:124, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 155 |
| Rule checks passed | 311 of 313 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0000 |
| Document SHA-256 | `580b1334f2deeb7b` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 130 | 5 | credit | Rs. 900,916.72 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 130 | 5 | debit | (blank) | Rs. 900,916.72 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 124, page 5

```
previous balance         1,179,515.09
movement                  -124,022.17
should read              1,055,492.92
transcribed balance      1,015,492.92
difference                 -40,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12-03-2024 21:49:54 | Rs. 124,022.17 | (blank) | Rs. 1,015,492.92 |
| `qwen/qwen3.5-flash-02-23` | 12-03-2024 21:49:54 | Rs. 124,022.17 | (blank) | Rs. 1,015,492.92 |
| third reading (first reader, higher resolution) | 12-03-2024 | Rs. 124,022.17 | (blank) | Rs. 1,015,492.92 |

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

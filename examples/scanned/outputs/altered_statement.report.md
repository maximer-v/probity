# Verification report: altered_statement

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:127, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 167 |
| Rule checks passed | 335 of 337 |
| Rows corrected | 6 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0000 |
| Document SHA-256 | `fdca935188108f2d` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

1 row(s) marked *third reading* were first transcribed the same way by both models, and the rule failed. The first reader then transcribed the page again at a higher resolution, differently, and with that reading the rule passed. Both models had shared a misreading.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 69 | 3 | balance | 5,200,854.40 | 5,200,854.44 | DATE_ORDER, ROW_BAL | second reader |
| 73 | 3 | credit | (blank) | 7,066,847.42 | DATE_ORDER, ROW_BAL | second reader |
| 73 | 3 | debit | 7,066,847.42 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | credit | (blank) | 5,653,748.36 | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | debit | 5,653,748.36 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 78 | 3 | credit | 5,637,798.30 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 78 | 3 | debit | (blank) | 5,637,798.30 | DATE_ORDER, ROW_BAL | second reader |
| 135 | 5 | credit | 2,105,191.83 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 135 | 5 | debit | (blank) | 2,105,191.83 | DATE_ORDER, ROW_BAL | second reader |
| 148 | 5 | credit | (blank) | 115,417.78 | DATE_ORDER, ROW_BAL | third reading |
| 148 | 5 | debit | 115,417.78 | (blank) | DATE_ORDER, ROW_BAL | third reading |

## Rows where both readers agree and a rule fails

### Row 127, page 5

```
previous balance         4,518,868.31
movement                   -23,823.71
should read              4,495,044.60
transcribed balance      4,425,044.60
difference                 -70,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 11/03/2024 | 23,823.71 | (blank) | 4,425,044.60 |
| `qwen/qwen3.5-flash-02-23` | 11/03/2024 | 23,823.71 | (blank) | 4,425,044.60 |
| third reading (first reader, higher resolution) | 11/03/2024 | 23,823.71 | (blank) | 4,425,044.60 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 166 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 167 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

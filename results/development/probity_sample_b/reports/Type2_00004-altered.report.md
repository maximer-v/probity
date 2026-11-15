# Verification report: agami-Digital_Type2_00004-scan-tampered

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:108, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 156 |
| Rule checks passed | 313 of 315 |
| Rows corrected | 5 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0000 |
| Document SHA-256 | `93bcc343a3b6064d` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 42 | 2 | credit | 39,371.30 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 42 | 2 | debit | (blank) | 39,371.30 | DATE_ORDER, ROW_BAL | second reader |
| 81 | 3 | credit | 1,795,855.11 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 81 | 3 | debit | (blank) | 1,795,855.11 | DATE_ORDER, ROW_BAL | second reader |
| 82 | 3 | credit | (blank) | 241,580.45 | DATE_ORDER, ROW_BAL | second reader |
| 82 | 3 | debit | 241,580.45 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 113 | 4 | balance | 6,106,103.06 | 6,106,933.06 | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | credit | 702,176.22 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | debit | (blank) | 702,176.22 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 108, page 4

```
previous balance         2,614,160.28
movement                    58,718.93
should read              2,672,879.21
transcribed balance      2,665,879.21
difference                  -7,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 05/03/2024 | (blank) | 58,718.93 | 2,665,879.21 |
| `qwen/qwen3.5-flash-02-23` | 05/03/2024 | (blank) | 58,718.93 | 2,665,879.21 |
| third reading (first reader, higher resolution) | 05/03/2024 | (blank) | 58,718.93 | 2,665,879.21 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 155 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 156 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

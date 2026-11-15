# Verification report: Type1_00078-row_removed-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:19, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 160 |
| Rule checks passed | 321 of 323 |
| Rows corrected | 3 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0577 |
| Document SHA-256 | `23ecdbd62de7f9a6` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 35 | 2 | date | 22-01-2024 10:6:42 | 22-01-2024 06:10:42 | DATE_ORDER, ROW_BAL | second reader |
| 54 | 3 | balance | Rs. 1,671,278.10 | Rs. 1,671,728.10 | DATE_ORDER, ROW_BAL | second reader |
| 138 | 5 | credit | Rs. 551.33 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 138 | 5 | debit | (blank) | Rs. 551.33 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 19, page 2

```
previous balance           918,993.78
movement                     9,588.65
should read                928,582.43
transcribed balance        977,196.65
difference                  48,614.22
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 11-01-2024 10:52:49 | (blank) | Rs. 9,588.65 | Rs. 977,196.65 |
| `qwen/qwen3.5-flash-02-23` | 11-01-2024 10:52:49 | (blank) | Rs. 9,588.65 | Rs. 977,196.65 |
| third reading (first reader, higher resolution) | 11-01-2024 10:52:49 | (blank) | Rs. 9,588.65 | Rs. 977,196.65 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 160 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

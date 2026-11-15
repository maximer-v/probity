# Verification report: Type1_00054-amount-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:99, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 164 |
| Rule checks passed | 329 of 331 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0513 |
| Document SHA-256 | `58222612a7bbf630` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 111 | 4 | credit | (blank) | Rs. 540,330.93 | DATE_ORDER, ROW_BAL | second reader |
| 111 | 4 | debit | Rs. 540,330.93 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 99, page 4

```
previous balance           274,286.15
movement                    22,017.86
should read                296,304.01
transcribed balance        298,304.01
difference                   2,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 23-02-2024 16:52:36 | (blank) | Rs. 22,017.86 | Rs. 298,304.01 |
| `qwen/qwen3.5-flash-02-23` | 23-02-2024 16:52:36 | (blank) | Rs. 22,017.86 | Rs. 298,304.01 |
| third reading (first reader, higher resolution) | 23-02-2024 16:52:36 | (blank) | Rs. 22,017.86 | Rs. 298,304.01 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 163 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 164 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

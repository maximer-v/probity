# Verification report: Type1_00063-balance-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:19, row:20, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 165 |
| Rule checks passed | 331 of 333 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0518 |
| Document SHA-256 | `9ec0b2929f646056` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 42 | 2 | credit | Rs. 13,758.46 | Rs. 13,758.58 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 19, page 2

```
previous balance         1,148,359.48
movement                    12,542.05
should read              1,160,901.53
transcribed balance      4,160,901.53
difference               3,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12-01-2024 | (blank) | Rs. 12,542.05 | Rs. 4,160,901.53 |
| `qwen/qwen3.5-flash-02-23` | 12-01-2024 14:48:08 | (blank) | Rs. 12,542.05 | Rs. 4,160,901.53 |
| third reading (first reader, higher resolution) | 12-01-2024 14:48:08 | (blank) | Rs. 12,542.05 | Rs. 4,160,901.53 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 20, page 2

```
previous balance         4,160,901.53
movement                    38,972.12
should read              4,199,873.65
transcribed balance      1,199,873.65
difference              -3,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12-01-2024 | (blank) | Rs. 38,972.12 | Rs. 1,199,873.65 |
| `qwen/qwen3.5-flash-02-23` | 12-01-2024 16:20:52 | (blank) | Rs. 38,972.12 | Rs. 1,199,873.65 |
| third reading (first reader, higher resolution) | 12-01-2024 16:20:52 | (blank) | Rs. 38,972.12 | Rs. 1,199,873.65 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 163 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 165 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

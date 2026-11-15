# Verification report: Type2_00052-balance-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:80, row:81, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 161 |
| Rule checks passed | 323 of 325 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0492 |
| Document SHA-256 | `d7194e9cf3c247c3` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 117 | 4 | credit | 9,844.88 | 9,844.89 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 80, page 3

```
previous balance           331,213.69
movement                    91,298.52
should read                422,512.21
transcribed balance        482,512.21
difference                  60,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 22/02/2024 | (blank) | 91,298.52 | 482,512.21 |
| `qwen/qwen3.5-flash-02-23` | 22/02/2024 | (blank) | 91,298.52 | 482,512.21 |
| third reading (first reader, higher resolution) | 22/02/2024 | (blank) | 91,298.52 | 482,512.21 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 81, page 3

```
previous balance           482,512.21
movement                     6,979.71
should read                489,491.92
transcribed balance        429,491.92
difference                 -60,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 22/02/2024 | (blank) | 6,979.71 | 429,491.92 |
| `qwen/qwen3.5-flash-02-23` | 22/02/2024 | (blank) | 6,979.71 | 429,491.92 |
| third reading (first reader, higher resolution) | 22/02/2024 | (blank) | 6,979.71 | 429,491.92 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 161 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

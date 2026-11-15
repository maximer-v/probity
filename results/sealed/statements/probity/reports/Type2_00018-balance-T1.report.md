# Verification report: Type2_00018-balance-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:19, row:20, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 157 |
| Rule checks passed | 315 of 317 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0487 |
| Document SHA-256 | `ea2eef192068acd5` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 114 | 4 | credit | 189,775.19 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 114 | 4 | debit | (blank) | 189,775.19 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 19, page 2

```
previous balance         1,203,455.99
movement                  -238,174.69
should read                965,281.30
transcribed balance        935,281.30
difference                 -30,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 13/01/2024 | 238,174.69 | (blank) | 935,281.30 |
| `qwen/qwen3.5-flash-02-23` | 13/01/2024 | 238,174.69 | (blank) | 935,281.30 |
| third reading (first reader, higher resolution) | 13/01/2024 | 238,174.69 | (blank) | 935,281.30 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 20, page 2

```
previous balance           935,281.30
movement                    14,732.67
should read                950,013.97
transcribed balance        980,013.97
difference                  30,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 15/01/2024 | (blank) | 14,732.67 | 980,013.97 |
| `qwen/qwen3.5-flash-02-23` | 15/01/2024 | (blank) | 14,732.67 | 980,013.97 |
| third reading (first reader, higher resolution) | 15/01/2024 | (blank) | 14,732.67 | 980,013.97 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 155 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 157 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

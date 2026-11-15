# Verification report: Type2_00044-balance-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:122, row:123, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 166 |
| Rule checks passed | 333 of 335 |
| Rows corrected | 3 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0501 |
| Document SHA-256 | `0363f9cf853f350b` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 111 | 4 | credit | 15,250,663.56 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 111 | 4 | debit | (blank) | 15,250,663.56 | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | credit | 3,648,625.00 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 115 | 4 | debit | (blank) | 3,648,625.00 | DATE_ORDER, ROW_BAL | second reader |
| 117 | 4 | credit | 2,297,645.56 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 117 | 4 | debit | (blank) | 2,297,645.56 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 122, page 5

```
previous balance         5,424,778.70
movement                 3,156,756.44
should read              8,581,535.14
transcribed balance      5,881,535.14
difference              -2,700,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12/03/2024 | (blank) | 3,156,756.44 | 5,881,535.14 |
| `qwen/qwen3.5-flash-02-23` | 12/03/2024 | (blank) | 3,156,756.44 | 5,881,535.14 |
| third reading (first reader, higher resolution) | 12/03/2024 | (blank) | 3,156,756.44 | 5,881,535.14 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 123, page 5

```
previous balance         5,881,535.14
movement                  -823,522.09
should read              5,058,013.05
transcribed balance      7,758,013.05
difference               2,700,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12/03/2024 | 823,522.09 | (blank) | 7,758,013.05 |
| `qwen/qwen3.5-flash-02-23` | 12/03/2024 | 823,522.09 | (blank) | 7,758,013.05 |
| third reading (first reader, higher resolution) | 12/03/2024 | 823,522.09 | (blank) | 7,758,013.05 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 164 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 166 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

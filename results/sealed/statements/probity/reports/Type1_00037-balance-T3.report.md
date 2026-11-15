# Verification report: Type1_00037-balance-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:16, row:17, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 157 |
| Rule checks passed | 315 of 317 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0498 |
| Document SHA-256 | `04cc355489c4fe42` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 16, page 2

```
previous balance         1,077,827.26
movement                     1,481.15
should read              1,079,308.41
transcribed balance      3,079,308.41
difference               2,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12-01-2024 10:31:14 | (blank) | Rs. 1,481.15 | Rs. 3,079,308.41 |
| `qwen/qwen3.5-flash-02-23` | 12-01-2024 10:31:14 | (blank) | Rs. 1,481.15 | Rs. 3,079,308.41 |
| third reading (first reader, higher resolution) | 12-01-2024 | (blank) | Rs. 1,481.15 | Rs. 3,079,308.41 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 17, page 2

```
previous balance         3,079,308.41
movement                   -54,690.51
should read              3,024,617.90
transcribed balance      1,024,617.90
difference              -2,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 12-01-2024 12:22:20 | Rs. 54,690.51 | (blank) | Rs. 1,024,617.90 |
| `qwen/qwen3.5-flash-02-23` | 12-01-2024 12:22:20 | Rs. 54,690.51 | (blank) | Rs. 1,024,617.90 |
| third reading (first reader, higher resolution) | 12-01-2024 | Rs. 54,690.51 | (blank) | Rs. 1,024,617.90 |

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

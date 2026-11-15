# Verification report: Type1_00049-row_removed-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:131, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 156 |
| Rule checks passed | 313 of 315 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0502 |
| Document SHA-256 | `ed9163cdc40658e1` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 131, page 5

```
previous balance         2,806,767.99
movement                   -45,257.62
should read              2,761,510.37
transcribed balance      2,717,984.39
difference                 -43,525.98
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 16-03-2024 12:21:14 | Rs. 45,257.62 | (blank) | Rs. 2,717,984.39 |
| `qwen/qwen3.5-flash-02-23` | 16-03-2024 12:21:14 | Rs. 45,257.62 | (blank) | Rs. 2,717,984.39 |
| third reading (first reader, higher resolution) | 16-03-2024 12:21:14 | Rs. 45,257.62 | (blank) | Rs. 2,717,984.39 |

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

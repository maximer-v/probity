# Verification report: Type2_00059-amount-T2

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:149, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 164 |
| Rule checks passed | 329 of 331 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0462 |
| Document SHA-256 | `7eab01b7af21a35a` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 149, page 5

```
previous balance           -65,968.95
movement                 1,310,734.47
should read              1,244,765.52
transcribed balance        944,765.52
difference                -300,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 20/03/2024 | (blank) | 1,310,734.47 | 944,765.52 |
| `qwen/qwen3.5-flash-02-23` | 20/03/2024 | (blank) | 1,310,734.47 | 944,765.52 |
| third reading (first reader, higher resolution) | 20/03/2024 | (blank) | 1,310,734.47 | 944,765.52 |

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

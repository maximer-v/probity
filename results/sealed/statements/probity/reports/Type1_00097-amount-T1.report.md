# Verification report: Type1_00097-amount-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:128, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 166 |
| Rule checks passed | 333 of 335 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0519 |
| Document SHA-256 | `9d034afc9ac6c2bf` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 128, page 5

```
previous balance           460,722.63
movement                   840,742.45
should read              1,301,465.08
transcribed balance      1,271,465.08
difference                 -30,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 16-03-2024 11:44:11 | (blank) | Rs. 840,742.45 | Rs. 1,271,465.08 |
| `qwen/qwen3.5-flash-02-23` | 16-03-2024 11:44:11 | (blank) | Rs. 840,742.45 | Rs. 1,271,465.08 |
| third reading (first reader, higher resolution) | 16-03-2024 11:44:11 | (blank) | Rs. 840,742.45 | Rs. 1,271,465.08 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 165 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 166 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

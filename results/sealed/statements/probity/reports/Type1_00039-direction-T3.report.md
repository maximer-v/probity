# Verification report: Type1_00039-direction-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:139, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 162 |
| Rule checks passed | 325 of 327 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0510 |
| Document SHA-256 | `e75bcaecc9488ea1` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 139, page 5

```
previous balance         5,037,883.72
movement                   689,228.83
should read              5,727,112.55
transcribed balance      4,348,654.89
difference              -1,378,457.66
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 15-03-2024 10:19:41 | (blank) | Rs. 689,228.83 | Rs. 4,348,654.89 |
| `qwen/qwen3.5-flash-02-23` | 15-03-2024 10:19:41 | (blank) | Rs. 689,228.83 | Rs. 4,348,654.89 |
| third reading (first reader, higher resolution) | 15-03-2024 10:19:41 | (blank) | Rs. 689,228.83 | Rs. 4,348,654.89 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 161 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 162 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

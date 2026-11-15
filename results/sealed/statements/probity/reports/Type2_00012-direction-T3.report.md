# Verification report: Type2_00012-direction-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:110, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 161 |
| Rule checks passed | 323 of 325 |
| Rows corrected | 4 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 4 |
| Model cost | $0.0554 |
| Document SHA-256 | `a096a851b10f39e2` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 23 | 2 | balance | 339,451.06 | 339,451.09 | DATE_ORDER, ROW_BAL | second reader |
| 62 | 3 | balance | 263,385.67 | 263,385.57 | DATE_ORDER, ROW_BAL | second reader |
| 101 | 4 | balance | 1,376,151.40 | 1,376,151.03 | DATE_ORDER, ROW_BAL | second reader |
| 150 | 5 | credit | 187,374.57 | 187,374.51 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 110, page 4

```
previous balance         2,656,232.75
movement                    50,244.47
should read              2,706,477.22
transcribed balance      2,605,988.28
difference                -100,488.94
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 04/03/2024 | (blank) | 50,244.47 | 2,605,988.28 |
| `qwen/qwen3.5-flash-02-23` | 04/03/2024 | (blank) | 50,244.47 | 2,605,988.28 |
| third reading (first reader, higher resolution) | 04/03/2024 | (blank) | 50,244.47 | 2,605,988.28 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 160 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 161 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

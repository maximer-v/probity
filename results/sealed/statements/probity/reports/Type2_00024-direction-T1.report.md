# Verification report: Type2_00024-direction-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:111, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 162 |
| Rule checks passed | 325 of 327 |
| Rows corrected | 20 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 5 |
| Model cost | $0.0579 |
| Document SHA-256 | `fd5f7d345925c31a` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 0 | 1 | debit | (blank) | 1,418,951.74 | DATE_ORDER, ROW_BAL | second reader |
| 1 | 1 | credit | (blank) | 437,925.72 | DATE_ORDER, ROW_BAL | second reader |
| 2 | 1 | credit | (blank) | 398,558.91 | DATE_ORDER, ROW_BAL | second reader |
| 3 | 1 | credit | (blank) | 913,768.29 | DATE_ORDER, ROW_BAL | second reader |
| 4 | 1 | debit | (blank) | 14,585.41 | DATE_ORDER, ROW_BAL | second reader |
| 5 | 1 | credit | (blank) | 20,792.19 | DATE_ORDER, ROW_BAL | second reader |
| 6 | 1 | credit | (blank) | 68,087.78 | DATE_ORDER, ROW_BAL | second reader |
| 7 | 1 | credit | (blank) | 2,994,113.65 | DATE_ORDER, ROW_BAL | second reader |
| 8 | 1 | credit | (blank) | 542,842.68 | DATE_ORDER, ROW_BAL | second reader |
| 9 | 1 | debit | (blank) | 3,093,602.62 | DATE_ORDER, ROW_BAL | second reader |
| 10 | 1 | credit | (blank) | 1,075,964.86 | DATE_ORDER, ROW_BAL | second reader |
| 11 | 1 | debit | (blank) | 268,174.06 | DATE_ORDER, ROW_BAL | second reader |
| 12 | 1 | debit | (blank) | 4,585,728.98 | DATE_ORDER, ROW_BAL | second reader |
| 13 | 1 | credit | (blank) | 4,796,606.77 | DATE_ORDER, ROW_BAL | second reader |
| 14 | 1 | credit | (blank) | 4,763,444.09 | DATE_ORDER, ROW_BAL | second reader |
| 15 | 1 | credit | (blank) | 1,173,507.09 | DATE_ORDER, ROW_BAL | second reader |
| 26 | 2 | balance | 3,023,672.62 | 3,023,673.62 | DATE_ORDER, ROW_BAL | second reader |
| 80 | 3 | credit | (blank) | 792,387.77 | DATE_ORDER, ROW_BAL | second reader |
| 80 | 3 | debit | 792,387.77 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 96 | 4 | credit | (blank) | 250,399.42 | DATE_ORDER, ROW_BAL | second reader |
| 96 | 4 | debit | 250,399.42 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 147 | 5 | credit | 634,743.33 CR | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 147 | 5 | debit | (blank) | 634,743.33 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 111, page 4

```
previous balance         1,222,865.32
movement                  -144,755.53
should read              1,078,109.79
transcribed balance      1,367,620.85
difference                 289,511.06
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 05/03/2024 | 144,755.53 | (blank) | 1,367,620.85 |
| `qwen/qwen3.5-flash-02-23` | 05/03/2024 | 144,755.53 | (blank) | 1,367,620.85 |
| third reading (first reader, higher resolution) | 05/03/2024 | 144,755.53 | (blank) | 1,367,620.85 |

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

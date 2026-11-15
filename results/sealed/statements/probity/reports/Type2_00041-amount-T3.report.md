# Verification report: Type2_00041-amount-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:3, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 160 |
| Rule checks passed | 321 of 323 |
| Rows corrected | 7 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 4 |
| Model cost | $0.0513 |
| Document SHA-256 | `89333308f5a177d2` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 100 | 4 | balance | 7,414,982.92 | 7,414,982.94 | DATE_ORDER, ROW_BAL | second reader |
| 140 | 5 | credit | 1,186,030.19 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 140 | 5 | debit | (blank) | 1,186,030.19 | DATE_ORDER, ROW_BAL | second reader |
| 143 | 5 | credit | 1,577,705.20 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 143 | 5 | debit | (blank) | 1,577,705.20 | DATE_ORDER, ROW_BAL | second reader |
| 156 | 6 | debit | (blank) | 244.46 | DATE_ORDER, ROW_BAL | second reader |
| 157 | 6 | credit | (blank) | 13,583,890.16 | DATE_ORDER, ROW_BAL | second reader |
| 158 | 6 | debit | (blank) | 11,747,738.19 | DATE_ORDER, ROW_BAL | second reader |
| 159 | 6 | credit | (blank) | 905,482.58 | DATE_ORDER, LAST_ROW_EQ_CLOSING, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 3, page 1

```
previous balance         3,626,144.70
movement                 3,056,220.97
should read              6,682,365.67
transcribed balance      8,682,365.67
difference               2,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 02/01/2024 | (blank) | 3,056,220.97 | 8,682,365.67 |
| `qwen/qwen3.5-flash-02-23` | 02/01/2024 | (blank) | 3,056,220.97 CR | 8,682,365.67 |
| third reading (first reader, higher resolution) | 02/01/2024 | (blank) | 3,056,220.97 | 8,682,365.67 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 160 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

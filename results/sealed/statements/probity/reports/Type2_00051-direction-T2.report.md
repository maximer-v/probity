# Verification report: Type2_00051-direction-T2

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:116, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 162 |
| Rule checks passed | 325 of 327 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0502 |
| Document SHA-256 | `01f724c311beac90` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 78 | 3 | balance | 608,459.82 | 608,459.84 | DATE_ORDER, ROW_BAL | second reader |
| 100 | 4 | credit | (blank) | 287,730.91 | DATE_ORDER, ROW_BAL | second reader |
| 100 | 4 | debit | 287,730.91 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 116, page 4

```
previous balance         1,672,095.38
movement                   762,290.89
should read              2,434,386.27
transcribed balance        909,804.49
difference              -1,524,581.78
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 05/03/2024 | (blank) | 762,290.89 | 909,804.49 |
| `qwen/qwen3.5-flash-02-23` | 05/03/2024 | (blank) | 762,290.89 | 909,804.49 |
| third reading (first reader, higher resolution) | 05/03/2024 | (blank) | 762,290.89 | 909,804.49 |

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

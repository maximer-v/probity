# Verification report: Type2_00063-amount-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:10, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 164 |
| Rule checks passed | 329 of 331 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0485 |
| Document SHA-256 | `44e359d7ec8627b9` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 77 | 3 | credit | 822,867.63 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 77 | 3 | debit | (blank) | 822,867.63 | DATE_ORDER, ROW_BAL | second reader |
| 119 | 4 | credit | 220,104.82 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 119 | 4 | debit | (blank) | 220,104.82 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 10, page 1

```
previous balance           217,506.96
movement                     2,886.37
should read                220,393.33
transcribed balance        219,693.33
difference                    -700.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 04/01/2024 | (blank) | 2,886.37 | 219,693.33 |
| `qwen/qwen3.5-flash-02-23` | 04/01/2024 | (blank) | 2,886.37 | 219,693.33 |
| third reading (first reader, higher resolution) | 04/01/2024 | (blank) | 2,886.37 | 219,693.33 |

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

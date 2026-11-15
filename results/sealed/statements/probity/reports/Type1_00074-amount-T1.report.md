# Verification report: Type1_00074-amount-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:61, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 172 |
| Rule checks passed | 345 of 347 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0539 |
| Document SHA-256 | `b2c61d2c3fe82b72` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 73 | 3 | credit | (blank) | Rs. 11,762.31 | DATE_ORDER, ROW_BAL | second reader |
| 73 | 3 | debit | Rs. 11,762.31 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 61, page 3

```
previous balance            90,698.22
movement                   146,183.86
should read                236,882.08
transcribed balance        237,512.08
difference                     630.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 05-02-2024 11:22:01 | (blank) | Rs. 146,183.86 | Rs. 237,512.08 |
| `qwen/qwen3.5-flash-02-23` | 05-02-2024 11:22:01 | (blank) | Rs. 146,183.86 | Rs. 237,512.08 |
| third reading (first reader, higher resolution) | 05-02-2024 11:22:01 | (blank) | Rs. 146,183.86 | Rs. 237,512.08 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 171 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 172 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

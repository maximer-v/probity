# Verification report: agami-Digital_Type1_00006-scan-tampered

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:96, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 159 |
| Rule checks passed | 319 of 321 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0000 |
| Document SHA-256 | `8585b41d54237bd0` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 70 | 3 | credit | (blank) | Rs. 1,037,009.01 | DATE_ORDER, ROW_BAL | second reader |
| 70 | 3 | debit | Rs. 1,037,009.01 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 99 | 4 | credit | (blank) | Rs. 155,786.43 | DATE_ORDER, ROW_BAL | second reader |
| 99 | 4 | debit | Rs. 155,786.43 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 96, page 4

```
previous balance         1,049,893.55
movement                   769,207.54
should read              1,819,101.09
transcribed balance      1,759,101.09
difference                 -60,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 27-02-2024 07:47:53 | (blank) | Rs. 769,207.54 | Rs. 1,759,101.09 |
| `qwen/qwen3.5-flash-02-23` | 27-02-2024 07:47:53 | (blank) | Rs. 769,207.54 | Rs. 1,759,101.09 |
| third reading (first reader, higher resolution) | 27-02-2024 07:47:53 | (blank) | Rs. 769,207.54 | Rs. 1,759,101.09 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 158 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 159 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

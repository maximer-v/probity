# Verification report: agami-Digital_Type1_00008-scan-tampered

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:148, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 166 |
| Rule checks passed | 333 of 335 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0000 |
| Document SHA-256 | `dd24d28360feb90e` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 39 | 2 | credit | Rs. 30,667.05 | Rs. 30,667.54 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 148, page 6

```
previous balance           226,322.60
movement                    -1,282.22
should read                225,040.38
transcribed balance        222,040.38
difference                  -3,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 22-03-2024 13:12:52 | Rs. 1,282.22 | (blank) | Rs. 222,040.38 |
| `qwen/qwen3.5-flash-02-23` | 22-03-2024 13:12:52 | Rs. 1,282.22 | (blank) | Rs. 222,040.38 |
| third reading (first reader, higher resolution) | 22-03-2024 13:12:52 | Rs. 1,282.22 | (blank) | Rs. 222,040.38 |

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

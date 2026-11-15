# Verification report: Type1_00080-row_removed-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:88, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 163 |
| Rule checks passed | 327 of 329 |
| Rows corrected | 4 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0563 |
| Document SHA-256 | `282b5ff142381039` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 95 | 4 | balance | Rs. 516,198.85 | Rs. 516,198.64 | DATE_ORDER, ROW_BAL | second reader |
| 129 | 5 | balance | Rs. 1,151,498.20 | Rs. 1,151,498.40 | DATE_ORDER, ROW_BAL | second reader |
| 131 | 5 | balance | Rs. 2,529,833.55 | Rs. 2,529,833.95 | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | credit | (blank) | Rs. 481,550.57 | DATE_ORDER, ROW_BAL | second reader |
| 141 | 5 | debit | Rs. 481,550.57 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 88, page 4

```
previous balance           521,605.00
movement                   293,831.92
should read                815,436.92
transcribed balance        676,094.60
difference                -139,342.32
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 20-02-2024 16:01:04 | (blank) | Rs. 293,831.92 | Rs. 676,094.60 |
| `qwen/qwen3.5-flash-02-23` | 20-02-2024 16:01:04 | (blank) | Rs. 293,831.92 | Rs. 676,094.60 |
| third reading (first reader, higher resolution) | 20-02-2024 16:01:04 | (blank) | Rs. 293,831.92 | Rs. 676,094.60 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

The closing total is off by exactly the amount the row(s) above are off by, so it is the same finding and not a separate one.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 162 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 163 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

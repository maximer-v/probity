# Verification report: agami-Digital_Type2_00008-scan-tampered

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:53, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 159 |
| Rule checks passed | 319 of 321 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0000 |
| Document SHA-256 | `4a995960d8134ee1` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 104 | 4 | credit | (blank) | 15,742,047.29 | DATE_ORDER, ROW_BAL | second reader |
| 104 | 4 | debit | 15,742,047.29 | (blank) | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 53, page 2

```
previous balance        12,808,827.07
movement                -2,986,462.63
should read              9,822,364.44
transcribed balance      9,822,360.84
difference                      -3.60
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 31/01/2024 | 2,986,462.63 | (blank) | 9,822,360.84 |
| `qwen/qwen3.5-flash-02-23` | 31/01/2024 | 2,986,462.63 | (blank) | 9,822,360.84 |
| third reading (first reader, higher resolution) | 31/01/2024 | 2,986,462.63 | (blank) | 9,822,360.84 |

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

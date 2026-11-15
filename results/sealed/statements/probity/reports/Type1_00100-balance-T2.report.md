# Verification report: Type1_00100-balance-T2

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:38, row:39, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 163 |
| Rule checks passed | 327 of 329 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0555 |
| Document SHA-256 | `91e389ead28cab0a` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 138 | 5 | balance | Rs. 177,652.78 | Rs. 177,652.70 | DATE_ORDER, ROW_BAL | second reader |
| 148 | 6 | balance | Rs. 547,931.94 | Rs. 547,931.95 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 38, page 2

```
previous balance           -20,700.36
movement                   131,770.73
should read                111,070.37
transcribed balance        181,070.37
difference                  70,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 22-01-2024 07:47:26 | (blank) | Rs. 131,770.73 | Rs. 181,070.37 |
| `qwen/qwen3.5-flash-02-23` | 22-01-2024 07:47:26 | (blank) | Rs. 131,770.73 | Rs. 181,070.37 |
| third reading (first reader, higher resolution) | 22-01-2024 07:47:26 | (blank) | Rs. 131,770.73 | Rs. 181,070.37 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 39, page 2

```
previous balance           181,070.37
movement                    -7,709.67
should read                173,360.70
transcribed balance        103,360.70
difference                 -70,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 22-01-2024 13:05:56 | Rs. 7,709.67 | (blank) | Rs. 103,360.70 |
| `qwen/qwen3.5-flash-02-23` | 22-01-2024 13:05:56 | Rs. 7,709.67 | (blank) | Rs. 103,360.70 |
| third reading (first reader, higher resolution) | 22-01-2024 13:05:56 | Rs. 7,709.67 | (blank) | Rs. 103,360.70 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 161 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 163 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

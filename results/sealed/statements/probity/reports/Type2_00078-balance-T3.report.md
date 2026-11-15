# Verification report: Type2_00078-balance-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:154, row:155, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 158 |
| Rule checks passed | 317 of 319 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 3 |
| Model cost | $0.0529 |
| Document SHA-256 | `0ccb349f37fee999` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 40 | 2 | credit | 6,870,509.72 | (blank) | DATE_ORDER, ROW_BAL | second reader |
| 40 | 2 | debit | (blank) | 6,870,509.72 | DATE_ORDER, ROW_BAL | second reader |
| 95 | 4 | balance | 3,669,253.07 | 3,669,253.08 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 154, page 5

```
previous balance        19,808,939.23
movement                  -876,090.61
should read             18,932,848.62
transcribed balance     19,932,848.62
difference               1,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 28/03/2024 | 876,090.61 | (blank) | 19,932,848.62 |
| `qwen/qwen3.5-flash-02-23` | 28/03/2024 | 876,090.61 | (blank) | 19,932,848.62 |
| third reading (first reader, higher resolution) | 28/03/2024 | 876,090.61 | (blank) | 19,932,848.62 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 155, page 5

```
previous balance        19,932,848.62
movement               -18,689,515.76
should read              1,243,332.86
transcribed balance        243,332.86
difference              -1,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 28/03/2024 | 18,689,515.76 | (blank) | 243,332.86 |
| `qwen/qwen3.5-flash-02-23` | 28/03/2024 | 18,689,515.76 | (blank) | 243,332.86 |
| third reading (first reader, higher resolution) | 28/03/2024 | 18,689,515.76 | (blank) | 243,332.86 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 156 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 158 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

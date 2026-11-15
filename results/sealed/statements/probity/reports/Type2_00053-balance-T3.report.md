# Verification report: Type2_00053-balance-T3

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:147, row:148, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 162 |
| Rule checks passed | 325 of 327 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0486 |
| Document SHA-256 | `d489de2baa0d64d7` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 73 | 3 | credit | 912,466.44 | 912,466.45 | DATE_ORDER, ROW_BAL | second reader |
| 130 | 5 | balance | 1,190,662.79 | 1,190,662.72 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 147, page 5

```
previous balance           617,140.74
movement                  -235,159.55
should read                381,981.19
transcribed balance        311,981.19
difference                 -70,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 22/03/2024 | 235,159.55 | (blank) | 311,981.19 |
| `qwen/qwen3.5-flash-02-23` | 22/03/2024 | 235,159.55 | (blank) | 311,981.19 |
| third reading (first reader, higher resolution) | 22/03/2024 | 235,159.55 | (blank) | 311,981.19 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 148, page 5

```
previous balance           311,981.19
movement                  -104,381.36
should read                207,599.83
transcribed balance        277,599.83
difference                  70,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 22/03/2024 | 104,381.36 | (blank) | 277,599.83 |
| `qwen/qwen3.5-flash-02-23` | 22/03/2024 | 104,381.36 | (blank) | 277,599.83 |
| third reading (first reader, higher resolution) | 22/03/2024 | 104,381.36 | (blank) | 277,599.83 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 160 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 162 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

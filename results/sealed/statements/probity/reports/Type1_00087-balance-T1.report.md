# Verification report: Type1_00087-balance-T1

**DOCUMENT INCONSISTENT: two readers agree on the reading, and as read the document breaks a rule**

Reason: the rules fail at row:152, row:153, and two readers agree on what is printed there and on the balance carried into it.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 160 |
| Rule checks passed | 321 of 323 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0440 |
| Document SHA-256 | `ae930b2aff5735c4` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 152, page 6

```
previous balance         1,505,248.94
movement                  -125,222.28
should read              1,380,026.66
transcribed balance      7,380,026.66
difference               6,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 27-03-2024 18:38:49 | Rs. 125,222.28 | (blank) | Rs. 7,380,026.66 |
| `qwen/qwen3.5-flash-02-23` | 27-03-2024 18:38:49 | Rs. 125,222.28 | (blank) | Rs. 7,380,026.66 |
| third reading (first reader, higher resolution) | 27-03-2024 18:38:49 | Rs. 125,222.28 | (blank) | Rs. 7,380,026.66 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

### Row 153, page 6

```
previous balance         7,380,026.66
movement                    97,013.22
should read              7,477,039.88
transcribed balance      1,477,039.88
difference              -6,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 28-03-2024 07:56:10 | (blank) | Rs. 97,013.22 | Rs. 1,477,039.88 |
| `qwen/qwen3.5-flash-02-23` | 28-03-2024 07:56:10 | (blank) | Rs. 97,013.22 | Rs. 1,477,039.88 |
| third reading (first reader, higher resolution) | 28-03-2024 07:56:10 | (blank) | Rs. 97,013.22 | Rs. 1,477,039.88 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 158 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 160 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

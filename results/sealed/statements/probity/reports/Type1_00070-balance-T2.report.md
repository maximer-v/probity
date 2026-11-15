# Verification report: Type1_00070-balance-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:4.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 156 |
| Rule checks passed | 313 of 315 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0468 |
| Document SHA-256 | `7e4b6b472bd63491` |

## Corrections

Values read by `google/gemini-3.1-flash-lite` on rows where a rule failed, read again independently by `qwen/qwen3.5-flash-02-23`, and replaced because the rule then passed and no other check failed. The rule selects the value; it does not prove what is printed.

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 39 | 2 | credit | Rs. 252,692.69 | Rs. 252,692.61 | DATE_ORDER, ROW_BAL | second reader |

## Rows where both readers agree and a rule fails

### Row 5, page 1

```
previous balance         1,170,108.37
movement                   -19,593.34
should read              1,150,515.03
transcribed balance      1,151,415.03
difference                     900.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 04-01-2024 14:10:32 | Rs. 19,593.34 | (blank) | Rs. 1,151,415.03 |
| `qwen/qwen3.5-flash-02-23` | 04-01-2024 14:10:32 | Rs. 19,593.34 | (blank) | Rs. 1,151,415.03 |
| third reading (first reader, higher resolution) | 04-01-2024 14:10:32 | Rs. 19,593.34 | (blank) | Rs. 1,151,415.03 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## For a person to check

- row 4, page 1, ROW_BAL: row 4: 101870098 + 15230739 = 117100837, but the balance column reads 117010837 (off by -90000)
  - second look (DISPUTED): row 3, which this row's rule is computed from, could not be matched in the second reading

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 154 | 2 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 156 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

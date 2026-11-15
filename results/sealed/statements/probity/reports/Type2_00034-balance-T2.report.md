# Verification report: Type2_00034-balance-T2

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:148.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 161 |
| Rule checks passed | 322 of 325 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 1 |
| Model cost | $0.0473 |
| Document SHA-256 | `373495db80f64f23` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 149, page 5

```
previous balance        14,522,201.95
movement                  -582,002.71
should read             13,940,199.24
transcribed balance     13,940,208.24
difference                       9.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 26/03/2024 | 582,002.71 | (blank) | 13,940,208.24 |
| `qwen/qwen3.5-flash-02-23` | 26/03/2024 | 582,002.71 | (blank) | 13,940,208.24 |
| third reading (first reader, higher resolution) | 26/03/2024 | 582,002.71 | (blank) | 13,940,208.24 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## For a person to check

- row 148, page 5, ROW_BAL: row 148: 1610902584 + -158618489 = 1452284095, but the balance column reads 1452220195 (off by -63900)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 26/03/2024 / 1,586,184.89 / (blank) / 14,522,201.95; second reader 26/03/2024 / 1,586,814.89 / (blank) / 14,522,201.95 (date / debit / credit / balance)
- document, GLOBAL_BAL: opening 397643764 + movements 280029813 = 677673577, closing balance reads 677610577

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 2 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 161 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

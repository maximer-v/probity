# Verification report: Type2_00083-amount-T1

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:63.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 161 |
| Rule checks passed | 322 of 325 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Calls to `qwen/qwen3.5-flash-02-23` | 2 |
| Model cost | $0.0507 |
| Document SHA-256 | `709d83f6ede92da0` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

### Row 30, page 2

```
previous balance         6,019,102.44
movement                 6,097,027.15
should read             12,116,129.59
transcribed balance      7,116,129.59
difference              -5,000,000.00
```

| Reader | Date | Debit | Credit | Balance |
|---|---|---|---|---|
| `google/gemini-3.1-flash-lite` | 16/01/2024 | (blank) | 6,097,027.15 | 7,116,129.59 |
| `qwen/qwen3.5-flash-02-23` | 16/01/2024 | (blank) | 6,097,027.15 | 7,116,129.59 |
| third reading (first reader, higher resolution) | 16/01/2024 | (blank) | 6,097,027.15 | 7,116,129.59 |

Both readers transcribed the same figures here and the same balance carried in, and a third reading has them too. As transcribed, the statement does not add up at this row.

## For a person to check

- row 63, page 3, ROW_BAL: row 63: 669249262 + -45261783 = 623987479, but the balance column reads 714511045 (off by 90523566)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 31/01/2024 / 452,617.83 / (blank) / 7,145,110.45; second reader 31/01/2024 / (blank) / (blank) / 7,145,110.45 (date / debit / credit / balance)
- document, GLOBAL_BAL: opening 212565416 + movements 585776308 = 798341724, closing balance reads 388865290

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

# Verification report: Type2_00069-amount_adjusted-T2

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 165 |
| Rule checks passed | 333 of 333 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 6 |
| Model cost | $0.0361 |
| Document SHA-256 | `41217d4df183c404` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 165 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 165 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

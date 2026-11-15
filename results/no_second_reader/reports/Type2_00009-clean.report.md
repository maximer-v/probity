# Verification report: agami-Digital_Type2_00009-scan-repaired

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 2 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 163 |
| Rule checks passed | 329 of 329 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `24156fc59e3810b4` |

## Corrections

4 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 79 | 3 | credit | 5,591,109.58 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 79 | 3 | debit | (blank) | 5,591,109.58 | DATE_ORDER, ROW_BAL | same reader |
| 85 | 4 | credit | (blank) | 16,062,965.88 | DATE_ORDER, ROW_BAL | same reader |
| 85 | 4 | debit | 16,062,965.88 | (blank) | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 163 | 0 |
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

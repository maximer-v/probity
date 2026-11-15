# Verification report: agami-Digital_Type1_00009-scan-repaired

**CONFIRMED: every rule passes on the final reading**

Reason: every rule passed; 1 row(s) were corrected on the way.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 159 |
| Rule checks passed | 321 of 321 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Model cost | $0.0000 |
| Document SHA-256 | `572fd46b1492d80a` |

## Corrections

2 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 78 | 3 | credit | (blank) | Rs. 307,788.17 | DATE_ORDER, ROW_BAL | same reader |
| 78 | 3 | debit | Rs. 307,788.17 | (blank) | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 159 | 0 |
| GLOBAL_BAL | 1 | 0 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 159 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

# Verification report: agami-Digital_Type1_00010-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:22.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 167 |
| Rule checks passed | 335 of 337 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `514323e1539320a8` |

## Corrections

2 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 2 | 1 | credit | (blank) | Rs. 731,194.73 | DATE_ORDER, ROW_BAL | same reader |
| 2 | 1 | debit | Rs. 731,194.73 | (blank) | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 22, page 2, ROW_BAL: row 22: 187196489 + 89772415 = 276968904, but the balance column reads 274968904 (off by -2000000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 97544129 + movements 101466883 = 199011012, closing balance reads 197011012

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 166 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 167 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

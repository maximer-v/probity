# Verification report: agami-Digital_Type1_00008-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:148.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 166 |
| Rule checks passed | 333 of 335 |
| Rows corrected | 1 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `dd24d28360feb90e` |

## Corrections

1 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 39 | 2 | credit | Rs. 30,667.05 | Rs. 30,667.54 | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 148, page 6, ROW_BAL: row 148: 22632260 + -128222 = 22504038, but the balance column reads 22204038 (off by -300000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 47724656 + movements -1525553 = 46199103, closing balance reads 45899103

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 165 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 166 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

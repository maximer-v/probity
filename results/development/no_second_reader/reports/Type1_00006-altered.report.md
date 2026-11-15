# Verification report: agami-Digital_Type1_00006-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:96.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 159 |
| Rule checks passed | 319 of 321 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `8585b41d54237bd0` |

## Corrections

4 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 70 | 3 | credit | (blank) | Rs. 1,037,009.01 | DATE_ORDER, ROW_BAL | same reader |
| 70 | 3 | debit | Rs. 1,037,009.01 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 99 | 4 | credit | (blank) | Rs. 155,786.43 | DATE_ORDER, ROW_BAL | same reader |
| 99 | 4 | debit | Rs. 155,786.43 | (blank) | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 96, page 4, ROW_BAL: row 96: 104989355 + 76920754 = 181910109, but the balance column reads 175910109 (off by -6000000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 31432561 + movements 100774296 = 132206857, closing balance reads 126206857

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 158 | 1 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 159 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

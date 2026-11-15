# Verification report: agami-Digital_Type2_00002-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:69, row:70, row:77, row:127.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 167 |
| Rule checks passed | 332 of 337 |
| Rows corrected | 4 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `fdca935188108f2d` |

## Corrections

8 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 73 | 3 | credit | (blank) | 7,066,847.42 | DATE_ORDER, ROW_BAL | same reader |
| 73 | 3 | debit | 7,066,847.42 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 78 | 3 | credit | 5,637,798.30 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 78 | 3 | debit | (blank) | 5,637,798.30 | DATE_ORDER, ROW_BAL | same reader |
| 135 | 5 | credit | 2,105,191.83 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 135 | 5 | debit | (blank) | 2,105,191.83 | DATE_ORDER, ROW_BAL | same reader |
| 148 | 5 | credit | (blank) | 115,417.78 | DATE_ORDER, ROW_BAL | same reader |
| 148 | 5 | debit | 115,417.78 | (blank) | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 69, page 3, ROW_BAL: row 69: 807096948 + -287011504 = 520085444, but the balance column reads 520085440 (off by -4)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 06/02/2024 / 2,870,115.04 / (blank) / 5,200,854.40; second reader 06/02/2024 / (blank) / 2,870,115.04 / 5,200,854.44 (date / debit / credit / balance)
- row 70, page 3, ROW_BAL: row 70: 520085440 + -203887164 = 316198276, but the balance column reads 316198280 (off by 4)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 77, page 3, ROW_BAL: row 77: 51122872 + -565374836 = -514251964, but the balance column reads 616497708 (off by 1130749672)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 127, page 5, ROW_BAL: row 127: 451886831 + -2382371 = 449504460, but the balance column reads 442504460 (off by -7000000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 258125025 + movements -592948673 = -334823648, closing balance reads 788926024

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 163 | 4 |
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

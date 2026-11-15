# Verification report: agami-Digital_Type2_00004-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:42, row:82, row:108, row:115.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 156 |
| Rule checks passed | 310 of 315 |
| Rows corrected | 2 |
| Calls to `google/gemini-3.1-flash-lite` | 9 |
| Model cost | $0.0000 |
| Document SHA-256 | `93bcc343a3b6064d` |

## Corrections

3 value(s) below were changed by the first reader re-reading the page itself, with no second reader behind them (marked *same reader*).

| Row | Page | Field | First reading | Changed to | Passing rules | By |
|---:|---:|---|---|---|---|---|
| 81 | 3 | credit | 1,795,855.11 | (blank) | DATE_ORDER, ROW_BAL | same reader |
| 81 | 3 | debit | (blank) | 1,795,855.11 | DATE_ORDER, ROW_BAL | same reader |
| 113 | 4 | balance | 6,106,103.06 | 6,106,933.06 | DATE_ORDER, ROW_BAL | same reader |

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 42, page 2, ROW_BAL: row 42: 47243773 + 3937130 = 51180903, but the balance column reads 43306643 (off by -7874260)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 82, page 3, ROW_BAL: row 82: 351416880 + -24158045 = 327258835, but the balance column reads 375574925 (off by 48316090)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 108, page 4, ROW_BAL: row 108: 261416028 + 5871893 = 267287921, but the balance column reads 266587921 (off by -700000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 115, page 4, ROW_BAL: row 115: 681101731 + 70217622 = 751319353, but the balance column reads 610884109 (off by -140435244)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 219780925 + movements 160450226 = 380231151, closing balance reads 279537737

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 152 | 4 |
| GLOBAL_BAL | 0 | 1 |
| LAST_ROW_EQ_CLOSING | 1 | 0 |
| DATE_ORDER | 156 | 0 |
| NO_DUP_ROW | 1 | 0 |

## What this report does not establish

- that the document is authentic, or that a corrected value is what is printed: the rules establish that the reading is consistent
- an amount altered together with every later balance, so the document remains internally exact and every value is printed on the page
- a set of transactions removed from the reading whose amounts cancel, leaving every remaining balance consistent
- on a scanned page, a transcription that is internally consistent but wrong
- a statement fabricated in full from a consistent ledger

# Verification report: agami-Digital_Type2_00008-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:53, row:104.

| | |
|---|---|
| Pages read | 5 |
| Rows read | 159 |
| Rule checks passed | 318 of 321 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `4a995960d8134ee1` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 53, page 2, ROW_BAL: row 53: 1280882707 + -298646263 = 982236444, but the balance column reads 982236084 (off by -360)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 104, page 4, ROW_BAL: row 104: 234709471 + -1574204729 = -1339495258, but the balance column reads 1808914200 (off by 3148409458)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 432893644 + movements -2750627863 = -2317734219, closing balance reads 830674879

## Rules

| Rule | Passed | Failed |
|---|---:|---:|
| ROW_BAL | 157 | 2 |
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

# Verification report: agami-Digital_Type1_00002-scan-tampered

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:6, row:74.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 161 |
| Rule checks passed | 322 of 325 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 8 |
| Model cost | $0.0000 |
| Document SHA-256 | `51150bea4286f1b0` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 6, page 1, ROW_BAL: row 6: 610130512 + -789076432 = -178945920, but the balance column reads 321054080 (off by 500000000)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- row 74, page 3, ROW_BAL: row 74: 500750539 + 25289291 = 526039830, but the balance column reads 526039831 (off by 1)
  - second look (DISPUTED): the two readings disagree on this row and the second does not satisfy the rule without breaking another, so both are shown and neither is used
  - first reader 12-02-2024 / (blank) / Rs. 252,892.91 / Rs. 5,260,398.31; second reader 12-02-2024 / (blank) / Rs. 252,892.05 / Rs. 5,260,398.31 (date / debit / credit / balance)
- document, GLOBAL_BAL: opening 77922650 + movements -329703032 = -251780382, closing balance reads 248219619

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

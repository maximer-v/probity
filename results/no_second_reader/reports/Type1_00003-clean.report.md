# Verification report: agami-Digital_Type1_00003-scan-repaired

**UNRESOLVED: a rule fails and the reading could not be confirmed; a person has to look**

Reason: not confirmed by a second reading: row:104.

| | |
|---|---|
| Pages read | 6 |
| Rows read | 159 |
| Rule checks passed | 319 of 321 |
| Rows corrected | 0 |
| Calls to `google/gemini-3.1-flash-lite` | 7 |
| Model cost | $0.0000 |
| Document SHA-256 | `c0253e53f5d066c0` |

## Corrections

None. No value of the first reading was changed.

## Rows where both readers agree and a rule fails

None.

## For a person to check

- row 104, page 4, ROW_BAL: row 104: 37403820 + 573984 = 37977804, but the balance column reads 37977814 (off by 10)
  - second look (REPEATED): the first reader transcribed the same figures again. That is the same opinion twice and confirms nothing
- document, GLOBAL_BAL: opening 20104975 + movements -10655483 = 9449492, closing balance reads 9449502

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
